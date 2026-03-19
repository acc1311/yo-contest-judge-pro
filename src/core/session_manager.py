#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Session Manager
Salveaza/incarca sesiunea completa de arbitraj (.yojudge JSON).
"""
import json
import os
import datetime

SESSION_EXT = ".yojudge"
SESSION_VERSION = "2.0"

def save_session(filepath, state):
    """
    Salveaza sesiunea completa.
    state = {
      contest_id, tolerance, loaded_logs, val_results,
      score_results, cc_matrix, ranking
    }
    """
    out = {
        "version":    SESSION_VERSION,
        "saved_at":   datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "contest_id": state.get("contest_id",""),
        "tolerance":  state.get("tolerance", 3),
        "logs":       {},
        "validation": {},
        "scores":     {},
        "cc_matrix":  {},
        "ranking":    state.get("ranking", []),
    }

    # Loguri importate
    for call, pr in state.get("loaded_logs", {}).items():
        out["logs"][call] = {
            "filename": pr.get("filename",""),
            "format":   pr.get("format",""),
            "callsign": pr.get("callsign",""),
            "total":    pr.get("total", 0),
            "qsos":     pr.get("qsos", []),
            "errors":   [
                e if isinstance(e, dict) else e.to_dict()
                for e in pr.get("errors", [])
            ],
        }

    # Rezultate validare
    for call, vr in state.get("val_results", {}).items():
        if not vr: continue
        out["validation"][call] = {
            "valid_count":   vr.get("valid_count", 0),
            "error_count":   vr.get("error_count", 0),
            "warning_count": vr.get("warning_count", 0),
            "qso_flags":     {str(k): v for k,v in vr.get("qso_flags",{}).items()},
            "errors": [
                e.to_dict() if hasattr(e,"to_dict") else e
                for e in vr.get("errors", [])
            ],
        }

    # Scoruri
    for call, sr in state.get("score_results", {}).items():
        if not sr: continue
        s = dict(sr)
        if "mult_set" in s:
            s["mult_set"] = list(s["mult_set"])
        out["scores"][call] = s

    # Cross-check matrix
    for key, cc in state.get("cc_matrix", {}).items():
        if not cc: continue
        out["cc_matrix"][key] = {
            "confirmed":   cc.get("confirmed",[]),
            "nil":         cc.get("nil",[]),
            "busted_call": cc.get("busted_call",[]),
            "busted_band": cc.get("busted_band",[]),
            "busted_time": cc.get("busted_time",[]),
            "stats":       cc.get("stats",{}),
            "details":     {str(k): v for k,v in cc.get("details",{}).items()},
        }

    if not filepath.endswith(SESSION_EXT):
        filepath += SESSION_EXT

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)

    return filepath

def load_session(filepath):
    """
    Incarca o sesiune salvata.
    Returneaza state dict cu aceleasi chei ca save_session.
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    ver = data.get("version","1.0")

    state = {
        "contest_id":    data.get("contest_id","simplu"),
        "tolerance":     data.get("tolerance", 3),
        "loaded_logs":   {},
        "val_results":   {},
        "score_results": {},
        "cc_matrix":     {},
        "ranking":       data.get("ranking",[]),
    }

    # Reconstituie loguri
    for call, log in data.get("logs",{}).items():
        state["loaded_logs"][call] = {
            "filename":  log.get("filename",""),
            "format":    log.get("format",""),
            "callsign":  log.get("callsign", call),
            "total":     log.get("total", len(log.get("qsos",[]))),
            "qsos":      log.get("qsos",[]),
            "errors":    log.get("errors",[]),
            "header":    log.get("header",{}),
        }

    # Reconstituie validari
    for call, vr in data.get("validation",{}).items():
        state["val_results"][call] = {
            "valid_count":      vr.get("valid_count",0),
            "error_count":      vr.get("error_count",0),
            "warning_count":    vr.get("warning_count",0),
            "qso_flags":        {int(k): v for k,v in vr.get("qso_flags",{}).items()},
            "errors":           vr.get("errors",[]),
            "duplicate_groups": {},
        }

    # Scoruri
    for call, sr in data.get("scores",{}).items():
        if "mult_set" in sr and isinstance(sr["mult_set"], list):
            sr["mult_set"] = set(sr["mult_set"])
        state["score_results"][call] = sr

    # Cross-check
    for key, cc in data.get("cc_matrix",{}).items():
        cc_restored = dict(cc)
        cc_restored["details"] = {int(k): v for k,v in cc.get("details",{}).items()}
        state["cc_matrix"][key] = cc_restored

    return state

def session_info(filepath):
    """Returneaza informatii rapide despre o sesiune (fara a incarca QSO-urile)."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        logs = data.get("logs",{})
        return {
            "version":    data.get("version","?"),
            "saved_at":   data.get("saved_at","?"),
            "contest_id": data.get("contest_id","?"),
            "logs":       len(logs),
            "calls":      list(logs.keys()),
            "total_qso":  sum(v.get("total",0) for v in logs.values()),
        }
    except Exception as e:
        return {"error": str(e)}
