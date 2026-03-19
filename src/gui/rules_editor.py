#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Editor Regulamente Concurs
Dialog complet pentru creare/editare concursuri custom JSON.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from core.contest_rules import (
    BANDS_ALL, MODES_ALL, save_contest_json, delete_contest_json
)

class RulesEditorDialog(tk.Toplevel):
    """
    Dialog modal pentru creare/editare regulament concurs.
    Apelat din meniul principal: Concursuri → Editare regulament.
    """
    def __init__(self, parent, contests_dir, contests, edit_id=None, on_save=None):
        super().__init__(parent)
        self.contests_dir = contests_dir
        self.contests     = contests
        self.edit_id      = edit_id
        self.on_save      = on_save   # callback dupa save

        self.title("Editor Regulament Concurs")
        self.resizable(True, True)
        self.configure(bg="#1e2a38")
        self.grab_set()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = min(820, int(sw*0.7)), min(700, int(sh*0.85))
        self.geometry("{}x{}+{}+{}".format(w, h,
            (sw-w)//2, (sh-h)//2))

        self._vars = {}
        self._band_vars  = {}
        self._mode_vars  = {}
        self._build()

        if edit_id and edit_id in contests:
            self._load(contests[edit_id])

    # ── UI ────────────────────────────────────────────────────
    def _lbl(self, parent, text, row, col, **kw):
        l = tk.Label(parent, text=text, bg="#1e2a38", fg="#e8edf3",
                     font=("Arial",9), anchor="w")
        l.grid(row=row, column=col, sticky="w", padx=6, pady=3, **kw)
        return l

    def _entry(self, parent, var_key, row, col, width=28, **kw):
        v = tk.StringVar()
        self._vars[var_key] = v
        e = tk.Entry(parent, textvariable=v, width=width,
                     bg="#253447", fg="#e8edf3", insertbackground="#e8edf3",
                     relief="flat", font=("Consolas",10))
        e.grid(row=row, column=col, sticky="ew", padx=6, pady=3, **kw)
        return e

    def _combo(self, parent, var_key, values, row, col, width=18, **kw):
        v = tk.StringVar()
        self._vars[var_key] = v
        c = ttk.Combobox(parent, textvariable=v, values=values,
                         state="readonly", width=width,
                         font=("Consolas",10))
        c.grid(row=row, column=col, sticky="w", padx=6, pady=3, **kw)
        if values: c.set(values[0])
        return c

    def _build(self):
        style = ttk.Style(self)
        style.configure("E.TLabelframe",       background="#1e2a38", foreground="#4a9de0")
        style.configure("E.TLabelframe.Label", background="#1e2a38", foreground="#4a9de0",
                        font=("Arial",10,"bold"))

        # ── Scroll frame simplu si stabil ──
        outer = tk.Frame(self, bg="#1e2a38")
        outer.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(outer, bg="#1e2a38", highlightthickness=0,
                           yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.configure(command=canvas.yview)

        inner = tk.Frame(canvas, bg="#1e2a38")
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(win_id, width=e.width)
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")

        inner.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        inner.bind("<MouseWheel>", _on_mousewheel)
        # Forteaza update dupa afisare
        self.after(100, lambda: canvas.configure(
            scrollregion=canvas.bbox("all")))

        # ── Sectiunea Informatii generale ──
        gf = ttk.LabelFrame(inner, text="Informatii generale", style="E.TLabelframe", padding=8)
        gf.pack(fill=tk.X, padx=10, pady=6)
        gf.columnconfigure(1, weight=1)

        self._lbl(gf, "ID concurs (fara spatii):",  0, 0)
        self._entry(gf, "id", 0, 1)
        self._lbl(gf, "Nume afisat:",                1, 0)
        self._entry(gf, "name", 1, 1)
        self._lbl(gf, "Cabrillo CONTEST:  header:",  2, 0)
        self._entry(gf, "cabrillo_name", 2, 1)
        self._lbl(gf, "Descriere:",                  3, 0)
        self._entry(gf, "description", 3, 1)
        self._lbl(gf, "Durata (ore, 0=nelimitat):",  4, 0)
        self._entry(gf, "duration_hours", 4, 1, width=8)
        self._lbl(gf, "QSO minim clasare:",          5, 0)
        self._entry(gf, "min_qso", 5, 1, width=8)

        # ── Sectiunea Scoring ──
        sf = ttk.LabelFrame(inner, text="Scoring", style="E.TLabelframe", padding=8)
        sf.pack(fill=tk.X, padx=10, pady=6)
        sf.columnconfigure(1, weight=1)

        self._lbl(sf, "Mod calcul scor:", 0, 0)
        self._combo(sf, "scoring_mode",
            ["per_qso","maraton","per_band","distance","none"], 0, 1)
        self._lbl(sf, "Puncte per QSO:",  1, 0)
        self._entry(sf, "points_per_qso", 1, 1, width=8)
        self._lbl(sf, "Multiplicatori:",  2, 0)
        self._combo(sf, "multiplier",
            ["none","county","dxcc_band","locator_field"], 2, 1)
        self._lbl(sf, "Schimb (exchange):", 3, 0)
        self._combo(sf, "exchange",
            ["county","serial","locator","none"], 3, 1)

        cv = tk.BooleanVar()
        self._vars["cross_check"] = cv
        tk.Checkbutton(sf, text="Activare cross-check", variable=cv,
                       bg="#1e2a38", fg="#e8edf3", selectcolor="#253447",
                       activebackground="#1e2a38", activeforeground="#e8edf3",
                       font=("Arial",9)).grid(row=4, column=0, columnspan=2,
                                              sticky="w", padx=6, pady=3)

        # ── Sectiunea Benzi ──
        bf = ttk.LabelFrame(inner, text="Benzi permise", style="E.TLabelframe", padding=8)
        bf.pack(fill=tk.X, padx=10, pady=6)
        for i, band in enumerate(BANDS_ALL):
            v = tk.BooleanVar(value=True)
            self._band_vars[band] = v
            tk.Checkbutton(bf, text=band, variable=v,
                           bg="#1e2a38", fg="#e8edf3", selectcolor="#253447",
                           activebackground="#1e2a38", activeforeground="#e8edf3",
                           font=("Consolas",9)).grid(
                               row=i//7, column=i%7, sticky="w", padx=4, pady=2)

        # ── Sectiunea Moduri ──
        mf = ttk.LabelFrame(inner, text="Moduri permise", style="E.TLabelframe", padding=8)
        mf.pack(fill=tk.X, padx=10, pady=6)
        for i, mode in enumerate(MODES_ALL):
            v = tk.BooleanVar(value=True)
            self._mode_vars[mode] = v
            tk.Checkbutton(mf, text=mode, variable=v,
                           bg="#1e2a38", fg="#e8edf3", selectcolor="#253447",
                           activebackground="#1e2a38", activeforeground="#e8edf3",
                           font=("Consolas",9)).grid(
                               row=i//6, column=i%6, sticky="w", padx=4, pady=2)

        # ── Butoane ──
        bf2 = tk.Frame(inner, bg="#1e2a38")
        bf2.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(bf2, text="💾  Salveaza", command=self._save,
                  bg="#2e75b6", fg="white", font=("Arial",10,"bold"),
                  relief="flat", padx=14, pady=6).pack(side=tk.LEFT, padx=4)

        if self.edit_id and self.edit_id not in (
            "simplu","maraton","stafeta","yodxhf","yovhf","fieldday","sprint","cupa_moldovei"):
            tk.Button(bf2, text="🗑  Sterge", command=self._delete,
                      bg="#e74c3c", fg="white", font=("Arial",10,"bold"),
                      relief="flat", padx=14, pady=6).pack(side=tk.LEFT, padx=4)

        tk.Button(bf2, text="Anuleaza", command=self.destroy,
                  bg="#444", fg="white", font=("Arial",10),
                  relief="flat", padx=14, pady=6).pack(side=tk.RIGHT, padx=4)

    def _load(self, data):
        """Incarca datele unui concurs existent in form."""
        for key in ("name","cabrillo_name","description"):
            if key in self._vars:
                self._vars[key].set(data.get(key,""))
        self._vars.get("id",tk.StringVar()).set(self.edit_id or "")
        self._vars.get("duration_hours",tk.StringVar()).set(str(data.get("duration_hours",0)))
        self._vars.get("min_qso",tk.StringVar()).set(str(data.get("min_qso",0)))
        self._vars.get("points_per_qso",tk.StringVar()).set(str(data.get("points_per_qso",1)))
        self._vars.get("scoring_mode",tk.StringVar()).set(data.get("scoring_mode","per_qso"))
        self._vars.get("multiplier",tk.StringVar()).set(data.get("multiplier","none"))
        self._vars.get("exchange",tk.StringVar()).set(data.get("exchange","none"))
        if "cross_check" in self._vars:
            self._vars["cross_check"].set(data.get("cross_check",False))
        ab = [b.lower() for b in data.get("allowed_bands",BANDS_ALL)]
        for band, v in self._band_vars.items():
            v.set(band.lower() in ab)
        am = [m.upper() for m in data.get("allowed_modes",MODES_ALL)]
        for mode, v in self._mode_vars.items():
            v.set(mode.upper() in am)

    def _collect(self):
        """Colecteaza datele din form si returneaza dict."""
        cid = self._vars.get("id",tk.StringVar()).get().strip().lower().replace(" ","_")
        if not cid:
            raise ValueError("ID-ul concursului nu poate fi gol!")
        data = {
            "name":           self._vars.get("name",tk.StringVar()).get().strip() or cid,
            "cabrillo_name":  self._vars.get("cabrillo_name",tk.StringVar()).get().strip().upper(),
            "description":    self._vars.get("description",tk.StringVar()).get().strip(),
            "scoring_mode":   self._vars.get("scoring_mode",tk.StringVar()).get(),
            "multiplier":     self._vars.get("multiplier",tk.StringVar()).get(),
            "exchange":       self._vars.get("exchange",tk.StringVar()).get(),
            "cross_check":    bool(self._vars.get("cross_check",tk.BooleanVar()).get()),
            "allowed_bands":  [b for b, v in self._band_vars.items() if v.get()],
            "allowed_modes":  [m for m, v in self._mode_vars.items() if v.get()],
        }
        try:
            data["duration_hours"] = int(self._vars.get("duration_hours",tk.StringVar()).get() or 0)
            data["min_qso"]        = int(self._vars.get("min_qso",tk.StringVar()).get() or 0)
            data["points_per_qso"] = int(self._vars.get("points_per_qso",tk.StringVar()).get() or 1)
        except ValueError as e:
            raise ValueError("Valoare numerica invalida: {}".format(e))
        return cid, data

    def _save(self):
        try:
            cid, data = self._collect()
        except ValueError as e:
            messagebox.showerror("Eroare", str(e), parent=self)
            return

        # Verifica suprascriere concursuri built-in
        builtin_ids = ["simplu","maraton","stafeta","yodxhf","yovhf","fieldday","sprint","cupa_moldovei"]
        if cid in builtin_ids and cid != self.edit_id:
            messagebox.showwarning("Atentie",
                "ID-ul '{}' este rezervat pentru un concurs built-in.\nFolositi un ID diferit.".format(cid),
                parent=self)
            return

        save_contest_json(cid, data, self.contests_dir)
        if self.on_save:
            self.on_save(cid, data)
        messagebox.showinfo("Salvat",
            "Concursul '{}' a fost salvat.".format(data["name"]), parent=self)
        self.destroy()

    def _delete(self):
        cid = self.edit_id
        if not messagebox.askyesno("Confirmare",
            "Stergi concursul '{}'?".format(cid), parent=self):
            return
        delete_contest_json(cid, self.contests_dir)
        if self.on_save:
            self.on_save(cid, None)
        self.destroy()
