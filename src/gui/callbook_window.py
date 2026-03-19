#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Fereastra Callbook
Cautare, vizualizare pe judete, editare, adaugare, import XLSX.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

from core.callbook_engine import CallbookDB, JUDETE_RO, county_code_to_name

BG  = "#1e2a38"; BG2 = "#253447"; BG3 = "#2e3f55"
FG  = "#e8edf3"; ACC = "#2e75b6"; ACC2= "#4a9de0"
GRN = "#2ecc71"; RED = "#e74c3c"; YLW = "#f1c40f"
WHT = "#ffffff"; GRY = "#7f8c8d"
FONT = ("Consolas",10); FONT_B = ("Consolas",10,"bold")

class CallbookWindow(tk.Toplevel):
    def __init__(self, parent, db: CallbookDB):
        super().__init__(parent)
        self.db = db
        self.title("Callbook Radioamatori YO — Editare")
        self.configure(bg=BG)
        self.resizable(True, True)

        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w = min(1280, int(sw*.92)); h = min(860, int(sh*.88))
        self.geometry("{}x{}+{}+{}".format(w,h,(sw-w)//2,(sh-h)//2))

        self._apply_style()
        self._build()
        self._load_county_list()
        self._search()

    def _apply_style(self):
        st = ttk.Style(self)
        st.configure("Treeview", background=BG2, foreground=FG,
                     fieldbackground=BG2, font=FONT, rowheight=22)
        st.configure("Treeview.Heading", background=BG3, foreground=ACC2, font=FONT_B)
        st.map("Treeview", background=[("selected",ACC)])
        st.configure("CB.TNotebook", background=BG)
        st.configure("CB.TNotebook.Tab", background=BG3, foreground=FG,
                     padding=(10,4), font=FONT_B)
        st.map("CB.TNotebook.Tab",
               background=[("selected",ACC)], foreground=[("selected",WHT)])

    def _build(self):
        # Top bar
        top = tk.Frame(self, bg=ACC, height=44)
        top.pack(fill=tk.X)
        tk.Label(top, text="CALLBOOK RADIOAMATORI ROMANIA",
                 font=("Arial",13,"bold"), bg=ACC, fg=WHT, padx=14).pack(side=tk.LEFT, pady=8)
        # Stats
        st = self.db.stats()
        tk.Label(top, text="{} indicative | {} publice | {} repetoare".format(
                     st["total"], st["public"], st["repeaters"]),
                 font=("Arial",9), bg=ACC, fg="#dce8f5").pack(side=tk.LEFT)

        tk.Button(top, text="+ Adauga", command=self._add,
                  bg=GRN, fg=BG, font=FONT_B, relief="flat", padx=10
                  ).pack(side=tk.RIGHT, padx=6, pady=6)
        tk.Button(top, text="Import XLSX", command=self._import_xlsx,
                  bg="#f39c12", fg=WHT, font=FONT_B, relief="flat", padx=10
                  ).pack(side=tk.RIGHT, padx=2, pady=6)

        # Status bar
        self.status_var = tk.StringVar(value="Gata.")
        tk.Label(self, textvariable=self.status_var, bg=BG3, fg=ACC2,
                 font=("Consolas",9), anchor="w", padx=10).pack(side=tk.BOTTOM, fill=tk.X)

        # Notebook
        nb = ttk.Notebook(self, style="CB.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1: Cautare
        self.tab_search = ttk.Frame(nb)
        nb.add(self.tab_search, text="  Cautare  ")
        self._build_search_tab(self.tab_search)

        # Tab 2: Pe judete
        self.tab_county = ttk.Frame(nb)
        nb.add(self.tab_county, text="  Pe Judete  ")
        self._build_county_tab(self.tab_county)

        # Tab 3: Repetoare
        self.tab_rep = ttk.Frame(nb)
        nb.add(self.tab_rep, text="  Repetoare  ")
        self._build_repeater_tab(self.tab_rep)

    # ── Tab Cautare ───────────────────────────────────────────
    def _build_search_tab(self, p):
        sf = tk.Frame(p, bg=BG); sf.pack(fill=tk.X, padx=8, pady=6)

        tk.Label(sf, text="Cauta:", bg=BG, fg=FG, font=FONT).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        se = tk.Entry(sf, textvariable=self.search_var, width=22,
                      bg=BG2, fg=FG, insertbackground=FG, relief="flat", font=FONT)
        se.pack(side=tk.LEFT, padx=6)
        se.bind("<Return>", lambda e: self._search())
        se.bind("<KeyRelease>", lambda e: self._search())

        tk.Label(sf, text="in:", bg=BG, fg=FG, font=FONT).pack(side=tk.LEFT)
        self.field_var = tk.StringVar(value="any")
        ttk.Combobox(sf, textvariable=self.field_var,
                     values=["any","call","name","city","county"],
                     state="readonly", width=8, font=FONT
                     ).pack(side=tk.LEFT, padx=4)

        tk.Label(sf, text="Judet:", bg=BG, fg=FG, font=FONT).pack(side=tk.LEFT, padx=(12,0))
        self.county_filter = tk.StringVar(value="Toate")
        self.county_cb = ttk.Combobox(sf, textvariable=self.county_filter,
                                       state="readonly", width=18, font=FONT)
        self.county_cb.pack(side=tk.LEFT, padx=4)
        self.county_cb.bind("<<ComboboxSelected>>", lambda e: self._search())

        ttk.Button(sf, text="Cauta", command=self._search).pack(side=tk.LEFT, padx=4)

        self.result_lbl = tk.Label(sf, text="", bg=BG, fg=GRY, font=("Consolas",9))
        self.result_lbl.pack(side=tk.RIGHT, padx=10)

        # Treeview rezultate
        cols = ("call","name","class","city","county","email","expires","src")
        hdrs = ("Indicativ","Titular","Cls","Localitate","Judet","Email","Expira","Sursa")
        wids = (90, 180, 35, 140, 130, 180, 90, 55)
        self.tree = ttk.Treeview(p, columns=cols, show="headings")
        for col, hdr, w in zip(cols, hdrs, wids):
            self.tree.heading(col, text=hdr, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w, anchor="w" if w>60 else "center")
        vsb = ttk.Scrollbar(p, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(p, orient="horizontal",  command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.tag_configure("user",    background="#1b3a2a", foreground=GRN)
        self.tree.tag_configure("private", foreground=GRY)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Delete>",   self._delete_selected)

        # Butoane actiune
        bf = tk.Frame(p, bg=BG); bf.pack(fill=tk.X, padx=8, pady=4)
        for lbl, cmd, col in [
            ("Editeaza [DblClick]", self._edit_selected, ACC),
            ("Sterge selectat",     self._delete_selected, RED),
        ]:
            tk.Button(bf, text=lbl, command=cmd, bg=col, fg=WHT,
                      font=FONT, relief="flat", padx=8, pady=3
                      ).pack(side=tk.LEFT, padx=4)

    # ── Tab Pe Judete ─────────────────────────────────────────
    def _build_county_tab(self, p):
        paned = tk.PanedWindow(p, orient=tk.HORIZONTAL, bg=BG, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        # Lista judete stanga
        lf = tk.Frame(paned, bg=BG, width=220)
        paned.add(lf)
        tk.Label(lf, text="Judete Romania", bg=BG3, fg=ACC2,
                 font=FONT_B, padx=8, pady=4).pack(fill=tk.X)
        self.county_tree = ttk.Treeview(lf, columns=("cod","jud","cnt"), show="headings")
        self.county_tree.heading("cod", text="Cod")
        self.county_tree.heading("jud", text="Judet")
        self.county_tree.heading("cnt", text="Nr.")
        self.county_tree.column("cod", width=40, anchor="center")
        self.county_tree.column("jud", width=130)
        self.county_tree.column("cnt", width=40, anchor="center")
        vsb2 = ttk.Scrollbar(lf, orient="vertical", command=self.county_tree.yview)
        self.county_tree.configure(yscrollcommand=vsb2.set)
        self.county_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb2.pack(side=tk.RIGHT, fill=tk.Y)
        self.county_tree.bind("<<TreeviewSelect>>", self._on_county_select)

        # Lista radioamatori dreapta
        rf = tk.Frame(paned, bg=BG)
        paned.add(rf)
        self.county_lbl = tk.Label(rf, text="Selectati un judet", bg=BG3, fg=ACC2,
                                    font=FONT_B, padx=8, pady=4)
        self.county_lbl.pack(fill=tk.X)
        cols = ("call","name","class","city","email")
        hdrs = ("Indicativ","Titular","Cls","Localitate","Email")
        wids = (90, 180, 35, 160, 200)
        self.county_detail = ttk.Treeview(rf, columns=cols, show="headings")
        for col, hdr, w in zip(cols, hdrs, wids):
            self.county_detail.heading(col, text=hdr)
            self.county_detail.column(col, width=w, anchor="w" if w>60 else "center")
        vsb3 = ttk.Scrollbar(rf, orient="vertical",  command=self.county_detail.yview)
        hsb3 = ttk.Scrollbar(rf, orient="horizontal", command=self.county_detail.xview)
        self.county_detail.configure(yscrollcommand=vsb3.set, xscrollcommand=hsb3.set)
        self.county_detail.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb3.pack(side=tk.RIGHT, fill=tk.Y)
        hsb3.pack(side=tk.BOTTOM, fill=tk.X)
        self.county_detail.bind("<Double-1>", self._county_detail_dbl)

    # ── Tab Repetoare ─────────────────────────────────────────
    def _build_repeater_tab(self, p):
        sf = tk.Frame(p, bg=BG); sf.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(sf, text="Cauta:", bg=BG, fg=FG, font=FONT).pack(side=tk.LEFT)
        self.rep_var = tk.StringVar()
        re_entry = tk.Entry(sf, textvariable=self.rep_var, width=20,
                            bg=BG2, fg=FG, insertbackground=FG, relief="flat", font=FONT)
        re_entry.pack(side=tk.LEFT, padx=6)
        re_entry.bind("<KeyRelease>", lambda e: self._search_rep())

        cols = ("call","owner","freq_tx","freq_rx","type","lat","lon")
        hdrs = ("Indicativ","Titular","Freq TX","Freq RX","Tip","Latitudine","Longitudine")
        wids = (130, 220, 100, 100, 70, 120, 120)
        self.rep_tree = ttk.Treeview(p, columns=cols, show="headings")
        for col, hdr, w in zip(cols, hdrs, wids):
            self.rep_tree.heading(col, text=hdr)
            self.rep_tree.column(col, width=w, anchor="w" if w>80 else "center")
        vsb = ttk.Scrollbar(p, orient="vertical",  command=self.rep_tree.yview)
        hsb = ttk.Scrollbar(p, orient="horizontal", command=self.rep_tree.xview)
        self.rep_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.rep_tree.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._load_repeaters()

    # ── Logica ────────────────────────────────────────────────
    def _load_county_list(self):
        counties = self.db.get_all_counties()
        # Combobox filtru cautare
        opts = ["Toate"] + ["{} — {}".format(code, name) for code,name,cnt in counties if cnt>0]
        self.county_cb["values"] = opts

        # Treeview judete
        for item in self.county_tree.get_children():
            self.county_tree.delete(item)
        for code, name, cnt in counties:
            self.county_tree.insert("","end", values=(code, name, cnt))

    def _search(self, event=None):
        q     = self.search_var.get().strip()
        field = self.field_var.get()
        cf    = self.county_filter.get()
        cc    = ""
        if cf and cf != "Toate":
            cc = cf.split(" — ")[0].strip()

        self.db._ensure_loaded()
        results = self.db.search(q, field, county_code=cc, limit=500)

        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in results:
            tag = "user" if r.get("_src")=="user" else ("private" if r.get("private") else "")
            name  = r.get("name","") if not r.get("private") else "[DATE PERSONALE]"
            city  = r.get("city","") if not r.get("private") else ""
            email = r.get("email","") if not r.get("private") else ""
            self.tree.insert("","end", tags=(tag,), values=(
                r.get("call",""),
                name,
                r.get("class",""),
                city,
                r.get("county",""),
                email,
                r.get("expires","")[:10] if r.get("expires") else "",
                r.get("_src","arr"),
            ))
        self.result_lbl.configure(text="{} rezultate".format(len(results)))

    def _search_rep(self):
        q = self.rep_var.get().strip().upper()
        for item in self.rep_tree.get_children():
            self.rep_tree.delete(item)
        self.db._ensure_loaded()
        count = 0
        for call, r in self.db.rep_records.items():
            if q and q not in call.upper() and q not in r.get("owner","").upper():
                continue
            freq_tx = "{:.3f} MHz".format(r["freq_tx"]) if r.get("freq_tx") else ""
            freq_rx = "{:.3f} MHz".format(r["freq_rx"]) if r.get("freq_rx") else ""
            self.rep_tree.insert("","end", values=(
                call, r.get("owner",""), freq_tx, freq_rx,
                r.get("type",""), r.get("lat",""), r.get("lon",""),
            ))
            count += 1
        self.status_var.set("{} repetoare".format(count))

    def _load_repeaters(self):
        self._search_rep()

    def _on_county_select(self, event=None):
        sel = self.county_tree.selection()
        if not sel: return
        code, name, cnt = self.county_tree.item(sel[0])["values"]
        self.county_lbl.configure(text="{} — {} ({} radioamatori)".format(code, name, cnt))
        recs = self.db.get_by_county(code)
        for item in self.county_detail.get_children():
            self.county_detail.delete(item)
        for r in recs:
            n = r.get("name","") if not r.get("private") else "[DATE PERSONALE]"
            c = r.get("city","") if not r.get("private") else ""
            e = r.get("email","") if not r.get("private") else ""
            self.county_detail.insert("","end", values=(
                r.get("call",""), n, r.get("class",""), c, e))
        self.status_var.set("{} radioamatori in {}".format(len(recs), name))

    def _county_detail_dbl(self, event=None):
        sel = self.county_detail.selection()
        if not sel: return
        call = self.county_detail.item(sel[0])["values"][0]
        rec  = self.db.lookup(call)
        if rec: self._open_edit_dialog(rec)

    def _on_double_click(self, event=None):
        self._edit_selected()

    def _edit_selected(self):
        sel = self.tree.selection()
        if not sel: return
        call = self.tree.item(sel[0])["values"][0]
        rec  = self.db.lookup(call)
        if rec: self._open_edit_dialog(rec)

    def _delete_selected(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        call = self.tree.item(sel[0])["values"][0]
        rec  = self.db.lookup(call)
        if rec and rec.get("_src") != "user":
            messagebox.showinfo("Info",
                "Doar inregistrarile adaugate manual pot fi sterse.\n"
                "{} provine din Callbook-ul ARR oficial.".format(call), parent=self)
            return
        if messagebox.askyesno("Confirmare", "Stergi {}?".format(call), parent=self):
            if self.db.delete(call):
                self._search()
                self.status_var.set("{} sters.".format(call))

    def _add(self):
        self._open_edit_dialog(None)

    def _open_edit_dialog(self, rec):
        EditDialog(self, self.db, rec, on_save=self._on_saved)

    def _on_saved(self, call):
        self._search()
        self._load_county_list()
        self.status_var.set("{} salvat.".format(call))

    def _import_xlsx(self):
        fp = filedialog.askopenfilename(
            parent=self, title="Import XLSX Callbook",
            filetypes=[("Excel","*.xlsx *.xls"),("Toate","*.*")])
        if not fp: return
        try:
            res = self.db.import_xlsx(fp)
            self._search()
            self._load_county_list()
            messagebox.showinfo("Import",
                "Import finalizat:\n"
                "Adaugate: {}\nActualizate: {}\nSarite: {}".format(
                    res["added"], res["updated"], res["skipped"]), parent=self)
        except Exception as e:
            messagebox.showerror("Eroare import", str(e), parent=self)

    def _sort(self, col):
        data = [(self.tree.set(c, col), c) for c in self.tree.get_children("")]
        data.sort(key=lambda x: x[0].lower())
        for i, (_, c) in enumerate(data):
            self.tree.move(c, "", i)


class EditDialog(tk.Toplevel):
    """Dialog adaugare/editare inregistrare callbook."""
    def __init__(self, parent, db: CallbookDB, rec, on_save=None):
        super().__init__(parent)
        self.db      = db
        self.rec     = rec or {}
        self.on_save = on_save
        self.is_new  = (rec is None)
        title = "Adauga Radioamator" if self.is_new else "Editeaza — {}".format(rec.get("call",""))
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w, h = 480, 420
        self.geometry("{}x{}+{}+{}".format(w,h,(sw-w)//2,(sh-h)//2))

        self._vars = {}
        self._build()
        if not self.is_new:
            self._load(self.rec)

    def _field(self, parent, label, key, row, values=None, width=28):
        tk.Label(parent, text=label, bg=BG, fg=FG, font=("Arial",9),
                 anchor="w").grid(row=row, column=0, sticky="w", padx=10, pady=4)
        v = tk.StringVar()
        self._vars[key] = v
        if values:
            w = ttk.Combobox(parent, textvariable=v, values=values,
                             state="readonly", width=width-2, font=FONT)
        else:
            w = tk.Entry(parent, textvariable=v, width=width,
                         bg=BG2, fg=FG, insertbackground=FG, relief="flat", font=FONT)
        w.grid(row=row, column=1, sticky="ew", padx=10, pady=4)
        return w

    def _build(self):
        f = tk.Frame(self, bg=BG); f.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        f.columnconfigure(1, weight=1)

        self._field(f, "Indicativ *:",    "call",    0)
        self._field(f, "Titular:",        "name",    1)
        self._field(f, "Clasa:",          "class",   2, values=["","1","2","3","4"])
        self._field(f, "Localitate:",     "city",    3)
        county_opts = [""] + ["{} — {}".format(k,v) for k,v in sorted(JUDETE_RO.items())]
        self._field(f, "Judet:",          "county",  4, values=county_opts, width=30)
        self._field(f, "Email:",          "email",   5)
        self._field(f, "Data expirare:",  "expires", 6)
        self._field(f, "Note:",           "note",    7)

        if not self.is_new and self.rec.get("_src") == "arr":
            tk.Label(f, text="Sursa: Callbook ARR oficial (read-only pentru date originale)",
                     bg=BG, fg=YLW, font=("Arial",8)).grid(
                         row=8, column=0, columnspan=2, padx=10, pady=2)

        bf = tk.Frame(self, bg=BG); bf.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(bf, text="Salveaza", command=self._save,
                  bg=GRN, fg=BG, font=FONT_B, relief="flat", padx=14, pady=5
                  ).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="Anuleaza", command=self.destroy,
                  bg="#555", fg=WHT, font=FONT, relief="flat", padx=14, pady=5
                  ).pack(side=tk.RIGHT, padx=4)

    def _load(self, rec):
        self._vars["call"].set(rec.get("call",""))
        self._vars["name"].set(rec.get("name","") if not rec.get("private") else "")
        self._vars["class"].set(str(rec.get("class","")) if rec.get("class") else "")
        self._vars["city"].set(rec.get("city","") if not rec.get("private") else "")
        county = rec.get("county","")
        from core.callbook_engine import county_code_to_name
        # Gaseste optiunea corecta in combobox
        code = rec.get("county_code","")
        if code and code in JUDETE_RO:
            self._vars["county"].set("{} — {}".format(code, JUDETE_RO[code]))
        else:
            self._vars["county"].set(county)
        self._vars["email"].set(rec.get("email","") if not rec.get("private") else "")
        self._vars["expires"].set(rec.get("expires",""))
        self._vars["note"].set(rec.get("note",""))

    def _save(self):
        call = self._vars["call"].get().strip().upper()
        if not call:
            messagebox.showerror("Eroare", "Indicativul este obligatoriu!", parent=self)
            return
        county_raw = self._vars["county"].get().strip()
        county = county_raw.split(" — ")[0].strip() if " — " in county_raw else county_raw

        rec = {
            "call":    call,
            "name":    self._vars["name"].get().strip(),
            "city":    self._vars["city"].get().strip(),
            "county":  county,
            "email":   self._vars["email"].get().strip(),
            "expires": self._vars["expires"].get().strip(),
            "note":    self._vars["note"].get().strip(),
            "private": False,
        }
        try:
            rec["class"] = int(self._vars["class"].get()) if self._vars["class"].get() else 0
        except ValueError:
            rec["class"] = 0

        self.db.add_or_update(rec)
        if self.on_save: self.on_save(call)
        self.destroy()
