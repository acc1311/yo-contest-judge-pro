#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Calendar Concursuri YO 2026
Afiseaza toate concursurile de pe radioamator.ro cu link-uri la regulamente PDF.
Permite: deschidere PDF in browser, selectare concurs pentru arbitraj,
         adaugare concurs nou custom, editare regulament existent.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os

from core.contest_calendar import CALENDAR_2026, CALENDAR_SOURCE

BG  = "#1e2a38"; BG2 = "#253447"; BG3 = "#2e3f55"
FG  = "#e8edf3"; ACC = "#2e75b6"; ACC2= "#4a9de0"
GRN = "#2ecc71"; RED = "#e74c3c"; YLW = "#f1c40f"
ORG = "#f39c12"; WHT = "#ffffff"; GRY = "#7f8c8d"
FONT = ("Consolas", 10); FONT_B = ("Consolas", 10, "bold")

class CalendarWindow(tk.Toplevel):
    """
    Fereastra Calendar Concursuri YO 2026.
    Afiseaza toate concursurile, permite deschiderea regulamentelor PDF
    si selectarea unui concurs pentru arbitraj.
    """
    def __init__(self, parent, contests, on_select=None):
        super().__init__(parent)
        self.contests   = contests    # dict cu concursurile din program
        self.on_select  = on_select   # callback(contest_id) la selectare

        self.title("Calendar Concursuri YO 2026 — radioamator.ro")
        self.configure(bg=BG)
        self.resizable(True, True)
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w = min(1100, int(sw*.88)); h = min(750, int(sh*.85))
        self.geometry("{}x{}+{}+{}".format(w, h, (sw-w)//2, (sh-h)//2))

        self._apply_style()
        self._build()
        self._populate()

    def _apply_style(self):
        st = ttk.Style(self)
        st.configure("Treeview", background=BG2, foreground=FG,
                     fieldbackground=BG2, font=FONT, rowheight=24)
        st.configure("Treeview.Heading", background=BG3, foreground=ACC2, font=FONT_B)
        st.map("Treeview", background=[("selected", ACC)])

    def _build(self):
        # Header
        top = tk.Frame(self, bg=ACC, height=48)
        top.pack(fill=tk.X)
        tk.Label(top, text="CALENDAR CONCURSURI YO 2026",
                 font=("Arial",13,"bold"), bg=ACC, fg=WHT, padx=14
                 ).pack(side=tk.LEFT, pady=10)
        tk.Label(top, text="Sursa: radioamator.ro/contest/",
                 font=("Arial",9), bg=ACC, fg="#dce8f5").pack(side=tk.LEFT)
        tk.Button(top, text="Deschide radioamator.ro/contest/",
                  command=lambda: webbrowser.open(CALENDAR_SOURCE),
                  bg=BG3, fg=WHT, font=FONT, relief="flat", padx=10
                  ).pack(side=tk.RIGHT, padx=8, pady=8)

        # Filtre
        ff = tk.Frame(self, bg=BG3)
        ff.pack(fill=tk.X, padx=0, pady=0)
        tk.Label(ff, text="  Filtru:", bg=BG3, fg=FG, font=FONT).pack(side=tk.LEFT, padx=4, pady=6)
        self.search_var = tk.StringVar()
        se = tk.Entry(ff, textvariable=self.search_var, width=25,
                      bg=BG2, fg=FG, insertbackground=FG, relief="flat", font=FONT)
        se.pack(side=tk.LEFT, padx=4, pady=6)
        se.bind("<KeyRelease>", lambda e: self._filter())

        tk.Label(ff, text="Tip:", bg=BG3, fg=FG, font=FONT).pack(side=tk.LEFT, padx=(12,4))
        self.type_var = tk.StringVar(value="Toate")
        ttk.Combobox(ff, textvariable=self.type_var,
                     values=["Toate","HF","VHF"],
                     state="readonly", width=8, font=FONT
                     ).pack(side=tk.LEFT, padx=4, pady=6)
        self.type_var.trace("w", lambda *a: self._filter())

        self.count_lbl = tk.Label(ff, text="", bg=BG3, fg=GRY, font=("Consolas",9))
        self.count_lbl.pack(side=tk.RIGHT, padx=14)

        # Treeview
        cols = ("date","name","organizer","type","band","mode","regul","in_prog")
        hdrs = ("Data","Concurs","Organizator","Tip","Banda","Mod","Regulament","In program")
        wids = (90, 280, 200, 50, 80, 80, 100, 90)

        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  selectmode="browse")
        for col, hdr, w in zip(cols, hdrs, wids):
            self.tree.heading(col, text=hdr,
                              command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w,
                             anchor="center" if w <= 90 else "w")

        vsb = ttk.Scrollbar(self, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal",  command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.tag_configure("has_prog",  background="#1b3a2a", foreground=GRN)
        self.tree.tag_configure("vhf",       background="#1a2a3a", foreground=ACC2)
        self.tree.tag_configure("no_prog",   foreground=FG)

        self.tree.bind("<Double-1>",        self._on_double)
        self.tree.bind("<Return>",          self._on_double)

        # Butoane actiune
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill=tk.X, padx=8, pady=6)

        btns = [
            ("Deschide Regulament PDF [DblClick]", self._open_pdf,   ACC),
            ("Selecteaza pt. Arbitraj",             self._select_contest, GRN),
            ("Adauga Concurs Nou...",               self._add_contest,    ORG),
            ("Editeaza Regulament...",              self._edit_contest,   YLW),
        ]
        for lbl, cmd, col in btns:
            tk.Button(bf, text=lbl, command=cmd,
                      bg=col, fg=BG if col in (GRN,YLW) else WHT,
                      font=FONT, relief="flat", padx=10, pady=4
                      ).pack(side=tk.LEFT, padx=4)

        # Info bar
        self.info_var = tk.StringVar(value="Selectati un concurs. DblClick = deschide regulament PDF in browser.")
        tk.Label(self, textvariable=self.info_var, bg=BG3, fg=ACC2,
                 font=("Consolas",9), anchor="w", padx=10
                 ).pack(side=tk.BOTTOM, fill=tk.X)

    def _populate(self, items=None):
        for row in self.tree.get_children():
            self.tree.delete(row)

        if items is None:
            items = CALENDAR_2026

        # Adauga si concursurile custom din program care nu sunt in calendar
        prog_names = {c.get("name","").lower() for c in self.contests.values()}

        count = 0
        for item in items:
            name     = item.get("name","")
            ctype    = item.get("type","HF")
            cid      = item.get("contest_id","")
            in_prog  = "DA" if (cid and cid in self.contests) else (
                       "DA" if any(name.lower() in k.lower() or k.lower() in name.lower()
                                   for k in prog_names) else "")

            tag = "has_prog" if in_prog else ("vhf" if ctype=="VHF" else "no_prog")
            self.tree.insert("","end", tags=(tag,), values=(
                item.get("date",""),
                name,
                item.get("organizer",""),
                ctype,
                item.get("band",""),
                item.get("mode",""),
                "PDF disponibil" if item.get("url","").endswith(".pdf") else "Link web",
                in_prog,
            ), iid=str(id(item)))
            count += 1

        self.count_lbl.configure(text="{} concursuri".format(count))
        self._items = items  # pastreaza pentru lookup

    def _filter(self):
        q    = self.search_var.get().strip().lower()
        ctyp = self.type_var.get()
        filtered = []
        for item in CALENDAR_2026:
            if ctyp != "Toate" and item.get("type","HF") != ctyp:
                continue
            if q and q not in item.get("name","").lower() and \
               q not in item.get("organizer","").lower() and \
               q not in item.get("date","").lower():
                continue
            filtered.append(item)
        self._populate(filtered)

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selectati un concurs din lista.", parent=self)
            return None
        iid = sel[0]
        # Gaseste item-ul original
        vals = self.tree.item(iid)["values"]
        name = vals[1]
        for item in CALENDAR_2026:
            if item.get("name","") == name:
                return item
        return None

    def _on_double(self, event=None):
        self._open_pdf()

    def _open_pdf(self):
        item = self._get_selected()
        if not item: return
        url = item.get("url","")
        if url:
            webbrowser.open(url)
            self.info_var.set("Deschis: {}".format(url))
        else:
            messagebox.showinfo("Info", "Niciun link disponibil pentru acest concurs.", parent=self)

    def _select_contest(self):
        """Selecteaza concursul pentru arbitraj si inchide fereastra."""
        item = self._get_selected()
        if not item: return
        cid  = item.get("contest_id","")
        name = item.get("name","")

        if cid and cid in self.contests:
            if self.on_select:
                self.on_select(cid)
            messagebox.showinfo("Selectat",
                "Concursul '{}' a fost selectat pentru arbitraj.".format(
                    self.contests[cid]["name"]), parent=self)
            self.destroy()
        else:
            # Cauta dupa nume
            for k, v in self.contests.items():
                if name.lower() in v.get("name","").lower() or \
                   v.get("name","").lower() in name.lower():
                    if self.on_select:
                        self.on_select(k)
                    messagebox.showinfo("Selectat",
                        "Concursul '{}' a fost selectat.".format(v["name"]), parent=self)
                    self.destroy()
                    return
            # Nu exista in program — ofera optiunea de a-l adauga
            if messagebox.askyesno("Concurs negasit",
                "Concursul '{}' nu are reguli definite in program.\n\n"
                "Doriti sa il adaugati acum cu setari de baza?".format(name),
                parent=self):
                self._add_contest(prefill=item)

    def _add_contest(self, prefill=None):
        """Deschide editorul de regulamente pentru un concurs nou."""
        from gui.rules_editor import RulesEditorDialog
        contests_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "contests")
        dlg = RulesEditorDialog(
            self,
            contests_dir=contests_dir,
            contests=self.contests,
            edit_id=None,
            on_save=self._on_contest_saved,
        )
        # Pre-completeaza daca avem date
        if prefill and hasattr(dlg, "_vars"):
            import re
            cid = re.sub(r'[^a-z0-9]', '_',
                         prefill.get("name","").lower())[:20]
            dlg._vars.get("id", tk.StringVar()).set(cid)
            dlg._vars.get("name", tk.StringVar()).set(prefill.get("name",""))

    def _edit_contest(self):
        """Editeaza regulamentul unui concurs existent."""
        item = self._get_selected()
        if not item: return
        cid = item.get("contest_id","")
        if not cid:
            for k, v in self.contests.items():
                if item.get("name","").lower() in v.get("name","").lower():
                    cid = k; break
        if not cid:
            messagebox.showinfo("Info",
                "Acest concurs nu are reguli definite in program.\n"
                "Folositi 'Adauga Concurs Nou' pentru a-l crea.", parent=self)
            return
        from gui.rules_editor import RulesEditorDialog
        contests_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "contests")
        RulesEditorDialog(
            self,
            contests_dir=contests_dir,
            contests=self.contests,
            edit_id=cid,
            on_save=self._on_contest_saved,
        )

    def _on_contest_saved(self, cid, data):
        """Callback dupa salvarea unui concurs."""
        if data:
            self.contests[cid] = data
        self._populate()
        self.info_var.set("Concurs salvat: {}".format(cid))

    def _sort(self, col):
        data = [(self.tree.set(c, col), c) for c in self.tree.get_children("")]
        data.sort(key=lambda x: x[0])
        for i, (_, c) in enumerate(data):
            self.tree.move(c, "", i)
