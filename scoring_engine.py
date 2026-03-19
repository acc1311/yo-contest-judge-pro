#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Validator + Scoring Engine v2.2
Validare QSO: RST, data/ora, indicativ, banda, mod, exchange, duplicate,
              interval orar, serial secvential, locator Maidenhead.
Scoring: per-qso, per-banda, maraton IC (cu max 1 QSO/zi), distanta VHF.
"""
import re
import math
import datetime
from collections import defaultdict
from core.contest_rules import RST_RANGES, is_valid_county, BANDS_ALL, guess_dxcc

# ── Severitati ────────────────────────────────────────────────
ERR  = "ERROR"
WARN = "WARNING"
INFO = "INFO"

# Indicativ de baza: prefix(1-3) + cifra + sufix(1-4 litere)
# Sufixe portabile valide: /P (portabil), /M (mobil), /MM (maritim), /AM (aeronautic)
#   /QRP, /A, /B, sau indicativ complet (ex YO8ACR/YO3ABC)
_BASE_CALL = r'[A-Z0-9]{1,3}[0-9][A-Z]{1,4}'
_SUFFIX    = r'(/(?:P|M{1,2}|AM|QRP|[A-Z]{1,2}[0-9]?|[0-9]))?'
_CALL_RE   = re.compile(r'^' + _BASE_CALL + _SUFFIX + r'$', re.I)

# Sufixe portabile care nu schimba tara
PORTABLE_SUFFIXES = {"P","M","MM","AM","QRP","A","B"}

def _is_portable(callsign):
    """Returneaza True daca indicativul are sufix portabil (/P, /M, /MM etc.)"""
    if "/" not in callsign: return False
    suffix = callsign.upper().split("/",1)[1]
    return suffix in PORTABLE_SUFFIXES

def _base_call(callsign):
    """Returneaza indicativul de baza fara sufix portabil."""
    return callsign.upper().split("/")[0]

# Maidenhead locator: AA00 sau AA00aa
_LOC_RE  = re.compile(r'^[A-R]{2}[0-9]{2}([A-X]{2})?$', re.I)

class VErr:
    __slots__ = ("qso_idx","callsign","err_type","message","severity","field")
    def __init__(self, idx, call, etype, msg, sev=ERR, field=""):
        self.qso_idx  = idx
        self.callsign = call
        self.err_type = etype
        self.message  = msg
        self.severity = sev
        self.field    = field
    def to_dict(self):
        return {"qso_idx":self.qso_idx,"callsign":self.callsign,
                "type":self.err_type,"message":self.message,
                "severity":self.severity,"field":self.field}
    def __repr__(self):
        return "[{}] #{} {}: {}".format(self.severity, self.qso_idx, self.callsign, self.message)

# ── Validari individuale ───────────────────────────────────────
def _chk_rst(rst, mode):
    if not rst:
        return False, "RST lipsa"
    try:
        v = int(rst.strip())
    except ValueError:
        return False, "RST '{}' nu e numeric".format(rst)
    lo, hi = RST_RANGES.get(mode.upper(), RST_RANGES.get("SSB", (11, 59)))
    if v < lo or v > hi:
        return False, "RST {} in afara {}-{} pentru {}".format(v, lo, hi, mode)
    s = str(v)
    if len(s) == 2:
        if not 1 <= int(s[0]) <= 5: return False, "Readability {} invalid".format(s[0])
        if not 1 <= int(s[1]) <= 9: return False, "Tone {} invalid".format(s[1])
    elif len(s) == 3:
        if not 1 <= int(s[0]) <= 5: return False, "Readability {} invalid".format(s[0])
        if not 1 <= int(s[1]) <= 9: return False, "Tone {} invalid".format(s[1])
        if not 1 <= int(s[2]) <= 9: return False, "Strength {} invalid".format(s[2])
    return True, ""

def _chk_date(d):
    if not d: return False, "Data lipsa"
    try:
        dt = datetime.datetime.strptime(d.strip(), "%Y-%m-%d")
        if dt.year < 2000 or dt > datetime.datetime.now() + datetime.timedelta(days=1):
            return False, "Data suspcta: {}".format(d)
        return True, ""
    except ValueError:
        return False, "Format data invalid: '{}' (YYYY-MM-DD)".format(d)

def _chk_time(t):
    if not t: return False, "Ora lipsa"
    try:
        datetime.datetime.strptime(t.strip(), "%H:%M")
        return True, ""
    except ValueError:
        return False, "Ora invalida: '{}'".format(t)

def _chk_call(c, contest=None):
    """Valideaza indicativ. Accepta /P /M /MM /AM /QRP si sufixe tara."""
    if not c: return False, "Indicativ lipsa"
    cu = c.upper().strip()
    if not _CALL_RE.match(cu):
        return False, "Indicativ suspect: '{}'".format(c)
    # Avertisment informational daca e portabil/mobil
    if "/" in cu:
        sfx = cu.split("/",1)[1]
        if sfx in PORTABLE_SUFFIXES:
            return True, ""   # valid, fara avertisment
        # Altfel (ex /YO8ACR sau /3) — valid dar informam
    return True, ""

def _chk_locator(loc):
    """Valideaza format Maidenhead Locator (min 4 caractere: AA00)."""
    if not loc: return False, "Locator lipsa"
    if not _LOC_RE.match(loc.strip()):
        return False, "Locator invalid: '{}' (format corect: KN36 sau KN36LD)".format(loc)
    return True, ""

def _dt_from_qso(q):
    d, t = q.get("date","").strip(), q.get("time","").strip()
    if not d or not t: return None
    tc = t.replace(":", "")
    if len(tc) < 4: return None
    try:
        return datetime.datetime.strptime("{} {}:{}".format(d, tc[:2], tc[2:4]), "%Y-%m-%d %H:%M")
    except ValueError:
        return None

# ── Validare log ───────────────────────────────────────────────
def validate_log(qsos, contest_id=None, station_call="", contests=None):
    """
    Valideaza toate QSO-urile dintr-un log.
    Returneaza: errors, duplicate_groups, valid_count, error_count, warning_count, qso_flags
    """
    from core.contest_rules import BUILT_IN
    if contests is None:
        contests = BUILT_IN
    contest = contests.get(contest_id or "", {})

    all_err   = []
    qso_flags = {}

    # ── Intervale orare permise de concurs ────────────────────
    time_windows = contest.get("time_windows", [])  # lista de {"start":"HH:MM","end":"HH:MM"}

    # ── Tracker serial secvential ─────────────────────────────
    serials_seen = []

    for i, q in enumerate(qsos):
        errs = []
        call = q.get("callsign", "")
        _MODE_NORM = {"PH":"SSB","PHONE":"SSB","RY":"RTTY"}
        mode = _MODE_NORM.get(q.get("mode","SSB").upper(), q.get("mode","SSB").upper())

        # 1. Indicativ
        ok, msg = _chk_call(call)
        if not ok:
            errs.append(VErr(i, call, "BAD_CALL", msg, ERR, "callsign"))

        # Auto-QSO
        if station_call and call.upper() == station_call.upper():
            errs.append(VErr(i, call, "SELF_QSO", "QSO cu propriul indicativ", ERR, "callsign"))

        # 2. RST
        for fld, lbl in [("rst_s","RST trimis"), ("rst_r","RST primit")]:
            rst = q.get(fld, "")
            ok2, msg2 = _chk_rst(rst, mode)
            if rst and not ok2:
                errs.append(VErr(i, call, "BAD_RST", "{}: {}".format(lbl, msg2), WARN, fld))
            elif not rst:
                errs.append(VErr(i, call, "NO_RST", "{} lipsa".format(lbl), WARN, fld))

        # 3. Data / Ora
        ok3, msg3 = _chk_date(q.get("date", ""))
        if not ok3:
            errs.append(VErr(i, call, "BAD_DATE", msg3, ERR, "date"))

        ok4, msg4 = _chk_time(q.get("time", ""))
        if not ok4:
            errs.append(VErr(i, call, "BAD_TIME", msg4, WARN, "time"))

        # 4. Verificare interval orar (FIX #6)
        if time_windows and ok3 and ok4:
            qso_dt = _dt_from_qso(q)
            if qso_dt:
                qso_time_str = q.get("time","").replace(":","")[:4]
                qso_hhmm = int(qso_time_str) if qso_time_str.isdigit() else -1
                in_window = False
                for win in time_windows:
                    s = int(win.get("start","0000").replace(":",""))
                    e = int(win.get("end","2359").replace(":",""))
                    if s <= qso_hhmm <= e:
                        in_window = True
                        break
                if not in_window:
                    windows_str = ", ".join("{}-{}".format(w["start"],w["end"]) for w in time_windows)
                    errs.append(VErr(i, call, "OUT_OF_WINDOW",
                        "Ora {} in afara intervalelor permise ({})".format(
                            q.get("time","?"), windows_str), WARN, "time"))

        # 5. Banda / Mod permise de concurs
        if contest_id and contest:
            ab = [b.lower() for b in contest.get("allowed_bands", BANDS_ALL)]
            am_raw = [m.upper() for m in contest.get("allowed_modes", [])]
            am = list(am_raw)
            if "SSB" in am and "PH" not in am: am.append("PH")
            if "RTTY" in am and "RY" not in am: am.append("RY")
            b  = q.get("band", "").lower()
            m  = q.get("mode", "").upper()
            if b and ab and b not in ab:
                errs.append(VErr(i, call, "BAD_BAND",
                    "Banda '{}' nepermisa in {}".format(b, contest.get("name", contest_id)), ERR, "band"))
            if m and am and m not in am:
                errs.append(VErr(i, call, "BAD_MODE",
                    "Mod '{}' nepermis in {}".format(m, contest.get("name", contest_id)), ERR, "mode"))

        # 6. Exchange
        exch_type = contest.get("exchange", "none") if contest else "none"
        if contest_id and exch_type == "county":
            exch = q.get("exchange", "").strip().upper()
            if not exch:
                errs.append(VErr(i, call, "NO_EXCH", "Schimb (judet) lipsa", WARN, "exchange"))
            elif not is_valid_county(exch):
                errs.append(VErr(i, call, "BAD_COUNTY", "Judet invalid: '{}'".format(exch), WARN, "exchange"))

        # 7. Locator (FIX #5) — validare format Maidenhead pentru VHF
        if contest_id and exch_type == "locator":
            loc = q.get("locator","").strip() or q.get("exchange","").strip()
            ok_loc, msg_loc = _chk_locator(loc)
            if not ok_loc:
                errs.append(VErr(i, call, "BAD_LOCATOR", msg_loc, WARN, "locator"))

        # 8. Serial secvential (FIX #7)
        if contest_id and contest.get("check_serial", False):
            serial_str = q.get("serial","").strip() or q.get("exchange","").strip()
            try:
                serial_nr = int(re.sub(r'\D', '', serial_str)) if serial_str else None
            except (ValueError, TypeError):
                serial_nr = None
            if serial_nr is not None:
                serials_seen.append((i, serial_nr))

        has_err  = any(e.severity == ERR  for e in errs)
        has_warn = any(e.severity == WARN for e in errs)
        qso_flags[i] = "error" if has_err else ("warning" if has_warn else "ok")
        all_err.extend(errs)

    # ── Verificare serialuri (FIX #7) ────────────────────────
    if serials_seen:
        expected = 1
        for idx, nr in sorted(serials_seen, key=lambda x: x[1]):
            if nr != expected:
                # Nu eroare, doar avertisment — unele programe nu numeroteaza strict
                all_err.append(VErr(idx, qsos[idx].get("callsign",""),
                    "BAD_SERIAL",
                    "Serial {} neasteptat (asteptat ~{})".format(nr, expected),
                    WARN, "exchange"))
            expected = nr + 1

    # ── Duplicate ─────────────────────────────────────────────
    seen = defaultdict(list)
    for i, q in enumerate(qsos):
        seen[(q["callsign"].upper(), q["band"].lower())].append(i)
    dup_groups = {k: v for k, v in seen.items() if len(v) > 1}
    for (call, band), idxs in dup_groups.items():
        for idx in idxs[1:]:
            if qso_flags.get(idx) != "error":
                qso_flags[idx] = "duplicate"
            all_err.append(VErr(idx, call, "DUPLICATE",
                "Duplicat pe {} (primul: QSO #{})".format(band, idxs[0]+1), ERR, "callsign"))

    ec = sum(1 for e in all_err if e.severity == ERR)
    wc = sum(1 for e in all_err if e.severity == WARN)
    vc = sum(1 for f in qso_flags.values() if f == "ok")

    return {
        "errors": all_err,
        "duplicate_groups": dup_groups,
        "valid_count": vc,
        "error_count": ec,
        "warning_count": wc,
        "qso_flags": qso_flags,
    }

# ── Locator → distanta ────────────────────────────────────────
def _loc_to_ll(loc):
    s = loc.upper().strip()
    if len(s) < 4: return None, None
    try:
        lon = (ord(s[0])-ord('A'))*20 - 180 + int(s[2])*2
        lat = (ord(s[1])-ord('A'))*10 - 90  + int(s[3])
        if len(s) >= 6:
            lon += (ord(s[4])-ord('A')+0.5)/12
            lat += (ord(s[5])-ord('A')+0.5)/24
        else:
            lon += 1.0; lat += 0.5
        return lat, lon
    except (IndexError, ValueError):
        return None, None

def _km(la1, lo1, la2, lo2):
    R = 6371
    p1,p2 = math.radians(la1), math.radians(la2)
    a = math.sin(math.radians(la2-la1)/2)**2 + \
        math.cos(p1)*math.cos(p2)*math.sin(math.radians(lo2-lo1)/2)**2
    return round(2*R*math.asin(math.sqrt(a)))

# ── Scoring ────────────────────────────────────────────────────
def _pts_qso(q, contest, my_loc=""):
    mode = contest.get("scoring_mode","per_qso")
    if mode == "none":    return 0
    if mode == "per_qso": return contest.get("points_per_qso",1)
    if mode == "maraton": return contest.get("points_per_qso",1)
    if mode == "per_band":return contest.get("points_per_qso",1)
    if mode == "maraton_ic":
        worked = q.get("callsign","").upper()
        special = contest.get("special_calls", {})
        for sp_call, sp_pts in special.items():
            if sp_call.upper() in worked:
                return sp_pts
        if "/IC" in worked:
            # Lista cluburi IC explicita (FIX #4)
            ic_clubs = [c.upper() for c in contest.get("ic_clubs", [])]
            if ic_clubs and worked.replace("/IC","").strip() in ic_clubs:
                return contest.get("ic_club_points", 10)
            # Fallback: indicative de club au de obicei sufix > 3 litere
            base = worked.split("/")[0]
            suffix_letters = re.sub(r'[0-9]', '', base[2:]) if len(base) > 2 else ""
            if len(suffix_letters) >= 3:
                return contest.get("ic_club_points", 10)
            return contest.get("ic_individual_points", 5)
        return 0

    if mode == "cupa_moldovei":
        exch  = q.get("exchange","").strip().upper()
        qmode = q.get("mode","SSB").upper()
        moldova = [x.upper() for x in contest.get("moldova_counties",
                   ["BC","BT","GL","IS","NT","SV","VN","VS"])]
        is_cw = (qmode in ("CW",))
        if exch in moldova:
            return contest.get("points_moldova_cw",8) if is_cw else contest.get("points_moldova_ssb",4)
        return contest.get("points_cw",4) if is_cw else contest.get("points_per_qso",2)

    if mode == "per_qso_x_mult":
        return contest.get("points_per_qso", 2)

    if mode == "cupa_tomis":
        call = q.get("callsign","").upper()
        if call in [x.upper() for x in contest.get("special_calls_4pt",[])]:
            return contest.get("points_special_main", 4)
        if call in [x.upper() for x in contest.get("special_calls_2pt",[])]:
            return contest.get("points_special_members", 2)
        return contest.get("points_per_qso", 1)

    if mode == "distance":
        loc_t = q.get("locator","").strip() or q.get("exchange","").strip()
        if loc_t and my_loc:
            la1,lo1 = _loc_to_ll(my_loc)
            la2,lo2 = _loc_to_ll(loc_t)
            if la1 is not None and la2 is not None:
                return max(1, _km(la1,lo1,la2,lo2))
        return 1
    return contest.get("points_per_qso",1)

def _mults(qsos, contest, flags):
    mode = contest.get("multiplier","none")
    mults = set()
    for i, q in enumerate(qsos):
        if flags.get(i) in ("error","duplicate"): continue
        if mode == "county":
            e = q.get("exchange","").strip().upper()
            if is_valid_county(e): mults.add(e)
        elif mode == "county_dxcc":
            # FIX #3 — Cupa Moldovei: judete YO + prefix DXCC tara straina
            e = q.get("exchange","").strip().upper()
            call = q.get("callsign","").upper()
            if is_valid_county(e):
                mults.add("county:{}".format(e))
            elif not call.startswith("YO") and not call.startswith("YP") and \
                 not call.startswith("YR") and not call.startswith("YQ"):
                dx = guess_dxcc(call)
                if dx and dx != "Unknown":
                    mults.add("dxcc:{}".format(dx))
        elif mode == "dxcc_band":
            dx = guess_dxcc(q["callsign"])
            b  = q.get("band","").lower()
            if dx and b: mults.add("{}:{}".format(dx,b))
        elif mode == "locator_field":
            loc = q.get("locator","").upper()
            if len(loc) >= 4: mults.add(loc[:4])
    return len(mults), mults

def score_log(qsos, contest_id, station_call="", my_locator="",
              qso_flags=None, cc_result=None, contests=None):
    """
    Calculeaza scorul complet al unui log.
    Returneaza dict cu: scor total, QSO valide, erori, duplicate,
                        puncte QSO, multiplicatori, breakdown per QSO, per banda.
    """
    from core.contest_rules import BUILT_IN
    if contests is None: contests = BUILT_IN
    contest = contests.get(contest_id)
    if not contest:
        return {"error": "Concurs necunoscut: {}".format(contest_id)}
    if qso_flags is None:
        qso_flags = {i:"ok" for i in range(len(qsos))}

    # NIL/Busted din cross-check = penalizate
    nil_set = set()
    if cc_result:
        for idx in cc_result.get("nil", []):
            nil_set.add(idx)
        for ia, ib in cc_result.get("busted_band", []):
            nil_set.add(ia)
        for ia, ib, _ in cc_result.get("busted_time", []):
            nil_set.add(ia)
        for ia, ib, call in cc_result.get("busted_call", []):
            nil_set.add(ia)

    # FIX #1 — Maraton IC: max 1 QSO/zi per statie lucrată
    per_day_per_call = defaultdict(set)   # {date: {callsign, ...}}
    maraton_extra_dups = set()
    if contest.get("max_qso_per_day"):
        max_per_day = contest["max_qso_per_day"]
        for i, q in enumerate(qsos):
            if qso_flags.get(i) in ("error", "duplicate"):
                continue
            day  = q.get("date","")
            call = q.get("callsign","").upper()
            if call in per_day_per_call[day]:
                maraton_extra_dups.add(i)
            else:
                per_day_per_call[day].add(call)

    qso_pts   = 0
    valid_cnt = dup_cnt = err_cnt = nil_cnt = maraton_dup_cnt = 0
    per_band  = defaultdict(lambda: {"qsos":0,"points":0})
    breakdown = []

    for i, q in enumerate(qsos):
        flag   = qso_flags.get(i, "ok")
        status = flag

        if i in maraton_extra_dups and flag == "ok":
            status = "maraton_dup"
            maraton_dup_cnt += 1

        if i in nil_set and flag == "ok" and status == "ok":
            status = "nil"
            nil_cnt += 1

        if flag in ("error","duplicate") or status in ("nil","maraton_dup"):
            if flag == "error":       err_cnt += 1
            if flag == "duplicate":   dup_cnt += 1
            pts = 0
        else:
            pts = _pts_qso(q, contest, my_locator)
            qso_pts += pts
            valid_cnt += 1

        band = q.get("band","?").lower()
        per_band[band]["qsos"]   += 1
        per_band[band]["points"] += pts

        breakdown.append({
            "idx": i,
            "callsign": q.get("callsign",""),
            "band": band, "mode": q.get("mode",""),
            "date": q.get("date",""), "time": q.get("time",""),
            "rst_s": q.get("rst_s",""), "rst_r": q.get("rst_r",""),
            "exchange": q.get("exchange",""),
            "locator": q.get("locator",""),
            "points": pts, "status": status,
        })

    mult_cnt, mult_set = _mults(qsos, contest, qso_flags)
    sm = contest.get("scoring_mode","per_qso")
    if sm == "none":
        total = valid_cnt
    elif mult_cnt > 0:
        total = qso_pts * mult_cnt
    else:
        total = qso_pts

    return {
        "contest_id":    contest_id,
        "contest_name":  contest["name"],
        "callsign":      station_call,
        "total_qsos":    len(qsos),
        "valid_qsos":    valid_cnt,
        "error_qsos":    err_cnt,
        "duplicate_qsos":dup_cnt,
        "maraton_dup_qsos": maraton_dup_cnt,
        "nil_qsos":      nil_cnt,
        "qso_points":    qso_pts,
        "multipliers":   mult_cnt,
        "mult_set":      mult_set,
        "total_score":   total,
        "per_band":      dict(per_band),
        "breakdown":     breakdown,
    }

def build_ranking(scores):
    """Sorteaza o lista de score_log results si adauga pozitia."""
    valid = [s for s in scores if "error" not in s]
    ranked = sorted(valid, key=lambda s: s["total_score"], reverse=True)
    result = []
    for pos, s in enumerate(ranked, 1):
        result.append({
            "position":     pos,
            "callsign":     s["callsign"],
            "contest_name": s["contest_name"],
            "total_qsos":   s["total_qsos"],
            "valid_qsos":   s["valid_qsos"],
            "error_qsos":   s["error_qsos"],
            "dup_qsos":     s["duplicate_qsos"],
            "maraton_dup_qsos": s.get("maraton_dup_qsos", 0),
            "nil_qsos":     s["nil_qsos"],
            "qso_points":   s["qso_points"],
            "multipliers":  s["multipliers"],
            "total_score":  s["total_score"],
        })
    return result
