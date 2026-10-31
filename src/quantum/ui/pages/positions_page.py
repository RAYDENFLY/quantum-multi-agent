"""Positions workspace shell (Alt+5) displaying open paper positions and fill ledger standby state."""

from typing import Optional
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from quantum.ui.widgets.empty_state import EmptyStateWidget


class PositionsPage(QWidget):
    """Workspace 5: Positions, Orders, and Execution Ledger."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        lbl_title = QLabel("Workspace 5: Positions & Orders")
        lbl_title.setProperty("class", "title")
        lbl_subtitle = QLabel("Active paper positions, working limit orders, simulated execution fills, and trade journal.")
        lbl_subtitle.setProperty("class", "subtitle")
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # Positions Quick Metrics Strip
        kpi_frame = QFrame()
        kpi_frame.setProperty("class", "panel")
        kpi_layout = QHBoxLayout(kpi_frame)
        kpi_layout.setContentsMargins(16, 10, 16, 10)
        kpi_layout.setSpacing(24)

        metrics = [
            ("OPEN POSITIONS", "0 / 3 Max", "#94A3B8"),
            ("TOTAL NOTIONAL", "$0.00", "#F1F5F9"),
            ("MARGIN ALLOCATED", "$0.00", "#F1F5F9"),
            ("UNREALIZED PNL", "+$0.00 (+0.00%)", "#34D399"),
            ("WORKING ORDERS", "0 Active", "#7E8FA6"),
        ]

        for tag, val, color in metrics:
            box = QVBoxLayout()
            box.setSpacing(2)
            lbl_tag = QLabel(tag)
            lbl_tag.setProperty("class", "muted")
            lbl_val = QLabel(val)
            lbl_val.setProperty("class", "mono")
            lbl_val.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {color};")
            box.addWidget(lbl_tag)
            box.addWidget(lbl_val)
            kpi_layout.addLayout(box)

        kpi_layout.addStretch()
        layout.addWidget(kpi_frame)

        # Center Empty State
        empty_widget = EmptyStateWidget(
            badge_text="[ZERO OPEN POSITIONS: PHASE 6 PENDING]",
            title="Zero Open Paper Positions",
            description=(
                "The realistic paper execution engine (L2 order book depth walk, maker/taker fees, "
                "perpetual funding settlement, and Banker position lifecycle state machine) will be "
                "implemented in Phase 6. Working limit orders, active positions, and post-trade attribution "
                "journals will be recorded in SQLite WAL and displayed here."
            ),
        )
        layout.addWidget(empty_widget, stretch=1)
