#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Data Manager
Gestioneaza toate datele utilizatorului:
  - Structura directoare (creare automata la primul start)
  - Preferinte utilizator (tema, toleranta, ultima sesiune etc)
  - Backup automat sesiuni
  - Log erori aplicatie
  - Curatare fisiere vechi

Structura directoare date utilizator:
  %APPDATA%/YO_ContestJudge_PRO/          (Windows)
  ~/.yo_contest_judge_pro/                 (Linux/Mac)
  ├── sessions/          ← sesiuni arbitraj (.yojudge)
  ├── backups/           ← backup-uri automate
  ├── exports/           ← rapoarte exportate (HTML/CSV/TXT)
  ├── logs/              ← loguri importate recente
  ├── contests/          ← concursuri custom JSON
  ├── callbook/          ← callbook_user.json (adaosuri manuale)
  └── prefs.json         ← preferinte utilizator
"""
import os
import sys
import json
import shutil
import datetime
import traceback

APP_NAME    = "YO_ContestJudge_PRO"
PREFS_FILE  = "prefs.json"
ERROR_LOG   = "error.log"
MAX_BACKUPS = 20   # pastreaza maxim 20 backup-uri
MAX_LOG_MB  = 5    # sterge log erori daca depaseste 5 MB

# ── Director de date utilizator ───────────────────────────────
def get_data_dir():
    """Returneaza directorul de date al utilizatorului pentru aceasta aplicatie."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, APP_NAME)

def get_src_dir():
    """Returneaza directorul src/ al aplicatiei (langa main.py)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Structura directoare ──────────────────────────────────────
SUBDIRS = ["sessions", "backups", "exports", "logs_imported",
           "contests", "callbook"]

def ensure_data_dirs():
    """Creeaza structura de directoare la primul start. Idempotent."""
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    for sub in SUBDIRS:
        os.makedirs(os.path.join(data_dir, sub), exist_ok=True)

    # Copiaza callbook ARR din src/ in data_dir/callbook/ daca nu exista
    src_cb_dir = os.path.join(get_src_dir(), "callbook")
    dst_cb_dir = os.path.join(data_dir, "callbook")
    for fn in ["callbook_yo.json", "callbook_repetoare.json"]:
        src_fp = os.path.join(src_cb_dir, fn)
        dst_fp = os.path.join(dst_cb_dir, fn)
        if os.path.isfile(src_fp) and not os.path.isfile(dst_fp):
            shutil.copy2(src_fp, dst_fp)

    # Copiaza concursuri JSON din src/ in data_dir/contests/ daca nu exista
    src_c_dir = os.path.join(get_src_dir(), "contests")
    dst_c_dir = os.path.join(data_dir, "contests")
    if os.path.isdir(src_c_dir):
        for fn in os.listdir(src_c_dir):
            if fn.endswith(".json"):
                src_fp = os.path.join(src_c_dir, fn)
                dst_fp = os.path.join(dst_c_dir, fn)
                if not os.path.isfile(dst_fp):
                    shutil.copy2(src_fp, dst_fp)

    return data_dir

def get_subdir(sub):
    """Returneaza calea unui subdirector de date."""
    return os.path.join(get_data_dir(), sub)

# ── Preferinte utilizator ─────────────────────────────────────
DEFAULT_PREFS = {
    "theme":           "Albastru inchis (implicit)",
    "language":        "ro",
    "tolerance_min":   3,
    "last_session":    "",
    "last_contest":    "simplu",
    "last_dir":        "",
    "window_geometry": "",
    "font_size":       10,
    "show_private":    False,
    "auto_backup":     True,
    "backup_interval": 10,   # minute
    "max_recent":      10,
    "recent_sessions": [],
    "recent_dirs":     [],
    "version":         "2.1",
}

def load_prefs():
    """Incarca preferintele utilizatorului."""
    ensure_data_dirs()
    fp = os.path.join(get_data_dir(), PREFS_FILE)
    prefs = dict(DEFAULT_PREFS)
    if os.path.isfile(fp):
        try:
            with open(fp, encoding="utf-8") as f:
                saved = json.load(f)
            prefs.update(saved)
        except Exception:
            pass
    return prefs

def save_prefs(prefs):
    """Salveaza preferintele utilizatorului."""
    ensure_data_dirs()
    fp = os.path.join(get_data_dir(), PREFS_FILE)
    try:
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def update_pref(key, value):
    """Actualizeaza o singura preferinta."""
    prefs = load_prefs()
    prefs[key] = value
    save_prefs(prefs)

def add_recent_session(filepath):
    """Adauga o sesiune in lista de sesiuni recente."""
    prefs = load_prefs()
    recent = prefs.get("recent_sessions", [])
    if filepath in recent:
        recent.remove(filepath)
    recent.insert(0, filepath)
    prefs["recent_sessions"] = recent[:prefs.get("max_recent", 10)]
    prefs["last_session"] = filepath
    save_prefs(prefs)

def add_recent_dir(dirpath):
    """Adauga un director in lista de directoare recente."""
    prefs = load_prefs()
    recent = prefs.get("recent_dirs", [])
    if dirpath in recent:
        recent.remove(dirpath)
    recent.insert(0, dirpath)
    prefs["recent_dirs"] = recent[:5]
    prefs["last_dir"] = dirpath
    save_prefs(prefs)

# ── Backup automat ────────────────────────────────────────────
def create_backup(session_filepath):
    """
    Creeaza un backup al sesiunii curente in backups/.
    Returneaza calea backup-ului creat.
    """
    if not session_filepath or not os.path.isfile(session_filepath):
        return None
    backup_dir = get_subdir("backups")
    os.makedirs(backup_dir, exist_ok=True)

    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.splitext(os.path.basename(session_filepath))[0]
    dst  = os.path.join(backup_dir, "{}_backup_{}.yojudge".format(base, ts))

    try:
        shutil.copy2(session_filepath, dst)
        _cleanup_old_backups(backup_dir)
        return dst
    except Exception:
        return None

def create_auto_backup(state, name="autosave"):
    """
    Salveaza backup automat al starii curente fara interactiune utilizator.
    """
    from core.session_manager import save_session
    backup_dir = get_subdir("backups")
    os.makedirs(backup_dir, exist_ok=True)
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fp  = os.path.join(backup_dir, "{}_{}.yojudge".format(name, ts))
    try:
        save_session(fp, state)
        _cleanup_old_backups(backup_dir)
        return fp
    except Exception:
        return None

def _cleanup_old_backups(backup_dir, max_keep=MAX_BACKUPS):
    """Pastreaza doar ultimele max_keep backup-uri."""
    try:
        files = sorted([
            os.path.join(backup_dir, f)
            for f in os.listdir(backup_dir)
            if f.endswith(".yojudge")
        ], key=os.path.getmtime, reverse=True)
        for old in files[max_keep:]:
            os.remove(old)
    except Exception:
        pass

def list_backups():
    """Returneaza lista backup-urilor disponibile."""
    backup_dir = get_subdir("backups")
    if not os.path.isdir(backup_dir):
        return []
    files = []
    for fn in sorted(os.listdir(backup_dir), reverse=True):
        if fn.endswith(".yojudge"):
            fp   = os.path.join(backup_dir, fn)
            size = os.path.getsize(fp)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
            files.append({
                "filename": fn,
                "filepath": fp,
                "size_kb":  round(size/1024, 1),
                "date":     mtime.strftime("%Y-%m-%d %H:%M"),
            })
    return files

def list_sessions():
    """Returneaza lista sesiunilor salvate."""
    sessions_dir = get_subdir("sessions")
    if not os.path.isdir(sessions_dir):
        return []
    files = []
    for fn in sorted(os.listdir(sessions_dir), reverse=True):
        if fn.endswith(".yojudge"):
            fp    = os.path.join(sessions_dir, fn)
            size  = os.path.getsize(fp)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
            files.append({
                "filename": fn,
                "filepath": fp,
                "size_kb":  round(size/1024, 1),
                "date":     mtime.strftime("%Y-%m-%d %H:%M"),
            })
    return files

# ── Log erori ─────────────────────────────────────────────────
def log_error(message, exc=None):
    """Scrie o eroare in fisierul de log."""
    try:
        ensure_data_dirs()
        fp = os.path.join(get_data_dir(), ERROR_LOG)
        # Sterge log daca e prea mare
        if os.path.isfile(fp) and os.path.getsize(fp) > MAX_LOG_MB * 1024 * 1024:
            os.remove(fp)
        ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(fp, "a", encoding="utf-8") as f:
            f.write("\n[{}] {}\n".format(ts, message))
            if exc:
                f.write(traceback.format_exc())
                f.write("\n")
    except Exception:
        pass

def get_error_log():
    """Returneaza continutul log-ului de erori."""
    fp = os.path.join(get_data_dir(), ERROR_LOG)
    if not os.path.isfile(fp):
        return "Niciun log de erori."
    try:
        with open(fp, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "Nu pot citi log-ul de erori."

def clear_error_log():
    """Sterge log-ul de erori."""
    fp = os.path.join(get_data_dir(), ERROR_LOG)
    if os.path.isfile(fp):
        os.remove(fp)

# ── Info structura ────────────────────────────────────────────
def get_storage_info():
    """Returneaza informatii despre spatiul folosit."""
    data_dir = get_data_dir()
    info = {
        "data_dir":   data_dir,
        "exists":     os.path.isdir(data_dir),
        "subdirs":    {},
        "total_mb":   0,
    }
    if not info["exists"]:
        return info
    total = 0
    for sub in SUBDIRS:
        path  = os.path.join(data_dir, sub)
        if os.path.isdir(path):
            files = os.listdir(path)
            size  = sum(os.path.getsize(os.path.join(path, f))
                       for f in files if os.path.isfile(os.path.join(path, f)))
            info["subdirs"][sub] = {"files": len(files), "size_kb": round(size/1024, 1)}
            total += size
    info["total_mb"] = round(total / 1024 / 1024, 2)
    return info

def open_data_dir():
    """Deschide directorul de date in File Explorer / Finder / Nautilus."""
    import subprocess
    data_dir = get_data_dir()
    ensure_data_dirs()
    if sys.platform == "win32":
        os.startfile(data_dir)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", data_dir])
    else:
        subprocess.Popen(["xdg-open", data_dir])
