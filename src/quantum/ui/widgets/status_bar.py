"""Bottom telemetry bar displaying real-time RAM, SQLite status, and background worker state."""

from typing import Optional
import psutil
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QWidget,
)


class BottomTelemetryBar(QFrame):
    """Bottom telemetry status bar (26px height)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("BottomTelemetryBar")
        self._process = psutil.Process()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(14)

        # 1. SQLite WAL Status
        self.lbl_db = QLabel("[SQLite: WAL Active (18 Tables)]")
        self.lbl_db.setStyleSheet("color: #34D399;")
        layout.addWidget(self.lbl_db)

        layout.addWidget(self._make_divider())

        # 2. Resident Process Memory (RAM)
        self.lbl_ram = QLabel("[RAM: -- MB]")
        layout.addWidget(self.lbl_ram)

        layout.addWidget(self._make_divider())

        # 3. Market Scanner Status
        self.lbl_scan = QLabel("[Last Scan: Standby (Phase 4)]")
        layout.addWidget(self.lbl_scan)

        layout.addWidget(self._make_divider())

        # 4. CPU Inference Metric
        self.lbl_inference = QLabel("[CPU Inference P95: 0.0 ms]")
        layout.addWidget(self.lbl_inference)

        layout.addStretch()

        # 5. Training Worker Subprocess Status
        self.lbl_worker = QLabel("[Training Worker: IDLE]")
        self.lbl_worker.setStyleSheet("color: #94A3B8;")
        layout.addWidget(self.lbl_worker)

        # 2-second telemetry refresh timer
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self.refresh_telemetry)
        self._timer.start()

        # Initial refresh
        self.refresh_telemetry()

    def _make_divider(self) -> QLabel:
        """Create a subtle vertical separator."""
        lbl = QLabel("|")
        lbl.setStyleSheet("color: #1E2633;")
        return lbl

    def refresh_telemetry(self) -> None:
        """Measure current process RSS memory and refresh displayed value."""
        try:
            mem_info = self._process.memory_info()
            rss_mb = mem_info.rss / (1024 * 1024)
            color = "#34D399" if rss_mb <= 300.0 else "#FBBF24"
            self.lbl_ram.setText(f"[RAM: {rss_mb:.1f} MB]")
            self.lbl_ram.setStyleSheet(f"color: {color}; font-weight: 500;")
        except Exception:
            self.lbl_ram.setText("[RAM: N/A]")

    def set_db_status(self, table_count: int, wal_active: bool) -> None:
        """Update the SQLite status text."""
        mode_str = "WAL Active" if wal_active else "Standard"
        color = "#34D399" if wal_active else "#FB7185"
        self.lbl_db.setText(f"[SQLite: {mode_str} ({table_count} Tables)]")
        self.lbl_db.setStyleSheet(f"color: {color};")

    def set_worker_status(self, status: str) -> None:
        """Update training worker status text."""
        self.lbl_worker.setText(f"[Training Worker: {status}]")
