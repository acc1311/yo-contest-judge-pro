#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Fereastra Rezultate & Clasament
Afiseaza clasamentul final, scorul per statie, NIL-uri, busted calls.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import webbrowser

from core.reporter import export_html, export_csv, export_txt, export_json

# ── Culori ────────────────────────────────────────────────────
BG  = "#1e2a38"
BG2 = "#253447"
FG  = "#e8edf3"
ACC = "#2e75b6"
GRN = "#2ecc71"
RED = "#e74c3c"
YLW = "#f1c40f"
ORG = "#f39c12"
GRY = "#7f8c8d"
WHT = "#ffffff"

class ResultsWindow(tk.Toplevel):
    """
    Fereastra independenta cu rezultatele complete ale arbitrajului.
    Contine: clasament, detalii per statie, cross-check, export.
    """
    def __init__(self, parent, ranking, scores, validations,
                 cc_matrix=None, contest_name=""):
        super().__init__(parent)
        self.ranking      = ranking
        self.scores       = scores       # {call: score_result}
        self.validations  = validations  # {call: validation_result}
        self.cc_matrix    = cc_matrix or {}
        self.contest_name = contest_name

        self.title("Rezultate — {}".format(contest_name or "YO Contest Judge PRO"))
        self.configure(bg=BG)
        self.resizable(True, True)

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = min(1200, int(sw*0.92)), min(820, int(sh*0.88))
        self.geometry("{}x{}+{}+{}".format(w, h, (sw-w)//2, (sh-h)//2))

        self._apply_style()
        self._build()
        self._populate_ranking()

    def _apply_style(self):
        style = ttk.Style(self)
        style.configure("Treeview",
            background=BG2, foreground=FG, fieldbackground=BG2,
            font=("Consolas",10), rowheight=22)
        style.configure("Treeview.Heading",
            background="#2e3f55", foreground=ACC, font=("Arial",9,"bold"))
        style.map("Treeview", background=[("selected", ACC)])
        style.configure("R.TNotebook",     background=BG)
        style.configure("R.TNotebook.Tab", background="#2e3f55", foreground=FG,
                        padding=(12,5), font=("Arial",9,"bold"))
        style.map("R.TNotebook.Tab",
                  background=[("selected", ACC)],
                  foreground=[("selected", WHT)])

    def _build(self):
        # Top bar
        top = tk.Frame(self, bg=ACC, height=46)
        top.pack(fill=tk.X)
        tk.Label(top, text="REZULTATE CONCURS — {}".format(self.contest_name or ""),
                 font=("Arial",13,"bold"), bg=ACC, fg=WHT,
                 padx=16).pack(side=tk.LEFT, pady=8)
        tk.Label(top, text="{} statii clasificate".format(len(self.ranking)),
                 font=("Arial",9), bg=ACC, fg="#dce8f5").pack(side=tk.LEFT)

        # Butoane export
        bf = tk.Frame(top, bg=ACC)
        bf.pack(side=tk.RIGHT, padx=10)
        for lbl, fmt in [("HTML","html"),("CSV","csv"),("TXT","txt"),("JSON","json")]:
            tk.Button(bf, text=lbl,
                      command=lambda f=fmt: self._export(f),
                      bg="#1a3a5c", fg=WHT, font=("Arial",9,"bold"),
                      relief="flat", padx=8, pady=3).pack(side=tk.LEFT, padx=2, pady=6)

        # Notebook cu tab-uri
        self.nb = ttk.Notebook(self, style="R.TNotebook")
        self.nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # Tab 1: Clasament
        self.tab_rank = ttk.Frame(self.nb)
        self.nb.add(self.tab_rank, text="  Clasament  ")
        self._build_ranking_tab(self.tab_rank)

        # Tab 2: Detalii per statie
        self.tab_detail = ttk.Frame(self.nb)
        self.nb.add(self.tab_detail, text="  Detalii Statie  ")
        self._build_detail_tab(self.tab_detail)

        # Tab 3: Cross-Check
        self.tab_cc = ttk.Frame(self.nb)
        self.nb.add(self.tab_cc, text="  Cross-Check  ")
        self._build_cc_tab(self.tab_cc)

    # ── Tab Clasament ─────────────────────────────────────────
    def _build_ranking_tab(self, parent):
        cols = ("pos","call","total","valid","err","dup","nil","pts","mult","score")
        hdrs = ("#","Indicativ","Total QSO","Valide","Erori","Dup.","NIL","Pct QSO","Mult.","SCOR")
        wids = (40, 110, 75, 70, 60, 55, 55, 75, 60, 100)

        self.rank_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for col, hdr, w in zip(cols, hdrs, wids):
            self.rank_tree.heading(col, text=hdr)
            self.rank_tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(parent, orient="vertical",   command=self.rank_tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal",  command=self.rank_tree.xview)
        self.rank_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.rank_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        self.rank_tree.tag_configure("gold",   background="#3a3200", foreground=YLW)
        self.rank_tree.tag_configure("silver", background="#2a2a2a", foreground="#c0c0c0")
        self.rank_tree.tag_configure("bronze", background="#2a1a00", foreground="#cd7f32")
        self.rank_tree.bind("<<TreeviewSelect>>", self._on_rank_select)

    # ── Tab Detalii ───────────────────────────────────────────
    def _build_detail_tab(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(top, text="Statie:", bg=BG, fg=FG, font=("Arial",9)).pack(side=tk.LEFT)
        self.det_call_var = tk.StringVar()
        calls = list(self.scores.keys())
        self.det_cb = ttk.Combobox(top, textvariable=self.det_call_var,
                                    values=calls, state="readonly", width=14)
        self.det_cb.pack(side=tk.LEFT, padx=6)
        self.det_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_detail())
        if calls:
            self.det_cb.set(calls[0])

        # Sumar text
        self.det_summary = tk.Text(parent, height=6, bg=BG2, fg=FG,
                                    font=("Consolas",9), state="disabled",
                                    relief="flat", padx=8, pady=4)
        self.det_summary.pack(fill=tk.X, padx=6, pady=2)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=6, pady=2)

        # Treeview QSO-uri
        cols = ("#","Indicativ","Banda","Mod","Data","Ora","RST S","RST R","Schimb","Pct","Status")
        wids = (40, 100, 60, 55, 90, 60, 55, 55, 80, 50, 90)
        self.det_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for col, hdr, w in zip(cols, cols, wids):
            self.det_tree.heading(col, text=hdr)
            self.det_tree.column(col, width=w, anchor="center" if w<90 else "w")

        vsb = ttk.Scrollbar(parent, orient="vertical",  command=self.det_tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.det_tree.xview)
        self.det_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.det_tree.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        for tag, bg, fg in [("ok","#1b3a2a",GRN),("warning","#3a3000",YLW),
                              ("error","#3a1515",RED),("duplicate","#3a2500",ORG),
                              ("nil","#2a2a2a",GRY)]:
            self.det_tree.tag_configure(tag, background=bg, foreground=fg)

        if self.scores:
            self._refresh_detail()

    # ── Tab Cross-Check ───────────────────────────────────────
    def _build_cc_tab(self, parent):
        if not self.cc_matrix:
            tk.Label(parent, text="Cross-check nu a fost efectuat.",
                     bg=BG, fg=GRY, font=("Arial",11)).pack(pady=40)
            return

        top = tk.Frame(parent, bg=BG)
        top.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(top, text="Pereche:", bg=BG, fg=FG, font=("Arial",9)).pack(side=tk.LEFT)
        self.cc_pair_var = tk.StringVar()
        pairs = list(self.cc_matrix.keys())
        self.cc_pair_cb = ttk.Combobox(top, textvariable=self.cc_pair_var,
                                        values=pairs, state="readonly", width=30)
        self.cc_pair_cb.pack(side=tk.LEFT, padx=6)
        self.cc_pair_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_cc())
        if pairs:
            self.cc_pair_cb.set(pairs[0])

        self.cc_summary = tk.Text(parent, height=5, bg=BG2, fg=FG,
                                   font=("Consolas",9), state="disabled",
                                   relief="flat", padx=8, pady=4)
        self.cc_summary.pack(fill=tk.X, padx=6, pady=2)

        ttk.Separator(parent).pack(fill=tk.X, padx=6, pady=2)

        cols = ("#","Indicativ A","Banda","Data","Ora","Status","Detaliu")
        wids = (45, 100, 60, 90, 60, 120, 400)
        self.cc_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for col, hdr, w in zip(cols, cols, wids):
            self.cc_tree.heading(col, text=hdr)
            self.cc_tree.column(col, width=w, anchor="w" if w>80 else "center")

        vsb = ttk.Scrollbar(parent, orient="vertical",  command=self.cc_tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.cc_tree.xview)
        self.cc_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.cc_tree.pack(fill=tk.BOTH, expand=True, padx=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        for tag, bg, fg in [("confirmed","#1b3a2a",GRN),("nil","#3a1515",RED),
                              ("busted_call","#3a2000",ORG),("busted_band","#3a2000",ORG),
                              ("busted_time","#3a2800",YLW)]:
            self.cc_tree.tag_configure(tag, background=bg, foreground=fg)

        if pairs:
            self._refresh_cc()

    # ── Populare date ─────────────────────────────────────────
    def _populate_ranking(self):
        for item in self.rank_tree.get_children():
            self.rank_tree.delete(item)
        tag_map = {1:"gold", 2:"silver", 3:"bronze"}
        for r in self.ranking:
            tag = (tag_map.get(r["position"]),)
            self.rank_tree.insert("", "end", tags=tag, values=(
                "#{}".format(r["position"]),
                r["callsign"],
                r["total_qsos"],
                r["valid_qsos"],
                r["error_qsos"],
                r["dup_qsos"],
                r.get("nil_qsos",0),
                r["qso_points"],
                r["multipliers"],
                r["total_score"],
            ))

    def _on_rank_select(self, event=None):
        sel = self.rank_tree.selection()
        if not sel: return
        call = self.rank_tree.item(sel[0])["values"][1]
        if call in self.scores:
            self.det_call_var.set(call)
            self._refresh_detail()
            self.nb.select(self.tab_detail)

    def _refresh_detail(self):
        call = self.det_call_var.get()
        sr   = self.scores.get(call)
        vr   = self.validations.get(call, {})
        if not sr: return

        txt = (
            "=== {} | {} ===\n"
            "Total QSO: {}  Valide: {}  Erori: {}  Duplicate: {}  NIL: {}\n"
            "Puncte QSO: {}  x  Multiplicatori: {}  =>  SCOR FINAL: {}\n"
            "Per banda: {}"
        ).format(
            sr["callsign"], sr["contest_name"],
            sr["total_qsos"], sr["valid_qsos"],
            sr["error_qsos"], sr["duplicate_qsos"], sr.get("nil_qsos",0),
            sr["qso_points"], sr["multipliers"], sr["total_score"],
            "  ".join("{}:{}pct/{}qso".format(b,d["points"],d["qsos"])
                      for b, d in sorted(sr["per_band"].items()))
        )
        self.det_summary.configure(state="normal")
        self.det_summary.delete("1.0","end")
        self.det_summary.insert("end", txt)
        self.det_summary.configure(state="disabled")

        for item in self.det_tree.get_children():
            self.det_tree.delete(item)
        for b in sr.get("breakdown",[]):
            self.det_tree.insert("", "end", tags=(b["status"],), values=(
                b["idx"]+1, b["callsign"], b["band"], b["mode"],
                b["date"], b["time"], b["rst_s"], b["rst_r"],
                b["exchange"], b["points"], b["status"]
            ))

    def _refresh_cc(self):
        pair = self.cc_pair_var.get()
        cc   = self.cc_matrix.get(pair)
        if not cc: return
        st = cc.get("stats",{})
        txt = (
            "Pereche: {}  |  Toleranta: +/-{} min\n"
            "Total A: {}  |  Confirmate: {} ({}%)  |  NIL: {}  |  "
            "Busted Call: {}  |  Busted Band: {}  |  Busted Time: {}"
        ).format(
            pair, st.get("tolerance_min",3),
            st.get("total_a",0), st.get("confirmed",0), st.get("confirm_pct",0),
            st.get("nil",0), st.get("busted_call",0),
            st.get("busted_band",0), st.get("busted_time",0)
        )
        self.cc_summary.configure(state="normal")
        self.cc_summary.delete("1.0","end")
        self.cc_summary.insert("end", txt)
        self.cc_summary.configure(state="disabled")

        for item in self.cc_tree.get_children():
            self.cc_tree.delete(item)
        for idx_a, detail in sorted(cc.get("details",{}).items()):
            status = detail["status"]
            self.cc_tree.insert("", "end", tags=(status,), values=(
                idx_a+1,
                detail["callsign_a"],
                detail["band_a"],
                detail["date_a"],
                detail["time_a"],
                status.upper(),
                detail.get("issue",""),
            ))

    # ── Export ────────────────────────────────────────────────
    def _export(self, fmt):
        call = self.det_call_var.get() or (list(self.scores.keys())[0] if self.scores else None)
        if not call or call not in self.scores:
            messagebox.showwarning("Atentie", "Selectati o statie din tab-ul Detalii!", parent=self)
            return
        ext_map = {"html":".html","csv":".csv","txt":".txt","json":".json"}
        fp = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=ext_map.get(fmt,".txt"),
            initialfile="Rezultat_{}".format(call),
            filetypes=[(fmt.upper(), "*{}".format(ext_map.get(fmt,"")))])
        if not fp: return

        sr = self.scores[call]
        vr = self.validations.get(call,{})
        cc = None
        for k, v in self.cc_matrix.items():
            if k.startswith(call+"_"):
                cc = v; break

        try:
            if fmt == "html":
                export_html(sr, vr, fp, cc, self.ranking)
                if messagebox.askyesno("Export", "Deschideti raportul in browser?", parent=self):
                    webbrowser.open("file://{}".format(os.path.abspath(fp)))
            elif fmt == "csv":
                export_csv(sr, vr, fp)
            elif fmt == "txt":
                export_txt(sr, vr, fp)
            elif fmt == "json":
                export_json(sr, vr, fp)
        except Exception as e:
            messagebox.showerror("Eroare export", str(e), parent=self)
