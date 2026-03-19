#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Statistics Engine
Statistici complete: activitate per ora, distributie benzi/moduri,
rata NIL, top statii, grafice canvas.
"""
import datetime
from collections import defaultdict, Counter

def compute_stats(logs_dict, scores_dict, val_dict, cc_matrix, contest_name=""):
    """
    Calculeaza statistici complete pentru toate logurile unui concurs.
    logs_dict  = {call: parse_result}
    scores_dict= {call: score_result}
    val_dict   = {call: validation_result}
    cc_matrix  = {key: cc_result}
    """
    all_qsos = []
    for call, pr in logs_dict.items():
        for q in pr.get("qsos",[]):
            q2 = dict(q)
            q2["_owner"] = call
            all_qsos.append(q2)

    stats = {
        "contest_name":  contest_name,
        "generated_at":  datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "num_logs":      len(logs_dict),
        "total_qso":     len(all_qsos),
        "unique_calls":  set(),
        "by_band":       defaultdict(int),
        "by_mode":       defaultdict(int),
        "by_hour":       defaultdict(int),
        "by_county":     defaultdict(int),
        "by_log":        {},
        "top_active":    [],
        "nil_rate":      0.0,
        "cc_summary":    {},
    }

    # QSO per ora, banda, mod, judet
    for q in all_qsos:
        stats["unique_calls"].add(q.get("callsign","").upper())
        b = q.get("band","?").lower() or "?"
        m = q.get("mode","?").upper() or "?"
        stats["by_band"][b] += 1
        stats["by_mode"][m] += 1
        t = q.get("time","")
        if t and ":" in t:
            try: stats["by_hour"][int(t[:2])] += 1
            except: pass
        exch = q.get("exchange","").strip().upper()
        if exch: stats["by_county"][exch] += 1

    stats["unique_calls"] = len(stats["unique_calls"])
    stats["by_band"]  = dict(sorted(stats["by_band"].items(),  key=lambda x:-x[1]))
    stats["by_mode"]  = dict(sorted(stats["by_mode"].items(),  key=lambda x:-x[1]))
    stats["by_hour"]  = dict(sorted(stats["by_hour"].items()))
    stats["by_county"]= dict(sorted(stats["by_county"].items(),key=lambda x:-x[1]))

    # Per log
    for call, pr in logs_dict.items():
        vr = val_dict.get(call,{})
        sr = scores_dict.get(call,{})
        stats["by_log"][call] = {
            "total":     pr.get("total",0),
            "valid":     vr.get("valid_count",0),
            "errors":    vr.get("error_count",0),
            "dup":       len(vr.get("duplicate_groups",{})),
            "score":     sr.get("total_score",0),
            "format":    pr.get("format","?"),
        }

    # Top statii (cele mai contactate)
    call_cnt = Counter()
    for q in all_qsos:
        c = q.get("callsign","").upper()
        if c: call_cnt[c] += 1
    stats["top_active"] = call_cnt.most_common(20)

    # NIL rate global
    total_cc = conf = nil_total = 0
    for key, cc in cc_matrix.items():
        s = cc.get("stats",{})
        total_cc += s.get("total_a",0)
        conf      += s.get("confirmed",0)
        nil_total += s.get("nil",0)
    if total_cc > 0:
        stats["nil_rate"] = round(nil_total / total_cc * 100, 1)
        stats["cc_summary"] = {
            "total":     total_cc,
            "confirmed": conf,
            "nil":       nil_total,
            "rate":      round(conf / total_cc * 100, 1),
        }

    return stats

def stats_to_html(stats):
    """Genereaza un raport HTML complet cu statistici si grafice SVG."""

    # Grafic bare orizontale
    def bar_chart(data, title, color="#2e75b6", max_items=12):
        if not data: return ""
        items = list(data.items())[:max_items]
        max_val = max(v for _,v in items) or 1
        rows = ""
        for label, val in items:
            pct = int(val / max_val * 200)
            rows += (
                "<tr><td style='text-align:right;padding:2px 8px;font-size:12px;"
                "white-space:nowrap;color:#555'>{}</td>"
                "<td><div style='width:{}px;height:14px;background:{};border-radius:2px;"
                "display:inline-block'></div>"
                "<span style='font-size:11px;margin-left:6px;color:#333'>{}</span></td></tr>"
            ).format(label, pct, color, val)
        return (
            "<div style='margin:10px 0'><b style='font-size:13px;color:#1a3a5c'>{}</b>"
            "<table style='border-collapse:collapse;margin-top:4px'>{}</table></div>"
        ).format(title, rows)

    # Grafic activitate pe ore (SVG inline)
    def hour_chart(by_hour):
        if not by_hour: return ""
        hours = list(range(0, 24))
        vals  = [by_hour.get(h, 0) for h in hours]
        max_v = max(vals) or 1
        W, H, pad = 480, 90, 30
        bars = ""
        bw   = (W - 2*pad) / 24
        for i, (h, v) in enumerate(zip(hours, vals)):
            bh = int(v / max_v * (H - 20))
            x  = int(pad + i * bw)
            y  = H - bh - 5
            bars += "<rect x='{}' y='{}' width='{}' height='{}' fill='#2e75b6' rx='1'/>".format(
                x+1, y, int(bw)-2, bh)
            if i % 4 == 0:
                bars += "<text x='{}' y='{}' font-size='9' fill='#888' text-anchor='middle'>{:02d}</text>".format(
                    x + bw//2, H+2, h)
        return (
            "<div style='margin:10px 0'><b style='font-size:13px;color:#1a3a5c'>Activitate per ora</b><br>"
            "<svg width='{}' height='{}' style='margin-top:4px'>{}</svg></div>"
        ).format(W, H+12, bars)

    # Tabel clasament
    def ranking_table(by_log):
        if not by_log: return ""
        rows = ""
        sorted_logs = sorted(by_log.items(), key=lambda x: -x[1].get("score",0))
        for i, (call, d) in enumerate(sorted_logs, 1):
            bg = "#fff9c4" if i==1 else "#f5f5f5" if i==2 else "white"
            rows += (
                "<tr style='background:{}'><td><b>#{}</b></td>"
                "<td><b>{}</b></td><td>{}</td><td style='color:green'>{}</td>"
                "<td style='color:red'>{}</td><td style='color:orange'>{}</td>"
                "<td>{}</td><td><b>{}</b></td></tr>"
            ).format(bg, i, call, d["format"].upper(),
                     d["valid"], d["errors"], d["dup"], d["total"], d["score"])
        return (
            "<h2 style='color:#2e75b6;border-bottom:2px solid #2e75b6;padding-bottom:3px'>Clasament</h2>"
            "<table style='border-collapse:collapse;width:100%'>"
            "<tr style='background:#1a3a5c;color:white'>"
            "<th style='padding:6px'>#</th><th>Indicativ</th><th>Format</th>"
            "<th>QSO Valide</th><th>Erori</th><th>Dup.</th><th>Total</th><th>SCOR</th></tr>"
            "{}</table>"
        ).format(rows)

    cc = stats.get("cc_summary",{})
    cc_html = ""
    if cc:
        cc_html = (
            "<div style='background:#e8f4fd;border-left:4px solid #2e75b6;"
            "padding:8px 14px;border-radius:3px;margin:10px 0'>"
            "<b>Cross-Check global:</b> {} QSO verificate &nbsp;|&nbsp; "
            "{} confirmate ({}%) &nbsp;|&nbsp; {} NIL &nbsp;|&nbsp; "
            "Rata NIL: <b style='color:red'>{:.1f}%</b></div>"
        ).format(cc.get("total",0), cc.get("confirmed",0), cc.get("rate",0),
                 cc.get("nil",0), stats.get("nil_rate",0))

    top_html = ""
    if stats.get("top_active"):
        rows = "".join(
            "<tr><td style='padding:2px 8px'><b>{}</b></td>"
            "<td style='text-align:right;padding:2px 8px'>{}</td></tr>".format(c, n)
            for c, n in stats["top_active"][:10]
        )
        top_html = (
            "<div style='display:inline-block;vertical-align:top;margin:10px 20px 10px 0'>"
            "<b style='font-size:13px;color:#1a3a5c'>Top 10 statii contactate</b>"
            "<table style='border-collapse:collapse;margin-top:4px'>{}</table></div>"
        ).format(rows)

    return """<!DOCTYPE html>
<html lang="ro">
<head><meta charset="UTF-8">
<title>Statistici — {name}</title>
<style>
body{{font-family:Arial,sans-serif;font-size:13px;margin:20px;color:#111}}
h1{{background:#1a3a5c;color:#fff;padding:10px 16px;border-radius:4px}}
h2{{color:#2e75b6;border-bottom:2px solid #2e75b6;padding-bottom:3px;margin-top:22px}}
.box{{display:inline-block;background:#f2f5f8;border-left:4px solid #2e75b6;
      padding:8px 16px;border-radius:3px;margin:4px}}
.val{{font-size:1.8em;font-weight:bold;color:#1a3a5c}}
.lbl{{font-size:.82em;color:#555}}
table td,table th{{border-bottom:1px solid #ddd;padding:4px 8px}}
@media print{{h1{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style>
</head>
<body>
<h1>Statistici Concurs — {name}</h1>
<p>Generat: {gen} | {nl} loguri procesate</p>
<div>
  <div class="box"><div class="val">{tq}</div><div class="lbl">Total QSO</div></div>
  <div class="box"><div class="val">{uc}</div><div class="lbl">Indicative unice</div></div>
  <div class="box"><div class="val">{nl2}</div><div class="lbl">Loguri</div></div>
  <div class="box"><div class="val" style="color:red">{nr:.1f}%</div><div class="lbl">Rata NIL globala</div></div>
</div>
{cc_html}
<h2>Clasament</h2>
{rank}
<h2>Distributie QSO-uri</h2>
<div style="display:flex;flex-wrap:wrap;gap:20px">
  {band_chart}
  {mode_chart}
  {county_chart}
</div>
{hour_chart}
<h2>Top statii contactate</h2>
{top}
<hr>
<p style="color:#888;font-size:11px">YO Contest Judge PRO v2.2 — YO8ACR | yo8acr@gmail.com</p>
</body></html>""".format(
        name=stats["contest_name"] or "Concurs",
        gen=stats["generated_at"],
        nl=stats["num_logs"],
        nl2=stats["num_logs"],
        tq=stats["total_qso"],
        uc=stats["unique_calls"],
        nr=stats.get("nil_rate",0),
        cc_html=cc_html,
        rank=ranking_table(stats["by_log"]),
        band_chart=bar_chart(stats["by_band"],"Per banda","#2e75b6"),
        mode_chart=bar_chart(stats["by_mode"],"Per mod","#2ecc71"),
        county_chart=bar_chart(dict(list(stats["by_county"].items())[:12]),"Top judete schimb","#e67e22"),
        hour_chart=hour_chart(stats["by_hour"]),
        top=top_html,
    )
