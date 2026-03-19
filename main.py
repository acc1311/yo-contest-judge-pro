#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO v2.2
Arbitraj profesional pentru concursuri de radioamatori YO
Autor: Ardei Constantin-Catalin (YO8ACR) — yo8acr@gmail.com
Cerinte: Python 3.6+, Tkinter (stdlib — ZERO dependente externe)
Compatibil: Windows 7 / 8 / 10 / 11, Linux, macOS
"""
import sys
import os

APP_VERSION = "2.2"
APP_NAME    = "YO Contest Judge PRO"
APP_AUTHOR  = "YO8ACR"
APP_EMAIL   = "yo8acr@gmail.com"

# Windows DPI awareness (Win7 SP1+)
try:
    if sys.platform == "win32":
        import ctypes
        try:    ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try: ctypes.windll.user32.SetProcessDPIAware()
            except Exception: pass
except Exception:
    pass

# Asigura ca src/ e in path indiferent de unde e rulat
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def main():
    try:
        from core.data_manager import ensure_data_dirs
        ensure_data_dirs()
    except Exception:
        pass

    from gui.main_window import JudgeApp
    app = JudgeApp()
    app.mainloop()

if __name__ == "__main__":
    main()
