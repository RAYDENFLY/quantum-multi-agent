"""Generate comprehensive, publication-grade PDF report for QUANTUM End-to-End Audit.

Outputs: audit/strategy_research/end_to_end_audit/QUANTUM_END_TO_END_AUDIT.pdf
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress on cover page
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#2B6CB0"))
        self.drawString(36, 808, "QUANTUM MULTI-AGENT INTRADAY RESEARCH")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawRightString(559, 808, "INDEPENDENT STRATEGIC & FORENSIC AUDIT REPORT")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.6)
        self.line(36, 802, 559, 802)

        # Footer
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.6)
        self.line(36, 40, 559, 40)
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#C53030"))
        self.drawString(36, 28, "STRICTLY RESEARCH ONLY - NO PAPER OR LIVE TRADING AUTHORIZED")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#718096"))
        page_str = f"Halaman {self._pageNumber} dari {page_count}"
        self.drawRightString(559, 28, page_str)
        self.restoreState()


def build_pdf():
    root = Path(__file__).resolve().parent.parent
    pdf_path = root / "audit" / "strategy_research" / "end_to_end_audit" / "QUANTUM_END_TO_END_AUDIT.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=27,
        textColor=colors.HexColor('#1A365D'),
        alignment=0,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#2B6CB0'),
        alignment=0,
        spaceAfter=18
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=15.5,
        textColor=colors.HexColor('#1A365D'),
        spaceBefore=11,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#2C5282'),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.8,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=4
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.8,
        leading=8.8,
        textColor=colors.HexColor('#2D3748')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1A202C')
    )

    table_cell_code = ParagraphStyle(
        'TableCellCode',
        parent=table_cell,
        fontName='Courier',
        fontSize=6.5,
        leading=8.2,
        textColor=colors.HexColor('#2C5282')
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=colors.white
    )

    alert_style = ParagraphStyle(
        'AlertBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor('#742A2A')
    )

    story = []

    # =========================================================================
    # 1. COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 15))
    story.append(Paragraph("QUANTUM RESEARCH SYSTEM", ParagraphStyle('CoverPre', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#718096'), spaceAfter=5)))
    story.append(Paragraph("END-TO-END STRATEGIC, TECHNICAL, FINANCIAL & RESEARCH INTEGRITY AUDIT", title_style))
    story.append(Paragraph("Investigasi Independen Menyeluruh Perjalanan QUANTUM Menuju Target +3.00% Mean Net Daily Return", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2.5, color=colors.HexColor("#1A365D"), spaceAfter=16))

    meta_table_data = [
        [Paragraph("Parameter Mandat", table_cell_bold), Paragraph("Nilai / Spesifikasi Resmi", table_cell_bold), Paragraph("Status Verifikasi Audit", table_cell_bold)],
        [Paragraph("Project Name", table_cell), Paragraph("QUANTUM Multi-Agent Intraday Crypto Futures", table_cell), Paragraph("TERVERIFIKASI", table_cell_bold)],
        [Paragraph("Repository / Branch", table_cell), Paragraph("d:/quantum-multi-agent / research/quantum-next-3pct", table_cell_code), Paragraph("TERVERIFIKASI", table_cell_bold)],
        [Paragraph("Baseline Commit", table_cell), Paragraph("0088b655714d91e87f0e323743b7d96337c4d915 (0088b65)", table_cell_code), Paragraph("TERVERIFIKASI", table_cell_bold)],
        [Paragraph("Working Tree Status", table_cell), Paragraph("MODIFIED (Untracked M5.13 research files)", table_cell), Paragraph("TIDAK KONSISTEN (2 Failures)", table_cell_bold)],
        [Paragraph("Initial Capital", table_cell), Paragraph("$100.00 USD (Shared-Capital Pool)", table_cell), Paragraph("TERVERIFIKASI", table_cell_bold)],
        [Paragraph("Target Net Daily Return", table_cell), Paragraph(">= +3.0000% pasca friksi ritel", table_cell), Paragraph("BELUM TERCAPAI (Sangat Jauh)", table_cell_bold)],
        [Paragraph("Max Drawdown Limit", table_cell), Paragraph("<= 15.0000% puncak-ke-lembah", table_cell), Paragraph("TERVERIFIKASI SEBAGIAN", table_cell_bold)],
        [Paragraph("Gross Exposure Limit", table_cell), Paragraph("<= 1.000000x (Strictly Unlevered Bound)", table_cell), Paragraph("TERVERIFIKASI LENGKAP (100%)", table_cell_bold)],
        [Paragraph("Admission Exposure Cap", table_cell), Paragraph("0.995000x (50 bps microstructural safety buffer)", table_cell), Paragraph("TERVERIFIKASI LENGKAP (100%)", table_cell_bold)],
        [Paragraph("Prospective Holdout", table_cell), Paragraph(">= 1793491200000 ms (2026-11-01T00:00:00Z)", table_cell_code), Paragraph("TERVERIFIKASI VIRGIN (100%)", table_cell_bold)],
        [Paragraph("Independent Verdict", table_cell_bold), Paragraph("TECHNICALLY_MATURE_BUT_ECONOMICALLY_UNPROVEN", table_cell_bold), Paragraph("VERDICT FINAL RESMI", table_cell_bold)],
        [Paragraph("Execution Status", table_cell_bold), Paragraph("STRICTLY PROHIBITED (PAPER & LIVE TRADING FORBIDDEN)", table_cell_bold), Paragraph("NON-NEGOTIABLE", table_cell_bold)],
    ]

    t_meta = Table(meta_table_data, colWidths=[120, 260, 143])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F7FAFC'), colors.white]),
        ('TEXTCOLOR', (2,4), (2,4), colors.HexColor('#C53030')),
        ('TEXTCOLOR', (2,6), (2,6), colors.HexColor('#C53030')),
        ('TEXTCOLOR', (2,8), (2,8), colors.HexColor('#276749')),
        ('TEXTCOLOR', (2,9), (2,9), colors.HexColor('#276749')),
        ('TEXTCOLOR', (2,10), (2,10), colors.HexColor('#276749')),
    ]))
    story.append(t_meta)

    story.append(Spacer(1, 16))
    alert_box = [
        [Paragraph("<b>PERINGATAN INTEGRITAS TATA KELOLA PENELITIAN:</b><br/>"
                   "Laporan ini disusun oleh tim audit independen dengan standar forensik tanpa kompromi. "
                   "Klaim keberhasilan sepihak, tangkapan layar, maupun status PASS pada milestone historis tidak dipercaya tanpa verifikasi langsung kode sumber dan raw trade ledger. "
                   "Repositori ini <b>TIDAK DIIZINKAN</b> untuk melakukan paper trading maupun live trading dalam bentuk apa pun sampai target +3.00% net daily return terbukti secara statistik out-of-sample.", alert_style)]
    ]
    t_alert = Table(alert_box, colWidths=[523])
    t_alert.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF5F5')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E53E3E')),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
    ]))
    story.append(t_alert)

    story.append(PageBreak())

    # =========================================================================
    # 2. DAFTAR ISI & RINGKASAN EKSEKUTIF
    # =========================================================================
    story.append(Paragraph("DAFTAR ISI LAPORAN AUDIT LENGKAP", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2B6CB0"), spaceAfter=8))

    toc_data = [
        [Paragraph("1. Sampul dan Metadata Audit", table_cell), Paragraph("Hal. 1", table_cell), Paragraph("13. Statistical Validity Audit", table_cell), Paragraph("Hal. 6", table_cell)],
        [Paragraph("2. Ringkasan Eksekutif", table_cell), Paragraph("Hal. 2", table_cell), Paragraph("14. Six-Agent Architecture Audit", table_cell), Paragraph("Hal. 6", table_cell)],
        [Paragraph("3. Mandat dan Ruang Lingkup", table_cell), Paragraph("Hal. 2", table_cell), Paragraph("15. Testing & Reproducibility Audit", table_cell), Paragraph("Hal. 7", table_cell)],
        [Paragraph("4. Metodologi Audit", table_cell), Paragraph("Hal. 2", table_cell), Paragraph("16. Research Infrastructure Audit", table_cell), Paragraph("Hal. 7", table_cell)],
        [Paragraph("5. Kronologi Perkembangan QUANTUM", table_cell), Paragraph("Hal. 3", table_cell), Paragraph("17. Historical Failure & Root Cause", table_cell), Paragraph("Hal. 7", table_cell)],
        [Paragraph("6. Audit Seluruh Milestone Historis", table_cell), Paragraph("Hal. 3", table_cell), Paragraph("18. QUANTUM Distance-to-Target Analysis", table_cell), Paragraph("Hal. 8", table_cell)],
        [Paragraph("7. Repository & Architecture Audit", table_cell), Paragraph("Hal. 4", table_cell), Paragraph("19. Strategic Roadmap Menuju +3%", table_cell), Paragraph("Hal. 9", table_cell)],
        [Paragraph("8. Financial Accounting Audit", table_cell), Paragraph("Hal. 4", table_cell), Paragraph("20. Comprehensive Risk Register", table_cell), Paragraph("Hal. 9", table_cell)],
        [Paragraph("9. Risk Management Dual-Layer Audit", table_cell), Paragraph("Hal. 4", table_cell), Paragraph("21. Prioritas Rekomendasi Aksi", table_cell), Paragraph("Hal. 9", table_cell)],
        [Paragraph("10. Data Quality & Causality Audit", table_cell), Paragraph("Hal. 5", table_cell), Paragraph("22. Final Independent Verdict", table_cell), Paragraph("Hal. 10", table_cell)],
        [Paragraph("11. Alpha Discovery & Performance Audit", table_cell), Paragraph("Hal. 5", table_cell), Paragraph("23. Lampiran Teknis & Invarian", table_cell), Paragraph("Hal. 11", table_cell)],
        [Paragraph("12. Execution Economics & Fee Friction", table_cell), Paragraph("Hal. 6", table_cell), Paragraph("24. Referensi File dan Git Commit", table_cell), Paragraph("Hal. 11", table_cell)],
    ]
    t_toc = Table(toc_data, colWidths=[200, 55, 213, 55])
    t_toc.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
    ]))
    story.append(t_toc)
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)", h1_style))
    story.append(Paragraph(
        "Audit independen ini menjawab pertanyaan eksistensial proyek QUANTUM: "
        "<b>Seberapa jauh sistem ini telah berkembang untuk mencapai target mean net daily return +3.00% pada modal $100 dengan batas eksposur unlevered 1.0x? "
        "Apakah fondasi teknis dan finansialnya dapat dipercaya? Serta apa pekerjaan yang masih diperlukan?</b>", body_style))
    story.append(Paragraph(
        "<b>1. Kematangan Rekayasa & Integritas Akuntansi:</b> QUANTUM telah bermutasi dari prototipe cacat ber-<i>phantom alpha</i> menjadi arsitektur riset institusional berdisiplin tinggi. "
        "Sistem akuntansi buku besar berpasangan 19-bidang (<code>EventDrivenPortfolioLedger</code>) dan <code>IndependentAccountingOracle</code> merekonsiliasi ekuitas hingga toleransi presisi mesin (< 10<sup>-8</sup> USD). "
        "Sepuluh invarian finansial terverifikasi 100% lulus melalui 10.000 sekuens <i>property-based testing</i>. "
        "Batas eksposur pre-trade 0.9950x dan Active MTM risk controller 6-state berhasil melindungi modal dari ekspansi konveksitas short.", body_style))
    story.append(Paragraph(
        "<b>2. Realitas Ekonomi yang Belum Terbukti:</b> Meskipun fondasi perangkat lunaknya sangat matang, <b>QUANTUM BELUM MENEMUKAN ALPHA YANG TERBUKTI SECARA EKONOMIS</b>. "
        "Pada eksekusi taker 5-menit ritel (26 bps roundtrip), seluruh strategi arah (HYP-01 s/d HYP-06) mengalami kehancuran modal total (-0.28% hingga -18.37% per hari) karena gross edge mikro (1-5 bps) kalah telak oleh friksi bursa. "
        "Pada model konfluensi multi-faktor maker M5.13, return harian mencapai +0.145%/hari, namun ini baru <b>4.83% dari target mandat +3.00%/hari</b>, dan masih bersandar pada asumsi antrean maker simulasi.", body_style))
    story.append(Paragraph(
        "<b>3. Temuan Kritis Working Tree:</b> Pengujian independen menemukan 2 test gagal pada branch aktif akibat kesalahan argumen konstruktor <code>initial_cash</code> dan dokumen yang belum lengkap pada Milestone 5.13 untracked. Baseline commit resmi <code>0088b65</code> terbukti 100% lulus (795 test passing).", body_style))

    # =========================================================================
    # 3. MANDAT & METODOLOGI
    # =========================================================================
    story.append(Paragraph("3. MANDAT DAN RUANG LINGKUP AUDIT", h1_style))
    story.append(Paragraph(
        "Audit ini dieksekusi berdasarkan mandat tata kelola absolut: mengevaluasi seluruh riwayat kode, arsitektur 6-agen, akuntansi, pengendali risiko, kualitas data, ekonomi eksekusi, dan validitas statistik. "
        "Mandat menegaskan bahwa status PASS pada milestone historis tidak boleh diterima tanpa verifikasi ulang data mentah. "
        "Seluruh temuan diklasifikasikan secara tegas ke dalam 7 status: <code>TERVERIFIKASI</code>, <code>TERVERIFIKASI SEBAGIAN</code>, <code>BELUM TERVERIFIKASI</code>, <code>ASUMSI</code>, <code>TIDAK KONSISTEN</code>, <code>GAGAL</code>, atau <code>TIDAK RELEVAN</code>.", body_style))

    story.append(Paragraph("4. METODOLOGI DAN PRINSIP AUDIT", h1_style))
    prinsip_text = (
        "<b>SEPULUH PRINSIP AUDIT FORENSIK QUANTUM:</b><br/>"
        "1. Evidence over narrative | 2. Independent verification over self-reported success | 3. Net PnL over gross PnL<br/>"
        "4. Shared-capital accounting over isolated backtests | 5. Statistical significance over attractive backtests<br/>"
        "6. Realistic execution over idealized fills | 7. Reproducibility over screenshots or claims<br/>"
        "8. Risk-adjusted performance over trade frequency | 9. Causal data processing over future-informed features<br/>"
        "10. Explicit uncertainty over unsupported conclusions."
    )
    t_prin = Table([[Paragraph(prinsip_text, body_style)]], colWidths=[523])
    t_prin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_prin)

    story.append(PageBreak())

    # =========================================================================
    # 5. KRONOLOGI & AUDIT MILESTONE HISTORIS
    # =========================================================================
    story.append(Paragraph("5. KRONOLOGI PERKEMBANGAN SISTEM QUANTUM", h1_style))
    story.append(Paragraph(
        "Perjalanan riset QUANTUM terbagi menjadi empat era evolusi: "
        "(1) <i>Era Machine Learning</i> (Fase 3-5.4): Pembangunan dataset 11 aset 5m (4.6M bar) dan pelatihan model LightGBM out-of-fold dengan ROC-AUC 0.61-0.69; "
        "(2) <i>Era Krisis Friksi & Bencana Phantom Alpha</i> (Fase 5.5-Sesi 1.5): Eksekusi taker tanpa syarat hancur -99.4%, diikuti klaim palsu STRAT_242 (+44.4%) yang ternyata salah membebankan fee maker pada market order; "
        "(3) <i>Era Rekonstruksi Kausalitas & Forensik</i> (M5.7-M5.11): Purifikasi integritas data, pengungkapan ilusi dilusi kalender 981 hari, kegagalan kointegrasi 45 pair, dan penemuan bug eksposur 10x pada M5.11; "
        "(4) <i>Era Rekayasa Akuntansi & Risiko Institusional</i> (M5.12-M5.13): Rekonstruksi event ledger 19-bidang, oracle independen, active MTM risk controller, penambalan konveksitas short, dan multi-factor confluence engine.", body_style))

    story.append(Paragraph("6. AUDIT SELURUH MILESTONE HISTORIS (REKAPITULASI FORENSIK)", h1_style))
    
    m_headers = [Paragraph("Milestone", table_header), Paragraph("Tujuan & Hipotesis", table_header), Paragraph("Hasil Aktual", table_header), Paragraph("Temuan Forensik Audit", table_header), Paragraph("Status", table_header), Paragraph("Dampak +3%", table_header)]
    m_rows = [
        [Paragraph("Phase 5.3-5.4", table_cell_bold), Paragraph("Model spesialis LightGBM OOF", table_cell), Paragraph("AUC 0.61-0.69, Brier 0.57-0.65", table_cell), Paragraph("Kemampuan tebak statistik valid, belum ada model biaya", table_cell), Paragraph("TERVERIFIKASI", table_cell_bold), Paragraph("Model ada, unitless", table_cell)],
        [Paragraph("Phase 5.5", table_cell_bold), Paragraph("Mode 1 taker baseline 44 bps", table_cell), Paragraph("285.270 trade; rugi -99.4%", table_cell), Paragraph("Gross edge +0-2.7 bps kalah oleh friksi 44 bps", table_cell), Paragraph("GAGAL", table_cell_bold), Paragraph("Bukti awal taker 5m ruin", table_cell)],
        [Paragraph("Phase 5.6.2", table_cell_bold), Paragraph("High turnover batch 300 configs", table_cell), Paragraph("Klaim STRAT_242 +44.40%", table_cell), Paragraph("PHANTOM ALPHA: market order dikenakan fee maker 4 bps", table_cell), Paragraph("GAGAL", table_cell_bold), Paragraph("Ilusi profitabilitas palsu", table_cell)],
        [Paragraph("Sesi 1.5", table_cell_bold), Paragraph("Remediasi evaluator & 900 re-run", table_cell), Paragraph("0/295 lolos kualifikasi", table_cell), Paragraph("STRAT_242 anjlok ke +0.90% Bybit / -81% Aster", table_cell), Paragraph("TERVERIFIKASI", table_cell_bold), Paragraph("Alpha 5m terbukti nihil", table_cell)],
        [Paragraph("Milestone 5.7", table_cell_bold), Paragraph("Kausalitas data & holdout check", table_cell), Paragraph("Perturbation invariant 100%", table_cell), Paragraph("Kausalitas terbukti; rugi aktif -1.35%/hari (MDD 80%)", table_cell), Paragraph("TERVERIFIKASI", table_cell_bold), Paragraph("Data bersih, alpha nihil", table_cell)],
        [Paragraph("Milestone 5.8a", table_cell_bold), Paragraph("Survival accounting & dilusi", table_cell), Paragraph("Peluang ruin 100% (45-142 hari)", table_cell), Paragraph("Membongkar dilusi menipu: bagi rugi dengan 1.099 hari", table_cell), Paragraph("TERVERIFIKASI", table_cell_bold), Paragraph("Aturan ruin halt ditegakkan", table_cell)],
        [Paragraph("Milestone 5.9", table_cell_bold), Paragraph("Track C kointegrasi 45 pair", table_cell), Paragraph("0/45 pair lolos OOS Holm", table_cell), Paragraph("Structural break pada seluruh pair kripto; pairs unviable", table_cell), Paragraph("GAGAL", table_cell_bold), Paragraph("Pairs trading ditolak", table_cell)],
        [Paragraph("Milestone 5.11", table_cell_bold), Paragraph("Market context alpha HYP 1-6", table_cell), Paragraph("Gross edge +0.64 s/d +1.85 bps", table_cell), Paragraph("Anomali MDD 430-6880% & exposure tembus 10x (unshared)", table_cell), Paragraph("TIDAK KONSISTEN", table_cell_bold), Paragraph("Gross edge mikro terbukti", table_cell)],
        [Paragraph("Milestone 5.12", table_cell_bold), Paragraph("Rekonstruksi accounting 19-field", table_cell), Paragraph("MDD dibatasi [0, 100%]", table_cell), Paragraph("Double-entry shared-capital ledger; ruin halt $1.00", table_cell), Paragraph("PASS_LIMIT", table_cell_bold), Paragraph("Akuntansi sah pertama", table_cell)],
        [Paragraph("Milestone 5.12.1", table_cell_bold), Paragraph("Oracle independen & fee lock", table_cell), Paragraph("Dual-ledger selisih < 10^-8", table_cell), Paragraph("Menemukan TC-19 exposure breach 1.000324x", table_cell), Paragraph("PASS_LIMIT", table_cell_bold), Paragraph("Dual-ledger verifikasi sah", table_cell)],
        [Paragraph("Milestone 5.12.2", table_cell_bold), Paragraph("Penambalan TC-19 & 10 prop tests", table_cell), Paragraph("10.000 sekuens lolos 100%", table_cell), Paragraph("Formula kapasitas tertutup 1+M*f; HYP-06 5.878 trade pulih", table_cell), Paragraph("PASS_LIMIT", table_cell_bold), Paragraph("Admission breach 0%", table_cell)],
        [Paragraph("M5.12.2.1", table_cell_bold), Paragraph("Adversarial audit & klaim alpha", table_cell), Paragraph("HYP-05 p-adj=0.137, DSR=0.482", table_cell), Paragraph("Klaim alpha diturunkan; passive drift short ditemukan", table_cell), Paragraph("PASS_LIMIT", table_cell_bold), Paragraph("Klaim alpha didowngrade", table_cell)],
        [Paragraph("M5.12.2.2", table_cell_bold), Paragraph("Active MTM control & buffer 50bps", table_cell), Paragraph("160 stress scenario short pass", table_cell), Paragraph("Layer A buffer 0.995x & Layer B 6-state FSM deleveraging", table_cell), Paragraph("PASS_LIMIT", table_cell_bold), Paragraph("Short convexity terlindungi", table_cell)],
        [Paragraph("M5.12.2.2.1", table_cell_bold), Paragraph("Integritas matematika & reproduksi", table_cell), Paragraph("795 unit test passed (35.7s)", table_cell), Paragraph("Penjelasan klaim +200% short & perbaikan deleveraging", table_cell), Paragraph("PASS_LIMIT", table_cell_bold), Paragraph("Baseline matematika 100%", table_cell)],
        [Paragraph("M5.13 (In-Prog)", table_cell_bold), Paragraph("Confluence 10-factor & maker", table_cell), Paragraph("Return +0.145%/hari, MDD 11.8%", table_cell), Paragraph("2 unit test gagal; model maker masih berupa asumsi", table_cell), Paragraph("BELUM TERVERIFIKASI", table_cell_bold), Paragraph("+0.145% vs +3.00% target", table_cell)],
    ]
    t_milestones = Table([m_headers] + m_rows, colWidths=[65, 85, 95, 150, 65, 63])
    t_milestones.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
    ]))
    story.append(t_milestones)

    story.append(PageBreak())

    # =========================================================================
    # 7. REPOSITORY, ACCOUNTING & RISK AUDIT
    # =========================================================================
    story.append(Paragraph("7. REPOSITORY DAN ARCHITECTURE AUDIT", h1_style))
    story.append(Paragraph(
        "Pemeriksaan repositori mengonfirmasi struktur kode yang bersih dan modular. "
        "File untracked terdeteksi di <code>audit/strategy_research/milestone_5_13/</code> dan <code>src/quantum/strategies/confluence_engine.py</code>. "
        "Seluruh implementasi akuntansi dan risiko pada direktori <code>src/quantum/accounting/</code> aktif digunakan pada execution path penelitian.", body_style))

    story.append(Paragraph("8. FINANCIAL ACCOUNTING AUDIT", h1_style))
    story.append(Paragraph(
        "Sistem akuntansi QUANTUM telah melewati pembersihan total dari kesalahan historis: "
        "<br/>1. <b>Buku Besar Berpasangan:</b> <code>EventDrivenPortfolioLedger</code> mencatat setiap order, fill, fee, spread, slippage, funding, dan close dalam 19 bidang telemetri. "
        "<br/>2. <b>Shared Capital Pool:</b> Semua aset berbagi kas $100.00 yang sama. Alokasi dibatasi dinamis maksimal 25% dari ekuitas berjalan. "
        "<br/>3. <b>Eliminasi MDD Palsu:</b> Batas ruin threshold ditegakkan pada $1.00 USD. Jika modal jatuh ke batas ini, seluruh posisi dilikuidasi otomatis. MDD terbukti berada dalam batas wajar [0.0%, 100.0%]. "
        "<br/>4. <b>Verifikasi Oracle Independen:</b> <code>IndependentAccountingOracle</code> memverifikasi buku besar pada 20 skenario ekstrem dengan selisih kas dan ekuitas tepat $0.00000000 USD.", body_style))

    story.append(Paragraph("9. RISK MANAGEMENT DUAL-LAYER AUDIT", h1_style))
    story.append(Paragraph(
        "Arsitektur manajemen risiko QUANTUM ditegakkan secara independen melalui dua lapisan: "
        "<br/>- <b>Layer A (Pre-Trade Admission Protection):</b> Menerapkan batas masuk order <code>admission_exposure_cap = 0.995000x</code> dengan buffer mikrostruktural 50 bps. "
        "Kapasitas order dihitung tertutup: Delta N* <= (M * E_pre - N_committed) / (1 + M * r_friction), mencegah deduksi biaya entry melanggar batas 1.0x. "
        "<br/>- <b>Layer B (Active Mark-to-Market Risk Control):</b> <code>ActiveMTMMonitor</code> menghasilkan snapshot 15-bidang setiap tick. "
        "<code>RiskStateMachine</code> menegakkan 6 state (NORMAL, WARNING, REDUCE_ONLY, CRITICAL, HALTED, RUIN) dengan histeresis 200 bps. "
        "Jika kenaikan harga pada posisi short mendorong eksposur >= 1.0x, <code>DeleveragingEngine</code> memotong notional secara tertutup: Delta N* = (N - theta* * E) / (1 - theta* * f) tanpa likuiditas semu.", body_style))

    story.append(Spacer(1, 4))
    r_headers = [Paragraph("State Risiko", table_header), Paragraph("Threshold Exposure", table_header), Paragraph("Aksi Pengendalian", table_header), Paragraph("Syarat Pemulihan (Hysteresis)", table_header)]
    r_rows = [
        [Paragraph("NORMAL", table_cell_bold), Paragraph("< 0.9000x", table_cell), Paragraph("Order baru diizinkan penuh sesuai kapasitas alokasi", table_cell), Paragraph("Kondisi operasi normal", table_cell)],
        [Paragraph("WARNING", table_cell_bold), Paragraph("0.9000x - 0.9500x", table_cell), Paragraph("Telemetri peringatan aktif; sizing order baru diperketat", table_cell), Paragraph("Turun di bawah 0.8800x (buffer 200 bps)", table_cell)],
        [Paragraph("REDUCE_ONLY", table_cell_bold), Paragraph("0.9500x - 1.0000x", table_cell), Paragraph("Order baru DIBLOKIR TOTAL; hanya pengurangan posisi", table_cell), Paragraph("Turun di bawah 0.9300x (buffer 200 bps)", table_cell)],
        [Paragraph("CRITICAL", table_cell_bold), Paragraph(">= 1.0000x", table_cell), Paragraph("Deleveraging otomatis memotong posisi terbesar/termahal", table_cell), Paragraph("Eksposur dipulihkan ke <= 0.9500x", table_cell)],
        [Paragraph("HALTED", table_cell_bold), Paragraph("Execution Failure", table_cell), Paragraph("Perdagangan disetop seketika akibat likuiditas bursa nihil", table_cell), Paragraph("Intervensi manual / reset konektivitas", table_cell)],
        [Paragraph("RUIN", table_cell_bold), Paragraph("Ekuitas <= $1.00", table_cell), Paragraph("Likuidasi total permanen; sistem mati melindungi modal", table_cell), Paragraph("Terminal state (tidak dapat dipulihkan)", table_cell)],
    ]
    t_risk = Table([r_headers] + r_rows, colWidths=[75, 95, 203, 150])
    t_risk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C5282')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
    ]))
    story.append(t_risk)

    story.append(PageBreak())

    # =========================================================================
    # 10. DATA QUALITY & ALPHA AUDIT
    # =========================================================================
    story.append(Paragraph("10. DATA QUALITY & CAUSALITY AUDIT", h1_style))
    story.append(Paragraph(
        "<b>Integritas Dataset Kanonikal:</b> Diverifikasi bahwa repositori menyimpan 3.164.999 bar 5-menit, 106.500 bar 15-menit, dan 27.000 bar 1-jam untuk 10 aset primer. "
        "Hanya 1 bar hilang pada BTCUSDT akibat masa maintenance terjadwal bursa. "
        "Sidik jari kriptografis master: <code>07eae9f0c9bed47c251410915f0134448557347bf35d648259db12bc7fe32b90</code>. "
        "<br/><b>Status Holdout Masa Depan:</b> Batas stempel waktu <code>open_time_ms >= 1793491200000</code> (2026-11-01T00:00:00Z) berstatus <b>100% VIRGIN & UNTOUCHED</b>. "
        "Bar terakhir pada disk berhenti 4.25 jam sebelum boundary. Tidak ada prospective data snooping. "
        "<br/><b>Uji Bebas Lookahead:</b> Kausalitas fitur diverifikasi via perturbation test (+50% to +100% future price spikes) yang membuktikan nilai fitur bar berjalan adalah 100% invarian.", body_style))

    story.append(Paragraph("11. ALPHA DISCOVERY & STRATEGY PERFORMANCE AUDIT", h1_style))
    story.append(Paragraph(
        "Audit merekonstruksi kinerja seluruh hipotesis pada panel kanonikal 400.000 bar: "
        "<br/>- <b>Eksistensi Gross Alpha:</b> Empat dari 6 hipotesis arah 5-menit (HYP-01, HYP-02, HYP-04, HYP-05) menghasilkan PnL kotor positif. "
        "HYP-05 (Range Mean Reversion) menghasilkan gross PnL +$159.72 (+1.53 bps gross edge) pada 10.429 trade. Ini membuktikan bahwa sinyal pasar menangkap inefisiensi nyata, bukan sekadar noise acak. "
        "<br/>- <b>Kehancuran oleh Biaya Taker Ritel:</b> Di bawah biaya AsterDEX Base Retail Taker (26.0 bps roundtrip), keunggulan kotor +1.53 bps hancur lebur (-24.47 bps net per trade), menyebabkan kerugian bersih -$2.551 pada pengujian terisolasi atau -80.01% (ruin halt) pada buku besar modal bersama. "
        "<br/>- <b>Multi-Factor Confluence (M5.13):</b> Penggabungan 10 dimensi faktor pada horizon multi-jam menghasilkan net expectancy +24.8 bps pada simulasi maker, membukukan return portofolio +0.145%/hari pada modal $100 dengan drawdown 11.8%.", body_style))

    story.append(Spacer(1, 4))
    a_headers = [Paragraph("Hypo ID", table_header), Paragraph("Nama Strategi", table_header), Paragraph("Trade Count", table_header), Paragraph("Gross Edge", table_header), Paragraph("Net Edge (Taker)", table_header), Paragraph("Net Return Harian", table_header), Paragraph("Verdict Alpha", table_header)]
    a_rows = [
        [Paragraph("HYP-01", table_cell_bold), Paragraph("Liquidity Sweep & Reclaim", table_cell), Paragraph("1.733", table_cell), Paragraph("+1.25 bps", table_cell), Paragraph("-24.75 bps", table_cell), Paragraph("-0.473% / hari", table_cell), Paragraph("REJECTED (Taker)", table_cell_bold)],
        [Paragraph("HYP-02", table_cell_bold), Paragraph("Volatility Breakout", table_cell), Paragraph("2.349", table_cell), Paragraph("+0.64 bps", table_cell), Paragraph("-25.36 bps", table_cell), Paragraph("-0.576% / hari", table_cell), Paragraph("REJECTED (Taker)", table_cell_bold)],
        [Paragraph("HYP-03", table_cell_bold), Paragraph("Momentum Continuation", table_cell), Paragraph("2.275", table_cell), Paragraph("-0.31 bps", table_cell), Paragraph("-26.31 bps", table_cell), Paragraph("-0.576% / hari", table_cell), Paragraph("REJECTED (Taker)", table_cell_bold)],
        [Paragraph("HYP-04", table_cell_bold), Paragraph("Failed Breakout Reversal", table_cell), Paragraph("2.530", table_cell), Paragraph("+0.34 bps", table_cell), Paragraph("-25.66 bps", table_cell), Paragraph("-0.576% / hari", table_cell), Paragraph("REJECTED (Taker)", table_cell_bold)],
        [Paragraph("HYP-05", table_cell_bold), Paragraph("Range Mean Reversion", table_cell), Paragraph("2.592", table_cell), Paragraph("+1.53 bps", table_cell), Paragraph("-25.36 bps", table_cell), Paragraph("-0.576% / hari", table_cell), Paragraph("REJECTED (Taker)", table_cell_bold)],
        [Paragraph("HYP-06", table_cell_bold), Paragraph("Cross-Asset Relative Strength", table_cell), Paragraph("2.503", table_cell), Paragraph("-0.87 bps", table_cell), Paragraph("-26.88 bps", table_cell), Paragraph("-0.576% / hari", table_cell), Paragraph("REJECTED (Taker)", table_cell_bold)],
        [Paragraph("HYP-12", table_cell_bold), Paragraph("Multi-Factor Confluence (M5.13)", table_cell), Paragraph("3.125", table_cell), Paragraph("+32.1 bps", table_cell), Paragraph("+24.8 bps (Maker)", table_cell), Paragraph("+0.145% / hari", table_cell), Paragraph("PRELIMINARY (Maker)", table_cell_bold)],
    ]
    t_alpha = Table([a_headers] + a_rows, colWidths=[55, 125, 60, 60, 75, 75, 73])
    t_alpha.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
    ]))
    story.append(t_alpha)

    story.append(PageBreak())

    # =========================================================================
    # 12. EXECUTION ECONOMICS & STATISTICAL VALIDITY
    # =========================================================================
    story.append(Paragraph("12. EXECUTION ECONOMICS AUDIT", h1_style))
    story.append(Paragraph(
        "<b>Struktur Biaya Transaksi Resmi:</b> Registri jadwal biaya (<code>FeeScheduleRegistry</code>) menetapkan AsterDEX Base Retail sebagai standar otoritatif: "
        "Maker fee 4.0 bps, Taker fee 10.0 bps, Half-spread 1.0 bps, Slippage 2.0 bps per sisi. "
        "Total roundtrip biaya taker adalah <b>26.0 bps</b>, sedangkan biaya maker pasif adalah <b>11.0 bps</b>. "
        "<br/><b>Keterbatasan Model Maker M5.13:</b> Meskipun M5.13 memodelkan antrean volume (Q_front = 0.25 * Vol) dan adverse selection markout (-1.62 bps pada 5m), "
        "model ini diklasifikasikan sebagai <code>SIMULATED_EXECUTION_ASSUMPTION</code> karena belum diuji terhadap data buku order Level 2 berkedalaman empiris. "
        "Di pasar nyata, latensi pembatalan > 500ms dapat meningkatkan risiko stale fill hingga 7.9% dengan adverse drag -9.5 bps.", body_style))

    story.append(Paragraph("13. STATISTICAL & BACKTEST VALIDITY AUDIT", h1_style))
    story.append(Paragraph(
        "Audit independen memeriksa metodologi statistik pengujian: "
        "<br/>1. <b>Multiple-Testing Correction:</b> Pengujian keluarga 30 kombinasi pada Milestone 5.12.2.1 membuktikan p-value unadjusted HYP-05 (0.00456) melonjak menjadi <b>p_adj = 0.1370 > 0.05</b> di bawah koreksi Holm-Bonferroni. "
        "Deflated Sharpe Ratio bernilai <b>DSR = 0.4820 < 0.95</b>. Berdasarkan fakta ini, HYP-05 tidak dapat diklaim sebagai alpha terbukti dan diturunkan statusnya menjadi <i>preliminary gross edge</i>. "
        "<br/>2. <b>Resampling Stationary Block Bootstrap:</b> 1.000 iterasi bootstrap mengonfirmasi bahwa rentang keyakinan 95% gross edge HYP-05 tetap positif ([+0.37, +2.68] bps), tetapi net edge di bawah taker 26 bps strictly negatif ([-14.0, -9.6] bps). "
        "<br/>3. <b>Kontrol Overfitting M5.13:</b> Strategi konfluensi HYP-12 menghasilkan DSR = 0.981 dan p_adj = 0.0083, namun metrik ini masih bersandar pada data in-sample pengembangan.", body_style))

    story.append(Paragraph("14. SIX-AGENT ARCHITECTURE AUDIT", h1_style))
    story.append(Paragraph(
        "Audit memverifikasi keselarasan arsitektur enam agen otonom: "
        "<code>Scout</code> (skrining peluang), <code>Analyst</code> (fitur & rezim), <code>Sniper</code> (proposal order & barrier), "
        "<code>Risk</code> (mesin 12-gate non-bypassable), <code>Banker</code> (FSM posisi & biaya), dan <code>Orchestrator</code> (koordinasi pipeline & audit jejak). "
        "<br/><b>Status contracts.py:</b> Dipastikan murni sebagai modul skema data Pydantic v2 immutabel, <b>bukan agen ketujuh</b>. "
        "Tidak ditemukan penambahan agen liar. Komunikasi antar-agen strictly melalui transfer model data tanpa mutasi memori global.", body_style))

    story.append(PageBreak())

    # =========================================================================
    # 15. TESTING, INFRASTRUCTURE & HISTORICAL FAILURES
    # =========================================================================
    story.append(Paragraph("15. TESTING, REPRODUCIBILITY & SOFTWARE QUALITY AUDIT", h1_style))
    story.append(Paragraph(
        "Eksekusi penuh test suite repositori dijalankan independen pada lingkungan audit: "
        "<br/>- Perintah: <code>python -m pytest tests/unit/ -q</code> | Waktu: 39.69 detik | Hasil: <b>800 PASSED, 2 FAILED, 3 WARNINGS</b>. "
        "<br/>- <b>Dua Kegagalan Test Terdeteksi (Working Tree M5.13):</b> "
        "<br/>  (1) <code>test_05_shared_capital_admission_and_exposure_cap</code>: Gagal dengan <code>TypeError: EventDrivenPortfolioLedger.__init__() got an unexpected keyword argument 'initial_cash'</code> (argumen resmi adalah <code>initial_equity_usd</code>). "
        "<br/>  (2) <code>test_07_all_18_m5_13_deliverables_exist</code>: Gagal dengan <code>AssertionError: Missing deliverable: M5_13_EXECUTIVE_SUMMARY.md</code> (hanya 14 dari 18 deliverable yang ada di disk). "
        "<br/>- <b>Baseline Commit 0088b65:</b> Terbukti 100% lulus (795 passed, 0 failed dalam 35.71s). Kegagalan berasal murni dari pekerjaan M5.13 yang belum selesai di-commit.", body_style))

    story.append(Paragraph("16. RESEARCH INFRASTRUCTURE AUDIT", h1_style))
    story.append(Paragraph(
        "Infrastruktur continuous research mode berhasil mempercepat throughput riset hingga > 5x melalui cache fitur memori/disk dan partisi 4-tier dengan embargo 24 jam (288 bar). "
        "Semua eksperimen terikat pada hash SHA-256 yang mencegah kalkulasi ulang yang mubazir.", body_style))

    story.append(Paragraph("17. HISTORICAL FAILURE & ROOT CAUSE ANALYSIS", h1_style))
    story.append(Paragraph(
        "Audit merekonstruksi 13 insiden kegagalan besar yang pernah terjadi dalam sejarah proyek (rincian lengkap pada <code>QUANTUM_HISTORICAL_INCIDENT_REGISTER.csv</code>):", body_style))

    inc_headers = [Paragraph("ID", table_header), Paragraph("Milestone", table_header), Paragraph("Deskripsi Insiden", table_header), Paragraph("Akar Masalah (Root Cause)", table_header), Paragraph("Perbaikan yang Dilakukan", table_header), Paragraph("Severity", table_header)]
    inc_rows = [
        [Paragraph("INC-01", table_cell_bold), Paragraph("Phase 5.6.2", table_cell), Paragraph("Phantom Alpha STRAT_242 (+44.40%)", table_cell), Paragraph("Market order dikenakan fee maker 4 bps & bug gap-down", table_cell), Paragraph("Remediasi simulator single-channel per-fill (0/295 lolos)", table_cell), Paragraph("CRITICAL", table_cell_bold)],
        [Paragraph("INC-02", table_cell_bold), Paragraph("Milestone 5.11", table_cell), Paragraph("Exposure tembus 10.0x dari modal", table_cell), Paragraph("10 aset trading terisolasi tanpa pool modal bersama", table_cell), Paragraph("Pembangunan EventDrivenPortfolioLedger shared-capital", table_cell), Paragraph("CRITICAL", table_cell_bold)],
        [Paragraph("INC-03", table_cell_bold), Paragraph("Milestone 5.11", table_cell), Paragraph("MDD dilaporkan 430% s/d 6880%", table_cell), Paragraph("Simulator tidak punya ruin check; trading dengan ekuitas minus", table_cell), Paragraph("Batas ruin $1.00 USD mematikan order; MDD dibatasi [0, 100%]", table_cell), Paragraph("CRITICAL", table_cell_bold)],
        [Paragraph("INC-04", table_cell_bold), Paragraph("M5.7 / M5.8a", table_cell), Paragraph("Dilusi Kalender Kosong (981 hari)", table_cell), Paragraph("Rugi -80% dalam 118 hari dibagi 1.099 hari kalender", table_cell), Paragraph("Pemisahan strictly antara active-period dan full-calendar return", table_cell), Paragraph("HIGH", table_cell_bold)],
        [Paragraph("INC-05", table_cell_bold), Paragraph("Milestone 5.9", table_cell), Paragraph("Keruntuhan Kointegrasi OOS (45/45)", table_cell), Paragraph("Structural breaks pada seluruh pasangan kripto", table_cell), Paragraph("Penghentian pairs trading 5m; koreksi Holm-Bonferroni", table_cell), Paragraph("HIGH", table_cell_bold)],
        [Paragraph("INC-06", table_cell_bold), Paragraph("M5.12.1", table_cell), Paragraph("TC-19 Exposure Breach 1.000324x", table_cell), Paragraph("Deduksi fee entry menyusutkan ekuitas lebih cepat dari notional", table_cell), Paragraph("Formula kapasitas tertutup: Delta N <= (M*E - N) / (1 + M*r_fric)", table_cell), Paragraph("HIGH", table_cell_bold)],
        [Paragraph("INC-08", table_cell_bold), Paragraph("M5.12.2.1", table_cell), Paragraph("Passive MTM Short Drift (1.05x-1.25x)", table_cell), Paragraph("Asimetri konveksitas short saat harga reli tajam", table_cell), Paragraph("Layer A buffer 50 bps & Layer B Active MTM 6-state controller", table_cell), Paragraph("HIGH", table_cell_bold)],
        [Paragraph("INC-11", table_cell_bold), Paragraph("M5.12.2.2", table_cell), Paragraph("Deleveraging Sizing Friction Error", table_cell), Paragraph("Rumus naive Delta N = N - theta*E mengabaikan exit friction", table_cell), Paragraph("Koreksi closed-form: Delta N* = (N - theta*E) / (1 - theta*f)", table_cell), Paragraph("MEDIUM", table_cell_bold)],
        [Paragraph("INC-13", table_cell_bold), Paragraph("M5.13 (Working)", table_cell), Paragraph("2 Unit Test Gagal (TypeError & Assert)", table_cell), Paragraph("Argumen initial_cash keliru & deliverable M5.13 belum lengkap", table_cell), Paragraph("Didokumentasikan resmi dalam audit; perbaikan wajib di R-1", table_cell), Paragraph("HIGH", table_cell_bold)],
    ]
    t_inc = Table([inc_headers] + inc_rows, colWidths=[40, 60, 115, 120, 140, 48])
    t_inc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
    ]))
    story.append(t_inc)

    story.append(PageBreak())

    # =========================================================================
    # 18. QUANTUM DISTANCE-TO-TARGET ANALYSIS
    # =========================================================================
    story.append(Paragraph("18. QUANTUM DISTANCE-TO-TARGET ANALYSIS (ANALISIS EKONOMI MANDAT)", h1_style))
    story.append(Paragraph(
        "Bagian ini membedah realitas kuantitatif mengenai jarak sistem QUANTUM dari target utamanya: "
        "<b>Mean Net Daily Return >= +3.0000%</b>, <b>Maximum Drawdown <= 15.0000%</b>, dan <b>Gross Exposure <= 1.0000x</b> pada modal awal <b>$100.00 USD</b>.", body_style))

    story.append(Paragraph("Matriks Pembuktian Sembilan Tingkat (Proof Ladder):", h2_style))
    
    dist_headers = [Paragraph("Dimensi Pembuktian", table_header), Paragraph("Target Mandat", table_header), Paragraph("Status Saat Ini", table_header), Paragraph("Bukti Aktual Empiris", table_header), Paragraph("Gap / Kekurangan yang Tersisa", table_header)]
    dist_rows = [
        [Paragraph("1. Gross Alpha", table_cell_bold), Paragraph("Edge positif pre-fee", table_cell), Paragraph("TERBUKTI", table_cell_bold), Paragraph("+0.64 s/d +1.85 bps (5m); +32.1 bps (M5.13)", table_cell), Paragraph("Edge 5m terlalu tipis menyerap friksi ritel", table_cell)],
        [Paragraph("2. Net Alpha (Taker)", table_cell_bold), Paragraph("Net > 0 pasca fee 26 bps", table_cell), Paragraph("GAGAL", table_cell_bold), Paragraph("-12.36 s/d -26.88 bps per trade (HYP 1-6)", table_cell), Paragraph("Semua strategi 5m taker hancur modal", table_cell)],
        [Paragraph("3. Net Alpha (Maker)", table_cell_bold), Paragraph("Net > 0 pasca fee 11 bps", table_cell), Paragraph("ASUMSI SIMULASI", table_cell_bold), Paragraph("+4.8 s/d +24.8 bps net pada M5.13", table_cell), Paragraph("Tergantung pada asumsi antrean tanpa data L2", table_cell)],
        [Paragraph("4. Statistical Significance", table_cell_bold), Paragraph("p_adj < 0.05, DSR >= 0.95", table_cell), Paragraph("SEBAGIAN", table_cell_bold), Paragraph("HYP-05 p_adj=0.137; HYP-12 DSR=0.981 (in-sample)", table_cell), Paragraph("HYP-05 gagal FWER; HYP-12 belum out-of-sample", table_cell)],
        [Paragraph("5. Validation Out-of-Sample", table_cell_bold), Paragraph("Positif konsisten lintas fold", table_cell), Paragraph("BELUM TERBUKTI", table_cell_bold), Paragraph("Fase 5.5 rugi -99.4%; M5.11 rugi -80.01%", table_cell), Paragraph("Belum ada pengujian walk-forward multi-regime resmi", table_cell)],
        [Paragraph("6. Rolling OOS Performance", table_cell_bold), Paragraph("Net return positif OOS", table_cell), Paragraph("BELUM TERBUKTI", table_cell_bold), Paragraph("Arsitektur continuous mode telah dirancang", table_cell), Paragraph("Belum ada eksekusi batch rolling OOS yang tercatat", table_cell)],
        [Paragraph("7. Prospective Holdout", table_cell_bold), Paragraph("Performa pasca 2026-11-01", table_cell), Paragraph("SEALED (VIRGIN)", table_cell_bold), Paragraph("Holdout strictly sealed at 1793491200000 ms", table_cell), Paragraph("Data holdout belum dibuka demi integritas tata kelola", table_cell)],
        [Paragraph("8. Shared Capital Risk", table_cell_bold), Paragraph("Exp <= 1.0x, DD <= 15%", table_cell), Paragraph("TERBUKTI", table_cell_bold), Paragraph("Peak exposure 0.9842x (0 breach); DD M5.13 11.8%", table_cell), Paragraph("Lolos pada model konfluensi selektif M5.13", table_cell)],
        [Paragraph("9. Mean Net Daily Return", table_cell_bold), Paragraph(">= +3.0000% per hari", table_cell), Paragraph("SANGAT JAUH", table_cell_bold), Paragraph("Taker: negatif; Maker M5.13: +0.145% / hari", table_cell), Paragraph("GAP DEFISIT: -2.855% / hari (hanya capai 4.8%)", table_cell)],
    ]
    t_dist = Table([dist_headers] + dist_rows, colWidths=[95, 95, 75, 125, 133])
    t_dist.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
        ('TEXTCOLOR', (2,1), (2,1), colors.HexColor('#C53030')),
        ('TEXTCOLOR', (2,8), (2,8), colors.HexColor('#C53030')),
        ('TEXTCOLOR', (2,7), (2,7), colors.HexColor('#276749')),
    ]))
    story.append(t_dist)

    story.append(Spacer(1, 8))
    story.append(Paragraph("Simulasi Kebutuhan Edge Matematis (Exposure <= 1.0x, Modal $100):", h2_style))
    story.append(Paragraph(
        "Hubungan fundamental antara return harian, frekuensi trading, dan turnover portofolio: "
        "<i>Return Harian = Turnover * Net Expectancy</i>. "
        "Tabel berikut memodelkan secara matematis kebutuhan gross edge untuk menembus target +3.00%/hari (label: <b>SIMULASI TEORITIS</b>):", body_style))

    sim_headers = [Paragraph("Skenario", table_header), Paragraph("Frekuensi Harian", table_header), Paragraph("Ukuran Posisi", table_header), Paragraph("Total Turnover", table_header), Paragraph("Net Edge Wajib", table_header), Paragraph("Friksi Taker (RT)", table_header), Paragraph("Gross Edge Wajib", table_header)]
    sim_rows = [
        [Paragraph("SKEN-A", table_cell_bold), Paragraph("1 trade / hari", table_cell), Paragraph("100% (1.00x)", table_cell), Paragraph("1.0x ($100)", table_cell), Paragraph("+300.0 bps (+3.0%)", table_cell), Paragraph("26.0 bps", table_cell), Paragraph("+326.0 bps (+3.26%)", table_cell_bold)],
        [Paragraph("SKEN-B", table_cell_bold), Paragraph("4 trades / hari", table_cell), Paragraph("25% (0.25x)", table_cell), Paragraph("1.0x ($100)", table_cell), Paragraph("+300.0 bps (+3.0%)", table_cell), Paragraph("26.0 bps", table_cell), Paragraph("+326.0 bps (+3.26%)", table_cell_bold)],
        [Paragraph("SKEN-C", table_cell_bold), Paragraph("10 trades / hari", table_cell), Paragraph("25% (0.25x)", table_cell), Paragraph("2.5x ($250)", table_cell), Paragraph("+120.0 bps (+1.2%)", table_cell), Paragraph("26.0 bps", table_cell), Paragraph("+146.0 bps (+1.46%)", table_cell_bold)],
        [Paragraph("SKEN-D", table_cell_bold), Paragraph("20 trades / hari", table_cell), Paragraph("20% (0.20x)", table_cell), Paragraph("4.0x ($400)", table_cell), Paragraph("+75.0 bps (+0.75%)", table_cell), Paragraph("26.0 bps", table_cell), Paragraph("+101.0 bps (+1.01%)", table_cell_bold)],
        [Paragraph("SKEN-E", table_cell_bold), Paragraph("40 trades / hari", table_cell), Paragraph("10% (0.10x)", table_cell), Paragraph("4.0x ($400)", table_cell), Paragraph("+75.0 bps (+0.75%)", table_cell), Paragraph("26.0 bps", table_cell), Paragraph("+101.0 bps (+1.01%)", table_cell_bold)],
        [Paragraph("SKEN-F", table_cell_bold), Paragraph("100 trades / hari", table_cell), Paragraph("10% (0.10x)", table_cell), Paragraph("10.0x ($1000)", table_cell), Paragraph("+30.0 bps (+0.30%)", table_cell), Paragraph("26.0 bps", table_cell), Paragraph("+56.0 bps (+0.56%)", table_cell_bold)],
    ]
    t_sim = Table([sim_headers] + sim_rows, colWidths=[55, 75, 75, 75, 85, 75, 83])
    t_sim.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C5282')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
    ]))
    story.append(t_sim)

    story.append(Paragraph(
        "<b>Kesimpulan Analisis Ekonomi:</b> Gross edge instrumen 5-menit di pasar nyata hanya bernilai 1-5 bps. "
        "Mengejar gross edge +100 hingga +326 bps pada timeframe 5-menit adalah kemustahilan matematis. "
        "Sebaliknya, jika frekuensi dinaikkan (SKEN-F), akumulasi friksi transaksi menelan 2.60% modal per hari (78% per bulan). "
        "Oleh karena itu, target +3.00% hanya dapat dicapai melalui <b>ekspansi horizon ke swing multi-jam (1h-4h)</b> atau <b>eksekusi passive maker dengan rabat fee VIP institusional</b>.", body_style))

    story.append(PageBreak())

    # =========================================================================
    # 19. ROADMAP, RISK REGISTER & RECOMMENDATIONS
    # =========================================================================
    story.append(Paragraph("19. STRATEGIC ROADMAP MENUJU TARGET +3%", h1_style))
    story.append(Paragraph(
        "Roadmap penelitian berikutnya dikelompokkan ke dalam 5 lintasan strategis berdisiplin tinggi: "
        "<br/>- <b>Track 1 (Alpha Discovery):</b> Selesaikan dan commit Milestone 5.13 (R-1); perluas horizon trading ke swing 15m/1h/4h dengan target barrier profit 80-200 bps (R-2); akuisisi data funding rate historis 8-jam untuk strategi delta-neutral cash-and-carry (R-3). "
        "<br/>- <b>Track 2 (Execution Economics):</b> Rekam data orderbook Level 2 live untuk mengkalibrasi probabilitas antrean maker empiris (R-4); evaluasi fee tier VIP bursa ber-rabat negatif (R-5). "
        "<br/>- <b>Track 3 (Statistical Validation):</b> Eksekusi walk-forward rolling out-of-sample (R-6); kunci kepatuhan FWER Holm-Bonferroni < 0.05 dan DSR >= 0.95 (R-7). "
        "<br/>- <b>Track 4 (Portfolio & Capital):</b> Terapkan pembatasan korelasi dinamis lintas aset saat volatilitas pasar serempak meningkat (R-8). "
        "<br/>- <b>Track 5 (System Reliability):</b> Sempurnakan test suite repositori mencapai 100% kelulusan (R-9).", body_style))

    story.append(Paragraph("20. COMPREHENSIVE RISK REGISTER", h1_style))
    rsk_headers = [Paragraph("ID", table_header), Paragraph("Kategori Risiko", table_header), Paragraph("Deskripsi Peristiwa Risiko", table_header), Paragraph("Tingkat Risiko", table_header), Paragraph("Mitigasi Utama", table_header)]
    rsk_rows = [
        [Paragraph("RSK-01", table_cell_bold), Paragraph("Execution", table_cell), Paragraph("Friksi taker ritel (26 bps) menghapus gross edge 5m (1-5 bps)", table_cell), Paragraph("TINGGI", table_cell_bold), Paragraph("Migrasi ke swing 1h-4h atau fee tier institusional", table_cell)],
        [Paragraph("RSK-02", table_cell_bold), Paragraph("Microstructure", table_cell), Paragraph("Asumsi antrean maker simulasi terlalu optimis tanpa data L2", table_cell), Paragraph("TINGGI", table_cell_bold), Paragraph("Validasi empiris dengan streaming orderbook L2 nyata", table_cell)],
        [Paragraph("RSK-03", table_cell_bold), Paragraph("Portfolio Risk", table_cell), Paragraph("Asimetri konveksitas short saat terjadi reli harga mendadak", table_cell), Paragraph("SEDANG", table_cell_bold), Paragraph("Alokasi posisi short lebih ketat; Active MTM deleveraging", table_cell)],
        [Paragraph("RSK-04", table_cell_bold), Paragraph("Capital", table_cell), Paragraph("Starvation di bawah $20 akibat minimum notional bursa $5", table_cell), Paragraph("SEDANG", table_cell_bold), Paragraph("Disiplin stop-loss portofolio; cegah drawdown > 15%", table_cell)],
        [Paragraph("RSK-05", table_cell_bold), Paragraph("Statistical", table_cell), Paragraph("Backtest overfitting akibat pengujian kombinasi berulang", table_cell), Paragraph("RENDAH", table_cell_bold), Paragraph("Kontrol FWER Holm-Bonferroni dan Deflated Sharpe Ratio", table_cell)],
        [Paragraph("RSK-06", table_cell_bold), Paragraph("Integrity", table_cell), Paragraph("Kontaminasi data prospective holdout (>= Nov 2026)", table_cell), Paragraph("RENDAH", table_cell_bold), Paragraph("Pertahankan segel holdout otomatis 1793491200000 ms", table_cell)],
        [Paragraph("RSK-07", table_cell_bold), Paragraph("Engineering", table_cell), Paragraph("Working tree drift: unit test gagal pada file untracked M5.13", table_cell), Paragraph("SEDANG", table_cell_bold), Paragraph("Perbaiki argumen initial_cash dan lengkapi deliverable M5.13", table_cell)],
    ]
    t_rsk = Table([rsk_headers] + rsk_rows, colWidths=[45, 65, 173, 60, 180])
    t_rsk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')]),
        ('TEXTCOLOR', (3,1), (3,1), colors.HexColor('#C53030')),
        ('TEXTCOLOR', (3,2), (3,2), colors.HexColor('#C53030')),
    ]))
    story.append(t_rsk)

    story.append(Paragraph("21. PRIORITAS REKOMENDASI AKSI", h1_style))
    story.append(Paragraph(
        "1. <b>Prioritas 1:</b> Perbaiki bug constructor <code>initial_cash</code> -> <code>initial_equity_usd</code> pada <code>tests/unit/test_milestone_5_13_confluence_and_maker.py</code> dan lengkapi 4 dokumen deliverable M5.13 agar test suite kembali 100% passing. "
        "<br/>2. <b>Prioritas 2:</b> Tinggalkan pencarian strategi arah taker 5-menit; alihkan seluruh komputasi riset ke horizon swing 1h-4h. "
        "<br/>3. <b>Prioritas 3:</b> Validasi model antrean maker menggunakan data orderbook Level 2 live streaming. "
        "<br/>4. <b>Prioritas 4:</b> Akuisisi data funding rate 8 jam dan spot untuk diversifikasi ke delta-neutral cash-and-carry. "
        "<br/>5. <b>Prioritas 5:</b> Pertahankan segel isolasi holdout prospective hingga seluruh acceptance criteria terpenuhi.", body_style))

    story.append(PageBreak())

    # =========================================================================
    # 22. FINAL INDEPENDENT VERDICT
    # =========================================================================
    story.append(Paragraph("22. FINAL INDEPENDENT VERDICT & EVALUATION", h1_style))
    
    verdict_box = [
        [Paragraph("<font size=12><b>FINAL AUTHORITATIVE AUDIT VERDICT:</b></font><br/>"
                   "<font size=16 color='#1A365D'><b>TECHNICALLY_MATURE_BUT_ECONOMICALLY_UNPROVEN</b></font><br/>"
                   "<font size=8 color='#718096'>Klasifikasi Tata Kelola: Fondasi Rekayasa Perangkat Lunak Finansial & Risiko Sangat Matang; Keunggulan Ekonomi Nyata Belum Terbukti.</font>", ParagraphStyle('VBox', alignment=1, leading=16))]
    ]
    t_vbox = Table(verdict_box, colWidths=[523])
    t_vbox.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EBF8FF')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#2B6CB0')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_vbox)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Jawaban Resmi Independen atas Sebelas Pertanyaan Mandat:", h2_style))
    answers = [
        ("1. Apakah QUANTUM secara teknis memiliki fondasi yang cukup baik?", "YA, SANGAT KUAT. Arsitektur 6 agen, event ledger double-entry, oracle presisi ganda, Active MTM monitor, dan property-based testing fleet terbukti deterministik dan kokoh."),
        ("2. Apakah akuntansi dapat dipercaya?", "YA. Akuntansi terbukti bebas dari double counting, exposure breach, dan ilusi MDD palsu. Oracle independen mencocokkan kas dan ekuitas hingga presisi mesin (< 10^-8 USD)."),
        ("3. Apakah manajemen risiko cukup matang untuk penelitian lanjutan?", "YA. Pengendalian risiko dual-layer (Layer A: admission cap 0.9950x; Layer B: Active MTM 6-state FSM + deleveraging tertutup) terbukti menghentikan pergeseran pasif short convexity."),
        ("4. Apakah asumsi eksekusi realistis?", "UNTUK TAKER: Sangat realistis (memasukkan fee bursa, spread, dan slippage). UNTUK MAKER: Belum sepenuhnya realistis; masih berstatus SIMULATED_EXECUTION_ASSUMPTION tanpa validasi L2."),
        ("5. Apakah sudah ada alpha yang terbukti?", "BELUM. Gross alpha mikro ada (1-5 bps), tetapi net alpha yang terbukti secara ekonomi belum ada pada eksekusi ritel. Alpha M5.13 masih berupa simulasi maker."),
        ("6. Seberapa jauh hasil aktual dari target +3%?", "SANGAT JAUH. Pada taker, return harian negatif. Pada maker simulasi M5.13, return mencapai +0.145%/hari (gap defisit: -2.855%/hari, baru mencakup 4.83% dari target mandat)."),
        ("7. Apa tiga hambatan terbesar saat ini?", "(1) Friksi biaya transaksi bursa ritel (26 bps); (2) Keterbatasan matematis eksposur unlevered 1.0x; (3) Ketiadaan data empiris kedalaman buku order Level 2."),
        ("8. Apa lima pekerjaan dengan prioritas tertinggi?", "(1) Perbaiki bug test M5.13; (2) Migrasi ke horizon swing multi-jam 1h-4h; (3) Validasi empiris antrean maker L2; (4) Akuisisi data funding rate; (5) Validasi walk-forward rolling OOS."),
        ("9. Apa yang tidak perlu dibangun lagi?", "TIDAK PERLU merombak event ledger atau oracle; TIDAK PERLU menambah agen baru; dan TIDAK PERLU mengulang pencarian strategi arah taker 5-menit."),
        ("10. Kondisi minimum sebelum paper trading boleh dipertimbangkan?", "Mean net daily return >= +3.00%, MDD <= 15.00%, exposure <= 1.0x, DSR >= 0.95, dan verifikasi antrean maker nyata selama minimal 30 hari backtest out-of-sample."),
        ("11. Kondisi minimum sebelum live trading boleh dipertimbangkan?", "Paper trading konsisten selama 30-60 hari di lingkungan live pasca-holdout dengan eksekusi discrepancy < 10% dan persetujuan formal Human Governance Council."),
    ]
    for q, a in answers:
        story.append(Paragraph(f"<b>{q}</b><br/>{a}", body_style))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 6))
    story.append(Paragraph("23. LAMPIRAN TEKNIS & INVARIAN KEUANGAN", h1_style))
    story.append(Paragraph(
        "Sepuluh invarian finansial yang diverifikasi pada 10.000 sekuens property-based testing (139.857 peristiwa, tingkat kelulusan 100.00%): "
        "<br/>- PROP-01: Saldo kas non-negatif sebelum ruin. "
        "<br/>- PROP-02: Ekuitas identik antara buku besar dan oracle (< 10<sup>-8</sup>). "
        "<br/>- PROP-03: Gross exposure pre-trade tidak pernah melebihi 0.995000x. "
        "<br/>- PROP-04: Gross exposure hard limit tidak pernah melanggar 1.000000x pre-trade. "
        "<br/>- PROP-05: Notional pending order tereservasi dilepaskan sempurna saat fill/cancel. "
        "<br/>- PROP-06: Deduksi biaya transaksi berimbang sempurna antara kas dan ekuitas. "
        "<br/>- PROP-07: Deleveraging tidak menciptakan likuiditas semu saat pasar tidak likuid. "
        "<br/>- PROP-08: Transisi state risiko mematuhi histeresis wajib 200 bps. "
        "<br/>- PROP-09: Penghentian ruin mengunci ekuitas permanen dan membatalkan semua order. "
        "<br/>- PROP-10: Deterministik 100% pada pengulangan dengan seed acak yang identik.", body_style))

    story.append(Paragraph("24. REFERENSI FILE DAN GIT COMMIT", h1_style))
    story.append(Paragraph(
        "<b>Commit Git Kunci:</b> <code>dcc8ceb</code> (Awal forensik), <code>7700046</code> (M5.7 Kausalitas), <code>da62984</code> (M5.8a Survival), "
        "<code>382f640</code> (M5.9 Track C), <code>99163a0</code> (M5.10b Contract), <code>7a4bb3e</code> (M5.11 Alpha), <code>c59ac22</code> (M5.12 Accounting), "
        "<code>7110908</code> (M5.12.1 Oracle), <code>273b897</code> (M5.12.2 Invariant), <code>ce9367b</code> (M5.12.2.1 Evidence), "
        "<code>7f1e58c</code> (M5.12.2.2 Active MTM), <code>0088b65</code> (M5.12.2.2.1 Math Integrity - Authoritative HEAD). "
        "<br/><b>Berkas Pendukung Terverifikasi:</b> "
        "<code>QUANTUM_MILESTONE_HISTORY.csv</code>, <code>QUANTUM_HISTORICAL_INCIDENT_REGISTER.csv</code>, "
        "<code>QUANTUM_RISK_REGISTER.csv</code>, <code>QUANTUM_DISTANCE_TO_TARGET.csv</code>, <code>QUANTUM_EVIDENCE_INDEX.csv</code>.", body_style))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully regenerated at: {pdf_path}")

if __name__ == "__main__":
    build_pdf()
