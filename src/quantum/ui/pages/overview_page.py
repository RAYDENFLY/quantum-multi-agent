"""Overview workspace shell (Alt+1) displaying desk KPI strip and pipeline standby state."""

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from quantum.ui.widgets.empty_state import EmptyStateWidget


class OverviewPage(QWidget):
    """Workspace 1: Overview and Desk Health."""

    def __init__(self, on_navigate_settings: Optional[Callable[[], None]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.on_navigate_settings = on_navigate_settings

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        lbl_title = QLabel("Workspace 1: Overview")
        lbl_title.setProperty("class", "title")
        lbl_subtitle = QLabel("Desk health, active paper exposure, and local multi-agent pipeline monitoring.")
        lbl_subtitle.setProperty("class", "subtitle")
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # 5-Metric Quick KPI Strip
        kpi_frame = QFrame()
        kpi_frame.setProperty("class", "panel")
        kpi_layout = QHBoxLayout(kpi_frame)
        kpi_layout.setContentsMargins(16, 12, 16, 12)
        kpi_layout.setSpacing(24)

        metrics = [
            ("PAPER EQUITY", "$10,000.00", "#F1F5F9"),
            ("SESSION PNL", "+$0.00 (+0.00%)", "#34D399"),
            ("DAILY DRAWDOWN", "0.00% / 2.50% Max", "#94A3B8"),
            ("ACTIVE POSITIONS", "0 / 3 Max", "#94A3B8"),
            ("ROLLING WIN RATE", "0.0% (N = 0)", "#7E8FA6"),
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
            badge_text="[SYSTEM STANDBY: PHASE 1 FOUNDATION]",
            title="Desk In Paper Trading Standby",
            description=(
                "The PySide6 desktop foundation and SQLite WAL persistence layer are active. "
                "Exchange ingestion (Bybit and AsterDEX) and the 4-stage market scanner will activate in "
                "subsequent phases. Trade proposals, agent reasoning logs, and open paper positions will "
                "populate here automatically once opportunities are discovered."
            ),
            action_text="Configure Settings (Alt+7)",
            action_callback=self.on_navigate_settings,
        )
        layout.addWidget(empty_widget, stretch=1)
