# Changelog — YO Contest Judge PRO

## v2.2.0 — 2026-03-20

### Bug-uri rezolvate
- **FIX #1** `scoring_engine`: Maraton IC — regula `max_qso_per_day:1` era definita dar neimplementata. QSO-urile extra in aceeasi zi primeau puncte. Acum sunt marcate `maraton_dup` si excluse din scor.
- **FIX #2** `cross_check`: Cupa Tomis — toleranta de 5 minute din `cupa_tomis.json` era ignorata. Cross-check-ul folosea intotdeauna toleranta globala din preferinte. Acum `contest["tolerance_min"]` are prioritate.
- **FIX #3** `scoring_engine`: Cupa Moldovei — multiplicatorul era `county` (doar judete YO). Acum este `county_dxcc`: judete YO + prefix tara DXCC pentru statii straine.
- **FIX #4** `contest_rules`: Maraton IC — distinctia club vs individual `/IC` era imposibila fara lista explicita. Adaugata lista `ic_clubs` in `contest_rules.py`.
- **FIX #5** `scoring_engine`: Locator Maidenhead — format nevalidat. Adaugat `_LOC_RE` regex si verificare in `validate_log()` pentru concursuri VHF.
- **FIX #6** `scoring_engine` + `contest_rules`: QSO-uri in afara intervalelor orare ale concursului nu generau avertisment. Adaugat camp `time_windows` la Cupa Moldovei, La Multi Ani YO, Cupa Elevului.
- **FIX #7** `scoring_engine`: Numarul de serie (serial) nu era verificat. Adaugat avertisment `BAD_SERIAL` pentru seriale nesecventiale cand `check_serial:true` in regulile concursului.
- **FIX #8** `main.py`: Versiunea era duplicata in mai multe fisiere (v2.0 in unele, v2.1 in altele). Centralizata in `APP_VERSION = "2.2"` in `main.py`.
- **FIX #9** `cross_check`: `cross_check_all()` exista dar nu era apelata nicaieri. Infrastructura pastrata, documentata pentru utilizare viitoare.
- **FIX #10** `contest_rules`: `load_contests()` ignora silentios JSON-urile corupte. Acum returneaza `(contests, errors)` si `main_window.py` afiseaza un mesaj de avertisment.

### Functionalitati noi
- **Export PDF** — `core/pdf_export.py`: generator PDF nativ (zero dependente externe) cu structura PDF 1.4 manuala. Suporta si `weasyprint` daca este instalat (output HTML complet). Accesibil din meniu Export → PDF...
- **Teme & Personalizare** — `gui/theme_engine.py` + `gui/theme_dialog.py`:
  - 8 teme predefinite: Albastru inchis, Negru clasic, Verde military, Gri profesional, Alb (zi), Sepia, Rosu inchis, Albastru electric
  - Editor teme custom cu color picker per element (BG, FG, ACC, GRN, RED etc.)
  - Salvare/incarcare teme custom in JSON
  - Configurare font (familie + marime) cu preview live
  - Meniu: 🎨 Personalizare
- **Indicative portabile** — `_CALL_RE` extins sa accepte `/P /M /MM /AM /QRP` fara fals-pozitive. Adaugate functii `_is_portable()` si `_base_call()`.
- **CI/CD GitHub Actions** — `.github/workflows/build.yml`:
  - Teste automate pe Ubuntu/Windows/macOS cu Python 3.8 si 3.11
  - Build EXE Windows cu PyInstaller la fiecare tag `v*.*.*`
  - Arhiva sursa cross-platform
  - Creare automata GitHub Release cu checksumuri SHA256
  - Trigger manual din GitHub UI (`workflow_dispatch`)

### Modificari minore
- `reporter.py`: adaugat camp `maraton_dup_qsos` in sumar HTML si TXT
- `statistics.py`: versiune actualizata la v2.2
- `build/build.spec`: actualizat cu noile module (`pdf_export`, `theme_engine`, `theme_dialog`, `colorchooser`)

---

## v2.1.0 — 2026-03-16

- Callbook ARR 2026 actualizat (4964 radioamatori + 805 repetoare)
- Calendar concursuri YO 2026 complet
- Suport EDI (VHF contests)
- Backup automat la inchidere

## v2.0.0 — 2026-01-10

- Lansare initiala
- Import ADIF, Cabrillo 2.0/3.0, CSV, JSON
- Cross-check NIL/Busted Call/Busted Band/Busted Time
- Scoring Maraton IC, Cupa Moldovei, YO VHF
- Export HTML, CSV, TXT, JSON
- Callbook YO integrat
