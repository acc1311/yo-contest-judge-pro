#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Fereastra Statistici
Afiseaza statistici complete ale concursului cu grafice canvas.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
import os

BG  = "#1e2a38"; BG2 = "#253447"; BG3 = "#2e3f55"
FG  = "#e8edf3"; ACC = "#2e75b6"; ACC2= "#4a9de0"
GRN = "#2ecc71"; RED = "#e74c3c"; YLW = "#f1c40f"
ORG = "#f39c12"; WHT = "#ffffff"; GRY = "#7f8c8d"
FONT = ("Consolas", 10); FONT_B = ("Consolas", 10, "bold")

class StatisticsWindow(tk.Toplevel):
    def __init__(self, parent, stats):
        super().__init__(parent)
        self.stats = stats
        self.title("Statistici — {}".format(stats.get("contest_name","Concurs")))
        self.configure(bg=BG)
        self.resizable(True, True)
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w = min(1100, int(sw*.88)); h = min(800, int(sh*.85))
        self.geometry("{}x{}+{}+{}".format(w, h, (sw-w)//2, (sh-h)//2))
        self._apply_style()
        self._build()

    def _apply_style(self):
        st = ttk.Style(self)
        st.configure("S.TNotebook",     background=BG)
        st.configure("S.TNotebook.Tab", background=BG3, foreground=FG,
                     padding=(10,4), font=FONT_B)
        st.map("S.TNotebook.Tab",
               background=[("selected",ACC)], foreground=[("selected",WHT)])
        st.configure("Treeview", background=BG2, foreground=FG,
                     fieldbackground=BG2, font=FONT, rowheight=21)
        st.configure("Treeview.Heading", background=BG3, foreground=ACC2, font=FONT_B)
        st.map("Treeview", background=[("selected",ACC)])

    def _build(self):
        # Header
        top = tk.Frame(self, bg=ACC, height=44)
        top.pack(fill=tk.X)
        tk.Label(top, text="STATISTICI CONCURS — {}".format(
                     self.stats.get("contest_name","").upper()),
                 font=("Arial",12,"bold"), bg=ACC, fg=WHT, padx=14).pack(side=tk.LEFT, pady=8)
        tk.Label(top, text="Generat: {}".format(self.stats.get("generated_at","")),
                 font=("Arial",9), bg=ACC, fg="#dce8f5").pack(side=tk.LEFT)
        tk.Button(top, text="Export HTML", command=self._export_html,
                  bg=BG3, fg=WHT, font=FONT, relief="flat", padx=10
                  ).pack(side=tk.RIGHT, padx=8, pady=6)

        nb = ttk.Notebook(self, style="S.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        t1 = ttk.Frame(nb); nb.add(t1, text="  Sumar  ")
        t2 = ttk.Frame(nb); nb.add(t2, text="  Per Banda/Mod  ")
        t3 = ttk.Frame(nb); nb.add(t3, text="  Activitate Orara  ")
        t4 = ttk.Frame(nb); nb.add(t4, text="  Top Statii  ")
        t5 = ttk.Frame(nb); nb.add(t5, text="  Per Judet  ")

        self._build_summary(t1)
        self._build_band_mode(t2)
        self._build_hour(t3)
        self._build_top(t4)
        self._build_county(t5)

    # ── Tab Sumar ─────────────────────────────────────────────
    def _build_summary(self, p):
        s = self.stats
        cc = s.get("cc_summary",{})

        canvas = tk.Canvas(p, bg=BG, highlightthickness=0)
        vsb    = ttk.Scrollbar(p, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(canvas, bg=BG)
        win   = canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        # Carduri metrice
        cards = [
            ("Total QSO",        s.get("total_qso",0),     ACC),
            ("Indicative unice",  s.get("unique_calls",0),  GRN),
            ("Loguri procesate",  s.get("num_logs",0),      ORG),
            ("Rata NIL globala",  "{:.1f}%".format(s.get("nil_rate",0)), RED),
        ]
        cf = tk.Frame(inner, bg=BG); cf.pack(fill=tk.X, padx=10, pady=10)
        for lbl, val, col in cards:
            c = tk.Frame(cf, bg=BG2, relief="flat", bd=0)
            c.pack(side=tk.LEFT, padx=6, pady=4, ipadx=14, ipady=8)
            tk.Label(c, text=str(val), font=("Arial",22,"bold"),
                     bg=BG2, fg=col).pack()
            tk.Label(c, text=lbl, font=("Arial",9),
                     bg=BG2, fg=GRY).pack()

        # Cross-check sumar
        if cc:
            cf2 = tk.LabelFrame(inner, text="Cross-Check Global",
                                 bg=BG, fg=ACC2, font=FONT_B)
            cf2.pack(fill=tk.X, padx=10, pady=6)
            info = [
                ("QSO verificate",  cc.get("total",0)),
                ("Confirmate",       cc.get("confirmed",0)),
                ("Rata confirmare",  "{}%".format(cc.get("rate",0))),
                ("NIL",              cc.get("nil",0)),
            ]
            for i, (lbl, val) in enumerate(info):
                tk.Label(cf2, text="{}: {}".format(lbl, val),
                         bg=BG, fg=FG, font=FONT).grid(
                             row=0, column=i, padx=14, pady=6)

        # Tabel per log
        lf = tk.LabelFrame(inner, text="Detalii per log",
                            bg=BG, fg=ACC2, font=FONT_B)
        lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        cols = ("call","total","valid","err","dup","score","fmt")
        hdrs = ("Indicativ","Total QSO","Valide","Erori","Dup.","Scor","Format")
        wids = (100,75,70,65,55,80,65)
        tree = ttk.Treeview(lf, columns=cols, show="headings", height=10)
        for col, hdr, w in zip(cols, hdrs, wids):
            tree.heading(col, text=hdr)
            tree.column(col, width=w, anchor="center")
        vsb2 = ttk.Scrollbar(lf, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb2.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb2.pack(side=tk.RIGHT, fill=tk.Y)
        by_log = sorted(s.get("by_log",{}).items(),
                        key=lambda x: -x[1].get("score",0))
        for i, (call, d) in enumerate(by_log):
            tag = ("gold",) if i==0 else ("silver",) if i==1 else ("bronze",) if i==2 else ()
            tree.insert("","end", tags=tag, values=(
                call, d["total"], d["valid"], d["errors"], d["dup"], d["score"],
                d["format"].upper()))
        tree.tag_configure("gold",   background="#3a3200", foreground=YLW)
        tree.tag_configure("silver", background="#2a2a2a", foreground="#c0c0c0")
        tree.tag_configure("bronze", background="#2a1a00", foreground="#cd7f32")

    # ── Tab Banda/Mod ─────────────────────────────────────────
    def _build_band_mode(self, p):
        paned = tk.PanedWindow(p, orient=tk.HORIZONTAL, bg=BG, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)
        for title, data, color in [
            ("Per banda", self.stats.get("by_band",{}), ACC),
            ("Per mod",   self.stats.get("by_mode",{}), GRN),
        ]:
            frame = tk.Frame(paned, bg=BG); paned.add(frame)
            tk.Label(frame, text=title, bg=BG3, fg=ACC2,
                     font=FONT_B, padx=8, pady=4).pack(fill=tk.X)
            self._draw_bars(frame, data, color)

    def _draw_bars(self, parent, data, color, max_items=20):
        if not data:
            tk.Label(parent, text="Fara date", bg=BG, fg=GRY, font=FONT).pack(pady=20)
            return
        items = list(data.items())[:max_items]
        max_v = max(v for _,v in items) or 1
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        vsb    = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(fill=tk.BOTH, expand=True)

        W = 350; row_h = 26; pad_l = 80; pad_r = 60
        H = len(items) * row_h + 20
        canvas.configure(scrollregion=(0, 0, W, H))

        for i, (label, val) in enumerate(items):
            y = 10 + i * row_h
            bar_w = int((val / max_v) * (W - pad_l - pad_r))
            canvas.create_text(pad_l-6, y+10, text=label,
                               anchor="e", fill=FG, font=FONT)
            canvas.create_rectangle(pad_l, y+3, pad_l+bar_w, y+19,
                                    fill=color, outline="")
            canvas.create_text(pad_l+bar_w+4, y+10, text=str(val),
                               anchor="w", fill=FG, font=("Consolas",9))

    # ── Tab Activitate Orara ──────────────────────────────────
    def _build_hour(self, p):
        tk.Label(p, text="QSO-uri per ora (UTC)",
                 bg=BG3, fg=ACC2, font=FONT_B, padx=8, pady=4).pack(fill=tk.X)
        by_hour = self.stats.get("by_hour",{})
        if not by_hour:
            tk.Label(p, text="Fara date de timp", bg=BG, fg=GRY, font=FONT).pack(pady=30)
            return

        W = 800; H = 200; pad_l = 40; pad_b = 30; pad_t = 20
        max_v = max(by_hour.values()) if by_hour else 1
        bar_w = (W - pad_l - 20) // 24

        canvas = tk.Canvas(p, bg=BG, width=W, height=H+pad_b,
                           highlightthickness=0)
        canvas.pack(padx=20, pady=20)

        # Grid linii
        for i in range(5):
            y = pad_t + (H - pad_b) * i // 4
            v = int(max_v * (4-i) / 4)
            canvas.create_line(pad_l, y, W-10, y, fill=BG3, width=1)
            canvas.create_text(pad_l-4, y, text=str(v),
                               anchor="e", fill=GRY, font=("Consolas",8))

        # Bare
        for h in range(24):
            val   = by_hour.get(h, 0)
            bar_h = int(val / max_v * (H - pad_b - pad_t)) if max_v > 0 else 0
            x1    = pad_l + h * bar_w + 2
            x2    = x1 + bar_w - 4
            y1    = pad_t + (H - pad_b) - bar_h
            y2    = pad_t + (H - pad_b)
            fill  = ACC2 if val > 0 else BG2
            canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="")
            if h % 3 == 0:
                canvas.create_text(x1 + (bar_w-4)//2, H + pad_t - 2,
                                   text="{:02d}".format(h),
                                   fill=GRY, font=("Consolas",8))
            if val > 0 and bar_h > 14:
                canvas.create_text(x1 + (bar_w-4)//2, y1-1,
                                   text=str(val), anchor="s",
                                   fill=WHT, font=("Consolas",7))

        canvas.create_text(pad_l + 12*bar_w, H+pad_t+12,
                           text="Ora UTC", fill=GRY, font=("Consolas",9))

    # ── Tab Top Statii ────────────────────────────────────────
    def _build_top(self, p):
        tk.Label(p, text="Top statii contactate (din toate logurile)",
                 bg=BG3, fg=ACC2, font=FONT_B, padx=8, pady=4).pack(fill=tk.X)
        top = self.stats.get("top_active", [])
        cols = ("pos","call","count")
        tree = ttk.Treeview(p, columns=cols, show="headings")
        tree.heading("pos",   text="#")
        tree.heading("call",  text="Indicativ")
        tree.heading("count", text="Nr. QSO-uri")
        tree.column("pos",   width=50,  anchor="center")
        tree.column("call",  width=120, anchor="w")
        tree.column("count", width=100, anchor="center")
        vsb = ttk.Scrollbar(p, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.tag_configure("gold",   background="#3a3200", foreground=YLW)
        tree.tag_configure("silver", background="#2a2a2a", foreground="#c0c0c0")
        tree.tag_configure("bronze", background="#2a1a00", foreground="#cd7f32")
        for i, (call, cnt) in enumerate(top, 1):
            tag = ("gold",) if i==1 else ("silver",) if i==2 else ("bronze",) if i==3 else ()
            tree.insert("","end", tags=tag, values=(i, call, cnt))

    # ── Tab Per Judet ─────────────────────────────────────────
    def _build_county(self, p):
        tk.Label(p, text="Distributie schimburi (judete in QSO-uri)",
                 bg=BG3, fg=ACC2, font=FONT_B, padx=8, pady=4).pack(fill=tk.X)
        by_county = self.stats.get("by_county", {})
        cols = ("pos","code","count")
        tree = ttk.Treeview(p, columns=cols, show="headings")
        tree.heading("pos",   text="#")
        tree.heading("code",  text="Judet")
        tree.heading("count", text="QSO-uri")
        tree.column("pos",   width=50,  anchor="center")
        tree.column("code",  width=120, anchor="w")
        tree.column("count", width=100, anchor="center")
        vsb = ttk.Scrollbar(p, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        for i, (code, cnt) in enumerate(by_county.items(), 1):
            tree.insert("","end", values=(i, code, cnt))

    # ── Export ────────────────────────────────────────────────
    def _export_html(self):
        from core.statistics import stats_to_html
        fp = filedialog.asksaveasfilename(
            parent=self, defaultextension=".html",
            initialfile="Statistici_{}".format(
                self.stats.get("contest_name","concurs").replace(" ","_")),
            filetypes=[("HTML","*.html")])
        if not fp: return
        html = stats_to_html(self.stats)
        with open(fp,"w",encoding="utf-8") as f: f.write(html)
        if messagebox.askyesno("Export","Deschideti in browser?", parent=self):
            webbrowser.open("file://{}".format(os.path.abspath(fp)))
