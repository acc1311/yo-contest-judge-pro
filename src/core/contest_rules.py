#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Reguli concursuri v2.2
Contine toate concursurile built-in + incarcator JSON pentru concursuri custom.
"""
import os
import json
import warnings

BANDS_HF  = ["160m","80m","40m","30m","20m","17m","15m","12m","10m"]
BANDS_VHF = ["6m","2m","70cm","23cm"]
BANDS_ALL = BANDS_HF + BANDS_VHF
MODES_ALL = ["SSB","CW","DIGI","FT8","FT4","RTTY","AM","FM","PSK31","JT65"]

RST_RANGES = {
    "SSB":(11,59), "AM":(11,59), "FM":(11,59),
    "CW":(111,599), "RTTY":(111,599), "PSK31":(111,599),
    "FT8":(111,599), "FT4":(111,599), "JT65":(111,599), "DIGI":(111,599),
}

YO_COUNTIES = [
    "AB","AR","AG","BC","BH","BN","BT","BV","BR","BZ",
    "CS","CL","CJ","CT","CV","DB","DJ","GL","GR","GJ",
    "HR","HD","IL","IS","IF","MM","MH","MS","NT","OT",
    "PH","SM","SJ","SB","SV","TR","TM","TL","VS","VL","VN","B",
]

DXCC_PREFIXES = {
    "YO":"Romania","DL":"Germany","G":"England","F":"France",
    "I":"Italy","SP":"Poland","OK":"Czech Republic","OM":"Slovakia",
    "HA":"Hungary","9A":"Croatia","S5":"Slovenia","OE":"Austria",
    "HB9":"Switzerland","PA":"Netherlands","ON":"Belgium",
    "LY":"Lithuania","YL":"Latvia","ES":"Estonia",
    "OH":"Finland","SM":"Sweden","LA":"Norway","OZ":"Denmark",
    "UA":"Russia","UR":"Ukraine","ER":"Moldova",
    "LZ":"Bulgaria","SV":"Greece","YU":"Serbia",
    "Z3":"North Macedonia","E7":"Bosnia","T9":"Bosnia",
    "4O":"Montenegro","ZA":"Albania","TA":"Turkey",
    "W":"USA","K":"USA","VE":"Canada","JA":"Japan",
    "VK":"Australia","ZL":"New Zealand","PY":"Brazil","LU":"Argentina",
}

# ── Concursuri built-in ────────────────────────────────────────
BUILT_IN = {
    "simplu": {
        "name":"Log Simplu / Fara concurs",
        "cabrillo_name":"SIMPLU",
        "scoring_mode":"per_qso",
        "points_per_qso":1,
        "min_qso":0,
        "allowed_bands":BANDS_ALL,
        "allowed_modes":MODES_ALL,
        "duration_hours":0,
        "exchange":"none",
        "multiplier":"none",
        "cross_check":False,
        "description":"Log general, fara reguli speciale.",
    },
    "maraton": {
        "name":"Maraton Ion Creanga",
        "cabrillo_name":"MARATON ION CREANGA",
        "scoring_mode":"maraton_ic",
        "points_per_qso":0,
        "min_qso":100,
        "allowed_bands":["80m"],
        "allowed_modes":["SSB","PH"],
        "duration_hours":336,
        "exchange":"none",
        "multiplier":"none",
        "cross_check":True,
        "description":"2-15 Martie, 80m SSB. /IC club=10pct, /IC individual=5pct, YP8IC/YR8TGN=20pct. Max 1 QSO/zi/statie. Min 100 QSO diploma.",
        "special_calls":{"YP8IC":20,"YR8TGN":20},
        "ic_club_points":10,
        "ic_individual_points":5,
        # Lista cluburi IC (FIX #4) — adauga indicativele de club fara /IC
        "ic_clubs":["YO8KZG","YO8TTT","YO8CRE","YO8CMG","YO8BPQ"],
        "max_qso_per_day":1,   # FIX #1 — verificat acum in scoring_engine
    },
    "cupa_elevului": {
        "name":"Cupa Elevului",
        "cabrillo_name":"CUPA ELEVULUI",
        "scoring_mode":"per_qso_x_mult",
        "points_per_qso":2,
        "min_qso":0,
        "allowed_bands":["80m"],
        "allowed_modes":["SSB","PH"],
        "duration_hours":2,
        "exchange":"county",
        "multiplier":"county",
        "cross_check":True,
        "check_serial":True,   # FIX #7 — verificare serial secvential
        "time_windows":[{"start":"09:00","end":"11:00"}],  # FIX #6
        "description":"30 Martie, 80m SSB. 2 etape. Schimb: RS+serial+judet. 2pct/QSO. Multiplicatori: judete. Organizator: Palatul Copiilor Piatra Neamt.",
        "organizer":"Palatul Copiilor Piatra Neamt",
        "url":"https://www.radioamator.ro/contest/us/cupa_elevilor.pdf",
    },
    "yodxhf": {
        "name":"YO DX HF Contest",
        "cabrillo_name":"YO DX HF",
        "scoring_mode":"per_band",
        "points_per_qso":1,
        "min_qso":0,
        "allowed_bands":BANDS_HF,
        "allowed_modes":["SSB","CW"],
        "duration_hours":24,
        "exchange":"county",
        "multiplier":"dxcc_band",
        "cross_check":True,
        "description":"Concurs DX 24h SSB+CW. Multiplicatori: DXCC per banda.",
    },
    "yovhf": {
        "name":"YO VHF Contest",
        "cabrillo_name":"YO VHF",
        "scoring_mode":"distance",
        "points_per_qso":1,
        "min_qso":0,
        "allowed_bands":["6m","2m","70cm","23cm"],
        "allowed_modes":["SSB","FM","CW"],
        "duration_hours":6,
        "exchange":"locator",   # FIX #5 — trigger validare locator
        "multiplier":"locator_field",
        "cross_check":True,
        "description":"Concurs VHF 6h. Puncte = distanta km din locator.",
    },
    "fieldday": {
        "name":"Field Day",
        "cabrillo_name":"FIELD DAY",
        "scoring_mode":"per_qso",
        "points_per_qso":2,
        "min_qso":0,
        "allowed_bands":BANDS_HF,
        "allowed_modes":MODES_ALL,
        "duration_hours":24,
        "exchange":"county",
        "multiplier":"county",
        "cross_check":True,
        "description":"Field Day 24h. 2 puncte/QSO. Multiplicatori: judete.",
    },
    "la_multi_ani": {
        "name":"La Multi Ani YO!",
        "cabrillo_name":"LA MULTI ANI YO",
        "scoring_mode":"per_qso_x_mult",
        "points_per_qso":2,
        "min_qso":0,
        "allowed_bands":["80m"],
        "allowed_modes":["SSB","PH"],
        "duration_hours":2,
        "exchange":"county",
        "multiplier":"county",
        "cross_check":True,
        "check_serial":True,
        "time_windows":[{"start":"15:00","end":"17:00"}],  # FIX #6
        "description":"2 Ianuarie, 80m SSB. 2 etape. Schimb: RS+serial+judet. Organizator: FRR.",
        "organizer":"FRR",
        "url":"https://www.radioamator.ro/contest/us/la_multi_ani_yo.pdf",
    },
    "cupa_moldovei": {
        "name":"Cupa Moldovei",
        "cabrillo_name":"CUPA MOLDOVEI",
        "scoring_mode":"cupa_moldovei",
        "points_per_qso":2,
        "points_cw":4,
        "points_moldova_ssb":4,
        "points_moldova_cw":8,
        "min_qso":0,
        "allowed_bands":["80m"],
        "allowed_modes":["SSB","CW","PH"],
        "duration_hours":2,
        "exchange":"county",
        "multiplier":"county_dxcc",   # FIX #3 — judete + prefix DXCC tara straina
        "cross_check":True,
        "check_serial":True,
        "time_windows":[                  # FIX #6 — 2 etape
            {"start":"15:00","end":"16:00"},
            {"start":"16:00","end":"17:00"},
        ],
        "moldova_counties":["BC","BT","GL","IS","NT","SV","VN","VS"],
        "description":"A treia luni din feb, 2 etape x 1h (15-16, 16-17 UTC). 80m CW+SSB. QSO cu Moldova: SSB=4pct/CW=8pct. QSO YO-YO: SSB=2pct/CW=4pct. Mult: judete+prefix tara.",
        "categories":{
            "A":"Statii de club CW & SSB",
            "B":"Statii individuale CW",
            "C":"Statii individuale SSB",
            "D":"Statii individuale CW & SSB",
            "E":"Statii individuale YL CW",
            "F":"Statii individuale YL SSB",
            "G":"Receptori CW & SSB"
        },
        "organizer":"Radioclubul Municipal Bacau",
        "email":"yo8bfb@gmail.com",
        "log_deadline_days":10,
    },
}

def load_contests(contests_dir=None):
    """Incarca built-in + JSON-urile custom din directorul contests/."""
    contests = {}
    contests.update(BUILT_IN)
    load_errors = []

    # Construieste set cu cheile si numele built-in pentru detectie duplicate
    builtin_keys  = set(BUILT_IN.keys())
    builtin_names = {v["name"].strip().lower() for v in BUILT_IN.values()}

    if contests_dir and os.path.isdir(contests_dir):
        for fn in sorted(os.listdir(contests_dir)):
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(contests_dir, fn)
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                cid = os.path.splitext(fn)[0]

                # FIX — sari peste JSON-urile care dubleaza un concurs built-in
                # (fie prin cheie identica, fie prin nume identic)
                if cid in builtin_keys:
                    continue
                json_name = data.get("name", "").strip().lower()
                if json_name and json_name in builtin_names:
                    continue

                for k, v in BUILT_IN["simplu"].items():
                    data.setdefault(k, v)
                contests[cid] = data
            except Exception as e:
                # FIX #10 — nu mai ignora silentios, colecteaza erorile
                load_errors.append((fn, str(e)))
    return contests, load_errors

def save_contest_json(contest_id, data, contests_dir):
    """Salveaza un concurs custom in contests/."""
    os.makedirs(contests_dir, exist_ok=True)
    fp = os.path.join(contests_dir, "{}.json".format(contest_id))
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return fp

def delete_contest_json(contest_id, contests_dir):
    fp = os.path.join(contests_dir, "{}.json".format(contest_id))
    if os.path.isfile(fp):
        os.remove(fp)
        return True
    return False

def freq_to_band(freq_khz):
    try:
        f = float(freq_khz)
    except (ValueError, TypeError):
        return None
    if 1800  <= f <= 2000:    return "160m"
    if 3500  <= f <= 3800:    return "80m"
    if 7000  <= f <= 7200:    return "40m"
    if 10100 <= f <= 10150:   return "30m"
    if 14000 <= f <= 14350:   return "20m"
    if 18068 <= f <= 18168:   return "17m"
    if 21000 <= f <= 21450:   return "15m"
    if 24890 <= f <= 24990:   return "12m"
    if 28000 <= f <= 29700:   return "10m"
    if 50000 <= f <= 54000:   return "6m"
    if 144000<= f <= 146000:  return "2m"
    if 430000<= f <= 440000:  return "70cm"
    if 1240000<=f<=1300000:   return "23cm"
    return None

def guess_dxcc(callsign):
    call = callsign.upper().strip()
    for ln in (4, 3, 2, 1):
        p = call[:ln]
        if p in DXCC_PREFIXES:
            return DXCC_PREFIXES[p]
    return "Unknown"

def is_valid_county(county):
    return county.upper().strip() in YO_COUNTIES
