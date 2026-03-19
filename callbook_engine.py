#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Callbook Engine
Baza de date radioamatori YO: cautare, editare, adaugare, import XLSX.
Sursa: Callbook ARR 16.03.2026 + repetoare + intrari manuale.
"""
import json
import os
import re
import datetime

# Judete Romania cu coduri standard
JUDETE_RO = {
    "AB":"Alba","AR":"Arad","AG":"Arges","BC":"Bacau","BH":"Bihor",
    "BN":"Bistrita-Nasaud","BT":"Botosani","BV":"Brasov","BR":"Braila",
    "BZ":"Buzau","CS":"Caras-Severin","CL":"Calarasi","CJ":"Cluj",
    "CT":"Constanta","CV":"Covasna","DB":"Dambovita","DJ":"Dolj",
    "GL":"Galati","GR":"Giurgiu","GJ":"Gorj","HR":"Harghita",
    "HD":"Hunedoara","IL":"Ialomita","IS":"Iasi","IF":"Ilfov",
    "MM":"Maramures","MH":"Mehedinti","MS":"Mures","NT":"Neamt",
    "OT":"Olt","PH":"Prahova","SM":"Satu Mare","SJ":"Salaj",
    "SB":"Sibiu","SV":"Suceava","TR":"Teleorman","TM":"Timis",
    "TL":"Tulcea","VS":"Vaslui","VL":"Valcea","VN":"Vrancea",
    "B":"Bucuresti","S1":"Sector 1","S2":"Sector 2","S3":"Sector 3",
    "S4":"Sector 4","S5":"Sector 5","S6":"Sector 6",
}

# Mapare nume judet complet -> cod
_NAME_TO_CODE = {}
for code, name in JUDETE_RO.items():
    _NAME_TO_CODE[name.upper()] = code
    _NAME_TO_CODE[name.upper().replace("-","").replace(" ","")] = code

# Mapare pentru callbook (nume cu diacritice)
_CALLBOOK_COUNTY_MAP = {
    "ALBA":"AB","ARAD":"AR","ARGES":"AG","ARGEȘ":"AG",
    "BACAU":"BC","BACĂU":"BC","BIHOR":"BH",
    "BISTRITA-NASAUD":"BN","BISTRIȚA-NĂSĂUD":"BN",
    "BOTOSANI":"BT","BOTOȘANI":"BT","BRASOV":"BV","BRAȘOV":"BV",
    "BRAILA":"BR","BRĂILA":"BR","BUZAU":"BZ","BUZĂU":"BZ",
    "CARAS-SEVERIN":"CS","CARAȘ-SEVERIN":"CS",
    "CALARASI":"CL","CĂLĂRAȘI":"CL","CLUJ":"CJ",
    "CONSTANTA":"CT","CONSTANȚA":"CT","COVASNA":"CV",
    "DAMBOVITA":"DB","DÂMBOVIȚA":"DB","DOLJ":"DJ",
    "GALATI":"GL","GALAȚI":"GL","GIURGIU":"GR","GORJ":"GJ",
    "HARGHITA":"HR","HUNEDOARA":"HD","IALOMITA":"IL","IALOMIȚA":"IL",
    "IASI":"IS","IAȘI":"IS","ILFOV":"IF",
    "MARAMURES":"MM","MARAMUREȘ":"MM","MEHEDINTI":"MH","MEHEDINȚI":"MH",
    "MURES":"MS","MUREȘ":"MS","NEAMT":"NT","NEAMȚ":"NT","OLT":"OT",
    "PRAHOVA":"PH","SATU MARE":"SM","SALAJ":"SJ","SĂLAJ":"SJ",
    "SIBIU":"SB","SUCEAVA":"SV","TELEORMAN":"TR","TIMIS":"TM","TIMIȘ":"TM",
    "TULCEA":"TL","VASLUI":"VS","VALCEA":"VL","VÂLCEA":"VL",
    "VRANCEA":"VN","BUCURESTI":"B","BUCUREȘTI":"B",
    "SECTOR 1":"S1","SECTOR 2":"S2","SECTOR 3":"S3",
    "SECTOR 4":"S4","SECTOR 5":"S5","SECTOR 6":"S6",
}

def county_name_to_code(name):
    """Converteste numele unui judet (cu/fara diacritice) la codul standard."""
    n = (name or "").strip().upper()
    if n in _CALLBOOK_COUNTY_MAP:
        return _CALLBOOK_COUNTY_MAP[n]
    if n in _NAME_TO_CODE:
        return _NAME_TO_CODE[n]
    if n in JUDETE_RO:  # deja cod
        return n
    return ""

def county_code_to_name(code):
    return JUDETE_RO.get((code or "").upper().strip(), code)

class CallbookDB:
    """
    Baza de date radioamatori.
    - Incarca date din JSON (callbook oficial ARR)
    - Suporta adaugare/editare/stergere manuala
    - Salvare in fisier local callbook_user.json
    - Cautare dupa indicativ, nume, judet, oras
    """
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.records  = {}   # {call_upper: dict}
        self.rep_records = {}
        self._loaded  = False
        self._dirty   = False

    def _ensure_loaded(self):
        if self._loaded: return
        self._loaded = True
        # 1. Callbook oficial ARR
        fp = os.path.join(self.data_dir, "callbook_yo.json")
        if os.path.isfile(fp):
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                for r in data:
                    call = r.get("call","").upper().strip()
                    if call:
                        r["_src"] = "arr"
                        r["county_code"] = county_name_to_code(r.get("county",""))
                        self.records[call] = r
            except Exception:
                pass
        # 2. Repetoare
        fp2 = os.path.join(self.data_dir, "callbook_repetoare.json")
        if os.path.isfile(fp2):
            try:
                with open(fp2, encoding="utf-8") as f:
                    data2 = json.load(f)
                for r in data2:
                    call = r.get("call","").upper().strip()
                    if call: self.rep_records[call] = r
            except Exception:
                pass
        # 3. Intrari manuale utilizator
        fp3 = os.path.join(self.data_dir, "callbook_user.json")
        if os.path.isfile(fp3):
            try:
                with open(fp3, encoding="utf-8") as f:
                    user_data = json.load(f)
                for r in user_data:
                    call = r.get("call","").upper().strip()
                    if call:
                        r["_src"] = "user"
                        r["county_code"] = county_name_to_code(r.get("county",""))
                        self.records[call] = r  # suprascrie datele ARR
            except Exception:
                pass

    def lookup(self, call):
        """Returneaza inregistrarea pentru un indicativ sau None."""
        self._ensure_loaded()
        return self.records.get((call or "").upper().strip())

    def lookup_repeater(self, call):
        self._ensure_loaded()
        c = (call or "").upper().strip()
        for k, v in self.rep_records.items():
            if c in k.upper():
                return v
        return None

    def search(self, query, field="call", county_code="", limit=200):
        """
        Cauta in baza de date.
        field: 'call', 'name', 'city', 'county', 'any'
        """
        self._ensure_loaded()
        q = (query or "").upper().strip()
        cc = (county_code or "").upper().strip()
        results = []
        for call, rec in self.records.items():
            if cc and rec.get("county_code","") != cc:
                continue
            if not q:
                results.append(rec)
            elif field == "call" and q in call:
                results.append(rec)
            elif field == "name" and q in rec.get("name","").upper():
                results.append(rec)
            elif field == "city" and q in rec.get("city","").upper():
                results.append(rec)
            elif field == "county" and q in rec.get("county","").upper():
                results.append(rec)
            elif field == "any":
                if (q in call or q in rec.get("name","").upper() or
                    q in rec.get("city","").upper() or q in rec.get("county","").upper()):
                    results.append(rec)
            if len(results) >= limit:
                break
        return sorted(results, key=lambda r: r.get("call",""))

    def get_by_county(self, county_code):
        """Returneaza toti radioamatorii dintr-un judet (dupa cod)."""
        self._ensure_loaded()
        cc = (county_code or "").upper().strip()
        return sorted(
            [r for r in self.records.values() if r.get("county_code","") == cc],
            key=lambda r: r.get("call","")
        )

    def get_all_counties(self):
        """Returneaza lista de (cod, nume, count) sortata dupa cod."""
        self._ensure_loaded()
        from collections import Counter
        cnt = Counter(r.get("county_code","") for r in self.records.values())
        result = []
        for code, name in sorted(JUDETE_RO.items()):
            result.append((code, name, cnt.get(code, 0)))
        return result

    def add_or_update(self, rec):
        """Adauga sau actualizeaza o inregistrare (salvata in callbook_user.json)."""
        self._ensure_loaded()
        call = (rec.get("call","") or "").upper().strip()
        if not call:
            raise ValueError("Indicativul nu poate fi gol!")
        rec["call"] = call
        rec["_src"] = "user"
        rec["county_code"] = county_name_to_code(rec.get("county",""))
        rec["modified"] = datetime.datetime.now().strftime("%Y-%m-%d")
        self.records[call] = rec
        self._dirty = True
        self.save_user_data()

    def delete(self, call):
        """Sterge o inregistrare (doar cele cu _src='user')."""
        self._ensure_loaded()
        c = (call or "").upper().strip()
        rec = self.records.get(c)
        if rec and rec.get("_src") == "user":
            del self.records[c]
            self._dirty = True
            self.save_user_data()
            return True
        return False

    def save_user_data(self):
        """Salveaza toate inregistrarile cu _src='user' in callbook_user.json."""
        user_recs = [r for r in self.records.values() if r.get("_src") == "user"]
        fp = os.path.join(self.data_dir, "callbook_user.json")
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(user_recs, f, ensure_ascii=False, indent=2)

    def import_xlsx(self, filepath):
        """Importa un fisier XLSX cu indicative (format ARR sau custom)."""
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("pandas nu este instalat. Importul XLSX nu e disponibil.")
        df = pd.read_excel(filepath)
        cols = [c.upper().strip() for c in df.columns]
        added = updated = skipped = 0
        for _, row in df.iterrows():
            rec = {}
            for i, col in enumerate(cols):
                val = str(row.iloc[i]).strip() if str(row.iloc[i]) not in ("nan","NaT","") else ""
                if col in ("INDICATIVUL","CALL","INDICATIV"): rec["call"] = val.upper()
                elif col in ("TITULARUL","NAME","NUME"):       rec["name"] = val
                elif col in ("CLASA","CLASS","CATEGORIA"):     
                    try: rec["class"] = int(float(val))
                    except: rec["class"] = 0
                elif col in ("LOCALITATEA","CITY","ORAS"):     rec["city"] = val
                elif col in ("JUDETUL","COUNTY","JUDET"):      rec["county"] = val
                elif col in ("E-MAIL","EMAIL"):                rec["email"] = val
            if not rec.get("call"):
                skipped += 1; continue
            existing = self.records.get(rec["call"])
            if existing and existing.get("_src") == "arr":
                updated += 1
            else:
                added += 1
            self.add_or_update(rec)
        return {"added": added, "updated": updated, "skipped": skipped}

    def stats(self):
        self._ensure_loaded()
        from collections import Counter
        total = len(self.records)
        pub = sum(1 for r in self.records.values() if not r.get("private"))
        priv = total - pub
        user = sum(1 for r in self.records.values() if r.get("_src") == "user")
        by_class = Counter(r.get("class",0) for r in self.records.values())
        return {
            "total": total,
            "public": pub,
            "private": priv,
            "user_added": user,
            "by_class": dict(sorted(by_class.items())),
            "repeaters": len(self.rep_records),
        }
