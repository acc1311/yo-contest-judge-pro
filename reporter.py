#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Reporter
Export rapoarte: HTML (print-ready), CSV (Excel), TXT, JSON.
"""
import csv
import io
import json
import os
import datetime

_NOW = lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

_SCOL = {
    "ok":          "#d4edda",
    "warning":     "#fff3cd",
    "error":       "#f8d7da",
    "duplicate":   "#fce4ec",
    "nil":         "#e0e0e0",
}
_SLBL = {
    "ok":"OK","warning":"Avertisment","error":"Eroare",
    "duplicate":"Duplicat","nil":"NIL",
}

# ── CSV ───────────────────────────────────────────────────────
def export_csv(score, validation, filepath):
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["YO Contest Judge PRO", _NOW()])
        w.writerow([])
        w.writerow(["Concurs",     score.get("contest_name","")])
        w.writerow(["Indicativ",   score.get("callsign","")])
        w.writerow(["Total QSO",   score.get("total_qsos",0)])
        w.writerow(["QSO Valide",  score.get("valid_qsos",0)])
        w.writerow(["Erori",       score.get("error_qsos",0)])
        w.writerow(["Duplicate",   score.get("duplicate_qsos",0)])
        w.writerow(["NIL",         score.get("nil_qsos",0)])
        w.writerow(["Puncte QSO",  score.get("qso_points",0)])
        w.writerow(["Multiplicatori", score.get("multipliers",0)])
        w.writerow(["SCOR FINAL",  score.get("total_score",0)])
        w.writerow([])
        w.writerow(["#","Indicativ","Banda","Mod","Data","Ora",
                    "RST S","RST R","Schimb","Puncte","Status"])
        for b in score.get("breakdown",[]):
            w.writerow([b["idx"]+1, b["callsign"], b["band"], b["mode"],
                        b["date"], b["time"], b["rst_s"], b["rst_r"],
                        b["exchange"], b["points"], b["status"]])
        w.writerow([])
        if validation:
            w.writerow(["ERORI VALIDARE"])
            w.writerow(["#QSO","Indicativ","Tip","Mesaj","Severitate"])
            for e in validation.get("errors",[]):
                d = e.to_dict() if hasattr(e,"to_dict") else e
                w.writerow([d["qso_idx"]+1, d["callsign"], d["type"],
                             d["message"], d["severity"]])
    return filepath

# ── HTML ──────────────────────────────────────────────────────
def export_html(score, validation, filepath, cc_result=None, ranking=None):
    call    = score.get("callsign","—")
    contest = score.get("contest_name","—")

    per_band_rows = ""
    for band, bd in sorted(score.get("per_band",{}).items()):
        per_band_rows += "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            band, bd["qsos"], bd["points"])

    qso_rows = ""
    for b in score.get("breakdown",[]):
        bg  = _SCOL.get(b["status"],"#fff")
        lbl = _SLBL.get(b["status"], b["status"])
        qso_rows += (
            "<tr style='background:{}'>"
            "<td>{}</td><td><b>{}</b></td><td>{}</td><td>{}</td>"
            "<td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>"
            "<td><b>{}</b></td><td>{}</td></tr>"
        ).format(bg, b["idx"]+1, b["callsign"], b["band"], b["mode"],
                 b["date"], b["time"], b["rst_s"], b["rst_r"],
                 b["exchange"], b["points"], lbl)

    err_rows = ""
    if validation:
        for e in validation.get("errors",[]):
            d = e.to_dict() if hasattr(e,"to_dict") else e
            sc = {"ERROR":"#f8d7da","WARNING":"#fff3cd","INFO":"#d1ecf1"}.get(d["severity"],"#fff")
            err_rows += (
                "<tr style='background:{}'>"
                "<td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>"
            ).format(sc, d["qso_idx"]+1, d["callsign"], d["type"], d["message"], d["severity"])

    cc_html = ""
    if cc_result:
        st = cc_result.get("stats",{})
        cc_html = """
        <h2>Cross-Check</h2>
        <table>
          <tr><th>Total A</th><th>Confirmate</th><th>NIL</th>
              <th>Busted Call</th><th>Busted Band</th><th>Busted Time</th><th>Rata confirmare</th></tr>
          <tr>
            <td>{ta}</td>
            <td style="color:green"><b>{co}</b></td>
            <td style="color:red">{ni}</td>
            <td style="color:orange">{bc}</td>
            <td style="color:orange">{bb}</td>
            <td style="color:orange">{bt}</td>
            <td><b>{pct}%</b></td>
          </tr>
        </table>""".format(
            ta=st.get("total_a",0), co=st.get("confirmed",0),
            ni=st.get("nil",0), bc=st.get("busted_call",0),
            bb=st.get("busted_band",0), bt=st.get("busted_time",0),
            pct=st.get("confirm_pct",0))

    rank_html = ""
    if ranking:
        rows = "".join(
            "<tr><td><b>#{}</b></td><td><b>{}</b></td><td>{}</td>"
            "<td>{}</td><td>{}</td><td>{}</td><td><b>{}</b></td></tr>".format(
                r["position"], r["callsign"], r["valid_qsos"],
                r["qso_points"], r["multipliers"],
                r.get("nil_qsos",0), r["total_score"])
            for r in ranking)
        rank_html = """
        <h2>Clasament Final</h2>
        <table>
          <tr><th>#</th><th>Indicativ</th><th>QSO Valide</th>
              <th>Puncte QSO</th><th>Mult.</th><th>NIL</th><th>SCOR</th></tr>
          {}
        </table>""".format(rows)

    html = """<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<title>YO Contest Judge PRO — {call}</title>
<style>
body{{font-family:Arial,sans-serif;font-size:13px;margin:20px;color:#111}}
h1{{background:#1a3a5c;color:#fff;padding:10px 16px;border-radius:4px}}
h2{{color:#2e75b6;border-bottom:2px solid #2e75b6;padding-bottom:3px;margin-top:24px}}
table{{border-collapse:collapse;width:100%;margin:10px 0}}
th{{background:#1a3a5c;color:#fff;padding:6px 9px;text-align:left;font-size:12px}}
td{{padding:4px 9px;border-bottom:1px solid #ddd}}
tr:hover{{filter:brightness(.95)}}
.box{{display:inline-block;background:#f2f5f8;border-left:4px solid #2e75b6;
      padding:8px 16px;border-radius:3px;margin:4px}}
.val{{font-size:1.7em;font-weight:bold;color:#1a3a5c}}
.lbl{{font-size:.82em;color:#555}}
.score{{background:#1a3a5c;color:#fff;font-size:1.3em;
        padding:10px 18px;border-radius:5px;display:inline-block;margin:8px 0}}
@media print{{th{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
              h1{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style>
</head>
<body>
<h1>YO Contest Judge PRO — Raport Arbitraj</h1>
<p>Generat: {now} | Concurs: <b>{contest}</b> | Indicativ: <b>{call}</b></p>
<h2>Sumar</h2>
<div>
  <div class="box"><div class="val">{tq}</div><div class="lbl">Total QSO</div></div>
  <div class="box"><div class="val" style="color:green">{vq}</div><div class="lbl">Valide</div></div>
  <div class="box"><div class="val" style="color:red">{eq}</div><div class="lbl">Erori</div></div>
  <div class="box"><div class="val" style="color:#e65100">{dq}</div><div class="lbl">Duplicate</div></div>
  <div class="box"><div class="val" style="color:#9c27b0">{mq}</div><div class="lbl">Dup. maraton/zi</div></div>
  <div class="box"><div class="val" style="color:#777">{nq}</div><div class="lbl">NIL</div></div>
  <div class="box"><div class="val">{pp}</div><div class="lbl">Puncte QSO</div></div>
  <div class="box"><div class="val">{mu}</div><div class="lbl">Multiplicatori</div></div>
</div>
<div class="score">SCOR FINAL: {ts}</div>
<h2>Per Banda</h2>
<table><tr><th>Banda</th><th>QSO</th><th>Puncte</th></tr>{pb}</table>
<h2>Log QSO-uri</h2>
<table>
<tr><th>#</th><th>Indicativ</th><th>Banda</th><th>Mod</th><th>Data</th><th>Ora</th>
    <th>RST S</th><th>RST R</th><th>Schimb</th><th>Pct</th><th>Status</th></tr>
{qr}
</table>
<h2>Erori Validare</h2>
<table>
<tr><th>#QSO</th><th>Indicativ</th><th>Tip</th><th>Mesaj</th><th>Severitate</th></tr>
{er}
</table>
{cc}{rk}
<hr>
<p style="color:#888;font-size:11px">YO Contest Judge PRO v2.2 — YO8ACR | yo8acr@gmail.com</p>
</body></html>""".format(
        call=call, now=_NOW(), contest=contest,
        tq=score.get("total_qsos",0), vq=score.get("valid_qsos",0),
        eq=score.get("error_qsos",0), dq=score.get("duplicate_qsos",0),
        nq=score.get("nil_qsos",0),   pp=score.get("qso_points",0),
        mu=score.get("multipliers",0), ts=score.get("total_score",0),
        pb=per_band_rows, qr=qso_rows,
        er=err_rows or "<tr><td colspan='5' style='color:green'>Nicio eroare</td></tr>",
        cc=cc_html, rk=rank_html)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath

# ── TXT ───────────────────────────────────────────────────────
def export_txt(score, validation, filepath):
    SEP = "=" * 70
    sep = "-" * 70
    lines = [SEP, "  YO Contest Judge PRO v2.2 — RAPORT ARBITRAJ", SEP,
             "  Generat:      {}".format(_NOW()),
             "  Concurs:      {}".format(score.get("contest_name","")),
             "  Indicativ:    {}".format(score.get("callsign","")),
             sep,
             "  Total QSO:         {}".format(score.get("total_qsos",0)),
             "  QSO Valide:        {}".format(score.get("valid_qsos",0)),
             "  Erori:             {}".format(score.get("error_qsos",0)),
             "  Duplicate:         {}".format(score.get("duplicate_qsos",0)),
             "  NIL:               {}".format(score.get("nil_qsos",0)),
             "  Puncte QSO:        {}".format(score.get("qso_points",0)),
             "  Multiplicatori:    {}".format(score.get("multipliers",0)),
             "  SCOR FINAL:        {}".format(score.get("total_score",0)),
             SEP, ""]

    lines += ["PER BANDA:", sep]
    lines += ["  {:<8} {:>6} {:>8}".format("Banda","QSO","Puncte"), sep]
    for band, bd in sorted(score.get("per_band",{}).items()):
        lines += ["  {:<8} {:>6} {:>8}".format(band, bd["qsos"], bd["points"])]
    lines += [""]

    errs = validation.get("errors",[]) if validation else []
    if errs:
        lines += ["ERORI ({} total):".format(len(errs)), sep]
        for e in errs:
            d = e.to_dict() if hasattr(e,"to_dict") else e
            lines += ["  [{:7}] #{:4d} {:<12} {:<20} {}".format(
                d["severity"], d["qso_idx"]+1, d["callsign"], d["type"], d["message"])]
        lines += [""]

    lines += [SEP, "  YO Contest Judge PRO v2.2 — YO8ACR | yo8acr@gmail.com", SEP]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath

# ── JSON ──────────────────────────────────────────────────────
def export_json(score, validation, filepath):
    out = {
        "generated": _NOW(),
        "score": score,
        "validation": {
            "errors": [(e.to_dict() if hasattr(e,"to_dict") else e)
                       for e in (validation.get("errors",[]) if validation else [])]
        }
    }
    if "mult_set" in out["score"]:
        out["score"]["mult_set"] = list(out["score"]["mult_set"])
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    return filepath
