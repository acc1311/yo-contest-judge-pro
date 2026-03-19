#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Universal Log Parser
Suporta: ADIF (.adi/.adif), Cabrillo 2.0/3.0 (.log/.cbr),
         CSV (.csv), JSON (.json), EDI (.edi — VHF contests)
"""
import re
import csv
import json
import io
import os
from core.contest_rules import freq_to_band

# ── Template QSO ──────────────────────────────────────────────
def _empty():
    return {
        "callsign":"", "freq":"", "band":"", "mode":"",
        "rst_s":"",  "rst_r":"", "date":"", "time":"",
        "exchange":"", "note":"", "dxcc":"", "serial":"",
        "locator":"", "my_call":"", "_line":0, "_raw":"", "_fmt":"",
    }

# ══════════════════════ ADIF ══════════════════════════════════
def _af(tag, text):
    m = re.search(r'<'+re.escape(tag)+r':(\d+)(?::[^>]*)?>([^<]*)', text, re.I)
    return m.group(2)[:int(m.group(1))].strip() if m else ""

def _adif(text):
    qsos, errs = [], []
    eoh = re.search(r'<EOH>', text, re.I)
    body = text[eoh.end():] if eoh else text
    for ln, rec in enumerate(re.split(r'<EOR>', body, flags=re.I), 1):
        rec = rec.strip()
        if not rec:
            continue
        q = _empty(); q["_line"] = ln; q["_raw"] = rec[:120]; q["_fmt"] = "adif"
        q["callsign"] = _af("CALL", rec).upper()
        q["freq"]     = _af("FREQ", rec)
        q["band"]     = _af("BAND", rec).lower()
        q["mode"]     = _af("MODE", rec).upper()
        q["rst_s"]    = _af("RST_SENT", rec)
        q["rst_r"]    = _af("RST_RCVD", rec)
        q["exchange"] = _af("STX_STRING", rec) or _af("SRX_STRING", rec)
        q["locator"]  = _af("GRIDSQUARE", rec).upper()
        q["serial"]   = _af("STX", rec)
        q["note"]     = _af("COMMENT", rec) or _af("NOTES", rec)
        q["dxcc"]     = _af("DXCC", rec) or _af("COUNTRY", rec)
        if q["freq"]:
            try: q["freq"] = str(round(float(q["freq"]) * 1000, 1))
            except ValueError: pass
        if not q["band"] and q["freq"]:
            q["band"] = freq_to_band(q["freq"]) or ""
        d = _af("QSO_DATE", rec)
        q["date"] = "{}-{}-{}".format(d[:4], d[4:6], d[6:8]) if len(d) == 8 else d
        t = _af("TIME_ON", rec)
        q["time"] = "{}:{}".format(t[:2], t[2:4]) if len(t) >= 4 else t
        if q["callsign"]:
            qsos.append(q)
        elif rec.strip():
            errs.append({"line":ln, "type":"MISSING_CALL", "message":"QSO ADIF fara indicativ", "raw":rec[:60]})
    return qsos, errs

# ══════════════════════ CABRILLO ══════════════════════════════
def _cab(text):
    qsos, errs, hdr = [], [], {}
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line: continue
        up = line.upper()
        if up.startswith("START-OF-LOG"): continue
        if up.startswith("END-OF-LOG"): break
        if ":" in line and not up.startswith("QSO:"):
            k, _, v = line.partition(":")
            hdr[k.strip().upper()] = v.strip()
            continue
        if not up.startswith("QSO:"):
            continue
        parts = line.split()
        if len(parts) < 9:
            errs.append({"line":ln, "type":"SHORT_QSO",
                         "message":"Linie QSO incompleta ({} campuri)".format(len(parts)),
                         "raw":raw[:80]})
            continue
        q = _empty(); q["_line"] = ln; q["_raw"] = raw[:120]; q["_fmt"] = "cabrillo"
        try:
            q["freq"]     = parts[1]
            q["band"]     = freq_to_band(float(parts[1])) or parts[1].lower()
            raw_mode = parts[2].upper()
            # Cabrillo 2.0 foloseste PH pentru Phone/SSB, CW, RY pentru RTTY
            _MODE_NORM = {"PH":"SSB","PHONE":"SSB","RY":"RTTY","FM":"FM","AM":"AM"}
            q["mode"] = _MODE_NORM.get(raw_mode, raw_mode)
            d = parts[3].replace("-", "")
            q["date"]     = "{}-{}-{}".format(d[:4],d[4:6],d[6:8]) if len(d)==8 else parts[3]
            t = parts[4].replace(":", "")
            q["time"]     = "{}:{}".format(t[:2],t[2:4]) if len(t)>=4 else parts[4]
            q["my_call"]  = parts[5].upper()
            q["rst_s"]    = parts[6]
            q["exchange"] = parts[7]
            q["callsign"] = parts[8].upper()
            q["rst_r"]    = parts[9] if len(parts) > 9 else ""
            if len(parts) > 10:
                q["note"] = " ".join(parts[10:])
        except (IndexError, ValueError) as e:
            errs.append({"line":ln, "type":"CAB_PARSE", "message":str(e), "raw":raw[:80]})
            continue
        if q["callsign"]:
            qsos.append(q)
        else:
            errs.append({"line":ln, "type":"MISSING_CALL", "message":"QSO Cabrillo fara indicativ", "raw":raw[:80]})
    return qsos, errs, hdr

# ══════════════════════ CSV ═══════════════════════════════════
_CSV_MAP = {
    "call":"callsign", "callsign":"callsign", "indicativ":"callsign",
    "freq":"freq", "frequency":"freq", "frecventa":"freq",
    "band":"band", "banda":"band",
    "mode":"mode", "mod":"mode",
    "rst_s":"rst_s", "rst_sent":"rst_s", "rst sent":"rst_s",
    "rst_r":"rst_r", "rst_rcvd":"rst_r", "rst recv":"rst_r",
    "date":"date", "data":"date",
    "time":"time", "ora":"time",
    "exchange":"exchange", "schimb":"exchange",
    "locator":"locator", "grid":"locator",
    "note":"note", "nota":"note", "comment":"note",
    "serial":"serial",
}

def _csv(text):
    qsos, errs = [], []
    sep = ","
    sample = text[:2048]
    for s in [";", "\t", "|", ","]:
        if s in sample:
            sep = s
            break
    try:
        reader = csv.DictReader(io.StringIO(text), delimiter=sep)
        hdrs = reader.fieldnames or []
    except Exception as e:
        return [], [{"line":1, "type":"CSV_ERR", "message":"Nu pot citi CSV: {}".format(e), "raw":""}]
    col_map = {}
    for h in hdrs:
        k = h.strip().lower().replace(" ", "_")
        if k in _CSV_MAP:
            col_map[h] = _CSV_MAP[k]
    for ln, row in enumerate(reader, 2):
        q = _empty(); q["_line"] = ln; q["_fmt"] = "csv"
        for ch, ci in col_map.items():
            q[ci] = (row.get(ch) or "").strip()
        if not q["callsign"] and hdrs:
            q["callsign"] = (list(row.values())[0] or "").strip()
        q["callsign"] = q["callsign"].upper()
        q["mode"]     = q["mode"].upper()
        if not q["band"] and q["freq"]:
            q["band"] = freq_to_band(q["freq"]) or ""
        d = q["date"]
        if d and "-" not in d and "." not in d and len(d) == 8:
            q["date"] = "{}-{}-{}".format(d[:4], d[4:6], d[6:8])
        elif d and "." in d:
            p = d.split(".")
            if len(p) == 3 and len(p[0]) == 2:
                q["date"] = "{}-{}-{}".format(p[2], p[1], p[0])
        t = q["time"].replace(":", "")
        if len(t) >= 4:
            q["time"] = "{}:{}".format(t[:2], t[2:4])
        if q["callsign"]:
            qsos.append(q)
        else:
            errs.append({"line":ln, "type":"MISSING_CALL", "message":"Rand CSV fara indicativ", "raw":""})
    return qsos, errs

# ══════════════════════ JSON ══════════════════════════════════
_JSON_MAP = {
    "call":"callsign","callsign":"callsign","indicativ":"callsign",
    "freq":"freq","band":"band","mode":"mode",
    "rst_s":"rst_s","rst_r":"rst_r","date":"date","time":"time",
    "exchange":"exchange","locator":"locator","note":"note","serial":"serial",
}

def _json(text):
    qsos, errs = [], []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return [], [{"line":1, "type":"JSON_ERR", "message":"JSON invalid: {}".format(e), "raw":""}]
    if isinstance(data, dict):
        records = data.get("log") or data.get("qsos") or data.get("data") or []
    elif isinstance(data, list):
        records = data
    else:
        return [], [{"line":1, "type":"JSON_FMT", "message":"Format JSON nerecunoscut", "raw":""}]
    for ln, rec in enumerate(records, 1):
        if not isinstance(rec, dict):
            errs.append({"line":ln,"type":"JSON_REC","message":"Inregistrare nu e dict","raw":str(rec)[:60]})
            continue
        q = _empty(); q["_line"] = ln; q["_fmt"] = "json"
        for k, v in rec.items():
            m = _JSON_MAP.get(k.lower().strip())
            if m:
                q[m] = str(v).strip() if v is not None else ""
        q["callsign"] = q["callsign"].upper()
        q["mode"]     = q["mode"].upper()
        if not q["band"] and q["freq"]:
            q["band"] = freq_to_band(q["freq"]) or ""
        d = q["date"]
        if d and len(d) == 8 and d.isdigit():
            q["date"] = "{}-{}-{}".format(d[:4], d[4:6], d[6:8])
        t = q["time"].replace(":", "")
        if len(t) >= 4:
            q["time"] = "{}:{}".format(t[:2], t[2:4])
        if q["callsign"]:
            qsos.append(q)
        else:
            errs.append({"line":ln,"type":"MISSING_CALL","message":"Inregistrare JSON fara indicativ","raw":""})
    return qsos, errs

# ══════════════════════ EDI (VHF) ═════════════════════════════
def _edi(text):
    """EDI — format european pentru concursuri VHF/UHF."""
    qsos, errs, hdr = [], [], {}
    in_qso = False
    my_call = ""
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("["):
            section = line.strip("[]").upper()
            in_qso = (section == "QSORECORDS")
            continue
        if not in_qso:
            if "=" in line:
                k, _, v = line.partition("=")
                hdr[k.strip().upper()] = v.strip()
                if k.strip().upper() == "MYCALL":
                    my_call = v.strip().upper()
            continue
        # date;time;call;mode;sent_rst;sent_serial;rcvd_rst;rcvd_serial;locator;pts
        parts = line.split(";")
        if len(parts) < 8:
            continue
        q = _empty(); q["_line"] = ln; q["_fmt"] = "edi"; q["my_call"] = my_call
        try:
            d = parts[0].strip()
            if len(d) == 6:
                q["date"] = "20{}-{}-{}".format(d[:2], d[2:4], d[4:6])
            elif len(d) == 8:
                q["date"] = "{}-{}-{}".format(d[:4], d[4:6], d[6:8])
            t = parts[1].strip()
            if len(t) >= 4:
                q["time"] = "{}:{}".format(t[:2], t[2:4])
            q["callsign"] = parts[2].strip().upper()
            q["mode"]     = parts[3].strip().upper()
            q["rst_s"]    = parts[4].strip()
            q["serial"]   = parts[5].strip()
            q["rst_r"]    = parts[6].strip()
            q["exchange"] = parts[7].strip()
            if len(parts) > 8:
                q["locator"] = parts[8].strip().upper()
        except IndexError:
            continue
        if q["callsign"]:
            qsos.append(q)
    return qsos, errs, hdr

# ══════════════════════ DISPATCHER ════════════════════════════
def parse_file(filepath):
    """
    Auto-detecteaza formatul si parseaza fisierul.
    Returneaza:
      qsos, errors, format, header, callsign, filename, total
    """
    result = {
        "qsos":[], "errors":[], "format":"unknown",
        "header":{}, "callsign":"",
        "filename": os.path.basename(filepath), "total":0,
    }
    text = ""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1250", "cp1252"):
        try:
            with open(filepath, "r", encoding=enc) as f:
                text = f.read()
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        result["errors"].append({"line":0,"type":"ENCODING","message":"Nu pot citi fisierul (encoding necunoscut)","raw":""})
        return result

    ext = os.path.splitext(filepath)[1].lower()
    up  = text[:1024].upper()

    if ext in (".adi", ".adif") or "<CALL:" in up or "<EOH>" in up:
        result["format"] = "adif"
        result["qsos"], result["errors"] = _adif(text)

    elif ext == ".edi" or "[QSORECORDS" in up:
        result["format"] = "edi"
        q, e, h = _edi(text)
        result["qsos"], result["errors"], result["header"] = q, e, h
        result["callsign"] = h.get("MYCALL", "")

    elif ext in (".log", ".cbr") or "START-OF-LOG" in up or up.count("QSO:") > 2:
        result["format"] = "cabrillo"
        q, e, h = _cab(text)
        result["qsos"], result["errors"], result["header"] = q, e, h
        result["callsign"] = h.get("CALLSIGN", "")

    elif ext == ".json" or text.strip()[:1] in ("{", "["):
        result["format"] = "json"
        result["qsos"], result["errors"] = _json(text)

    elif ext == ".csv" or any(s in text[:500] for s in [",", ";", "\t"]):
        result["format"] = "csv"
        result["qsos"], result["errors"] = _csv(text)

    else:
        # Incearca pe rand
        for fn in [_adif, _csv, _json]:
            q, e = fn(text)
            if q:
                result["format"] = fn.__name__.strip("_")
                result["qsos"], result["errors"] = q, e
                break
        else:
            q, e, h = _cab(text)
            if q:
                result["format"] = "cabrillo"
                result["qsos"], result["errors"], result["header"] = q, e, h
                result["callsign"] = h.get("CALLSIGN", "")

    if not result["callsign"]:
        result["callsign"] = os.path.splitext(os.path.basename(filepath))[0].upper()

    result["total"] = len(result["qsos"])
    return result
