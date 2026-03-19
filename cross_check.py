#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Cross-Check Engine v2.2
Detecteaza: NIL (Not In Log), Busted Call, Busted Band, Busted Time.
Compara N loguri intre ele.
FIX #2: toleranta implicita poate fi suprascrisa de regula concursului (tolerance_min).
"""
import datetime
from collections import defaultdict

DEFAULT_TOL = 3  # minute

_MODE_GRP = {
    "SSB":{"SSB","USB","LSB","AM","FM"},
    "CW":{"CW"},
    "DIGI":{"FT8","FT4","RTTY","PSK31","JT65","DIGI"},
}

def _norm_mode(m):
    u = (m or "").upper()
    for g, s in _MODE_GRP.items():
        if u in s: return g
    return u

def _dt(q):
    d, t = q.get("date","").strip(), q.get("time","").strip()
    if not d or not t: return None
    tc = t.replace(":", "")
    if len(tc) < 4: return None
    try:
        return datetime.datetime.strptime("{} {}:{}".format(d, tc[:2], tc[2:4]), "%Y-%m-%d %H:%M")
    except ValueError:
        return None

def cross_check(log_a, log_b, call_a, call_b, tol_min=DEFAULT_TOL, contest=None):
    """
    Verifica fiecare QSO din log_a daca apare in log_b.
    log_a = logul statie A (se verifica)
    log_b = logul statie B (furnizeaza confirmare)
    call_a, call_b = indicativele
    contest = dict cu regulile concursului (optional) — se foloseste tolerance_min daca exista

    Returneaza:
      confirmed   — idx din log_a confirmat
      nil         — Not In Log (absent in log_b)
      busted_call — indicativ gresit
      busted_band — banda gresita
      busted_time — diferenta timp > toleranta
      details     — {idx_a: {...}}
      stats       — statistici globale
    """
    # FIX #2 — preia toleranta din regula concursului daca exista
    if contest and "tolerance_min" in contest:
        tol_min = contest["tolerance_min"]

    res = {
        "confirmed":[], "nil":[], "busted_call":[],
        "busted_band":[], "busted_time":[], "details":{}, "stats":{},
    }
    call_a_up = call_a.upper()
    tol = datetime.timedelta(minutes=tol_min)

    # Index log_b dupa callsign
    b_idx = defaultdict(list)
    for i, q in enumerate(log_b):
        b_idx[q["callsign"].upper()].append(i)

    for ia, qa in enumerate(log_a):
        band_a = (qa.get("band") or "").lower()
        dt_a   = _dt(qa)

        detail = {
            "callsign_a": qa["callsign"],
            "band_a": band_a,
            "date_a": qa.get("date",""),
            "time_a": qa.get("time",""),
            "status": "nil",
            "match_idx_b": None,
            "delta_min": None,
            "issue": "Absent din logul opus (NIL)",
        }

        cands = b_idx.get(call_a_up, [])
        best_ib = None
        best_delta = None

        for ib in cands:
            qb     = log_b[ib]
            band_b = (qb.get("band") or "").lower()
            dt_b   = _dt(qb)
            if band_a and band_b and band_a != band_b:
                continue
            if dt_a and dt_b:
                delta = abs(dt_a - dt_b)
                if delta > tol: continue
                if best_delta is None or delta < best_delta:
                    best_ib = ib; best_delta = delta
            else:
                if best_ib is None:
                    best_ib = ib; best_delta = datetime.timedelta(0)

        if best_ib is not None:
            res["confirmed"].append(ia)
            detail["status"] = "confirmed"
            detail["match_idx_b"] = best_ib
            if best_delta is not None:
                detail["delta_min"] = round(best_delta.total_seconds() / 60, 1)
            detail["issue"] = ""
        else:
            # Diagnoza motivului

            # 1. Busted band
            for ib in cands:
                qb = log_b[ib]
                band_b = (qb.get("band") or "").lower()
                dt_b   = _dt(qb)
                if dt_a and dt_b and abs(dt_a - dt_b) > tol:
                    continue
                if band_a and band_b and band_a != band_b:
                    res["busted_band"].append((ia, ib))
                    detail.update({
                        "status":"busted_band", "match_idx_b":ib,
                        "issue":"Banda diferita: A={}, B={}".format(band_a, band_b),
                    })
                    break

            # 2. Busted time
            if detail["status"] == "nil":
                for ib in cands:
                    qb  = log_b[ib]
                    dt_b = _dt(qb)
                    if dt_a and dt_b:
                        delta = abs(dt_a - dt_b)
                        if delta > tol:
                            mins = round(delta.total_seconds() / 60, 1)
                            res["busted_time"].append((ia, ib, mins))
                            detail.update({
                                "status":"busted_time", "match_idx_b":ib,
                                "delta_min": mins,
                                "issue":"Diferenta timp: {} min (>{} min toleranta)".format(mins, tol_min),
                            })
                            break

            # 3. Busted call
            if detail["status"] == "nil":
                pfx = call_a_up[:3]
                for ib, qb in enumerate(log_b):
                    fc = qb["callsign"].upper()
                    if fc[:3] == pfx and fc != call_a_up:
                        band_b = (qb.get("band") or "").lower()
                        dt_b   = _dt(qb)
                        if band_a and band_b and band_a != band_b:
                            continue
                        if dt_a and dt_b and abs(dt_a - dt_b) > tol:
                            continue
                        res["busted_call"].append((ia, ib, fc))
                        detail.update({
                            "status":"busted_call", "match_idx_b":ib,
                            "issue":"Posibil indicativ gresit: in logul B apare '{}'".format(fc),
                        })
                        break

            if detail["status"] == "nil":
                res["nil"].append(ia)

        res["details"][ia] = detail

    total = len(log_a)
    confirmed = len(res["confirmed"])
    res["stats"] = {
        "total_a":      total,
        "confirmed":    confirmed,
        "nil":          len(res["nil"]),
        "busted_call":  len(res["busted_call"]),
        "busted_band":  len(res["busted_band"]),
        "busted_time":  len(res["busted_time"]),
        "tolerance_min": tol_min,
        "confirm_pct":  round(confirmed / max(total, 1) * 100, 1),
    }
    return res


def cross_check_all(logs, tol_min=DEFAULT_TOL, contest=None):
    """
    Cross-check N loguri intre ele.
    logs = [{"callsign": str, "qsos": [...]}, ...]
    contest = dict cu regulile concursului (pentru tolerance_min)
    Returneaza matrix (A vs B) si summary per statie.
    """
    n = len(logs)
    matrix = {}
    for i in range(n):
        for j in range(n):
            if i == j: continue
            key = "{}_vs_{}".format(logs[i]["callsign"], logs[j]["callsign"])
            matrix[key] = cross_check(
                logs[i]["qsos"], logs[j]["qsos"],
                logs[i]["callsign"], logs[j]["callsign"],
                tol_min, contest
            )
    summary = {}
    for i, log in enumerate(logs):
        call = log["callsign"]
        conf = nil = 0
        for j in range(n):
            if i == j: continue
            k = "{}_vs_{}".format(call, logs[j]["callsign"])
            if k in matrix:
                s = matrix[k]["stats"]
                conf += s["confirmed"]
                nil  += s["nil"]
        summary[call] = {
            "total": len(log["qsos"]),
            "confirmed": conf,
            "nil": nil,
        }
    return {"matrix": matrix, "summary": summary}
