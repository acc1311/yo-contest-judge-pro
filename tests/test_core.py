#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO v2.2 — Unit Tests
Ruleaza cu: python -m pytest tests/test_core.py -v
"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# ── contest_rules ─────────────────────────────────────────────
from core.contest_rules import (
    load_contests, freq_to_band, guess_dxcc, is_valid_county,
    BUILT_IN, BANDS_ALL, MODES_ALL, YO_COUNTIES
)

class TestContestRules(unittest.TestCase):
    def test_builtin_contests_loaded(self):
        c, errs = load_contests()
        self.assertEqual(errs, [])
        for cid in ("simplu","maraton","yodxhf","yovhf","cupa_moldovei"):
            self.assertIn(cid, c)

    def test_maraton_has_max_qso_per_day(self):
        c, _ = load_contests()
        self.assertEqual(c["maraton"]["max_qso_per_day"], 1)

    def test_maraton_has_ic_clubs(self):
        c, _ = load_contests()
        self.assertIn("ic_clubs", c["maraton"])
        self.assertIsInstance(c["maraton"]["ic_clubs"], list)

    def test_cupa_moldovei_multiplier_county_dxcc(self):
        c, _ = load_contests()
        self.assertEqual(c["cupa_moldovei"]["multiplier"], "county_dxcc")

    def test_cupa_tomis_tolerance_in_json(self):
        c, _ = load_contests()
        # Cupa Tomis e in contests/ dir — verifica doar daca e incarcat
        # Regula principala: tolerance_min trebuie sa fie in datele concursului
        cupa_t = c.get("cupa_tomis")
        if cupa_t:
            self.assertEqual(cupa_t.get("tolerance_min"), 5)

    def test_time_windows_present(self):
        c, _ = load_contests()
        self.assertIn("time_windows", c["cupa_moldovei"])
        self.assertEqual(len(c["cupa_moldovei"]["time_windows"]), 2)

    def test_freq_to_band_hf(self):
        self.assertEqual(freq_to_band(14200), "20m")
        self.assertEqual(freq_to_band(7050),  "40m")
        self.assertEqual(freq_to_band(3750),  "80m")
        self.assertEqual(freq_to_band(21200), "15m")
        self.assertEqual(freq_to_band(28500), "10m")
        self.assertEqual(freq_to_band(1900),  "160m")

    def test_freq_to_band_vhf(self):
        self.assertEqual(freq_to_band(144300), "2m")
        self.assertEqual(freq_to_band(50200),  "6m")
        self.assertEqual(freq_to_band(432100), "70cm")

    def test_freq_to_band_invalid(self):
        self.assertIsNone(freq_to_band(0))
        self.assertIsNone(freq_to_band(99999))
        self.assertIsNone(freq_to_band("abc"))

    def test_guess_dxcc(self):
        self.assertEqual(guess_dxcc("YO8ACR"), "Romania")
        self.assertEqual(guess_dxcc("DL1ABC"), "Germany")
        self.assertEqual(guess_dxcc("W1AW"),   "USA")

    def test_is_valid_county(self):
        for c in ["IS","BT","VS","B","TM","CJ","CL"]:
            self.assertTrue(is_valid_county(c))
        for c in ["XX","ZZ","RO","EU"]:
            self.assertFalse(is_valid_county(c))

    def test_yo_counties_count(self):
        self.assertEqual(len(YO_COUNTIES), 42)

# ── scoring_engine ────────────────────────────────────────────
from core.scoring_engine import (
    validate_log, score_log, build_ranking, _chk_call, _chk_locator,
    _CALL_RE, _LOC_RE
)

class TestCallValidation(unittest.TestCase):
    def test_normal_calls(self):
        for c in ["YO8ACR","DL1ABC","W1AW","G3ABC","9A1AA"]:
            ok, _ = _chk_call(c)
            self.assertTrue(ok, "Should be valid: {}".format(c))

    def test_portable_suffixes(self):
        for c in ["YO8ACR/P","YO8ACR/M","YO8ACR/MM","YO8ACR/AM","YO8ACR/QRP"]:
            ok, _ = _chk_call(c)
            self.assertTrue(ok, "Portable suffix should be valid: {}".format(c))

    def test_invalid_calls(self):
        for c in ["","INVALID","123","ABC"]:
            ok, _ = _chk_call(c)
            self.assertFalse(ok, "Should be invalid: {}".format(c))

class TestLocatorValidation(unittest.TestCase):
    def test_valid_locators(self):
        for loc in ["KN36","KN46","JO31","KN36LD","JO31MX"]:
            ok, msg = _chk_locator(loc)
            self.assertTrue(ok, "Should be valid: {} — {}".format(loc, msg))

    def test_invalid_locators(self):
        for loc in ["","XX99","KN","123456","ABCDEF"]:
            ok, _ = _chk_locator(loc)
            self.assertFalse(ok, "Should be invalid: {}".format(loc))

class TestValidateLog(unittest.TestCase):
    def _qso(self, **kw):
        q = {"callsign":"YO3ABC","band":"80m","mode":"SSB",
             "rst_s":"59","rst_r":"59","date":"2024-03-15",
             "time":"10:00","exchange":"IS","serial":"001",
             "locator":"","freq":"3750","note":"","dxcc":"",
             "my_call":"","_line":1,"_raw":"","_fmt":"cabrillo"}
        q.update(kw)
        return q

    def test_valid_qso(self):
        res = validate_log([self._qso()])
        self.assertEqual(res["valid_count"], 1)
        self.assertEqual(res["error_count"], 0)

    def test_missing_callsign(self):
        res = validate_log([self._qso(callsign="")])
        self.assertGreater(res["error_count"], 0)

    def test_duplicate_detection(self):
        qsos = [self._qso(callsign="YO3ABC"), self._qso(callsign="YO3ABC")]
        res = validate_log(qsos)
        self.assertEqual(len(res["duplicate_groups"]), 1)

    def test_bad_band_in_contest(self):
        contests, _ = load_contests()
        qso = self._qso(band="20m")  # 20m nepermis in maraton (doar 80m)
        res = validate_log([qso], contest_id="maraton", contests=contests)
        types = [e.err_type for e in res["errors"]]
        self.assertIn("BAD_BAND", types)

    def test_locator_validation_vhf(self):
        contests, _ = load_contests()
        qso = self._qso(band="2m", mode="SSB", exchange="INVALID", locator="INVALID")
        res = validate_log([qso], contest_id="yovhf", contests=contests)
        types = [e.err_type for e in res["errors"]]
        self.assertIn("BAD_LOCATOR", types)

class TestMaratonMaxQsoPerDay(unittest.TestCase):
    def _qso(self, call, date, hour="10:00"):
        return {"callsign":call,"band":"80m","mode":"SSB",
                "rst_s":"59","rst_r":"59","date":date,"time":hour,
                "exchange":"","serial":"","locator":"","freq":"3750",
                "note":"","dxcc":"","my_call":"","_line":1,"_raw":"","_fmt":"cabrillo"}

    def test_one_qso_per_day_ok(self):
        contests, _ = load_contests()
        qsos = [
            self._qso("YO5IC/IC", "2024-03-02", "10:00"),
            self._qso("YO5IC/IC", "2024-03-03", "10:00"),  # alta zi - OK
        ]
        result = score_log(qsos, "maraton", station_call="YO8ACR",
                          contests=contests)
        self.assertEqual(result["maraton_dup_qsos"], 0)

    def test_two_qso_same_day_flagged(self):
        contests, _ = load_contests()
        qsos = [
            self._qso("YO5IC/IC", "2024-03-02", "10:00"),
            self._qso("YO5IC/IC", "2024-03-02", "11:00"),  # aceeasi zi - DUP
        ]
        result = score_log(qsos, "maraton", station_call="YO8ACR",
                          contests=contests)
        self.assertEqual(result["maraton_dup_qsos"], 1)

# ── cross_check ───────────────────────────────────────────────
from core.cross_check import cross_check

class TestCrossCheck(unittest.TestCase):
    def _q(self, call, band="80m", date="2024-03-15", time="10:00"):
        return {"callsign":call,"band":band,"date":date,"time":time,
                "mode":"SSB","rst_s":"59","rst_r":"59","exchange":"IS"}

    def test_confirmed(self):
        log_a = [self._q("YO3ABC")]
        log_b = [self._q("YO8ACR")]
        r = cross_check(log_a, log_b, "YO8ACR", "YO3ABC")
        self.assertEqual(len(r["confirmed"]), 1)

    def test_nil(self):
        log_a = [self._q("YO3ABC")]
        log_b = [self._q("YO5XYZ")]  # alta statie — NIL
        r = cross_check(log_a, log_b, "YO8ACR", "YO3ABC")
        self.assertEqual(len(r["nil"]), 1)

    def test_tolerance_from_contest(self):
        log_a = [self._q("YO3ABC", time="10:03")]
        log_b = [self._q("YO8ACR", time="10:00")]
        # toleranta 2 min — 3 min diferenta => busted_time (statie gasita dar timp diferit)
        r2 = cross_check(log_a, log_b, "YO8ACR", "YO3ABC", tol_min=2)
        self.assertEqual(r2["details"][0]["status"], "busted_time")
        # toleranta 5 min — 3 min diferenta => confirmat
        r5 = cross_check(log_a, log_b, "YO8ACR", "YO3ABC", tol_min=5)
        self.assertIn(0, r5["confirmed"])

    def test_contest_tolerance_override(self):
        log_a = [self._q("YO3ABC", time="10:04")]
        log_b = [self._q("YO8ACR", time="10:00")]
        contest_5min = {"tolerance_min": 5}
        r = cross_check(log_a, log_b, "YO8ACR", "YO3ABC",
                       tol_min=2, contest=contest_5min)
        self.assertIn(0, r["confirmed"], "contest tolerance_min=5 should override tol_min=2")

# ── cabrillo_parser ───────────────────────────────────────────
from core.cabrillo_parser import _adif, _cab

SAMPLE_CABRILLO = """START-OF-LOG: 3.0
CALLSIGN: YO8ACR
CONTEST: CUPA MOLDOVEI
QSO: 3750 PH 2024-03-15 1000 YO8ACR 59 IS YO3ABC 59 BT
QSO: 3750 PH 2024-03-15 1005 YO8ACR 59 IS YO5DEF 59 CJ
QSO: 7050 CW 2024-03-15 1010 YO8ACR 599 IS YO6GHI 599 TM
END-OF-LOG:
"""

SAMPLE_ADIF = """<EOH>
<CALL:6>YO3ABC<BAND:3>80m<MODE:3>SSB<QSO_DATE:8>20240315<TIME_ON:4>1000<RST_SENT:2>59<RST_RCVD:2>59<EOR>
<CALL:6>YO5DEF<BAND:3>40m<MODE:2>CW<QSO_DATE:8>20240315<TIME_ON:4>1010<RST_SENT:3>599<RST_RCVD:3>599<EOR>
"""

class TestParsers(unittest.TestCase):
    def test_cabrillo_parse(self):
        qsos, errs, hdr = _cab(SAMPLE_CABRILLO)  # _cab returneaza (qsos, errs, hdr)
        self.assertEqual(len(qsos), 3)
        self.assertEqual(len(errs), 0)
        self.assertEqual(qsos[0]["callsign"], "YO3ABC")
        self.assertEqual(qsos[0]["band"], "80m")
        # PH -> SSB normalizat
        self.assertEqual(qsos[0]["mode"], "SSB")

    def test_adif_parse(self):
        qsos, errs = _adif(SAMPLE_ADIF)
        self.assertEqual(len(qsos), 2)
        self.assertEqual(qsos[0]["callsign"], "YO3ABC")
        self.assertEqual(qsos[1]["mode"], "CW")

# ── pdf_export ────────────────────────────────────────────────
from core.pdf_export import pdf_available, pdf_quality, _make_text_pdf
import tempfile

class TestPDFExport(unittest.TestCase):
    def test_pdf_available(self):
        self.assertTrue(pdf_available())

    def test_pdf_quality_string(self):
        q = pdf_quality()
        self.assertIsInstance(q, str)
        self.assertGreater(len(q), 5)

    def test_make_text_pdf_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        lines = ["YO Contest Judge PRO — Test PDF", "=" * 40,
                 "  QSO 1: YO3ABC  80m  SSB  59  IS",
                 "  QSO 2: YO5DEF  40m  CW   599 CJ"]
        _make_text_pdf(lines, path)
        import os
        self.assertTrue(os.path.exists(path))
        size = os.path.getsize(path)
        self.assertGreater(size, 100)
        # Verifica ca incepe cu %PDF
        with open(path, "rb") as f:
            header = f.read(4)
        self.assertEqual(header, b"%PDF")
        os.unlink(path)

# ── theme_engine ──────────────────────────────────────────────
from gui.theme_engine import THEMES, get_theme, theme_names, is_dark, DEFAULT_THEME

class TestThemeEngine(unittest.TestCase):
    def test_default_theme_exists(self):
        self.assertIn(DEFAULT_THEME, THEMES)

    def test_all_themes_have_required_keys(self):
        required = {"BG","BG2","BG3","FG","ACC","ACC2","GRN","RED","YLW","ORG","GRY","WHT"}
        for name, t in THEMES.items():
            missing = required - set(t.keys())
            self.assertEqual(missing, set(), "Tema {} lipseste: {}".format(name, missing))

    def test_theme_count_min(self):
        self.assertGreaterEqual(len(THEMES), 8)

    def test_get_theme_returns_copy(self):
        t1 = get_theme(DEFAULT_THEME)
        t2 = get_theme(DEFAULT_THEME)
        t1["BG"] = "#000000"
        self.assertNotEqual(t1["BG"], t2["BG"])

    def test_theme_names_list(self):
        names = theme_names()
        self.assertIsInstance(names, list)
        self.assertIn(DEFAULT_THEME, names)

    def test_dark_themes(self):
        dark = [n for n in THEMES if is_dark(THEMES[n])]
        light = [n for n in THEMES if not is_dark(THEMES[n])]
        self.assertGreater(len(dark), 0)
        self.assertGreater(len(light), 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
