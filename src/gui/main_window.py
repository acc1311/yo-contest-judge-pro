#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Main Window v2.2
Interfata principala: import loguri, validare, cross-check, scoring, clasament.
Tkinter stdlib — zero dependente externe. Compatibil Win7/8/10/11.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os, sys, webbrowser

# ── Teme disponibile ──────────────────────────────────────────

# ── Tema engine ───────────────────────────────────────────────
from gui.theme_engine import (
    THEMES, DEFAULT_THEME, get_theme, theme_names, is_dark,
    load_custom_themes, save_custom_theme
)

# Culori globale (actualizate la schimbarea temei)
_T = get_theme(DEFAULT_THEME)
BG  = _T["BG"];  BG2 = _T["BG2"]; BG3 = _T["BG3"]
FG  = _T["FG"];  ACC = _T["ACC"]; ACC2 = _T["ACC2"]
GRN = _T["GRN"]; RED = _T["RED"]; YLW  = _T["YLW"]
ORG = _T["ORG"]; GRY = _T["GRY"]; WHT  = _T["WHT"]
FONT      = ("Consolas", 10)
FONT_B    = ("Consolas", 10, "bold")
FONT_H    = ("Arial", 11, "bold")
FONT_FAM  = "Consolas"
FONT_SIZE = 10

class JudgeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        from main import APP_VERSION, APP_NAME
        self.title("{} v{}".format(APP_NAME, APP_VERSION))
        self.configure(bg=BG)
        self.resizable(True, True)
        # Seteaza iconul ferestrei
        try:
            import os as _os
            _icon_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                       '..', '..', 'build', 'app_icon.ico')
            if _os.path.isfile(_icon_path):
                self.iconbitmap(_icon_path)
        except Exception:
            pass

        # Cai
        self.src_dir       = os.path.dirname(os.path.abspath(__file__))
        self.contests_dir  = os.path.join(self.src_dir, "..", "contests")
        self.lang_dir      = os.path.join(self.src_dir, "..", "lang")
        self.callbook_dir  = os.path.join(self.src_dir, "..", "callbook")
        self.last_session  = ""
        # Callbook DB (lazy-load)
        from core.callbook_engine import CallbookDB
        self.callbook_db = CallbookDB(self.callbook_dir)

        # State
        self.loaded_logs   = {}   # {call: parse_result}
        self.val_results   = {}
        self.score_results = {}
        self.cc_result     = None
        self.cc_matrix     = {}
        self.ranking       = []
        self.contests      = {}
        self.lang          = {}
        self.lang_code     = tk.StringVar(value="ro")
        self.contest_id    = tk.StringVar(value="simplu")
        self.tol_var       = tk.IntVar(value=3)
        self._current_theme     = DEFAULT_THEME
        self._current_font_fam  = FONT_FAM
        self._current_font_size = FONT_SIZE

        # Incarca preferinte utilizator
        try:
            from core.data_manager import load_prefs, get_subdir
            self._prefs = load_prefs()
            # Foloseste directoarele de date pentru callbook si contests
            self.callbook_dir = get_subdir("callbook")
            self.contests_dir = get_subdir("contests")
        except Exception:
            self._prefs = {}

        self._load_lang(self._prefs.get("language","ro"))
        self._load_contests()
        self._setup_geometry()
        self._apply_style()
        self._build_ui()
        self._build_menu()
        # Seteaza concursul implicit dupa ce UI e gata
        self.after(50, self._init_contest_combo)
        # Restaureaza toleranta din preferinte
        self.after(100, self._restore_prefs)

    # ── Init ──────────────────────────────────────────────────
    def _setup_geometry(self):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = min(1380, int(sw * 0.94))
        h  = min(860,  int(sh * 0.90))
        self.geometry("{}x{}+{}+{}".format(w, h, (sw-w)//2, (sh-h)//2))
        self.minsize(960, 600)

    def _load_lang(self, code):
        import json
        fp = os.path.join(self.lang_dir, "{}.json".format(code))
        try:
            with open(fp, encoding="utf-8") as f:
                self.lang = json.load(f)
        except Exception:
            self.lang = {}

    def _load_contests(self):
        from core.contest_rules import load_contests
        result = load_contests(self.contests_dir)
        if isinstance(result, tuple):
            self.contests, load_errs = result
        else:
            self.contests, load_errs = result, []
        if load_errs:
            errmsg = "Atentie: %d fisier(e) JSON corupt(e)" % len(load_errs)
            for fn, err in load_errs:
                errmsg += "\n  - %s - %s" % (fn, str(err))
            messagebox.showwarning("Erori incarcare concursuri", errmsg)
            messagebox.showwarning("Erori incarcare concursuri", msg)

    def _t(self, key, default=None):
        return self.lang.get(key, default or key)

    def _apply_style(self):
        st = ttk.Style(self)
        # 'clam' e disponibila pe Win7/8/10/11; fallback la 'alt' sau 'default'
        available = st.theme_names()
        for _theme in ("clam", "alt", "default"):
            if _theme in available:
                st.theme_use(_theme)
                break
        st.configure(".",            background=BG, foreground=FG, font=FONT,
                     fieldbackground=BG2)
        st.configure("TFrame",       background=BG)
        st.configure("TLabel",       background=BG, foreground=FG, font=FONT)
        st.configure("TLabelframe",  background=BG, foreground=ACC2)
        st.configure("TLabelframe.Label", background=BG, foreground=ACC2, font=FONT_H)
        st.configure("TButton",      background=ACC, foreground=WHT, font=FONT_B,
                     relief="flat", padding=(8,4))
        st.map("TButton",
               background=[("active",ACC2),("pressed",BG3)],
               foreground=[("active",WHT)])
        st.configure("G.TButton",    background=GRN, foreground=BG)
        st.configure("R.TButton",    background=RED, foreground=WHT)
        st.configure("TCombobox",    background=BG2, foreground=FG, fieldbackground=BG2)
        st.configure("TSpinbox",     background=BG2, foreground=FG, fieldbackground=BG2)
        st.configure("TNotebook",    background=BG)
        st.configure("TNotebook.Tab",background=BG3, foreground=FG,
                     padding=(12,5), font=FONT_B)
        st.map("TNotebook.Tab",
               background=[("selected",ACC),("active",BG2)],
               foreground=[("selected",WHT)])
        st.configure("Treeview",     background=BG2, foreground=FG,
                     fieldbackground=BG2, font=FONT, rowheight=22)
        st.configure("Treeview.Heading", background=BG3, foreground=ACC2, font=FONT_B)
        st.map("Treeview",           background=[("selected",ACC)])

    # ── Menu ──────────────────────────────────────────────────
    def _build_menu(self):
        mb = tk.Menu(self, bg=BG2, fg=FG, activebackground=ACC,
                     activeforeground=WHT, tearoff=0)
        self.configure(menu=mb)

        # Fisier
        fm = tk.Menu(mb, bg=BG2, fg=FG, activebackground=ACC,
                     activeforeground=WHT, tearoff=0)
        mb.add_cascade(label="Fisier", menu=fm)
        fm.add_command(label="Import Loguri...       [Ctrl+O]", command=self._import_log)
        fm.add_command(label="Import Folder (toate logurile)", command=self._import_folder)
        fm.add_separator()
        fm.add_command(label="Salveaza Sesiune...    [Ctrl+S]", command=self._save_session)
        fm.add_command(label="Deschide Sesiune...    [Ctrl+L]", command=self._load_session)
        fm.add_separator()
        fm.add_command(label="Sterge toate logurile", command=self._remove_all)
        fm.add_separator()
        fm.add_command(label="Date & Backup...   [F6]", command=self._open_storage)
        fm.add_separator()
        fm.add_command(label="Iesire", command=self.destroy)
        self.bind("<Control-o>", lambda e: self._import_log())
        self.bind("<F6>", lambda e: self._open_storage())
        self.bind("<Control-s>", lambda e: self._save_session())
        self.bind("<Control-l>", lambda e: self._load_session())

        # Arbitraj
        am = tk.Menu(mb, bg=BG2, fg=FG, activebackground=ACC,
                     activeforeground=WHT, tearoff=0)
        mb.add_cascade(label="Arbitraj", menu=am)
        am.add_command(label="Valideaza loguri", command=self._run_validation)
        am.add_command(label="Cross-Check (2 loguri)", command=self._run_crosscheck)
        am.add_command(label="Calculeaza scor", command=self._run_scoring)
        am.add_separator()
        am.add_command(label="Arbitraj complet  [F5]", command=self._run_all)
        am.add_separator()
        am.add_command(label="Statistici concurs...", command=self._show_statistics)
        self.bind("<F5>", lambda e: self._run_all())

        # Callbook
        cbm = tk.Menu(mb, bg=BG2, fg=FG, activebackground=ACC,
                      activeforeground=WHT, tearoff=0)
        mb.add_cascade(label="Callbook", menu=cbm)
        cbm.add_command(label="Deschide Callbook...  [F2]", command=self._open_callbook)
        cbm.add_command(label="Cauta indicativ...    [F3]", command=self._quick_lookup)
        self.bind("<F2>", lambda e: self._open_callbook())
        self.bind("<F3>", lambda e: self._quick_lookup())

        # Concursuri
        cm = tk.Menu(mb, bg=BG2, fg=FG, activebackground=ACC,
                     activeforeground=WHT, tearoff=0)
        mb.add_cascade(label="Concursuri", menu=cm)
        cm.add_command(label="Calendar Concursuri YO 2026  [F4]",
                       command=self._open_calendar)
        cm.add_separator()
        cm.add_command(label="Adauga concurs nou...", command=self._new_contest)
        cm.add_command(label="Editeaza concursul selectat...", command=self._edit_contest)
        cm.add_separator()
        for cid, cdata in self.contests.items():
            cm.add_command(label=cdata["name"],
                command=lambda c=cid: self._set_contest(c))
        self.bind("<F4>", lambda e: self._open_calendar())

        # Export
        em = tk.Menu(mb, bg=BG2, fg=FG, activebackground=ACC,
                     activeforeground=WHT, tearoff=0)
        mb.add_cascade(label="Export", menu=em)
        for lbl, fmt in [("HTML...","html"),("CSV (Excel)...","csv"),
                          ("TXT...","txt"),("JSON...","json"),("PDF...","pdf")]:
            em.add_command(label=lbl, command=lambda f=fmt: self._export(f))
        em.add_separator()
        em.add_command(label="Statistici HTML...", command=self._export_stats)

        # Teme / Personalizare
        mb.add_command(label="🎨 Personalizare",
                       command=self._open_theme_dialog)

        # Limba
        lm = tk.Menu(mb, bg=BG2, fg=FG, activebackground=ACC,
                     activeforeground=WHT, tearoff=0)
        mb.add_cascade(label="Limba", menu=lm)
        lm.add_command(label="Romana", command=lambda: self._change_lang("ro"))
        lm.add_command(label="English", command=lambda: self._change_lang("en"))

        # Ajutor
        hm = tk.Menu(mb, bg=BG2, fg=FG, activebackground=ACC,
                     activeforeground=WHT, tearoff=0)
        mb.add_cascade(label="Ajutor", menu=hm)
        hm.add_command(label="Despre...", command=self._about)

    # ── UI principal ──────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        top = tk.Frame(self, bg=ACC, height=50)
        top.pack(fill=tk.X)
        tk.Label(top, text="YO CONTEST JUDGE PRO v2.2",
                 font=("Arial",14,"bold"), bg=ACC, fg=WHT,
                 padx=16).pack(side=tk.LEFT, pady=8)
        tk.Label(top, text="Arbitraj profesional — zero dependente externe — Win7/8/10/11",
                 font=("Arial",9), bg=ACC, fg="#dce8f5").pack(side=tk.LEFT)

        # Status bar
        self.status_var = tk.StringVar(value="Gata. Importati loguri pentru a incepe arbitrajul.")
        tk.Label(self, textvariable=self.status_var, bg=BG3, fg=ACC2,
                 font=("Consolas",9), anchor="w", padx=10).pack(side=tk.BOTTOM, fill=tk.X)

        # Paned window
        # tk.PanedWindow (non-ttk) exista din Python 2.x — maxima compatibilitate Win7
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        left = ttk.Frame(paned, width=290)
        paned.add(left)
        self._build_left(left)

        right = ttk.Frame(paned)
        paned.add(right)
        self._build_right(right)

    def _build_left(self, parent):
        # Config concurs
        cf = ttk.LabelFrame(parent, text="Configurare")
        cf.pack(fill=tk.X, padx=6, pady=4)

        ttk.Label(cf, text="Concurs:").grid(row=0, column=0, sticky="w", padx=6, pady=3)
        names = [v["name"] for v in self.contests.values()]
        self.contest_cb = ttk.Combobox(cf, values=names, state="readonly", width=22)
        self.contest_cb.grid(row=0, column=1, padx=6, pady=3, sticky="ew")
        self.contest_cb.set(self.contests.get("simplu",{}).get("name","Simplu"))
        self.contest_cb.bind("<<ComboboxSelected>>", self._on_contest_change)

        ttk.Label(cf, text="Toleranta +/-min:").grid(row=1, column=0, sticky="w", padx=6)
        ttk.Spinbox(cf, from_=1, to=15, textvariable=self.tol_var, width=5
                    ).grid(row=1, column=1, sticky="w", padx=6, pady=3)

        # Loguri importate
        lf = ttk.LabelFrame(parent, text="Loguri Importate")
        lf.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.log_tree = ttk.Treeview(lf,
            columns=("call","qsos","fmt","status"), show="headings", height=8)
        for col, hdr, w in [("call","Indicativ",90),("qsos","QSO",50),
                             ("fmt","Format",60),("status","Status",70)]:
            self.log_tree.heading(col, text=hdr)
            self.log_tree.column(col, width=w, anchor="center")
        vsb = ttk.Scrollbar(lf, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=vsb.set)
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_tree.bind("<<TreeviewSelect>>", self._on_log_select)

        for txt, cmd, style in [
            ("+ Import Log",       self._import_log,    "TButton"),
            ("+ Import Folder",    self._import_folder, "TButton"),
            ("- Sterge Selectat",  self._remove_log,    "R.TButton"),
            ("Golire / Refresh",   self._clear_results, "TButton"),
        ]:
            ttk.Button(parent, text=txt, command=cmd, style=style
                       ).pack(fill=tk.X, padx=6, pady=2)

        ttk.Separator(parent).pack(fill=tk.X, padx=6, pady=4)

        # Butoane arbitraj
        af = ttk.LabelFrame(parent, text="Actiuni")
        af.pack(fill=tk.X, padx=6, pady=4)
        for txt, cmd, sty in [
            ("Valideaza Loguri",        self._run_validation, "TButton"),
            ("Cross-Check (2 loguri)",  self._run_crosscheck, "TButton"),
            ("Calculeaza Scor",         self._run_scoring,    "TButton"),
            ("ARBITRAJ COMPLET  [F5]",  self._run_all,        "G.TButton"),
        ]:
            ttk.Button(af, text=txt, command=cmd, style=sty
                       ).pack(fill=tk.X, padx=4, pady=2)

    def _build_right(self, parent):
        self.nb = ttk.Notebook(parent)
        self.nb.pack(fill=tk.BOTH, expand=True)

        self.tab_log  = ttk.Frame(self.nb)
        self.tab_val  = ttk.Frame(self.nb)
        self.tab_cc   = ttk.Frame(self.nb)
        self.tab_rank = ttk.Frame(self.nb)

        self.nb.add(self.tab_log,  text="  Log QSO-uri  ")
        self.nb.add(self.tab_val,  text="  Validare  ")
        self.nb.add(self.tab_cc,   text="  Cross-Check  ")
        self.nb.add(self.tab_rank, text="  Clasament  ")

        self._build_log_tab(self.tab_log)
        self._build_val_tab(self.tab_val)
        self._build_cc_tab(self.tab_cc)
        self._build_rank_tab(self.tab_rank)

    # ── Tab Log ───────────────────────────────────────────────
    def _build_log_tab(self, p):
        ff = ttk.Frame(p); ff.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(ff, text="Log:").pack(side=tk.LEFT)
        self.log_sel_var = tk.StringVar()
        self.log_sel_cb = ttk.Combobox(ff, textvariable=self.log_sel_var,
                                        state="readonly", width=14)
        self.log_sel_cb.pack(side=tk.LEFT, padx=4)
        self.log_sel_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_log_tab())

        ttk.Label(ff, text="Status:").pack(side=tk.LEFT, padx=(8,0))
        self.stat_filter = ttk.Combobox(ff,
            values=["Toate","ok","warning","error","duplicate","nil"],
            state="readonly", width=10)
        self.stat_filter.set("Toate")
        self.stat_filter.pack(side=tk.LEFT, padx=4)
        self.stat_filter.bind("<<ComboboxSelected>>", lambda e: self._refresh_log_tab())

        self.qso_cnt_lbl = ttk.Label(ff, text="")
        self.qso_cnt_lbl.pack(side=tk.RIGHT, padx=10)

        cols = ("#","Indicativ","Banda","Mod","Data","Ora","RST S","RST R","Schimb","Pct","Status")
        wids = (40,100,60,55,90,60,55,55,80,50,80)
        self.qso_tree = ttk.Treeview(p, columns=cols, show="headings")
        for col, hdr, w in zip(cols, cols, wids):
            self.qso_tree.heading(col, text=hdr,
                command=lambda c=col: self._sort(self.qso_tree, c))
            self.qso_tree.column(col, width=w, anchor="center" if w<90 else "w")
        vsb = ttk.Scrollbar(p, orient="vertical",   command=self.qso_tree.yview)
        hsb = ttk.Scrollbar(p, orient="horizontal",  command=self.qso_tree.xview)
        self.qso_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.qso_tree.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        for tag, bg, fg in [("ok","#1b3a2a",GRN),("warning","#3a3000",YLW),
                              ("error","#3a1515",RED),("duplicate","#3a2500",ORG),
                              ("nil","#2a2a2a",GRY)]:
            self.qso_tree.tag_configure(tag, background=bg, foreground=fg)

    # ── Tab Validare ──────────────────────────────────────────
    def _build_val_tab(self, p):
        self.val_summary = tk.Text(p, height=6, bg=BG2, fg=FG,
                                    font=FONT, state="disabled", relief="flat", padx=8, pady=4)
        self.val_summary.pack(fill=tk.X, padx=6, pady=4)
        ttk.Separator(p).pack(fill=tk.X, padx=6)

        cols = ("qso","call","tip","mesaj","severitate","camp")
        wids = (50,100,140,460,80,60)
        self.val_tree = ttk.Treeview(p, columns=cols, show="headings")
        for col, hdr, w in zip(cols, ("#QSO","Indicativ","Tip","Mesaj","Sev.","Camp"), wids):
            self.val_tree.heading(col, text=hdr)
            self.val_tree.column(col, width=w, anchor="w" if w>80 else "center")
        vsb = ttk.Scrollbar(p, orient="vertical",  command=self.val_tree.yview)
        hsb = ttk.Scrollbar(p, orient="horizontal", command=self.val_tree.xview)
        self.val_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.val_tree.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.val_tree.tag_configure("ERROR",   background="#3a1515", foreground=RED)
        self.val_tree.tag_configure("WARNING", background="#3a3000", foreground=YLW)

    # ── Tab Cross-Check ───────────────────────────────────────
    def _build_cc_tab(self, p):
        sf = ttk.Frame(p); sf.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(sf, text="Log A:").pack(side=tk.LEFT)
        self.cc_a = ttk.Combobox(sf, state="readonly", width=14)
        self.cc_a.pack(side=tk.LEFT, padx=4)
        ttk.Label(sf, text="Log B:").pack(side=tk.LEFT, padx=(12,0))
        self.cc_b = ttk.Combobox(sf, state="readonly", width=14)
        self.cc_b.pack(side=tk.LEFT, padx=4)
        ttk.Button(sf, text="Ruleaza Cross-Check", command=self._run_crosscheck
                   ).pack(side=tk.LEFT, padx=12)

        self.cc_summary = tk.Text(p, height=5, bg=BG2, fg=FG,
                                   font=FONT, state="disabled", relief="flat", padx=8, pady=4)
        self.cc_summary.pack(fill=tk.X, padx=6, pady=4)
        ttk.Separator(p).pack(fill=tk.X, padx=6, pady=2)

        cols = ("#","Indicativ A","Banda","Data","Ora","Status","Detaliu")
        wids = (45,100,60,90,60,120,450)
        self.cc_tree = ttk.Treeview(p, columns=cols, show="headings")
        for col, hdr, w in zip(cols, cols, wids):
            self.cc_tree.heading(col, text=hdr)
            self.cc_tree.column(col, width=w, anchor="w" if w>80 else "center")
        vsb = ttk.Scrollbar(p, orient="vertical",  command=self.cc_tree.yview)
        hsb = ttk.Scrollbar(p, orient="horizontal", command=self.cc_tree.xview)
        self.cc_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.cc_tree.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        for tag, bg, fg in [("confirmed","#1b3a2a",GRN),("nil","#3a1515",RED),
                              ("busted_call","#3a2000",ORG),("busted_band","#3a2000",ORG),
                              ("busted_time","#3a2800",YLW)]:
            self.cc_tree.tag_configure(tag, background=bg, foreground=fg)

    # ── Tab Clasament ─────────────────────────────────────────
    def _build_rank_tab(self, p):
        self.rank_summary = tk.Text(p, height=5, bg=BG2, fg=FG,
                                     font=FONT, state="disabled", relief="flat", padx=8, pady=4)
        self.rank_summary.pack(fill=tk.X, padx=6, pady=4)
        ttk.Separator(p).pack(fill=tk.X, padx=6)
        ttk.Button(p, text="Deschide fereastra Rezultate completa",
                   command=self._open_results_window, style="G.TButton"
                   ).pack(padx=6, pady=4, fill=tk.X)

        cols = ("#","Indicativ","Total QSO","Valide","Erori","Dup.","NIL","Pct QSO","Mult.","SCOR")
        wids = (40,110,75,70,60,55,55,75,60,100)
        self.rank_tree = ttk.Treeview(p, columns=cols, show="headings")
        for col, hdr, w in zip(cols, cols, wids):
            self.rank_tree.heading(col, text=hdr)
            self.rank_tree.column(col, width=w, anchor="center")
        vsb = ttk.Scrollbar(p, orient="vertical", command=self.rank_tree.yview)
        self.rank_tree.configure(yscrollcommand=vsb.set)
        self.rank_tree.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.rank_tree.tag_configure("gold",   background="#3a3200", foreground=YLW)
        self.rank_tree.tag_configure("silver", background="#2a2a2a", foreground="#c0c0c0")
        self.rank_tree.tag_configure("bronze", background="#2a1a00", foreground="#cd7f32")

    # ══════════════════ ACTIUNI ═══════════════════════════════
    def _set_status(self, msg):
        self.status_var.set(msg)

    def _on_contest_change(self, event=None):
        name = self.contest_cb.get()
        for cid, cdata in self.contests.items():
            if cdata["name"] == name:
                self.contest_id.set(cid)
                break

    def _set_contest(self, cid):
        if cid in self.contests:
            self.contest_id.set(cid)
            self.contest_cb.set(self.contests[cid]["name"])

    def _on_log_select(self, event=None):
        sel = self.log_tree.selection()
        if sel:
            call = self.log_tree.item(sel[0])["values"][0]
            self.log_sel_var.set(call)
            self._refresh_log_tab()

    def _import_log(self):
        from core.cabrillo_parser import parse_file
        files = filedialog.askopenfilenames(
            title="Import Loguri",
            filetypes=[
                ("Toate formatele","*.adi *.adif *.log *.cbr *.csv *.json *.edi"),
                ("ADIF","*.adi *.adif"),
                ("Cabrillo","*.log *.cbr"),
                ("CSV","*.csv"),
                ("JSON","*.json"),
                ("EDI (VHF)","*.edi"),
                ("Toate","*.*"),
            ])
        for fp in files:
            self._set_status("Se importa: {}...".format(os.path.basename(fp)))
            self.update_idletasks()
            try:
                res = parse_file(fp)
                call = res["callsign"] or os.path.splitext(os.path.basename(fp))[0].upper()
                if call in self.loaded_logs:
                    if not messagebox.askyesno("Duplicat",
                        "Log-ul {} exista deja. Il inlocuiti?".format(call)):
                        continue
                    for item in self.log_tree.get_children():
                        if self.log_tree.item(item)["values"][0] == call:
                            self.log_tree.delete(item)
                self.loaded_logs[call] = res
                errs = len(res["errors"])
                st = "OK" if not errs else "{} erori".format(errs)
                self.log_tree.insert("", "end",
                    values=(call, res["total"], res["format"].upper(), st))
                self._set_status("{}: {} QSO-uri ({}){}".format(
                    call, res["total"], res["format"].upper(),
                    " — {} erori import".format(errs) if errs else ""))
            except Exception as e:
                messagebox.showerror("Eroare import", str(e))
        self._update_combos()

    def _remove_log(self):
        for item in self.log_tree.selection():
            call = self.log_tree.item(item)["values"][0]
            self.loaded_logs.pop(call, None)
            self.val_results.pop(call, None)
            self.score_results.pop(call, None)
            self.log_tree.delete(item)
        self._update_combos()

    def _remove_all(self):
        if not messagebox.askyesno("Confirmare", "Stergeti toate log-urile?"):
            return
        self.loaded_logs.clear(); self.val_results.clear(); self.score_results.clear()
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        self._update_combos()

    def _update_combos(self):
        calls = list(self.loaded_logs.keys())
        self.log_sel_cb["values"] = calls
        self.cc_a["values"] = calls
        self.cc_b["values"] = calls
        if calls:
            if self.log_sel_var.get() not in calls:
                self.log_sel_var.set(calls[0])
            if not self.cc_a.get() or self.cc_a.get() not in calls:
                self.cc_a.set(calls[0])
            if len(calls) > 1 and (not self.cc_b.get() or self.cc_b.get() not in calls):
                self.cc_b.set(calls[1])

    # ── Validare ──────────────────────────────────────────────
    def _run_validation(self):
        from core.scoring_engine import validate_log
        if not self.loaded_logs:
            messagebox.showwarning("Atentie", "Importati cel putin un log!"); return
        self.val_results.clear()
        for item in self.val_tree.get_children():
            self.val_tree.delete(item)
        cid = self.contest_id.get()
        total_e = total_w = 0
        for call, pr in self.loaded_logs.items():
            vr = validate_log(pr["qsos"], cid, call, self.contests)
            self.val_results[call] = vr
            total_e += vr["error_count"]
            total_w += vr["warning_count"]
            for e in vr["errors"]:
                d = e.to_dict()
                self.val_tree.insert("","end", tags=(d["severity"],), values=(
                    d["qso_idx"]+1, "{}:{}".format(call, d["callsign"]),
                    d["type"], d["message"], d["severity"], d.get("field","")))

        lines = ["=== VALIDARE ==="]
        for call, vr in self.val_results.items():
            lines.append("  {:<14} Total:{:4d}  Valide:{:4d}  Erori:{:3d}  Avert:{:3d}".format(
                call, vr["valid_count"]+vr["error_count"],
                vr["valid_count"], vr["error_count"], vr["warning_count"]))
        self._set_text(self.val_summary, "\n".join(lines))
        self._set_status("Validare: {} erori, {} avertismente".format(total_e, total_w))
        self.nb.select(self.tab_val)
        self._refresh_log_tab()

    # ── Cross-Check ───────────────────────────────────────────
    def _run_crosscheck(self):
        from core.cross_check import cross_check
        ca, cb = self.cc_a.get(), self.cc_b.get()
        if not ca or not cb:
            messagebox.showwarning("Atentie","Selectati ambele loguri A si B!"); return
        if ca == cb:
            messagebox.showwarning("Atentie","Log-urile A si B trebuie sa fie diferite!"); return
        tol = self.tol_var.get()
        # FIX #2 — pasa si regulile concursului (pt tolerance_min per concurs)
        cid = self.contest_id.get()
        cur_contest = self.contests.get(cid, {})
        self.cc_result = cross_check(
            self.loaded_logs[ca]["qsos"], self.loaded_logs[cb]["qsos"],
            ca, cb, tol, contest=cur_contest)
        key = "{}_vs_{}".format(ca, cb)
        self.cc_matrix[key] = self.cc_result
        st = self.cc_result["stats"]
        txt = (
            "{} vs {}  |  Toleranta: +/-{} min\n"
            "Total A: {}  |  Confirmate: {} ({}%)  |  NIL: {}\n"
            "Busted Call: {}  |  Busted Band: {}  |  Busted Time: {}"
        ).format(ca, cb, tol,
                 st["total_a"], st["confirmed"], st["confirm_pct"], st["nil"],
                 st["busted_call"], st["busted_band"], st["busted_time"])
        self._set_text(self.cc_summary, txt)
        for item in self.cc_tree.get_children():
            self.cc_tree.delete(item)
        for ia, detail in sorted(self.cc_result["details"].items()):
            status = detail["status"]
            pr = self.loaded_logs.get(ca, {})
            self.cc_tree.insert("","end", tags=(status,), values=(
                ia+1, detail["callsign_a"], detail["band_a"],
                detail["date_a"], detail["time_a"],
                status.upper(), detail.get("issue","")))
        self._set_status("Cross-Check {}<>{}: {} confirmate, {} NIL".format(
            ca, cb, st["confirmed"], st["nil"]))
        self.nb.select(self.tab_cc)

    # ── Scoring ───────────────────────────────────────────────
    def _run_scoring(self):
        from core.scoring_engine import score_log, build_ranking
        if not self.loaded_logs:
            messagebox.showwarning("Atentie","Importati cel putin un log!"); return
        cid = self.contest_id.get()
        self.score_results.clear()
        for call, pr in self.loaded_logs.items():
            vr  = self.val_results.get(call)
            qso_flags = vr["qso_flags"] if vr else None
            sr = score_log(pr["qsos"], cid, call,
                           qso_flags=qso_flags,
                           cc_result=self.cc_result,
                           contests=self.contests)
            self.score_results[call] = sr
        self.ranking = build_ranking(list(self.score_results.values()))

        for item in self.rank_tree.get_children():
            self.rank_tree.delete(item)
        tagmap = {1:"gold",2:"silver",3:"bronze"}
        for r in self.ranking:
            tag = (tagmap.get(r["position"]),) if r["position"] <= 3 else ()
            self.rank_tree.insert("","end", tags=tag, values=(
                "#{}".format(r["position"]), r["callsign"],
                r["total_qsos"], r["valid_qsos"], r["error_qsos"],
                r["dup_qsos"], r.get("nil_qsos",0),
                r["qso_points"], r["multipliers"], r["total_score"]))

        if self.ranking:
            top = self.ranking[0]
            txt = ("=== CLASAMENT FINAL | {} ===\n"
                   "Locul 1: {} — {} puncte\n"
                   "{} statii clasificate | {} total QSO procesate").format(
                self.contests.get(cid,{}).get("name", cid),
                top["callsign"], top["total_score"],
                len(self.ranking),
                sum(r["total_qsos"] for r in self.ranking))
            self._set_text(self.rank_summary, txt)
        self._set_status("Scor calculat: {} statii clasificate".format(len(self.ranking)))
        self.nb.select(self.tab_rank)
        self._refresh_log_tab()

    # ── Arbitraj complet ──────────────────────────────────────
    def _run_all(self):
        if not self.loaded_logs:
            messagebox.showwarning("Atentie","Importati cel putin un log!"); return
        self._run_validation()
        calls = list(self.loaded_logs.keys())
        if len(calls) >= 2:
            self.cc_a.set(calls[0])
            self.cc_b.set(calls[1])
            self._run_crosscheck()
        self._run_scoring()
        self._set_status("Arbitraj complet finalizat!")

    # ── Fereastra rezultate ───────────────────────────────────
    def _open_results_window(self):
        if not self.score_results:
            messagebox.showwarning("Atentie","Rulati mai intai arbitrajul!"); return
        from gui.results_window import ResultsWindow
        cname = self.contests.get(self.contest_id.get(),{}).get("name","")
        ResultsWindow(self, self.ranking, self.score_results,
                      self.val_results, self.cc_matrix, cname)

    # ── Editor concursuri ─────────────────────────────────────
    def _new_contest(self):
        from gui.rules_editor import RulesEditorDialog
        RulesEditorDialog(self, self.contests_dir, self.contests,
                          edit_id=None, on_save=self._on_contest_saved)

    def _edit_contest(self):
        from gui.rules_editor import RulesEditorDialog
        cid = self.contest_id.get()
        RulesEditorDialog(self, self.contests_dir, self.contests,
                          edit_id=cid, on_save=self._on_contest_saved)

    def _on_contest_saved(self, cid, data):
        self._load_contests()
        # Reface meniu si combobox
        try:
            self._build_menu()
        except Exception:
            pass
        self._init_contest_combo()
        # Seteaza concursul nou salvat ca activ
        if cid and cid in self.contests:
            self._set_contest(cid)

    # ── Refresh tab Log ───────────────────────────────────────
    def _refresh_log_tab(self):
        for item in self.qso_tree.get_children():
            self.qso_tree.delete(item)
        call = self.log_sel_var.get()
        if not call or call not in self.loaded_logs:
            return
        pr  = self.loaded_logs[call]
        vr  = self.val_results.get(call, {})
        sr  = self.score_results.get(call, {})
        flags     = vr.get("qso_flags", {})
        breakdown = {b["idx"]: b for b in sr.get("breakdown", [])}
        sf  = self.stat_filter.get()
        count = 0
        for i, q in enumerate(pr["qsos"]):
            flag = flags.get(i, "ok")
            if sf != "Toate" and flag != sf:
                continue
            pts = breakdown.get(i, {}).get("points", "—")
            self.qso_tree.insert("","end", tags=(flag,), values=(
                i+1, q.get("callsign",""), q.get("band",""), q.get("mode",""),
                q.get("date",""), q.get("time",""), q.get("rst_s",""),
                q.get("rst_r",""), q.get("exchange",""), pts, flag))
            count += 1
        self.qso_cnt_lbl.configure(
            text="{}/{} QSO-uri".format(count, len(pr["qsos"])))

    def _sort(self, tree, col):
        data = [(tree.set(c, col), c) for c in tree.get_children("")]
        try: data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
        except Exception: data.sort()
        for i, (_, c) in enumerate(data):
            tree.move(c, "", i)

    def _set_text(self, widget, txt):
        widget.configure(state="normal")
        widget.delete("1.0","end")
        widget.insert("end", txt)
        widget.configure(state="disabled")

    # ── Export ────────────────────────────────────────────────
    def _export(self, fmt):
        from core.reporter import export_html, export_csv, export_txt, export_json
        from core.pdf_export import export_pdf, pdf_quality
        if not self.score_results:
            messagebox.showwarning("Atentie","Rulati arbitrajul inainte de export!"); return
        call = self.log_sel_var.get() or list(self.score_results.keys())[0]
        ext = {"html":".html","csv":".csv","txt":".txt","json":".json","pdf":".pdf"}.get(fmt,".txt")
        fp  = filedialog.asksaveasfilename(
            defaultextension=ext,
            initialfile="Arbitraj_{}".format(call),
            filetypes=[(fmt.upper(), "*{}".format(ext))])
        if not fp: return
        sr = self.score_results.get(call, {})
        vr = self.val_results.get(call, {})
        try:
            if fmt == "html":
                export_html(sr, vr, fp, self.cc_result, self.ranking)
                if messagebox.askyesno("Export","Deschideti in browser?"):
                    webbrowser.open("file://{}".format(os.path.abspath(fp)))
            elif fmt == "csv":  export_csv(sr, vr, fp)
            elif fmt == "txt":  export_txt(sr, vr, fp)
            elif fmt == "json": export_json(sr, vr, fp)
            elif fmt == "pdf":
                export_pdf(sr, vr, fp, self.cc_result, self.ranking)
                q = pdf_quality()
                if messagebox.askyesno("Export PDF",
                        "PDF generat ({}).\nDeschideti fisierul?".format(q)):
                    webbrowser.open("file://{}".format(os.path.abspath(fp)))
            self._set_status("Exportat: {}".format(fp))
        except Exception as e:
            messagebox.showerror("Eroare export", str(e))

    # ── Lingua ────────────────────────────────────────────────
    def _change_lang(self, code):
        self._load_lang(code)
        messagebox.showinfo("Limba",
            "Limba schimbata. Reporniti aplicatia pentru efect complet.")

    # ── Despre ────────────────────────────────────────────────
    def _about(self):
        messagebox.showinfo("Despre",
            "YO Contest Judge PRO v2.2\n\n"
            "Arbitraj profesional pentru concursuri de radioamatori YO.\n"
            "Autor: Ardei Constantin-Catalin (YO8ACR)\n"
            "Email: yo8acr@gmail.com\n\n"
            "Formate: ADIF | Cabrillo 2.0/3.0 | CSV | JSON | EDI\n"
            "Dependente externe: ZERO (Tkinter stdlib)\n"
            "Compatibil: Windows 7 / 8 / 10 / 11\n\n"
            "73 de YO8ACR!")

    # ── Import Folder ─────────────────────────────────────────
    def _import_folder(self):
        from core.cabrillo_parser import parse_file
        folder = filedialog.askdirectory(title="Selectati folderul cu loguri")
        if not folder: return
        exts = (".adi",".adif",".log",".cbr",".csv",".json",".edi")
        files = [os.path.join(folder,f) for f in os.listdir(folder)
                 if os.path.splitext(f)[1].lower() in exts]
        if not files:
            messagebox.showinfo("Info","Niciun fisier de log gasit in folderul selectat."); return
        ok = err = 0
        for fp in sorted(files):
            try:
                res = parse_file(fp)
                call = res["callsign"] or os.path.splitext(os.path.basename(fp))[0].upper()
                self.loaded_logs[call] = res
                for item in self.log_tree.get_children():
                    if self.log_tree.item(item)["values"][0] == call:
                        self.log_tree.delete(item); break
                errs = len(res["errors"])
                st   = "OK" if not errs else "{} erori".format(errs)
                self.log_tree.insert("","end",
                    values=(call, res["total"], res["format"].upper(), st))
                ok += 1
            except Exception:
                err += 1
        self._update_combos()
        self._set_status("Folder importat: {} loguri OK, {} erori".format(ok, err))

    # ── Sesiune ───────────────────────────────────────────────
    def _save_session(self):
        from core.session_manager import save_session, SESSION_EXT
        if not self.loaded_logs:
            messagebox.showwarning("Atentie","Nu exista loguri de salvat!"); return
        fp = filedialog.asksaveasfilename(
            title="Salveaza Sesiune",
            defaultextension=SESSION_EXT,
            initialfile="arbitraj_{}".format(self.contest_id.get()),
            filetypes=[("Sesiune YO Judge","*.yojudge"),("Toate","*.*")])
        if not fp: return
        try:
            state = {
                "contest_id":   self.contest_id.get(),
                "tolerance":    self.tol_var.get(),
                "loaded_logs":  self.loaded_logs,
                "val_results":  self.val_results,
                "score_results":self.score_results,
                "cc_matrix":    self.cc_matrix,
                "ranking":      self.ranking,
            }
            save_session(fp, state)
            self.last_session = fp
            self._set_status("Sesiune salvata: {}".format(os.path.basename(fp)))
        except Exception as e:
            messagebox.showerror("Eroare salvare", str(e))

    def _load_session(self):
        from core.session_manager import load_session, session_info, SESSION_EXT
        fp = filedialog.askopenfilename(
            title="Deschide Sesiune",
            filetypes=[("Sesiune YO Judge","*.yojudge"),("Toate","*.*")])
        if not fp: return
        try:
            info = session_info(fp)
            if "error" in info:
                messagebox.showerror("Eroare", info["error"]); return
            if not messagebox.askyesno("Deschide sesiune",
                "Sesiune din {}\nConcurs: {}\nLoguri: {} | Total QSO: {}\n\nDeschizi?".format(
                    info["saved_at"], info["contest_id"],
                    info["logs"], info["total_qso"])): return
            state = load_session(fp)
            self.loaded_logs   = state["loaded_logs"]
            self.val_results   = state["val_results"]
            self.score_results = state["score_results"]
            self.cc_matrix     = state["cc_matrix"]
            self.ranking       = state["ranking"]
            cid = state.get("contest_id","simplu")
            self.contest_id.set(cid)
            if cid in self.contests:
                self.contest_cb.set(self.contests[cid]["name"])
            self.tol_var.set(state.get("tolerance",3))
            # Repopuleaza log_tree
            for item in self.log_tree.get_children():
                self.log_tree.delete(item)
            for call, pr in self.loaded_logs.items():
                vr  = self.val_results.get(call,{})
                ec  = vr.get("error_count",0)
                st  = "OK" if not ec else "{} erori".format(ec)
                self.log_tree.insert("","end",
                    values=(call, pr.get("total",0), pr.get("format","?").upper(), st))
            # Repopuleaza clasament
            for item in self.rank_tree.get_children():
                self.rank_tree.delete(item)
            tagmap = {1:"gold",2:"silver",3:"bronze"}
            for r in self.ranking:
                tag = (tagmap.get(r["position"]),) if r["position"] <= 3 else ()
                self.rank_tree.insert("","end", tags=tag, values=(
                    "#{}".format(r["position"]), r["callsign"],
                    r["total_qsos"], r["valid_qsos"], r["error_qsos"],
                    r["dup_qsos"], r.get("nil_qsos",0),
                    r["qso_points"], r["multipliers"], r["total_score"]))
            self._update_combos()
            self.last_session = fp
            self._set_status("Sesiune incarcata: {} loguri, {} QSO total".format(
                len(self.loaded_logs),
                sum(pr.get("total",0) for pr in self.loaded_logs.values())))
        except Exception as e:
            messagebox.showerror("Eroare incarcare sesiune", str(e))

    # ── Statistici ────────────────────────────────────────────
    def _show_statistics(self):
        from core.statistics import compute_stats
        if not self.loaded_logs:
            messagebox.showwarning("Atentie","Importati loguri mai intai!"); return
        cname = self.contests.get(self.contest_id.get(),{}).get("name","Concurs")
        stats = compute_stats(self.loaded_logs, self.score_results,
                               self.val_results, self.cc_matrix, cname)
        from gui.statistics_window import StatisticsWindow
        StatisticsWindow(self, stats)

    def _export_stats(self):
        from core.statistics import compute_stats, stats_to_html
        if not self.loaded_logs:
            messagebox.showwarning("Atentie","Importati loguri mai intai!"); return
        fp = filedialog.asksaveasfilename(
            defaultextension=".html",
            initialfile="Statistici_{}".format(self.contest_id.get()),
            filetypes=[("HTML","*.html")])
        if not fp: return
        cname = self.contests.get(self.contest_id.get(),{}).get("name","Concurs")
        stats = compute_stats(self.loaded_logs, self.score_results,
                               self.val_results, self.cc_matrix, cname)
        html = stats_to_html(stats)
        with open(fp,"w",encoding="utf-8") as f: f.write(html)
        self._set_status("Statistici exportate: {}".format(fp))
        if messagebox.askyesno("Export","Deschideti in browser?"):
            webbrowser.open("file://{}".format(os.path.abspath(fp)))

    # ── Callbook ──────────────────────────────────────────────
    def _open_callbook(self):
        from gui.callbook_window import CallbookWindow
        CallbookWindow(self, self.callbook_db)

    def _quick_lookup(self):
        """Cauta rapid un indicativ in callbook si afiseaza rezultatul."""
        call = tk.simpledialog.askstring("Cauta Indicativ",
            "Introduceti indicativul:", parent=self)
        if not call: return
        rec = self.callbook_db.lookup(call.strip().upper())
        if rec:
            priv = rec.get("private", False)
            msg = "Indicativ: {}\n".format(rec.get("call",""))
            if not priv:
                msg += "Titular:   {}\n".format(rec.get("name","—"))
                msg += "Clasa:     {}\n".format(rec.get("class","—"))
                msg += "Localitate:{}\n".format(rec.get("city","—"))
                msg += "Judet:     {}\n".format(rec.get("county","—"))
                msg += "Email:     {}\n".format(rec.get("email","—") or "—")
                msg += "Expira:    {}\n".format(rec.get("expires","—"))
            else:
                msg += "Titular:   [DATE PERSONALE]\n"
                msg += "Judet:     {}\n".format(rec.get("county","—"))
            messagebox.showinfo("Callbook — {}".format(rec.get("call","")), msg)
        else:
            messagebox.showinfo("Callbook",
                "Indicativul {} nu a fost gasit in callbook.".format(
                    call.strip().upper()))


    # ── Tema & Personalizare ──────────────────────────────────
    def _open_theme_dialog(self):
        """Deschide dialogul complet de personalizare aspect."""
        from gui.theme_dialog import ThemeDialog
        themes_data_dir = None
        try:
            from core.data_manager import get_subdir
            themes_data_dir = get_subdir("themes")
            from gui.theme_engine import load_custom_themes
            load_custom_themes(themes_data_dir)
        except Exception:
            pass
        ThemeDialog(
            self,
            current_theme=getattr(self, "_current_theme", DEFAULT_THEME),
            current_font=getattr(self, "_current_font_fam", "Consolas"),
            current_font_size=getattr(self, "_current_font_size", 10),
            on_apply=self._apply_theme_full,
            themes_dir=themes_data_dir,
        )

    def _apply_theme_full(self, theme_name, font_fam, font_size):
        """Aplica tema + font selectate din dialog."""
        self._apply_theme(theme_name, font_fam=font_fam, font_size=font_size, silent=False)

    def _apply_theme(self, theme_name, font_fam=None, font_size=None, silent=True):
        """Aplica tema selectata - schimba culorile intregii interfete."""
        global BG, BG2, BG3, FG, ACC, ACC2, GRN, RED, YLW, ORG, GRY, WHT
        global FONT, FONT_B, FONT_H, FONT_FAM, FONT_SIZE
        from gui.theme_engine import get_theme
        t = get_theme(theme_name)
        BG  = t["BG"];  BG2 = t["BG2"]; BG3 = t["BG3"]
        FG  = t["FG"];  ACC = t["ACC"]; ACC2 = t["ACC2"]
        GRN = t["GRN"]; RED = t["RED"]; YLW  = t["YLW"]
        ORG = t["ORG"]; GRY = t["GRY"]; WHT  = t["WHT"]
        if font_fam:  FONT_FAM  = font_fam
        if font_size: FONT_SIZE = font_size
        FONT   = (FONT_FAM, FONT_SIZE)
        FONT_B = (FONT_FAM, FONT_SIZE, "bold")
        FONT_H = ("Arial", FONT_SIZE + 1, "bold")
        self.configure(bg=BG)
        self._apply_style()
        self._current_theme     = theme_name
        self._current_font_fam  = FONT_FAM
        self._current_font_size = FONT_SIZE
        if not silent:
            self._set_status("Tema aplicata: {}. Reporniti pentru efect complet.".format(theme_name))
            messagebox.showinfo("Tema",
                "Tema \'{}\' aplicata.\nUnele elemente necesita repornirea aplicatiei pentru efect complet.".format(theme_name))


    # ── Golire rezultate / Refresh ────────────────────────────
    def _clear_results(self):
        """Goleste rezultatele arbitrajului (validare, cross-check, scoring) dar pastreaza logurile."""
        self.val_results.clear()
        self.score_results.clear()
        self.cc_result   = None
        self.cc_matrix.clear()
        self.ranking.clear()
        # Curata tab-urile
        for item in self.val_tree.get_children():   self.val_tree.delete(item)
        for item in self.cc_tree.get_children():    self.cc_tree.delete(item)
        for item in self.rank_tree.get_children():  self.rank_tree.delete(item)
        self._set_text(self.val_summary,  "")
        self._set_text(self.cc_summary,   "")
        self._set_text(self.rank_summary, "")
        # Actualizeaza statusul logurilor in log_tree
        for item in self.log_tree.get_children():
            vals = list(self.log_tree.item(item)["values"])
            vals[3] = "OK"
            self.log_tree.item(item, values=vals)
        self._refresh_log_tab()
        self._set_status("Rezultate curatate. Logurile sunt inca incarcate.")


    # ── Calendar Concursuri ────────────────────────────────────
    def _open_calendar(self):
        from gui.calendar_window import CalendarWindow
        CalendarWindow(self, self.contests, on_select=self._set_contest)


    # ── Init combo concurs dupa UI gata ───────────────────────
    def _init_contest_combo(self):
        """Seteaza combobox-ul de concurs dupa ce UI e complet construit."""
        if not hasattr(self, 'contest_cb'): return
        names = [v["name"] for v in self.contests.values()]
        self.contest_cb["values"] = names
        default = self.contests.get("simplu", {}).get("name", "")
        if default:
            self.contest_cb.set(default)
        elif names:
            self.contest_cb.set(names[0])


    # ── Date & Backup ──────────────────────────────────────────
    def _open_storage(self):
        from gui.storage_window import StorageWindow
        StorageWindow(self, on_load=self._load_session)

    # ── Restaurare preferinte la start ────────────────────────
    def _restore_prefs(self):
        """Aplica preferintele salvate (tema, toleranta, concurs)."""
        try:
            prefs = getattr(self, "_prefs", {})
            # Toleranta
            tol = prefs.get("tolerance_min", 3)
            self.tol_var.set(tol)
            # Concurs
            last_c = prefs.get("last_contest","simplu")
            if last_c in self.contests:
                self._set_contest(last_c)
            # Tema + Font
            theme = prefs.get("theme", DEFAULT_THEME)
            font_fam  = prefs.get("font_fam", "Consolas")
            font_size = prefs.get("font_size", 10)
            self._current_font_fam  = font_fam
            self._current_font_size = font_size
            if theme in THEMES:
                self._apply_theme(theme, font_fam=font_fam, font_size=font_size, silent=True)
        except Exception:
            pass

    def _apply_theme_silent(self, theme_name):
        """Aplica tema fara mesaj popup (la start)."""
        try:
            self._apply_theme(theme_name, silent=True)
        except Exception:
            pass

    # ── Salveaza preferinte la inchidere ─────────────────────
    def destroy(self):
        """Salveaza preferintele inainte de inchidere."""
        try:
            from core.data_manager import save_prefs, load_prefs
            prefs = load_prefs()
            prefs["tolerance_min"]  = self.tol_var.get()
            prefs["last_contest"]   = self.contest_id.get()
            prefs["theme"]          = getattr(self, "_current_theme", DEFAULT_THEME)
            prefs["font_fam"]       = getattr(self, "_current_font_fam", "Consolas")
            prefs["font_size"]      = getattr(self, "_current_font_size", 10)
            prefs["language"]       = self.lang_code.get()
            # Backup automat la inchidere daca exista loguri
            if self.loaded_logs and prefs.get("auto_backup", True):
                from core.data_manager import create_auto_backup
                state = {
                    "contest_id":    self.contest_id.get(),
                    "tolerance":     self.tol_var.get(),
                    "loaded_logs":   self.loaded_logs,
                    "val_results":   self.val_results,
                    "score_results": self.score_results,
                    "cc_matrix":     self.cc_matrix,
                    "ranking":       self.ranking,
                }
                create_auto_backup(state, "autosave")
            save_prefs(prefs)
        except Exception:
            pass
        super().destroy()

