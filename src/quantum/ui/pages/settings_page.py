"""Settings workspace shell (Alt+7) providing real configuration management and persistence."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from quantum.config.settings import Settings, get_settings


class SettingsPage(QWidget):
    """Workspace 7: Application and Multi-Agent Desk Settings."""

    settings_saved = Signal(Settings)

    def __init__(self, settings: Optional[Settings] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._settings = settings or get_settings()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        lbl_title = QLabel("Workspace 7: Settings & Desk Configuration")
        lbl_title.setProperty("class", "title")
        lbl_subtitle = QLabel("Configure local ML thresholds, exchange polling, deterministic risk rules, and paper account parameters.")
        lbl_subtitle.setProperty("class", "subtitle")
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        main_layout.addLayout(header_layout)

        # Scroll Area for Form Sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        form_layout = QVBoxLayout(container)
        form_layout.setContentsMargins(0, 0, 10, 0)
        form_layout.setSpacing(16)

        # 1. Desktop Application Group
        grp_app = QGroupBox("1. Desktop Application Settings")
        f_app = QFormLayout(grp_app)
        f_app.setSpacing(10)

        self.lbl_data_dir = QLabel(str(self._settings.data_dir))
        self.lbl_data_dir.setProperty("class", "mono")
        self.lbl_data_dir.setStyleSheet("color: #22D3EE;")
        f_app.addRow("Data Storage Directory:", self.lbl_data_dir)

        self.cb_log_level = QComboBox()
        self.cb_log_level.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        self.cb_log_level.setCurrentText(self._settings.app.log_level)
        f_app.addRow("Rotating Log Level:", self.cb_log_level)

        self.cb_theme = QComboBox()
        self.cb_theme.addItems(["obsidian (Obsidian Slate Terminal)", "daylight (High-Contrast Light)"])
        self.cb_theme.setCurrentIndex(0 if self._settings.app.theme_mode == "obsidian" else 1)
        f_app.addRow("Interface Theme:", self.cb_theme)

        self.spin_refresh = QSpinBox()
        self.spin_refresh.setRange(1, 10)
        self.spin_refresh.setValue(self._settings.app.ui_refresh_hz)
        self.spin_refresh.setSuffix(" Hz")
        f_app.addRow("UI Refresh Rate:", self.spin_refresh)

        form_layout.addWidget(grp_app)

        # 2. Exchange Connectivity Group
        grp_ex = QGroupBox("2. Exchange Connectivity & Polling")
        f_ex = QFormLayout(grp_ex)
        f_ex.setSpacing(10)

        self.chk_bybit = QCheckBox("Enable Bybit Linear Perpetuals (USDT-margined)")
        self.chk_bybit.setChecked(self._settings.exchange.bybit_enabled)
        f_ex.addRow("Bybit Adapter:", self.chk_bybit)

        self.chk_aster = QCheckBox("Enable AsterDEX Linear Perpetuals (USDT-margined)")
        self.chk_aster.setChecked(self._settings.exchange.aster_enabled)
        f_ex.addRow("AsterDEX Adapter:", self.chk_aster)

        self.spin_poll = QSpinBox()
        self.spin_poll.setRange(10, 300)
        self.spin_poll.setValue(self._settings.exchange.rest_poll_interval_s)
        self.spin_poll.setSuffix(" seconds")
        f_ex.addRow("REST Polling Cycle:", self.spin_poll)

        self.spin_ws_subs = QSpinBox()
        self.spin_ws_subs.setRange(5, 100)
        self.spin_ws_subs.setValue(self._settings.exchange.max_ws_subscriptions)
        f_ex.addRow("Max Live WebSocket Streams:", self.spin_ws_subs)

        form_layout.addWidget(grp_ex)

        # 3. Deterministic Risk Engine Limits (Agent 4)
        grp_risk = QGroupBox("3. Deterministic Risk Controls (Agent 4)")
        f_risk = QFormLayout(grp_risk)
        f_risk.setSpacing(10)

        self.spin_equity = QDoubleSpinBox()
        self.spin_equity.setRange(1000.0, 1_000_000.0)
        self.spin_equity.setValue(self._settings.risk.starting_paper_equity_usdt)
        self.spin_equity.setPrefix("$ ")
        self.spin_equity.setDecimals(2)
        f_risk.addRow("Initial Paper Equity:", self.spin_equity)

        self.spin_risk_pct = QDoubleSpinBox()
        self.spin_risk_pct.setRange(0.1, 2.0)
        self.spin_risk_pct.setValue(self._settings.risk.risk_per_trade_pct * 100)
        self.spin_risk_pct.setSuffix(" %")
        self.spin_risk_pct.setDecimals(2)
        f_risk.addRow("Risk per Trade (Budget):", self.spin_risk_pct)

        self.spin_max_pos = QSpinBox()
        self.spin_max_pos.setRange(1, 8)
        self.spin_max_pos.setValue(self._settings.risk.max_concurrent_positions)
        f_risk.addRow("Max Concurrent Positions:", self.spin_max_pos)

        self.spin_max_lev = QDoubleSpinBox()
        self.spin_max_lev.setRange(1.0, 5.0)
        self.spin_max_lev.setValue(self._settings.risk.max_leverage_per_position)
        self.spin_max_lev.setSuffix("x")
        self.spin_max_lev.setDecimals(1)
        f_risk.addRow("Max Leverage Ceiling:", self.spin_max_lev)

        self.spin_min_rr = QDoubleSpinBox()
        self.spin_min_rr.setRange(1.5, 4.0)
        self.spin_min_rr.setValue(self._settings.risk.min_net_reward_risk)
        self.spin_min_rr.setDecimals(2)
        f_risk.addRow("Minimum Net R:R after Fees:", self.spin_min_rr)

        form_layout.addWidget(grp_risk)

        # 4. Local Machine Learning Group
        grp_ml = QGroupBox("4. Local CPU Machine Learning & Fallbacks")
        f_ml = QFormLayout(grp_ml)
        f_ml.setSpacing(10)

        self.cb_fallback = QComboBox()
        self.cb_fallback.addItems([
            "FALLBACK_RULE_ONLY (Use deterministic baseline when model is unpromoted)",
            "STRICT_ML_ONLY (Abort with SKIP if trained model artifact is missing)",
        ])
        self.cb_fallback.setCurrentIndex(0 if self._settings.ml.fallback_policy == "FALLBACK_RULE_ONLY" else 1)
        f_ml.addRow("Inference Policy:", self.cb_fallback)

        self.spin_scout_p = QDoubleSpinBox()
        self.spin_scout_p.setRange(0.50, 0.80)
        self.spin_scout_p.setValue(self._settings.ml.scout_min_prob)
        self.spin_scout_p.setDecimals(2)
        f_ml.addRow("Scout Min Probability:", self.spin_scout_p)

        self.spin_analyst_p = QDoubleSpinBox()
        self.spin_analyst_p.setRange(0.50, 0.85)
        self.spin_analyst_p.setValue(self._settings.ml.analyst_min_prob)
        self.spin_analyst_p.setDecimals(2)
        f_ml.addRow("Analyst Min Probability:", self.spin_analyst_p)

        self.spin_sniper_ev = QDoubleSpinBox()
        self.spin_sniper_ev.setRange(0.10, 1.00)
        self.spin_sniper_ev.setValue(self._settings.ml.sniper_min_expected_r)
        self.spin_sniper_ev.setSuffix(" R")
        self.spin_sniper_ev.setDecimals(2)
        f_ml.addRow("Sniper Min Expected Net R:", self.spin_sniper_ev)

        form_layout.addWidget(grp_ml)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, stretch=1)

        # Action Buttons Footer
        footer = QFrame()
        footer.setProperty("class", "panel")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(14, 10, 14, 10)
        f_layout.setSpacing(12)

        self.lbl_status = QLabel("Settings loaded from ~/.quantum/config.json")
        self.lbl_status.setProperty("class", "muted")
        f_layout.addWidget(self.lbl_status)

        f_layout.addStretch()

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.clicked.connect(self._reset_defaults)
        f_layout.addWidget(self.btn_reset)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setProperty("class", "primary")
        self.btn_save.clicked.connect(self._save_settings)
        f_layout.addWidget(self.btn_save)

        main_layout.addWidget(footer)

    def _save_settings(self) -> None:
        """Collect form values, update Settings model, and persist to disk."""
        self._settings.app.log_level = self.cb_log_level.currentText()
        self._settings.app.theme_mode = "obsidian" if self.cb_theme.currentIndex() == 0 else "daylight"
        self._settings.app.ui_refresh_hz = self.spin_refresh.value()

        self._settings.exchange.bybit_enabled = self.chk_bybit.isChecked()
        self._settings.exchange.aster_enabled = self.chk_aster.isChecked()
        self._settings.exchange.rest_poll_interval_s = self.spin_poll.value()
        self._settings.exchange.max_ws_subscriptions = self.spin_ws_subs.value()

        self._settings.risk.starting_paper_equity_usdt = self.spin_equity.value()
        self._settings.risk.risk_per_trade_pct = self.spin_risk_pct.value() / 100.0
        self._settings.risk.max_concurrent_positions = self.spin_max_pos.value()
        self._settings.risk.max_leverage_per_position = self.spin_max_lev.value()
        self._settings.risk.min_net_reward_risk = self.spin_min_rr.value()

        self._settings.ml.fallback_policy = "FALLBACK_RULE_ONLY" if self.cb_fallback.currentIndex() == 0 else "STRICT_ML_ONLY"
        self._settings.ml.scout_min_prob = self.spin_scout_p.value()
        self._settings.ml.analyst_min_prob = self.spin_analyst_p.value()
        self._settings.ml.sniper_min_expected_r = self.spin_sniper_ev.value()

        self._settings.save()
        self.lbl_status.setText("Settings saved successfully to config.json")
        self.lbl_status.setStyleSheet("color: #34D399; font-weight: 600;")
        self.settings_saved.emit(self._settings)

    def _reset_defaults(self) -> None:
        """Reset form controls to conservative institutional defaults."""
        default_settings = Settings()
        self.cb_log_level.setCurrentText(default_settings.app.log_level)
        self.cb_theme.setCurrentIndex(0)
        self.spin_refresh.setValue(default_settings.app.ui_refresh_hz)
        self.chk_bybit.setChecked(default_settings.exchange.bybit_enabled)
        self.chk_aster.setChecked(default_settings.exchange.aster_enabled)
        self.spin_poll.setValue(default_settings.exchange.rest_poll_interval_s)
        self.spin_ws_subs.setValue(default_settings.exchange.max_ws_subscriptions)
        self.spin_equity.setValue(default_settings.risk.starting_paper_equity_usdt)
        self.spin_risk_pct.setValue(default_settings.risk.risk_per_trade_pct * 100)
        self.spin_max_pos.setValue(default_settings.risk.max_concurrent_positions)
        self.spin_max_lev.setValue(default_settings.risk.max_leverage_per_position)
        self.spin_min_rr.setValue(default_settings.risk.min_net_reward_risk)
        self.cb_fallback.setCurrentIndex(0)
        self.spin_scout_p.setValue(default_settings.ml.scout_min_prob)
        self.spin_analyst_p.setValue(default_settings.ml.analyst_min_prob)
        self.spin_sniper_ev.setValue(default_settings.ml.sniper_min_expected_r)
        self._save_settings()
        self.lbl_status.setText("Reset to conservative defaults successfully")
        self.lbl_status.setStyleSheet("color: #FBBF24; font-weight: 600;")
