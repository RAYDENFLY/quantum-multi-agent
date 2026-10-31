"""Analytics workspace shell (Alt+6) displaying performance metrics and 5-tier ablation empty state."""

from typing import Optional
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from quantum.ui.widgets.empty_state import EmptyStateWidget


class AnalyticsPage(QWidget):
    """Workspace 6: Quantitative Performance Analytics and 5-Tier Ablation."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        lbl_title = QLabel("Workspace 6: Analytics & Baseline Ablation")
        lbl_title.setProperty("class", "title")
        lbl_subtitle = QLabel("Performance curves, net expectancy attribution, and 5-tier multi-agent ablation suite.")
        lbl_subtitle.setProperty("class", "subtitle")
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # Statistical Confidence Warning Banner
        banner = QFrame()
        banner.setProperty("class", "panel")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(12, 8, 12, 8)

        lbl_warn = QLabel("[PRELIMINARY: N = 0 CLOSED TRADES - MINIMUM 30 TRADES REQUIRED FOR STATISTICAL SIGNIFICANCE]")
        lbl_warn.setProperty("class", "mono")
        lbl_warn.setStyleSheet("color: #FBBF24; font-size: 11px; font-weight: 600;")
        banner_layout.addWidget(lbl_warn)
        banner_layout.addStretch()
        layout.addWidget(banner)

        # Center Empty State
        empty_widget = EmptyStateWidget(
            badge_text="[NO CLOSED TRADES: PHASE 7 PENDING]",
            title="Ablation and Performance Analytics Standby",
            description=(
                "Performance curves, underwater drawdown charts, fee/slippage execution drag breakdown, "
                "and the 5-Tier Ablation Suite (RULE_ONLY baseline, SCOUT_ONLY, SCOUT_ANALYST, "
                "SCOUT_ANALYST_SNIPER, and QUANTUM_5_AGENT) will be implemented in Phase 7. Realized trades "
                "from PaperSimulator will be analyzed here for edge verification and Brier score calibration."
            ),
        )
        layout.addWidget(empty_widget, stretch=1)
