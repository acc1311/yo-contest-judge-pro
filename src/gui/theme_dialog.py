#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Theme Editor Dialog v2.2
Permite selectarea, previzualizarea si crearea temelor.
"""
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import copy
from gui.theme_engine import (
    THEMES, DEFAULT_THEME, FONT_FAMILIES, FONT_SIZES,
    get_theme, theme_names, is_dark, save_custom_theme, delete_custom_theme
)

COLOR_LABELS = {
    "BG":   "Fundal principal",
    "BG2":  "Fundal secundar (panouri)",
    "BG3":  "Fundal tertiar (titluri)",
    "FG":   "Text principal",
    "ACC":  "Accent (butoane, tab activ)",
    "ACC2": "Accent deschis (hover, titluri)",
    "GRN":  "Verde (OK / confirmat)",
    "RED":  "Rosu (Eroare / NIL)",
    "YLW":  "Galben (Avertisment)",
    "ORG":  "Portocaliu (Duplicat)",
    "GRY":  "Gri (text secundar)",
    "WHT":  "Alb / text pe fundal inchis",
}

class ThemeDialog(tk.Toplevel):
    def __init__(self, parent, current_theme, current_font, current_font_size,
                 on_apply, themes_dir=None):
        super().__init__(parent)
        self.title("Personalizare aspect")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.on_apply     = on_apply
        self.themes_dir   = themes_dir
        self._edit_colors = {}   # culori din tema editata
        self._preview_swatch = {}  # {key: Label widget}

        t = get_theme(current_theme)
        bg  = t["BG"]; fg = t["FG"]; acc = t["ACC"]; acc2 = t["ACC2"]
        bg2 = t["BG2"]; bg3 = t["BG3"]

        self.configure(bg=bg)

        # ── Header ───────────────────────────────────────────
        hdr = tk.Frame(self, bg=acc, pady=6)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎨  Personalizare aspect — YO Contest Judge PRO",
                 bg=acc, fg="white", font=("Arial",11,"bold")).pack(padx=12)

        body = tk.Frame(self, bg=bg)
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # ── Coloana stanga: selectie tema ────────────────────
        left = tk.LabelFrame(body, text=" Teme disponibile ",
                             bg=bg, fg=acc2, font=("Arial",9,"bold"),
                             relief="groove", bd=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,6), pady=0)

        self.theme_lb = tk.Listbox(left, width=24, height=12,
                                   bg=bg2, fg=fg, selectbackground=acc,
                                   selectforeground="white",
                                   activestyle="none", font=("Arial",9),
                                   relief="flat", bd=0, exportselection=False)
        self.theme_lb.pack(fill="both", expand=True, padx=4, pady=4)
        self._fill_theme_list()

        # Selecteaza tema curenta
        names = theme_names()
        if current_theme in names:
            idx = names.index(current_theme)
            self.theme_lb.selection_set(idx)
            self.theme_lb.see(idx)
        self.theme_lb.bind("<<ListboxSelect>>", self._on_theme_select)

        btn_frame = tk.Frame(left, bg=bg)
        btn_frame.pack(fill="x", padx=4, pady=(0,4))
        tk.Button(btn_frame, text="Aplica", bg=acc, fg="white",
                  font=("Arial",8,"bold"), relief="flat", cursor="hand2",
                  command=self._apply_selected).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Sterge custom", bg=t["RED"], fg="white",
                  font=("Arial",8), relief="flat", cursor="hand2",
                  command=self._delete_custom).pack(side="left", padx=2)

        # ── Coloana dreapta: editor culori ───────────────────
        right = tk.LabelFrame(body, text=" Editor culori (tema custom) ",
                              bg=bg, fg=acc2, font=("Arial",9,"bold"),
                              relief="groove", bd=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(0,0), pady=0)

        scroll_canvas = tk.Canvas(right, bg=bg, highlightthickness=0, width=320)
        scrollbar = ttk.Scrollbar(right, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)
        color_frame = tk.Frame(scroll_canvas, bg=bg)
        scroll_canvas.create_window((0,0), window=color_frame, anchor="nw")
        color_frame.bind("<Configure>",
            lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))

        # Grila culori
        for row_i, (key, label) in enumerate(COLOR_LABELS.items()):
            tk.Label(color_frame, text=label, bg=bg, fg=fg,
                     font=("Arial",8), anchor="w", width=28).grid(
                row=row_i, column=0, sticky="w", padx=6, pady=2)
            swatch = tk.Label(color_frame, text="  ", width=4,
                              relief="solid", bd=1, cursor="hand2")
            swatch.grid(row=row_i, column=1, padx=4, pady=2)
            self._preview_swatch[key] = swatch
            swatch.bind("<Button-1>", lambda e, k=key: self._pick_color(k))

        # Butoane editor
        ebar = tk.Frame(right, bg=bg)
        ebar.pack(fill="x", padx=6, pady=4)
        tk.Label(ebar, text="Nume tema:", bg=bg, fg=fg, font=("Arial",8)).pack(side="left")
        self.custom_name_var = tk.StringVar(value="Tema mea")
        tk.Entry(ebar, textvariable=self.custom_name_var, width=14,
                 bg=bg2, fg=fg, insertbackground=fg,
                 relief="flat", font=("Arial",8)).pack(side="left", padx=4)
        tk.Button(ebar, text="Salveaza tema", bg=t["GRN"], fg=bg,
                  font=("Arial",8,"bold"), relief="flat", cursor="hand2",
                  command=self._save_custom).pack(side="left", padx=2)

        # ── Font ─────────────────────────────────────────────
        font_frame = tk.LabelFrame(body, text=" Font & Marime ",
                                   bg=bg, fg=acc2, font=("Arial",9,"bold"),
                                   relief="groove", bd=1)
        font_frame.grid(row=1, column=0, columnspan=2, sticky="ew",
                        pady=(8,0))

        self.font_var = tk.StringVar(value=current_font)
        self.size_var = tk.IntVar(value=current_font_size)

        tk.Label(font_frame, text="Familie:", bg=bg, fg=fg,
                 font=("Arial",8)).grid(row=0, column=0, padx=6, pady=4, sticky="w")
        font_cb = ttk.Combobox(font_frame, textvariable=self.font_var,
                               values=FONT_FAMILIES, width=20, state="readonly")
        font_cb.grid(row=0, column=1, padx=4, pady=4, sticky="w")

        tk.Label(font_frame, text="Marime:", bg=bg, fg=fg,
                 font=("Arial",8)).grid(row=0, column=2, padx=6, pady=4, sticky="w")
        size_cb = ttk.Combobox(font_frame, textvariable=self.size_var,
                               values=FONT_SIZES, width=6, state="readonly")
        size_cb.grid(row=0, column=3, padx=4, pady=4, sticky="w")

        self.preview_lbl = tk.Label(font_frame,
            text="Preview: YO8ACR — 599 IS — 14.250 MHz SSB",
            bg=bg2, fg=fg, relief="flat", padx=8, pady=4)
        self.preview_lbl.grid(row=1, column=0, columnspan=4, sticky="ew",
                              padx=6, pady=(0,4))
        font_cb.bind("<<ComboboxSelected>>", self._update_font_preview)
        size_cb.bind("<<ComboboxSelected>>", self._update_font_preview)
        self._update_font_preview()

        # ── Butoane principale ────────────────────────────────
        bbar = tk.Frame(self, bg=bg)
        bbar.pack(fill="x", padx=10, pady=6)
        tk.Button(bbar, text="✔  Aplica si inchide",
                  bg=acc, fg="white", font=("Arial",9,"bold"),
                  relief="flat", cursor="hand2",
                  command=self._apply_and_close).pack(side="left", padx=4)
        tk.Button(bbar, text="Inchide",
                  bg=bg3, fg=fg, font=("Arial",9),
                  relief="flat", cursor="hand2",
                  command=self.destroy).pack(side="left", padx=4)

        # Initializeaza culori editor cu tema curenta
        self._load_colors_from_theme(current_theme)

        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)

        self._center()

    def _center(self):
        self.update_idletasks()
        w = self.winfo_reqwidth(); h = self.winfo_reqheight()
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        self.geometry("+{}+{}".format((sw-w)//2, (sh-h)//2))

    def _fill_theme_list(self):
        self.theme_lb.delete(0, "end")
        from gui.theme_engine import _BUILTIN_NAMES
        for name in theme_names():
            marker = "" if name in _BUILTIN_NAMES else " ★"
            self.theme_lb.insert("end", name + marker)

    def _on_theme_select(self, event=None):
        sel = self.theme_lb.curselection()
        if not sel: return
        raw = self.theme_lb.get(sel[0]).rstrip(" ★")
        self._load_colors_from_theme(raw)

    def _load_colors_from_theme(self, theme_name):
        t = get_theme(theme_name)
        self._edit_colors = {k: t[k] for k in COLOR_LABELS}
        self._refresh_swatches()

    def _refresh_swatches(self):
        for key, lbl in self._preview_swatch.items():
            c = self._edit_colors.get(key, "#888888")
            lbl.configure(bg=c)

    def _pick_color(self, key):
        current = self._edit_colors.get(key, "#888888")
        result = colorchooser.askcolor(color=current,
            title="Alege culoarea pentru: {}".format(COLOR_LABELS.get(key, key)))
        if result and result[1]:
            self._edit_colors[key] = result[1]
            self._preview_swatch[key].configure(bg=result[1])

    def _apply_selected(self):
        sel = self.theme_lb.curselection()
        if not sel:
            messagebox.showwarning("Atentie", "Selectati o tema din lista.", parent=self)
            return
        name = self.theme_lb.get(sel[0]).rstrip(" ★")
        self.on_apply(name, self.font_var.get(), self.size_var.get())

    def _save_custom(self):
        name = self.custom_name_var.get().strip()
        if not name:
            messagebox.showwarning("Atentie", "Introduceti un nume pentru tema.", parent=self)
            return
        if not self.themes_dir:
            messagebox.showerror("Eroare", "Directorul de date nu este configurat.", parent=self)
            return
        theme_data = dict(self._edit_colors)
        theme_data["_dark"] = True  # presupunem dark; utilizatorul poate schimba
        save_custom_theme(name, theme_data, self.themes_dir)
        self._fill_theme_list()
        # Selecteaza tema nou creata
        names = theme_names()
        if name in names:
            idx = names.index(name)
            self.theme_lb.selection_clear(0, "end")
            self.theme_lb.selection_set(idx)
            self.theme_lb.see(idx)
        messagebox.showinfo("Salvat", "Tema '{}' salvata.".format(name), parent=self)

    def _delete_custom(self):
        sel = self.theme_lb.curselection()
        if not sel: return
        name = self.theme_lb.get(sel[0]).rstrip(" ★")
        from gui.theme_engine import _BUILTIN_NAMES
        if name in _BUILTIN_NAMES:
            messagebox.showwarning("Atentie",
                "Temele predefinite nu pot fi sterse.", parent=self)
            return
        if messagebox.askyesno("Confirmare",
                "Stergi tema '{}'?".format(name), parent=self):
            delete_custom_theme(name, self.themes_dir or "")
            self._fill_theme_list()
            self.theme_lb.selection_set(0)
            self._on_theme_select()

    def _update_font_preview(self, event=None):
        fam = self.font_var.get()
        sz  = self.size_var.get()
        self.preview_lbl.configure(font=(fam, sz))

    def _apply_and_close(self):
        sel = self.theme_lb.curselection()
        if sel:
            name = self.theme_lb.get(sel[0]).rstrip(" ★")
        else:
            name = DEFAULT_THEME
        self.on_apply(name, self.font_var.get(), self.size_var.get())
        self.destroy()
