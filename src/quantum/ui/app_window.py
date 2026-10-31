"""Main application window for QUANTUM Trading Desk."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from quantum.config.settings import Settings, get_settings
from quantum.core.logging import get_logger
from quantum.ui.pages.agents_page import AgentsPage
from quantum.ui.pages.analytics_page import AnalyticsPage
from quantum.ui.pages.market_page import MarketPage
from quantum.ui.pages.overview_page import OverviewPage
from quantum.ui.pages.positions_page import PositionsPage
from quantum.ui.pages.scanner_page import ScannerPage
from quantum.ui.pages.settings_page import SettingsPage
from quantum.ui.widgets.nav_rail import NavRail
from quantum.ui.widgets.status_bar import BottomTelemetryBar
from quantum.ui.widgets.top_bar import TopCommandBar

logger = get_logger("ui.app_window")


class MainWindow(QMainWindow):
    """Primary desktop terminal window containing 7 workspace shells and global command bar."""

    window_closed = Signal()

    def __init__(self, settings: Optional[Settings] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.settings = settings or get_settings()

        self.setWindowTitle(f"{self.settings.app.app_name} v{self.settings.app.version} (Paper Trading)")
        self.resize(self.settings.app.window_width, self.settings.app.window_height)
        self.setMinimumSize(1024, 700)

        self._init_ui()
        self._setup_shortcuts()
        logger.info("MainWindow initialized with 7 workspace shells")

    def _init_ui(self) -> None:
        """Construct the main layout, command bar, navigation rail, and stacked pages."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Command Bar
        self.top_bar = TopCommandBar(self)
        self.top_bar.pause_toggled.connect(self._on_pause_toggled)
        root_layout.addWidget(self.top_bar)

        # 2. Middle Body: Left NavRail + Right Stacked Workspaces
        body_widget = QWidget(self)
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.nav_rail = NavRail(self)
        self.nav_rail.workspace_selected.connect(self.switch_workspace)
        body_layout.addWidget(self.nav_rail)

        # Seven Stacked Pages
        self.stack = QStackedWidget(self)

        self.page_overview = OverviewPage(on_navigate_settings=lambda: self.switch_workspace(6))
        self.page_scanner = ScannerPage()
        self.page_agents = AgentsPage()
        self.page_market = MarketPage()
        self.page_positions = PositionsPage()
        self.page_analytics = AnalyticsPage()
        self.page_settings = SettingsPage(settings=self.settings)

        self.stack.addWidget(self.page_overview)   # Index 0 (Alt+1)
        self.stack.addWidget(self.page_scanner)    # Index 1 (Alt+2)
        self.stack.addWidget(self.page_agents)     # Index 2 (Alt+3)
        self.stack.addWidget(self.page_market)     # Index 3 (Alt+4)
        self.stack.addWidget(self.page_positions)  # Index 4 (Alt+5)
        self.stack.addWidget(self.page_analytics)  # Index 5 (Alt+6)
        self.stack.addWidget(self.page_settings)   # Index 6 (Alt+7)

        body_layout.addWidget(self.stack, stretch=1)
        root_layout.addWidget(body_widget, stretch=1)

        # 3. Bottom Telemetry Bar
        self.status_bar = BottomTelemetryBar(self)
        root_layout.addWidget(self.status_bar)

    def _setup_shortcuts(self) -> None:
        """Register global desktop keyboard navigation shortcuts."""
        # Alt+1 through Alt+7 workspace shortcuts
        for i in range(7):
            shortcut = QShortcut(QKeySequence(f"Alt+{i+1}"), self)
            shortcut.activated.connect(lambda idx=i: self.switch_workspace(idx))

        # Ctrl+Shift+P: Toggle Pause Pipeline
        pause_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        pause_shortcut.activated.connect(self.top_bar.btn_pause.toggle)

        # Escape: Reset focus
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self._on_escape)

    def switch_workspace(self, index: int) -> None:
        """Switch active workspace in stacked widget and synchronize nav rail."""
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            # Synchronize navigation rail button state if needed
            if self.nav_rail.button_group.checkedId() != index:
                self.nav_rail.buttons[index].setChecked(True)
            logger.debug("Switched to workspace index: %d", index)

    def _on_pause_toggled(self, is_paused: bool) -> None:
        """Log pipeline pause state."""
        state = "PAUSED" if is_paused else "RESUMED"
        logger.info("Pipeline %s by operator", state)

    def _on_escape(self) -> None:
        """Clear active focus on Escape."""
        current_focus = self.focusWidget()
        if current_focus:
            current_focus.clearFocus()

    def set_database_telemetry(self, table_count: int, wal_active: bool) -> None:
        """Update SQLite status in bottom telemetry bar."""
        self.status_bar.set_db_status(table_count, wal_active)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Cleanly handle application window closing."""
        logger.info("MainWindow closing")
        # Save window geometry in settings
        self.settings.app.window_width = self.width()
        self.settings.app.window_height = self.height()
        try:
            self.settings.save()
        except Exception as e:
            logger.warning("Could not persist window dimensions on exit: %s", e)
        self.window_closed.emit()
        event.accept()
