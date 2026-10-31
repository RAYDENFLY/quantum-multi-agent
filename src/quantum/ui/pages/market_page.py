"""Market Chart and Historical Data workspace (Alt+4) with collection and features."""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quantum.ui.widgets.empty_state import EmptyStateWidget


class MarketPage(QWidget):
    """Workspace 4: Live Market Charts & Historical Data Engineering Desk."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        lbl_title = QLabel("Workspace 4: Market Desk & Historical Feature Store")
        lbl_title.setProperty("class", "title")
        lbl_subtitle = QLabel("Multi-timeframe candlestick analysis, historical dataset collection, and causal feature extraction.")
        lbl_subtitle.setProperty("class", "subtitle")
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        main_layout.addLayout(header_layout)

        # Tab Widget
        self.tabs = QTabWidget()

        # Tab 1: Live Market & Charts
        self.tab_live = QWidget()
        self._init_live_tab()
        self.tabs.addTab(self.tab_live, "Live Market Chart")

        # Tab 2: Historical Collection & Features
        self.tab_historical = QWidget()
        self._init_historical_tab()
        self.tabs.addTab(self.tab_historical, "Historical Collection & Features")

        main_layout.addWidget(self.tabs, stretch=1)

    def _init_live_tab(self) -> None:
        """Initialize the Live Market chart tab."""
        layout = QVBoxLayout(self.tab_live)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        # Instrument & Timeframe Bar
        bar_frame = QFrame()
        bar_frame.setProperty("class", "panel")
        bar_layout = QHBoxLayout(bar_frame)
        bar_layout.setContentsMargins(12, 8, 12, 8)
        bar_layout.setSpacing(12)

        lbl_sym = QLabel("Symbol:")
        lbl_sym.setProperty("class", "muted")
        self.cb_sym = QComboBox()
        self.cb_sym.addItems(["BYBIT:BTCUSDT", "BYBIT:ETHUSDT", "BYBIT:SOLUSDT", "ASTER:BTCUSDT", "ASTER:ETHUSDT"])
        bar_layout.addWidget(lbl_sym)
        bar_layout.addWidget(self.cb_sym)

        bar_layout.addSpacing(8)

        lbl_tf = QLabel("Timeframe:")
        lbl_tf.setProperty("class", "muted")
        bar_layout.addWidget(lbl_tf)

        for tf in ["1m", "5m", "15m", "1h", "4h"]:
            btn = QPushButton(tf)
            btn.setMaximumWidth(40)
            if tf == "15m":
                btn.setProperty("class", "primary")
            bar_layout.addWidget(btn)

        bar_layout.addStretch()

        self.lbl_feed_status = QLabel("[FEED: STANDBY]")
        self.lbl_feed_status.setProperty("class", "mono")
        self.lbl_feed_status.setStyleSheet("color: #7E8FA6; font-size: 11px;")
        bar_layout.addWidget(self.lbl_feed_status)

        layout.addWidget(bar_frame)

        # Center Empty State
        empty_widget = EmptyStateWidget(
            badge_text="[MARKET FEED STANDBY: READY FOR INGESTION]",
            title="Public Exchange Data Feeds Standby",
            description=(
                "Real-time market data ingestion via Bybit V5 Linear WebSocket and AsterDEX public "
                "streams are integrated. Live depth buffering, snapshot bridging, and hardware-accelerated "
                "candlestick rendering are ready."
            ),
        )
        layout.addWidget(empty_widget, stretch=1)

    def _init_historical_tab(self) -> None:
        """Initialize the Historical Collection & Feature Store tab."""
        layout = QVBoxLayout(self.tab_historical)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        # Control Panel Group
        grp_controls = QGroupBox("Historical Collection Configuration")
        grid = QGridLayout(grp_controls)
        grid.setSpacing(10)

        grid.addWidget(QLabel("Exchange:"), 0, 0)
        self.cb_hist_exchange = QComboBox()
        self.cb_hist_exchange.addItems(["ASTER", "BYBIT"])
        grid.addWidget(self.cb_hist_exchange, 0, 1)

        grid.addWidget(QLabel("Symbol:"), 0, 2)
        self.cb_hist_symbol = QComboBox()
        self.cb_hist_symbol.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])
        grid.addWidget(self.cb_hist_symbol, 0, 3)

        grid.addWidget(QLabel("Timeframe:"), 0, 4)
        self.cb_hist_timeframe = QComboBox()
        self.cb_hist_timeframe.addItems(["5m", "15m", "1h", "4h", "1d"])
        grid.addWidget(self.cb_hist_timeframe, 0, 5)

        grid.addWidget(QLabel("Coverage:"), 1, 0)
        self.cb_hist_range = QComboBox()
        self.cb_hist_range.addItems(["30 Days", "90 Days", "180 Days", "1 Year", "3 Years (Max)"])
        grid.addWidget(self.cb_hist_range, 1, 1)

        self.btn_start_download = QPushButton("Start Collection")
        self.btn_start_download.setProperty("class", "primary")
        grid.addWidget(self.btn_start_download, 1, 2)

        self.btn_cancel_download = QPushButton("Cancel")
        self.btn_cancel_download.setEnabled(False)
        grid.addWidget(self.btn_cancel_download, 1, 3)

        self.btn_compute_features = QPushButton("Compute Features")
        grid.addWidget(self.btn_compute_features, 1, 4)

        self.btn_mtf_join = QPushButton("Multi-TF Join")
        grid.addWidget(self.btn_mtf_join, 1, 5)

        layout.addWidget(grp_controls)

        # Progress and Status Bar
        status_frame = QFrame()
        status_frame.setProperty("class", "panel")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 8, 12, 8)
        status_layout.setSpacing(6)

        info_row = QHBoxLayout()
        self.lbl_job_status = QLabel("Status: Idle")
        self.lbl_job_status.setProperty("class", "mono")
        self.lbl_checkpoint = QLabel("Checkpoint: None")
        self.lbl_checkpoint.setProperty("class", "muted")
        self.lbl_coverage = QLabel("Coverage: 0.0%")
        self.lbl_coverage.setProperty("class", "mono")

        info_row.addWidget(self.lbl_job_status)
        info_row.addStretch()
        info_row.addWidget(self.lbl_checkpoint)
        info_row.addSpacing(20)
        info_row.addWidget(self.lbl_coverage)
        status_layout.addLayout(info_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(status_frame)

        # Bottom Area: Quality Reports & Manifest Table
        grp_jobs = QGroupBox("Collection Runs & Dataset Quality Audit")
        vbox_jobs = QVBoxLayout(grp_jobs)
        vbox_jobs.setContentsMargins(10, 10, 10, 10)

        self.table_jobs = QTableWidget(0, 8)
        self.table_jobs.setHorizontalHeaderLabels([
            "Run ID",
            "Exchange",
            "Symbol",
            "Timeframe",
            "Candles",
            "Coverage",
            "Status",
            "Audit Outcome",
        ])
        header = self.table_jobs.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_jobs.setAlternatingRowColors(True)
        vbox_jobs.addWidget(self.table_jobs)

        layout.addWidget(grp_jobs, stretch=1)
