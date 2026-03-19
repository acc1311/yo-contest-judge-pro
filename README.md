# YO Contest Judge PRO v2.2

**Arbitraj profesional pentru concursuri de radioamatori YO**

Autor: Ardei Constantin-Catalin **YO8ACR** — [yo8acr@gmail.com](mailto:yo8acr@gmail.com)

---

## Ce este nou în v2.2

| Fix | Detalii |
|-----|---------|
| **Maraton IC — max 1 QSO/zi** | QSO-urile duplicate în aceeași zi per stație sunt marcate `maraton_dup` și nu primesc puncte |
| **Toleranță Cupa Tomis** | `tolerance_min: 5` din JSON este preluat automat la cross-check |
| **Cupa Moldovei — multiplicatori** | Judete YO + prefix DXCC stații straine (mod `county_dxcc`) |
| **Maraton IC — club vs individual** | Lista `ic_clubs` explicită în `contest_rules.py` |
| **Locator Maidenhead** | Validare format strict `AA00` / `AA00aa` la concursuri VHF |
| **Intervale orare** | `time_windows` per concurs — QSO în afara intervalelor primesc avertisment |
| **Serial secvențial** | Avertisment dacă numerele de serie nu sunt consecutive |
| **Export PDF** | Zero dependențe externe — PDF structurat generat nativ; suport weasyprint dacă e instalat |
| **Teme & Personalizare** | 8 teme predefinite + teme custom (color picker), setare font și mărime |
| **Indicative portabile** | `/P /M /MM /AM /QRP` validate corect fără fals-pozitive |
| **Erori JSON** | `load_contests()` afișează mesaj dacă un JSON de concurs este corupt |
| **Versiune centralizată** | `APP_VERSION` definit o singură dată în `main.py` |

---

## Ce face acest program

| Functie | Detalii |
|---------|---------|
| **Import loguri** | ADIF, Cabrillo 2.0/3.0, CSV, JSON, EDI (VHF) |
| **Validare** | RST, data/ora, indicative, benzi, moduri, judete, locator, serial, interval orar |
| **Duplicate** | Detectare automata per banda + per zi (Maraton IC) |
| **Cross-Check** | NIL, Busted Call, Busted Band, Busted Time |
| **Scoring** | Per-QSO, Maraton IC, Cupa Moldovei, Distanta VHF |
| **Clasament** | Automat, sortabil |
| **Export** | HTML (print-ready), CSV (Excel), TXT, JSON, **PDF** |
| **Teme** | 8 teme predefinite + teme custom + configurare font |
| **Calendar** | Toate concursurile YO 2026 cu link PDF regulamente |
| **Callbook** | 4964 radioamatori YO + 805 repetoare (ARR 2026) |
| **Date & Backup** | Sesiuni, backup automat, preferinte utilizator |
| **Compatibilitate** | Windows 7 / 8 / 10 / 11, Linux, macOS |
| **Dependente externe** | **ZERO** (Tkinter stdlib) |

---

## Concursuri incluse

- Maraton Ion Creanga (2-15 Martie, 80m SSB, max 1 QSO/zi/statie, reguli /IC complete)
- Cupa Elevului (30 Martie, Palatul Copiilor Piatra Neamt)
- YO DX HF Contest (August, FRR, multiband SSB+CW)
- YO VHF Contest (puncte = km din locator, validare locator Maidenhead)
- Field Day (generic international)
- La Multi Ani YO! (2 Ianuarie, FRR)
- Cupa Moldovei (punctaj Moldova vs YO, CW+SSB, multiplicatori judete+DXCC)
- Cupa 1 Decembrie (1 Decembrie, Alba)
- Cupa Tomis (Constanta, toleranta 5 min, punctaj variabil)
- Concursul Lucian Blaga (9 Mai, Sebes)
- Memorial YO (Noiembrie, YO DX Club)
- + orice concurs custom creat din meniu

---

## Rulare directa (fara instalare)

```bash
# Necesita: Python 3.6+ cu Tkinter
python src/main.py
```

Pe Windows, Python include Tkinter automat.  
Pe Linux: `sudo apt install python3-tk`

---

## Creare EXE (Windows)

```bash
pip install pyinstaller
pyinstaller build/build.spec
# EXE-ul apare in dist/YOContestJudgePRO.exe
```

Sau descarca direct din [Releases](https://github.com/acc1311/yo-contest-judge-pro/releases).

---

## Teme disponibile

| Tema | Stil |
|------|------|
| Albastru inchis *(implicit)* | Dark blue — clasic |
| Negru clasic | Dark black — high contrast |
| Verde military | Dark green |
| Gri profesional | Dark gray |
| Alb (zi) | Light — pentru lumina naturala |
| Sepia | Light warm — pentru ochi sensibili |
| Rosu inchis | Dark red |
| Albastru electric | Dark neon blue |

Teme custom: meniu **Personalizare** → color picker + salvare JSON.

---

## Taste rapide

| Tasta | Functie |
|-------|---------|
| F2 | Callbook |
| F3 | Cauta indicativ rapid |
| F4 | Calendar Concursuri YO 2026 |
| F5 | Arbitraj complet |
| F6 | Date & Backup |
| Ctrl+O | Import log |
| Ctrl+S | Salveaza sesiune |
| Ctrl+L | Incarca sesiune |

---

## Structura proiect

```
src/
  main.py                  # Entry point, APP_VERSION
  core/
    contest_rules.py       # Reguli + concursuri built-in
    scoring_engine.py      # Validare + scoring
    cross_check.py         # NIL, Busted Call/Band/Time
    cabrillo_parser.py     # Parser ADIF/Cabrillo/CSV/JSON/EDI
    reporter.py            # Export HTML/CSV/TXT/JSON
    pdf_export.py          # Export PDF (zero deps)
    statistics.py          # Statistici + grafice SVG
    callbook_engine.py     # Callbook YO
    data_manager.py        # Sesiuni, backup, preferinte
  gui/
    main_window.py         # Fereastra principala
    theme_engine.py        # Teme + fonturi
    theme_dialog.py        # Dialog personalizare
    ...
  contests/                # JSON concursuri custom
  callbook/                # Date ARR 2026
  lang/                    # ro.json, en.json
tests/
  test_core.py
build/
  build.spec               # PyInstaller spec
  app_icon.ico
.github/workflows/
  build.yml                # CI/CD: build + release EXE
```

---

73 de YO8ACR!
