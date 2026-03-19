#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Export PDF v2.2
Genereaza PDF din raportul HTML folosind ZERO dependente externe.
Metoda: HTML -> PDF prin weasyprint (daca e instalat) sau
        fallback la PDF text simplu scris cu bytes (no deps).
"""
import os
import datetime

_NOW = lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# ── Incearca weasyprint (optiona, nu e in stdlib) ─────────────
def _has_weasyprint():
    try:
        import weasyprint  # noqa
        return True
    except ImportError:
        return False

def _has_fpdf():
    try:
        import fpdf  # noqa
        return True
    except ImportError:
        return False

# ── PDF text simplu (fallback absolut, zero deps) ─────────────
def _make_text_pdf(lines, filepath):
    """
    Scrie un PDF minimal valid cu text ASCII/Latin-1.
    Fara librarii externe — genereaza structura PDF manual.
    Suporta caractere Latin-1 (diacritice romanesti incluse).
    """
    def _enc(s):
        return s.encode("latin-1", errors="replace").decode("latin-1")

    # Font Helvetica built-in PDF — fara embedding necesar
    page_width  = 595   # A4 points
    page_height = 842
    margin_l    = 40
    margin_r    = 40
    margin_t    = 50
    line_height = 13
    font_size_normal = 9
    font_size_title  = 13
    font_size_head   = 10

    # Imparte liniile in pagini
    usable_h = page_height - margin_t - 40
    lines_per_page = int(usable_h / line_height)

    pages_content = []
    current_page  = []
    for line in lines:
        current_page.append(line)
        if len(current_page) >= lines_per_page:
            pages_content.append(current_page)
            current_page = []
    if current_page:
        pages_content.append(current_page)

    objects  = []
    offsets  = []

    def add_obj(content):
        objects.append(content)
        return len(objects)  # 1-based

    # Obj 1 — catalog
    add_obj(None)
    # Obj 2 — pages dict
    add_obj(None)
    # Obj 3 — font
    add_obj(
        "3 0 obj\n<< /Type /Font /Subtype /Type1 "
        "/BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n"
    )
    # Obj 4 — bold font
    add_obj(
        "4 0 obj\n<< /Type /Font /Subtype /Type1 "
        "/BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n"
    )

    page_obj_ids = []
    stream_obj_ids = []

    base_obj = 5  # pagini incep de la obj 5

    for pi, page_lines in enumerate(pages_content):
        stream_parts = []
        stream_parts.append("BT")
        stream_parts.append("/F2 {} Tf".format(font_size_title))
        stream_parts.append("{} {} Td".format(margin_l, page_height - margin_t))

        for li, line in enumerate(page_lines):
            # Detecteaza tipul liniei
            if li == 0 and pi == 0:
                # Titlu principal
                stream_parts.append("/F2 {} Tf".format(font_size_title))
            elif line.startswith("===") or line.startswith("---"):
                stream_parts.append("/F1 {} Tf".format(font_size_normal))
            elif line.startswith("  ") and ":" in line:
                stream_parts.append("/F1 {} Tf".format(font_size_normal))
            else:
                stream_parts.append("/F1 {} Tf".format(font_size_normal))

            encoded = _enc(line).replace("\\","\\\\").replace("(","\\(").replace(")","\\)")
            stream_parts.append("0 -{} Td".format(line_height))
            stream_parts.append("({}) Tj".format(encoded))

        stream_parts.append("ET")
        stream_text = "\n".join(stream_parts)
        stream_bytes = stream_text.encode("latin-1", errors="replace")

        sid = base_obj + pi * 2
        pid = base_obj + pi * 2 + 1
        stream_obj_ids.append(sid)
        page_obj_ids.append(pid)

    # Genera PDF bytes
    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

    obj_pos = {}

    def write_obj(obj_id, content_bytes):
        obj_pos[obj_id] = len(out)
        out.extend("{} 0 obj\n".format(obj_id).encode())
        out.extend(content_bytes)
        out.extend(b"\nendobj\n")

    # Font objects (3 si 4)
    write_obj(3,
        b"<< /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )
    write_obj(4,
        b"<< /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    )

    # Stream + page objects
    for pi, page_lines in enumerate(pages_content):
        stream_parts = ["BT", "/F1 {} Tf".format(font_size_normal),
                        "{} {} Td".format(margin_l, page_height - margin_t)]
        first = True
        for line in page_lines:
            if first and pi == 0:
                stream_parts[-1] = "/F2 {} Tf".format(font_size_title)
                first = False
            else:
                stream_parts.append("/F1 {} Tf".format(font_size_normal))
                first = False
            encoded = _enc(line).replace("\\","\\\\").replace("(","\\(").replace(")","\\)")
            stream_parts.append("0 -{} Td".format(line_height))
            stream_parts.append("({}) Tj".format(encoded))
        stream_parts.append("ET")
        stream_text = "\n".join(stream_parts)
        stream_data = stream_text.encode("latin-1", errors="replace")

        sid = base_obj + pi * 2
        write_obj(sid,
            "<< /Length {} >>\nstream\n".format(len(stream_data)).encode()
            + stream_data + b"\nendstream"
        )

        pid = base_obj + pi * 2 + 1
        write_obj(pid,
            "<< /Type /Page /Parent 2 0 R "
            "/MediaBox [0 0 {} {}] "
            "/Contents {} 0 R "
            "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> >>".format(
                page_width, page_height, sid).encode()
        )

    # Pages dict
    kids = " ".join("{} 0 R".format(base_obj + i*2+1) for i in range(len(pages_content)))
    write_obj(2,
        "<< /Type /Pages /Kids [{}] /Count {} >>".format(
            kids, len(pages_content)).encode()
    )

    # Catalog
    write_obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")

    # XRef
    xref_pos = len(out)
    all_ids = sorted(obj_pos.keys())
    out.extend("xref\n0 {}\n".format(max(all_ids)+1).encode())
    out.extend(b"0000000000 65535 f \n")
    for oid in range(1, max(all_ids)+1):
        if oid in obj_pos:
            out.extend("{:010d} 00000 n \n".format(obj_pos[oid]).encode())
        else:
            out.extend(b"0000000000 65535 f \n")

    out.extend("trailer\n<< /Size {} /Root 1 0 R >>\n".format(max(all_ids)+1).encode())
    out.extend("startxref\n{}\n%%EOF\n".format(xref_pos).encode())

    with open(filepath, "wb") as f:
        f.write(bytes(out))
    return filepath

# ── Export principal ──────────────────────────────────────────
def export_pdf(score, validation, filepath, cc_result=None, ranking=None, method="auto"):
    """
    Exporta raportul de arbitraj in format PDF.
    method: 'auto' — incearca weasyprint, apoi fallback text PDF
            'text' — forteaza text PDF (zero dependente)
            'weasyprint' — forteaza weasyprint (trebuie instalat)
    """
    # Incearca weasyprint (cel mai bun output)
    if method in ("auto", "weasyprint") and _has_weasyprint():
        return _export_weasyprint(score, validation, filepath, cc_result, ranking)

    # Fallback: PDF text structurat (zero dependente)
    return _export_text_pdf(score, validation, filepath, cc_result, ranking)

def _export_weasyprint(score, validation, filepath, cc_result, ranking):
    from weasyprint import HTML as WP_HTML
    from core.reporter import export_html
    import tempfile
    # Genereaza HTML temp, converteste cu weasyprint
    tmp = filepath.replace(".pdf", "_tmp.html")
    export_html(score, validation, tmp, cc_result, ranking)
    WP_HTML(filename=tmp).write_pdf(filepath)
    try: os.remove(tmp)
    except Exception: pass
    return filepath

def _export_text_pdf(score, validation, filepath, cc_result, ranking):
    SEP = "=" * 70
    sep = "-" * 70
    lines = [
        "YO Contest Judge PRO v2.2 - RAPORT ARBITRAJ",
        SEP,
        "  Generat:         {}".format(_NOW()),
        "  Concurs:         {}".format(score.get("contest_name","")),
        "  Indicativ:       {}".format(score.get("callsign","")),
        sep,
        "  Total QSO:            {}".format(score.get("total_qsos",0)),
        "  QSO Valide:           {}".format(score.get("valid_qsos",0)),
        "  Erori:                {}".format(score.get("error_qsos",0)),
        "  Duplicate:            {}".format(score.get("duplicate_qsos",0)),
        "  Duplicate maraton/zi: {}".format(score.get("maraton_dup_qsos",0)),
        "  NIL (cross-check):    {}".format(score.get("nil_qsos",0)),
        "  Puncte QSO:           {}".format(score.get("qso_points",0)),
        "  Multiplicatori:       {}".format(score.get("multipliers",0)),
        "  SCOR FINAL:           {}".format(score.get("total_score",0)),
        SEP, "",
    ]

    # Per banda
    lines += ["PER BANDA:", sep,
              "  {:<8} {:>6} {:>8}".format("Banda","QSO","Puncte"), sep]
    for band, bd in sorted(score.get("per_band",{}).items()):
        lines.append("  {:<8} {:>6} {:>8}".format(band, bd["qsos"], bd["points"]))
    lines.append("")

    # Cross-check summary
    if cc_result:
        st = cc_result.get("stats",{})
        lines += ["CROSS-CHECK:", sep,
            "  Confirmate: {} ({}%)  |  NIL: {}  |  Toleranta: {} min".format(
                st.get("confirmed",0), st.get("confirm_pct",0),
                st.get("nil",0), st.get("tolerance_min",3)),
            "  Busted Call: {}  |  Busted Band: {}  |  Busted Time: {}".format(
                st.get("busted_call",0), st.get("busted_band",0), st.get("busted_time",0)),
            ""]

    # Clasament
    if ranking:
        lines += ["CLASAMENT:", sep,
                  "  {:<4} {:<14} {:>6} {:>6} {:>6} {:>6} {:>10}".format(
                      "#","Indicativ","Valide","Erori","NIL","Mult","SCOR"), sep]
        for r in ranking:
            lines.append("  {:<4} {:<14} {:>6} {:>6} {:>6} {:>6} {:>10}".format(
                "#{}".format(r["position"]), r["callsign"],
                r["valid_qsos"], r["error_qsos"],
                r["nil_qsos"], r["multipliers"], r["total_score"]))
        lines.append("")

    # Erori validare
    errs = validation.get("errors",[]) if validation else []
    if errs:
        lines += ["ERORI VALIDARE ({} total):".format(len(errs)), sep]
        for e in errs[:100]:  # max 100 in PDF
            d = e.to_dict() if hasattr(e,"to_dict") else e
            lines.append("  [{:7}] #{:4d} {:<12} {}".format(
                d["severity"], d["qso_idx"]+1, d["callsign"], d["message"]))
        if len(errs) > 100:
            lines.append("  ... si inca {} erori (vezi export HTML/CSV pentru lista completa)".format(
                len(errs)-100))
        lines.append("")

    # Log QSO-uri (primele 200)
    breakdown = score.get("breakdown",[])
    lines += ["LOG QSO-URI (primele {} din {}):".format(
        min(200, len(breakdown)), len(breakdown)), sep,
        "  {:<4} {:<12} {:<7} {:<5} {:<12} {:<6} {:<5} {:<5} {:<6} {:>5} {}".format(
            "#","Indicativ","Banda","Mod","Data","Ora","RST_S","RST_R","Schimb","Pct","Status"),
        sep]
    for b in breakdown[:200]:
        lines.append("  {:<4} {:<12} {:<7} {:<5} {:<12} {:<6} {:<5} {:<5} {:<6} {:>5} {}".format(
            b["idx"]+1, b["callsign"], b["band"], b["mode"],
            b["date"], b["time"], b["rst_s"], b["rst_r"],
            b["exchange"], b["points"], b["status"]))
    if len(breakdown) > 200:
        lines.append("  ... si inca {} QSO (vezi export HTML/CSV pentru lista completa)".format(
            len(breakdown)-200))

    lines += ["", SEP, "  YO Contest Judge PRO v2.2 - YO8ACR | yo8acr@gmail.com", SEP]
    return _make_text_pdf(lines, filepath)

def pdf_available():
    """Returneaza True daca exportul PDF este disponibil (intotdeauna True - zero deps)."""
    return True

def pdf_quality():
    """Returneaza calitatea PDF disponibila."""
    if _has_weasyprint():
        return "weasyprint (HTML complet)"
    return "text structurat (zero dependente)"
