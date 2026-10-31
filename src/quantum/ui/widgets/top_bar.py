"""Top command strip displaying paper equity, pipeline stepper, and system health."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TopCommandBar(QFrame):
    """Top command and 5-stage pipeline status bar (52px height)."""

    pause_toggled = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopCommandBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(16)

        # 1. Paper Account KPI Box
        kpi_layout = QVBoxLayout()
        kpi_layout.setContentsMargins(0, 8, 0, 8)
        kpi_layout.setSpacing(1)

        equity_row = QHBoxLayout()
        equity_row.setSpacing(6)
        lbl_equity_tag = QLabel("PAPER EQUITY:")
        lbl_equity_tag.setProperty("class", "muted")
        self.lbl_equity_val = QLabel("$10,000.00")
        self.lbl_equity_val.setProperty("class", "mono")
        self.lbl_equity_val.setStyleSheet("font-weight: 700; font-size: 14px; color: #F1F5F9;")
        equity_row.addWidget(lbl_equity_tag)
        equity_row.addWidget(self.lbl_equity_val)
        equity_row.addStretch()
        kpi_layout.addLayout(equity_row)

        sub_row = QHBoxLayout()
        sub_row.setSpacing(10)
        self.lbl_pnl = QLabel("PnL: +$0.00 (+0.00%)")
        self.lbl_pnl.setProperty("class", "mono")
        self.lbl_pnl.setStyleSheet("font-size: 11px; color: #34D399;")
        self.lbl_dd = QLabel("DD: 0.00%")
        self.lbl_dd.setProperty("class", "mono")
        self.lbl_dd.setStyleSheet("font-size: 11px; color: #94A3B8;")
        sub_row.addWidget(self.lbl_pnl)
        sub_row.addWidget(self.lbl_dd)
        sub_row.addStretch()
        kpi_layout.addLayout(sub_row)
        layout.addLayout(kpi_layout)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.VLine)
        div1.setStyleSheet("color: #1E2633;")
        layout.addWidget(div1)

        # 2. Five-Stage Pipeline Stepper
        pipeline_layout = QHBoxLayout()
        pipeline_layout.setSpacing(6)

        lbl_pipe_tag = QLabel("PIPELINE:")
        lbl_pipe_tag.setProperty("class", "muted")
        pipeline_layout.addWidget(lbl_pipe_tag)

        self.stages = ["1 SCOUT", "2 ANALYST", "3 SNIPER", "4 RISK", "5 BANKER"]
        self.stage_labels = []

        for i, stage_name in enumerate(self.stages):
            lbl = QLabel(f"[{stage_name}: IDLE]")
            lbl.setProperty("class", "mono")
            lbl.setStyleSheet(
                "font-size: 10px; padding: 2px 5px; background: #171E2C; "
                "border: 1px solid #1E2633; border-radius: 3px; color: #94A3B8;"
            )
            pipeline_layout.addWidget(lbl)
            self.stage_labels.append(lbl)
            if i < len(self.stages) - 1:
                arr = QLabel(">")
                arr.setStyleSheet("color: #3B485E; font-size: 10px; font-weight: bold;")
                pipeline_layout.addWidget(arr)

        layout.addLayout(pipeline_layout)
        layout.addStretch()

        # 3. Connectivity & Model Pills
        pills_layout = QHBoxLayout()
        pills_layout.setSpacing(8)

        self.pill_bybit = QLabel("[BYBIT: DISCONNECTED]")
        self.pill_bybit.setProperty("class", "mono")
        self.pill_bybit.setStyleSheet("font-size: 10px; color: #7E8FA6; background: #111620; padding: 3px 6px; border: 1px solid #1E2633; border-radius: 3px;")
        pills_layout.addWidget(self.pill_bybit)

        self.pill_aster = QLabel("[ASTER: DISCONNECTED]")
        self.pill_aster.setProperty("class", "mono")
        self.pill_aster.setStyleSheet("font-size: 10px; color: #7E8FA6; background: #111620; padding: 3px 6px; border: 1px solid #1E2633; border-radius: 3px;")
        pills_layout.addWidget(self.pill_aster)

        self.pill_ml = QLabel("[ML: RULE_BASELINE]")
        self.pill_ml.setProperty("class", "mono")
        self.pill_ml.setStyleSheet("font-size: 10px; color: #FBBF24; background: #2E2108; padding: 3px 6px; border: 1px solid #FBBF24; border-radius: 3px;")
        pills_layout.addWidget(self.pill_ml)

        layout.addLayout(pills_layout)

        # 4. Emergency Pause Pipeline Button
        self.btn_pause = QPushButton("Pause Pipeline")
        self.btn_pause.setCheckable(True)
        self.btn_pause.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 5px 12px; } "
            "QPushButton:checked { background: #31101E; color: #FB7185; border: 1px solid #FB7185; }"
        )
        self.btn_pause.toggled.connect(self._on_pause_toggled)
        layout.addWidget(self.btn_pause)

    def _on_pause_toggled(self, is_paused: bool) -> None:
        """Handle pipeline pause/resume toggle."""
        if is_paused:
            self.btn_pause.setText("Resume Pipeline")
        else:
            self.btn_pause.setText("Pause Pipeline")
        self.pause_toggled.emit(is_paused)

    def update_equity(self, equity_usdt: float, pnl_usdt: float, pnl_pct: float, dd_pct: float) -> None:
        """Update top bar paper equity metrics."""
        self.lbl_equity_val.setText(f"${equity_usdt:,.2f}")
        sign = "+" if pnl_usdt >= 0 else ""
        color = "#34D399" if pnl_usdt >= 0 else "#FB7185"
        self.lbl_pnl.setText(f"PnL: {sign}${pnl_usdt:,.2f} ({sign}{pnl_pct:.2f}%)")
        self.lbl_pnl.setStyleSheet(f"font-size: 11px; color: {color};")
        self.lbl_dd.setText(f"DD: {dd_pct:.2f}%")
