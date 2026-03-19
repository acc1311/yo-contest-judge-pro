#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Fereastra Gestiune Date & Backup
Afiseaza: structura directoare, sesiuni salvate, backup-uri,
          spatiu ocupat, log erori. Permite: deschidere sesiune din backup,
          curatare, deschidere folder in Explorer.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import webbrowser

from core.data_manager import (
    get_data_dir, get_storage_info, list_sessions, list_backups,
    get_error_log, clear_error_log, open_data_dir, load_prefs
)

BG  = "#1e2a38"; BG2 = "#253447"; BG3 = "#2e3f55"
FG  = "#e8edf3"; ACC = "#2e75b6"; ACC2= "#4a9de0"
GRN = "#2ecc71"; RED = "#e74c3c"; YLW = "#f1c40f"
ORG = "#f39c12"; WHT = "#ffffff"; GRY = "#7f8c8d"
FONT = ("Consolas", 10); FONT_B = ("Consolas", 10, "bold")

class StorageWindow(tk.Toplevel):
    def __init__(self, parent, on_load=None):
        super().__init__(parent)
        self.on_load = on_load
        self.title("Gestiune Date & Backup")
        self.configure(bg=BG)
        self.resizable(True, True)
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w = min(900, int(sw*.75)); h = min(700, int(sh*.80))
        self.geometry("{}x{}+{}+{}".format(w, h, (sw-w)//2, (sh-h)//2))
        self._apply_style()
        self._build()
        self._refresh()

    def _apply_style(self):
        st = ttk.Style(self)
        st.configure("Treeview", background=BG2, foreground=FG,
                     fieldbackground=BG2, font=FONT, rowheight=22)
        st.configure("Treeview.Heading", background=BG3, foreground=ACC2, font=FONT_B)
        st.map("Treeview", background=[("selected", ACC)])
        st.configure("S.TNotebook", background=BG)
        st.configure("S.TNotebook.Tab", background=BG3, foreground=FG,
                     padding=(10,4), font=FONT_B)
        st.map("S.TNotebook.Tab",
               background=[("selected",ACC)], foreground=[("selected",WHT)])

    def _build(self):
        # Header
        top = tk.Frame(self, bg=ACC, height=44)
        top.pack(fill=tk.X)
        tk.Label(top, text="GESTIUNE DATE & BACKUP",
                 font=("Arial",12,"bold"), bg=ACC, fg=WHT, padx=14
                 ).pack(side=tk.LEFT, pady=10)
        tk.Button(top, text="Deschide folder in Explorer",
                  command=open_data_dir,
                  bg=BG3, fg=WHT, font=FONT, relief="flat", padx=10
                  ).pack(side=tk.RIGHT, padx=8, pady=8)

        # Info director
        data_dir = get_data_dir()
        tk.Label(self, text="Director date: {}".format(data_dir),
                 bg=BG3, fg=ACC2, font=("Consolas",8), anchor="w", padx=10
                 ).pack(fill=tk.X)

        nb = ttk.Notebook(self, style="S.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1: Structura
        t1 = ttk.Frame(nb); nb.add(t1, text="  Structura  ")
        self._build_structure(t1)

        # Tab 2: Sesiuni
        t2 = ttk.Frame(nb); nb.add(t2, text="  Sesiuni Salvate  ")
        self._build_sessions(t2)

        # Tab 3: Backup-uri
        t3 = ttk.Frame(nb); nb.add(t3, text="  Backup-uri Auto  ")
        self._build_backups(t3)

        # Tab 4: Log Erori
        t4 = ttk.Frame(nb); nb.add(t4, text="  Log Erori  ")
        self._build_error_log(t4)

        # Tab 5: Preferinte
        t5 = ttk.Frame(nb); nb.add(t5, text="  Preferinte  ")
        self._build_prefs(t5)

        # Status
        self.status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_var, bg=BG3, fg=ACC2,
                 font=("Consolas",9), anchor="w", padx=10
                 ).pack(side=tk.BOTTOM, fill=tk.X)

    # ── Tab Structura ─────────────────────────────────────────
    def _build_structure(self, p):
        tk.Label(p, text="Spatiu ocupat de datele aplicatiei",
                 bg=BG3, fg=ACC2, font=FONT_B, padx=8, pady=4).pack(fill=tk.X)

        self.struct_tree = ttk.Treeview(p,
            columns=("folder","files","size"), show="headings")
        self.struct_tree.heading("folder", text="Director")
        self.struct_tree.heading("files",  text="Fisiere")
        self.struct_tree.heading("size",   text="Dimensiune")
        self.struct_tree.column("folder", width=200)
        self.struct_tree.column("files",  width=80,  anchor="center")
        self.struct_tree.column("size",   width=100, anchor="center")
        self.struct_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        bf = tk.Frame(p, bg=BG); bf.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(bf, text="Deschide in Explorer", command=open_data_dir,
                  bg=ACC, fg=WHT, font=FONT, relief="flat", padx=10
                  ).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="Refresh", command=self._refresh,
                  bg=BG3, fg=WHT, font=FONT, relief="flat", padx=10
                  ).pack(side=tk.LEFT, padx=4)

    # ── Tab Sesiuni ───────────────────────────────────────────
    def _build_sessions(self, p):
        tk.Label(p, text="Sesiuni de arbitraj salvate manual",
                 bg=BG3, fg=ACC2, font=FONT_B, padx=8, pady=4).pack(fill=tk.X)

        cols = ("filename","date","size")
        self.sess_tree = ttk.Treeview(p, columns=cols, show="headings")
        self.sess_tree.heading("filename", text="Fisier")
        self.sess_tree.heading("date",     text="Data salvare")
        self.sess_tree.heading("size",     text="Marime")
        self.sess_tree.column("filename", width=300)
        self.sess_tree.column("date",     width=140, anchor="center")
        self.sess_tree.column("size",     width=80,  anchor="center")
        vsb = ttk.Scrollbar(p, orient="vertical", command=self.sess_tree.yview)
        self.sess_tree.configure(yscrollcommand=vsb.set)
        self.sess_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.sess_tree.bind("<Double-1>", lambda e: self._load_session(self.sess_tree))

        bf = tk.Frame(p, bg=BG); bf.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(bf, text="Deschide Sesiunea Selectata",
                  command=lambda: self._load_session(self.sess_tree),
                  bg=GRN, fg=BG, font=FONT_B, relief="flat", padx=10
                  ).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="Sterge Selectata",
                  command=lambda: self._delete_file(self.sess_tree),
                  bg=RED, fg=WHT, font=FONT, relief="flat", padx=10
                  ).pack(side=tk.LEFT, padx=4)

    # ── Tab Backup-uri ────────────────────────────────────────
    def _build_backups(self, p):
        tk.Label(p, text="Backup-uri automate (ultimele 20)",
                 bg=BG3, fg=ACC2, font=FONT_B, padx=8, pady=4).pack(fill=tk.X)

        cols = ("filename","date","size")
        self.bkp_tree = ttk.Treeview(p, columns=cols, show="headings")
        self.bkp_tree.heading("filename", text="Fisier backup")
        self.bkp_tree.heading("date",     text="Data backup")
        self.bkp_tree.heading("size",     text="Marime")
        self.bkp_tree.column("filename", width=320)
        self.bkp_tree.column("date",     width=140, anchor="center")
        self.bkp_tree.column("size",     width=80,  anchor="center")
        vsb = ttk.Scrollbar(p, orient="vertical", command=self.bkp_tree.yview)
        self.bkp_tree.configure(yscrollcommand=vsb.set)
        self.bkp_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.bkp_tree.bind("<Double-1>", lambda e: self._load_session(self.bkp_tree))

        bf = tk.Frame(p, bg=BG); bf.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(bf, text="Restaureaza Backup Selectat",
                  command=lambda: self._load_session(self.bkp_tree),
                  bg=ORG, fg=WHT, font=FONT_B, relief="flat", padx=10
                  ).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="Curata toate backup-urile",
                  command=self._clear_backups,
                  bg=RED, fg=WHT, font=FONT, relief="flat", padx=10
                  ).pack(side=tk.LEFT, padx=4)

    # ── Tab Log Erori ─────────────────────────────────────────
    def _build_error_log(self, p):
        tk.Label(p, text="Log erori aplicatie",
                 bg=BG3, fg=ACC2, font=FONT_B, padx=8, pady=4).pack(fill=tk.X)
        self.log_text = tk.Text(p, bg=BG2, fg=FG, font=("Consolas",9),
                                 state="disabled", relief="flat", wrap="word")
        vsb = ttk.Scrollbar(p, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=vsb.set)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        bf = tk.Frame(p, bg=BG); bf.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(bf, text="Sterge log erori",
                  command=self._clear_log,
                  bg=RED, fg=WHT, font=FONT, relief="flat", padx=10
                  ).pack(side=tk.LEFT, padx=4)

    # ── Tab Preferinte ────────────────────────────────────────
    def _build_prefs(self, p):
        tk.Label(p, text="Preferinte utilizator salvate",
                 bg=BG3, fg=ACC2, font=FONT_B, padx=8, pady=4).pack(fill=tk.X)
        self.prefs_text = tk.Text(p, bg=BG2, fg=FG, font=("Consolas",10),
                                   state="disabled", relief="flat", wrap="none")
        vsb = ttk.Scrollbar(p, orient="vertical",  command=self.prefs_text.yview)
        hsb = ttk.Scrollbar(p, orient="horizontal", command=self.prefs_text.xview)
        self.prefs_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.prefs_text.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        fp_lbl = tk.Label(p,
            text="Fisier: {}".format(os.path.join(get_data_dir(), "prefs.json")),
            bg=BG, fg=GRY, font=("Consolas",8), anchor="w")
        fp_lbl.pack(fill=tk.X, padx=8, pady=2)

    # ── Refresh date ──────────────────────────────────────────
    def _refresh(self):
        # Structura
        info = get_storage_info()
        for item in self.struct_tree.get_children():
            self.struct_tree.delete(item)
        self.struct_tree.insert("","end", values=(
            "TOTAL", "", "{} MB".format(info["total_mb"])))
        for sub, d in info["subdirs"].items():
            self.struct_tree.insert("","end", values=(
                sub + "/", d["files"], "{} KB".format(d["size_kb"])))
        self.struct_tree.insert("","end", values=(
            "prefs.json", "1 fisier",
            "{} KB".format(
                round(os.path.getsize(os.path.join(get_data_dir(),"prefs.json"))/1024, 1)
                if os.path.isfile(os.path.join(get_data_dir(),"prefs.json")) else "0 KB")))

        # Sesiuni
        for item in self.sess_tree.get_children():
            self.sess_tree.delete(item)
        for s in list_sessions():
            self.sess_tree.insert("","end", values=(
                s["filename"], s["date"], "{} KB".format(s["size_kb"])))

        # Backup-uri
        for item in self.bkp_tree.get_children():
            self.bkp_tree.delete(item)
        for b in list_backups():
            self.bkp_tree.insert("","end", values=(
                b["filename"], b["date"], "{} KB".format(b["size_kb"])))

        # Log erori
        log_content = get_error_log()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0","end")
        self.log_text.insert("end", log_content)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

        # Preferinte
        import json
        prefs = load_prefs()
        self.prefs_text.configure(state="normal")
        self.prefs_text.delete("1.0","end")
        self.prefs_text.insert("end", json.dumps(prefs, ensure_ascii=False, indent=2))
        self.prefs_text.configure(state="disabled")

        self.status_var.set("Actualizat: {} sesiuni, {} backup-uri".format(
            len(list_sessions()), len(list_backups())))

    def _load_session(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selectati o sesiune.", parent=self)
            return
        fname = tree.item(sel[0])["values"][0]
        # Gaseste calea completa
        for s in list_sessions() + list_backups():
            if s["filename"] == fname:
                if self.on_load:
                    self.on_load(s["filepath"])
                self.destroy()
                return

    def _delete_file(self, tree):
        sel = tree.selection()
        if not sel: return
        fname = tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmare",
            "Stergi '{}'?".format(fname), parent=self): return
        for s in list_sessions() + list_backups():
            if s["filename"] == fname:
                try:
                    os.remove(s["filepath"])
                    self._refresh()
                except Exception as e:
                    messagebox.showerror("Eroare", str(e), parent=self)
                return

    def _clear_backups(self):
        if not messagebox.askyesno("Confirmare",
            "Stergi TOATE backup-urile automate?", parent=self): return
        import shutil
        bkp_dir = os.path.join(get_data_dir(), "backups")
        for fn in os.listdir(bkp_dir):
            if fn.endswith(".yojudge"):
                os.remove(os.path.join(bkp_dir, fn))
        self._refresh()

    def _clear_log(self):
        clear_error_log()
        self._refresh()
        self.status_var.set("Log erori sters.")
