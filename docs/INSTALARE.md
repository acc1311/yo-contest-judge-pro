# Ghid de instalare — YO Contest Judge PRO v2.2

## Windows (recomandat — EXE standalone)

1. Descarca `YOContestJudgePRO-v2.2.0.exe` din [Releases](https://github.com/acc1311/yo-contest-judge-pro/releases)
2. Dublu-click pe EXE — nu necesita instalare
3. Daca apare avertisment Windows SmartScreen:
   - Click **"More info"**
   - Click **"Run anyway"**

Verificare integritate SHA256:
```powershell
Get-FileHash YOContestJudgePRO-v2.2.0.exe -Algorithm SHA256
```

## Windows (din surse Python)

```powershell
python --version   # necesita 3.6+
python src/main.py
```

## Linux

```bash
sudo apt install python3-tk python3
python3 src/main.py
```

## macOS

```bash
python3 src/main.py
```

## Creare EXE propriu

```bash
pip install pyinstaller>=6.0
pyinstaller build/build.spec
# Output: dist/YOContestJudgePRO.exe
```

## Date utilizator

- Windows: `%LOCALAPPDATA%\YOContestJudgePRO\`
- Linux/macOS: `~/.local/share/YOContestJudgePRO/`
