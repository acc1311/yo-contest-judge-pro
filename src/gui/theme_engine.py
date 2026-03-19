#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Theme Engine v2.2
Gestioneaza temele predefinite, temele custom si fonturile.
"""
import json, os, copy

# ── Teme predefinite ──────────────────────────────────────────
THEMES = {
    "Albastru inchis": {
        "_dark": True,
        "BG":"#1e2a38","BG2":"#253447","BG3":"#2e3f55",
        "FG":"#e8edf3","ACC":"#2e75b6","ACC2":"#4a9de0",
        "GRN":"#2ecc71","RED":"#e74c3c","YLW":"#f1c40f",
        "ORG":"#f39c12","GRY":"#7f8c8d","WHT":"#ffffff",
    },
    "Negru clasic": {
        "_dark": True,
        "BG":"#0d0d0d","BG2":"#1a1a1a","BG3":"#262626",
        "FG":"#e0e0e0","ACC":"#00bcd4","ACC2":"#4dd0e1",
        "GRN":"#4caf50","RED":"#f44336","YLW":"#ffeb3b",
        "ORG":"#ff9800","GRY":"#757575","WHT":"#ffffff",
    },
    "Verde military": {
        "_dark": True,
        "BG":"#1a2416","BG2":"#243020","BG3":"#2e3c28",
        "FG":"#d4e8c2","ACC":"#6aaa3a","ACC2":"#8bc34a",
        "GRN":"#4caf50","RED":"#e53935","YLW":"#cddc39",
        "ORG":"#ff9800","GRY":"#78909c","WHT":"#ffffff",
    },
    "Gri profesional": {
        "_dark": True,
        "BG":"#2b2b2b","BG2":"#3c3c3c","BG3":"#4a4a4a",
        "FG":"#f0f0f0","ACC":"#5b9bd5","ACC2":"#79b8f5",
        "GRN":"#6abf69","RED":"#e57373","YLW":"#fff176",
        "ORG":"#ffb74d","GRY":"#9e9e9e","WHT":"#ffffff",
    },
    "Alb (zi)": {
        "_dark": False,
        "BG":"#f5f5f5","BG2":"#ffffff","BG3":"#e0e0e0",
        "FG":"#212121","ACC":"#1565c0","ACC2":"#1976d2",
        "GRN":"#2e7d32","RED":"#c62828","YLW":"#f57f17",
        "ORG":"#e65100","GRY":"#757575","WHT":"#1a1a1a",
    },
    "Sepia": {
        "_dark": False,
        "BG":"#f5f0e8","BG2":"#fffdf7","BG3":"#ede8dc",
        "FG":"#3e2c1c","ACC":"#8b5e3c","ACC2":"#b07848",
        "GRN":"#4a7c4e","RED":"#a33a2a","YLW":"#c8960c",
        "ORG":"#c06020","GRY":"#8a7060","WHT":"#2a1a0a",
    },
    "Rosu inchis": {
        "_dark": True,
        "BG":"#1a0a0a","BG2":"#2a1010","BG3":"#3a1818",
        "FG":"#f0e0e0","ACC":"#cc3333","ACC2":"#e05555",
        "GRN":"#4caf50","RED":"#ff5555","YLW":"#ffcc44",
        "ORG":"#ff8800","GRY":"#886666","WHT":"#ffffff",
    },
    "Albastru electric": {
        "_dark": True,
        "BG":"#050a1a","BG2":"#0a1430","BG3":"#0f1e48",
        "FG":"#c8e0ff","ACC":"#3399ff","ACC2":"#66bbff",
        "GRN":"#00e676","RED":"#ff1744","YLW":"#ffea00",
        "ORG":"#ff6d00","GRY":"#607d8b","WHT":"#ffffff",
    },
}

DEFAULT_THEME = "Albastru inchis"

FONT_FAMILIES = ["Consolas","Courier New","Lucida Console","DejaVu Sans Mono",
                 "Liberation Mono","Arial","Helvetica","Segoe UI","Tahoma"]
FONT_SIZES    = [8, 9, 10, 11, 12, 13, 14]

def get_theme(name):
    """Returneaza copia unui tema dupa nume (built-in sau custom)."""
    return copy.deepcopy(THEMES.get(name, THEMES[DEFAULT_THEME]))

def theme_names():
    return list(THEMES.keys())

def is_dark(theme_dict):
    return theme_dict.get("_dark", True)

# ── Teme custom (salvate/incarcate din JSON) ──────────────────
def load_custom_themes(themes_dir):
    """Incarca temele custom din <data>/themes/*.json ."""
    loaded = {}
    if not themes_dir or not os.path.isdir(themes_dir):
        return loaded
    for fn in os.listdir(themes_dir):
        if not fn.endswith(".json"): continue
        fp = os.path.join(themes_dir, fn)
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name") or os.path.splitext(fn)[0]
            # Valideaza ca are cheile necesare
            required = {"BG","BG2","BG3","FG","ACC","ACC2","GRN","RED","YLW","ORG","GRY","WHT"}
            if required.issubset(data.keys()):
                THEMES[name] = data
                loaded[name] = data
        except Exception:
            pass
    return loaded

def save_custom_theme(name, theme_dict, themes_dir):
    """Salveaza o tema custom in <data>/themes/<name>.json ."""
    os.makedirs(themes_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
    fp = os.path.join(themes_dir, "{}.json".format(safe_name))
    data = dict(theme_dict)
    data["name"] = name
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    THEMES[name] = copy.deepcopy(data)
    return fp

def delete_custom_theme(name, themes_dir):
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
    fp = os.path.join(themes_dir, "{}.json".format(safe_name))
    if os.path.isfile(fp):
        os.remove(fp)
    if name in THEMES and name not in _BUILTIN_NAMES:
        del THEMES[name]
    return True

# Retine numele built-in ca sa nu fie sterse accidental
_BUILTIN_NAMES = set(THEMES.keys())
