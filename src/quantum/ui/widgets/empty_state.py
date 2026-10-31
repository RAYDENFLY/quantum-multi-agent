"""Reusable empty state widget strictly compliant with anti-slop rule R-27."""

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class EmptyStateWidget(QFrame):
    """Empty state panel explaining cause, current system state, and next action."""

    def __init__(
        self,
        badge_text: str,
        title: str,
        description: str,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        # Status Badge
        badge_layout = QHBoxLayout()
        badge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label = QLabel(badge_text)
        self.badge_label.setProperty("class", "badge-info")
        badge_layout.addWidget(self.badge_label)
        layout.addLayout(badge_layout)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Description
        self.desc_label = QLabel(description)
        self.desc_label.setProperty("class", "subtitle")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumWidth(580)
        layout.addWidget(self.desc_label)

        # Optional Action Button
        if action_text and action_callback:
            btn_layout = QHBoxLayout()
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.action_btn = QPushButton(action_text)
            self.action_btn.setProperty("class", "primary")
            self.action_btn.clicked.connect(action_callback)
            btn_layout.addWidget(self.action_btn)
            layout.addSpacing(6)
            layout.addLayout(btn_layout)
