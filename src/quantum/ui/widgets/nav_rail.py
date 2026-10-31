"""Left navigation rail managing workspace switching via mouse and Alt+1..7 shortcuts."""

from typing import List, Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NavRail(QFrame):
    """Left navigation rail with 7 workspace switch buttons."""

    workspace_selected = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("NavRail")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(2)

        # Desk Header
        lbl_brand = QLabel("QUANTUM DESK")
        lbl_brand.setStyleSheet("font-weight: 700; font-size: 11px; color: #22D3EE; padding: 6px 14px;")
        layout.addWidget(lbl_brand)

        lbl_sub = QLabel("LOCAL MULTI-AGENT")
        lbl_sub.setStyleSheet("font-size: 9px; color: #7E8FA6; padding: 0px 14px 10px 14px;")
        layout.addWidget(lbl_sub)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #1E2633; margin-bottom: 6px;")
        layout.addWidget(div)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.nav_items: List[str] = [
            "1. Overview (Alt+1)",
            "2. Market Scanner (Alt+2)",
            "3. Agents & Models (Alt+3)",
            "4. Market Chart (Alt+4)",
            "5. Positions (Alt+5)",
            "6. Analytics (Alt+6)",
            "7. Settings (Alt+7)",
        ]

        self.buttons: List[QPushButton] = []

        for idx, label_text in enumerate(self.nav_items):
            btn = QPushButton(label_text)
            btn.setProperty("class", "nav-item")
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            self.button_group.addButton(btn, idx)
            layout.addWidget(btn)
            self.buttons.append(btn)

        self.button_group.idClicked.connect(self._on_button_clicked)

        layout.addStretch()

        # System Mode Tag
        lbl_mode = QLabel("MODE: PAPER TRADING")
        lbl_mode.setStyleSheet("font-size: 10px; color: #34D399; font-weight: 600; padding: 10px 14px;")
        layout.addWidget(lbl_mode)

    def _on_button_clicked(self, index: int) -> None:
        """Handle button click and emit workspace_selected signal."""
        self.workspace_selected.emit(index)

    def set_active_workspace(self, index: int) -> None:
        """Programmatically switch active navigation button."""
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)
            self.workspace_selected.emit(index)
