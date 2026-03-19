# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — YO Contest Judge PRO v2.2
# Compatibil cu PyInstaller 5.x (Win7) si 6.x (Win8+)
# Rulare: pyinstaller build/build.spec

import os, sys

block_cipher = None
src_path = os.path.join(os.path.dirname(os.path.abspath(SPEC)), '..', 'src')

a = Analysis(
    [os.path.join(src_path, 'main.py')],
    pathex=[src_path],
    binaries=[],
    datas=[
        (os.path.join(src_path, 'callbook', '*.json'),  'callbook'),
        (os.path.join(src_path, 'contests', '*.json'),  'contests'),
        (os.path.join(src_path, 'lang',     '*.json'),  'lang'),
    ],
    hiddenimports=[
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox',
        'tkinter.filedialog', 'tkinter.simpledialog',
        'tkinter.colorchooser',
        'core.cabrillo_parser', 'core.callbook_engine',
        'core.contest_calendar', 'core.contest_rules',
        'core.cross_check', 'core.data_manager',
        'core.pdf_export', 'core.reporter',
        'core.scoring_engine', 'core.session_manager',
        'core.statistics',
        'gui.calendar_window', 'gui.callbook_window',
        'gui.main_window', 'gui.results_window',
        'gui.rules_editor', 'gui.statistics_window',
        'gui.storage_window', 'gui.theme_dialog',
        'gui.theme_engine',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'pandas', 'matplotlib', 'scipy', 'PIL',
              'cryptography', 'OpenSSL', 'gi'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# One-file EXE — mai simplu de distribuit
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YOContestJudgePRO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'app_icon.ico'),
)
