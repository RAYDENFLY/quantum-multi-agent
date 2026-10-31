"""Market Scanner workspace shell (Alt+2) displaying Stage A-D discovery controls and empty state."""

from typing import Optional
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from quantum.ui.widgets.empty_state import EmptyStateWidget


class ScannerPage(QWidget):
    """Workspace 2: Dynamic Market Scanner."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        lbl_title = QLabel("Workspace 2: Market Scanner")
        lbl_title.setProperty("class", "title")
        lbl_subtitle = QLabel("Dynamic linear perpetual futures opportunity discovery across Bybit and AsterDEX.")
        lbl_subtitle.setProperty("class", "subtitle")
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # Controls & Funnel Header
        ctrl_frame = QFrame()
        ctrl_frame.setProperty("class", "panel")
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(12, 8, 12, 8)
        ctrl_layout.setSpacing(12)

        lbl_ex = QLabel("Exchange:")
        lbl_ex.setProperty("class", "muted")
        cb_ex = QComboBox()
        cb_ex.addItems(["ALL (Bybit + AsterDEX)", "BYBIT Only", "ASTER Only"])
        ctrl_layout.addWidget(lbl_ex)
        ctrl_layout.addWidget(cb_ex)

        lbl_bias = QLabel("Bias:")
        lbl_bias.setProperty("class", "muted")
        cb_bias = QComboBox()
        cb_bias.addItems(["ALL Biases", "LONG Only", "SHORT Only"])
        ctrl_layout.addWidget(lbl_bias)
        ctrl_layout.addWidget(cb_bias)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Filter symbol (e.g. BTC, ETH, SOL)...")
        search_input.setMaximumWidth(220)
        ctrl_layout.addWidget(search_input)

        ctrl_layout.addStretch()

        funnel_pill = QLabel("Stage Funnel: Universe (0) > Screened (0) > Classified (0) > Queued (0)")
        funnel_pill.setProperty("class", "mono")
        funnel_pill.setStyleSheet("color: #7E8FA6; font-size: 11px; padding: 4px 8px; background: #171E2C; border: 1px solid #1E2633; border-radius: 4px;")
        ctrl_layout.addWidget(funnel_pill)

        layout.addWidget(ctrl_frame)

        # Center Empty State
        empty_widget = EmptyStateWidget(
            badge_text="[SCANNER STANDBY: PHASE 4 PENDING]",
            title="Dynamic Market Scanner Inactive",
            description=(
                "Stage A Universe Discovery, Stage B Hygiene Screening, Stage C 7-Bucket Classification "
                "(Top Gainers/Losers, Volume Surge, Momentum Acceleration, Volatility Expansion, Reversal, "
                "and Breakout), and Stage D Deduplication will activate upon Phase 4 implementation. "
                "Discovered candidates will appear in this workspace ranking table."
            ),
        )
        layout.addWidget(empty_widget, stretch=1)
