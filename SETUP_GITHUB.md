# Setup GitHub Repository — YO Contest Judge PRO v2.2

## Pas 1 — Creeaza repository nou pe GitHub

1. Mergi la: https://github.com/acc1311/
2. Click **"New repository"**
3. Completeaza:
   - **Repository name:** `yo-contest-judge-pro`
   - **Description:** `Arbitraj profesional pentru concursuri de radioamatori YO — Python/Tkinter, zero dependente externe`
   - **Visibility:** Public
   - **Nu** bifa "Add a README file" (avem deja)
4. Click **"Create repository"**

## Pas 2 — Incarca codul (prima data)

```bash
# Dezarhiveaza yo-contest-judge-pro-v2.2.zip
# Deschide terminal in folderul dezarhivat

git init
git add .
git commit -m "YO Contest Judge PRO v2.2 — release initial

- Fix: Maraton IC max 1 QSO/zi per statie (scoring_engine)
- Fix: Toleranta Cupa Tomis din JSON (cross_check)
- Fix: Cupa Moldovei multiplicatori county_dxcc
- Fix: Maraton IC club vs individual (lista ic_clubs)
- Fix: Validare locator Maidenhead (VHF)
- Fix: Intervale orare per concurs (time_windows)
- Fix: Serial secvential (check_serial)
- Fix: Versiune centralizata APP_VERSION
- Fix: Erori JSON concursuri afisate utilizatorului
- Nou: Export PDF nativ (zero dependente)
- Nou: 8 teme predefinite + editor teme custom + setare font
- Nou: Indicative portabile /P /M /MM /AM /QRP validate corect
- Nou: GitHub Actions CI/CD (teste + build EXE + release automat)
- Nou: 39 teste unitare

73 de YO8ACR!"

git branch -M main
git remote add origin https://github.com/acc1311/yo-contest-judge-pro.git
git push -u origin main
```

## Pas 3 — Creeaza primul Release (v2.2.0)

```bash
git tag v2.2.0
git push origin v2.2.0
```

Asta declanseaza automat GitHub Actions:
1. ✅ Teste pe Ubuntu + Windows + macOS
2. ✅ Build EXE Windows cu PyInstaller
3. ✅ Arhiva sursa
4. ✅ Release GitHub cu EXE + ZIP + SHA256

Monitorizeaza la: https://github.com/acc1311/yo-contest-judge-pro/actions

## Pas 4 — Verificare Release

La ~5-10 minute, Release-ul apare la:
https://github.com/acc1311/yo-contest-judge-pro/releases

Fisiere disponibile automat:
- `YOContestJudgePRO-v2.2.0.exe` — EXE standalone Windows
- `YOContestJudgePRO-v2.2.0-Windows-portable.zip`
- `YOContestJudgePRO-v2.2.0-source.zip`
- `SHA256SUMS.txt`

## Update-uri viitoare (release nou)

```bash
# Dupa modificari:
git add .
git commit -m "v2.3: descriere modificari"
git push origin main

# Release nou:
git tag v2.3.0
git push origin v2.3.0
# GitHub Actions construieste automat EXE + Release
```
