"""Dark terminal design system, color tokens, and QSS stylesheet generator."""

from typing import Dict

# WCAG AA verified color tokens compliant with docs/UI_DESIGN_SYSTEM.md
COLORS: Dict[str, str] = {
    "bg.canvas": "#0B0E14",
    "bg.panel": "#111620",
    "bg.elevated": "#171E2C",
    "border.subtle": "#1E2633",
    "border.control": "#3B485E",
    "border.focus": "#22D3EE",
    "text.primary": "#F1F5F9",
    "text.secondary": "#94A3B8",
    "text.muted": "#7E8FA6",
    "accent.primary": "#22D3EE",
    "accent.hover": "#06B6D4",
    "status.long_profit": "#34D399",
    "status.long_bg": "#062E22",
    "status.short_loss": "#FB7185",
    "status.short_bg": "#31101E",
    "status.warning": "#FBBF24",
    "status.warning_bg": "#2E2108",
    "status.info": "#60A5FA",
    "status.info_bg": "#0F233D",
}

FONT_SANS = '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif'
FONT_MONO = '"JetBrains Mono", "Cascadia Mono", "Consolas", monospace'


def generate_qss() -> str:
    """Generate the complete high-density dark terminal QSS stylesheet."""
    return f"""
    /* QUANTUM Master Obsidian Terminal Stylesheet */

    QWidget {{
        background-color: {COLORS["bg.canvas"]};
        color: {COLORS["text.primary"]};
        font-family: {FONT_SANS};
        font-size: 12px;
        selection-background-color: {COLORS["bg.elevated"]};
        selection-color: {COLORS["accent.primary"]};
    }}

    QMainWindow {{
        background-color: {COLORS["bg.canvas"]};
    }}

    QFrame.panel {{
        background-color: {COLORS["bg.panel"]};
        border: 1px solid {COLORS["border.subtle"]};
        border-radius: 6px;
    }}

    QFrame.card {{
        background-color: {COLORS["bg.elevated"]};
        border: 1px solid {COLORS["border.subtle"]};
        border-radius: 4px;
    }}

    /* Top Command Strip */
    QFrame#TopCommandBar {{
        background-color: {COLORS["bg.panel"]};
        border-bottom: 1px solid {COLORS["border.subtle"]};
        min-height: 52px;
        max-height: 52px;
    }}

    /* Bottom Telemetry Bar */
    QFrame#BottomTelemetryBar {{
        background-color: {COLORS["bg.panel"]};
        border-top: 1px solid {COLORS["border.subtle"]};
        min-height: 26px;
        max-height: 26px;
        font-family: {FONT_MONO};
        font-size: 11px;
        color: {COLORS["text.secondary"]};
    }}

    /* Navigation Rail */
    QFrame#NavRail {{
        background-color: {COLORS["bg.panel"]};
        border-right: 1px solid {COLORS["border.subtle"]};
        min-width: 190px;
        max-width: 190px;
    }}

    QPushButton.nav-item {{
        background-color: transparent;
        color: {COLORS["text.secondary"]};
        border: none;
        border-left: 3px solid transparent;
        border-radius: 0px;
        padding: 9px 14px;
        text-align: left;
        font-size: 12px;
        font-weight: 500;
    }}

    QPushButton.nav-item:hover {{
        background-color: {COLORS["bg.elevated"]};
        color: {COLORS["text.primary"]};
    }}

    QPushButton.nav-item:checked {{
        background-color: {COLORS["bg.elevated"]};
        color: {COLORS["accent.primary"]};
        border-left: 3px solid {COLORS["accent.primary"]};
        font-weight: 600;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {COLORS["bg.elevated"]};
        color: {COLORS["text.primary"]};
        border: 1px solid {COLORS["border.control"]};
        border-radius: 4px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 500;
        min-height: 20px;
    }}

    QPushButton:hover {{
        border-color: {COLORS["accent.primary"]};
        color: {COLORS["accent.primary"]};
    }}

    QPushButton:pressed {{
        background-color: {COLORS["bg.canvas"]};
    }}

    QPushButton:focus {{
        border: 2px solid {COLORS["border.focus"]};
        outline: none;
    }}

    QPushButton.primary {{
        background-color: {COLORS["accent.primary"]};
        color: {COLORS["bg.canvas"]};
        border: 1px solid {COLORS["accent.primary"]};
        font-weight: 600;
    }}

    QPushButton.primary:hover {{
        background-color: {COLORS["accent.hover"]};
        border-color: {COLORS["accent.hover"]};
    }}

    QPushButton.danger {{
        background-color: {COLORS["status.short_bg"]};
        color: {COLORS["status.short_loss"]};
        border: 1px solid {COLORS["status.short_loss"]};
    }}

    /* Input Fields */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {COLORS["bg.elevated"]};
        color: {COLORS["text.primary"]};
        border: 1px solid {COLORS["border.control"]};
        border-radius: 4px;
        padding: 5px 8px;
        font-family: {FONT_MONO};
        font-size: 12px;
        min-height: 20px;
    }}

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 2px solid {COLORS["border.focus"]};
        outline: none;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS["bg.elevated"]};
        color: {COLORS["text.primary"]};
        border: 1px solid {COLORS["border.control"]};
        selection-background-color: {COLORS["bg.panel"]};
        selection-color: {COLORS["accent.primary"]};
    }}

    /* Labels */
    QLabel {{
        background: transparent;
        color: {COLORS["text.primary"]};
    }}

    QLabel.title {{
        font-size: 16px;
        font-weight: 600;
        color: {COLORS["text.primary"]};
    }}

    QLabel.subtitle {{
        font-size: 12px;
        color: {COLORS["text.secondary"]};
    }}

    QLabel.muted {{
        font-size: 11px;
        color: {COLORS["text.muted"]};
    }}

    QLabel.mono {{
        font-family: {FONT_MONO};
    }}

    /* Status Badges */
    QLabel.badge-long {{
        background-color: {COLORS["status.long_bg"]};
        color: {COLORS["status.long_profit"]};
        border: 1px solid {COLORS["status.long_profit"]};
        border-radius: 3px;
        padding: 2px 6px;
        font-family: {FONT_MONO};
        font-size: 11px;
        font-weight: 600;
    }}

    QLabel.badge-short {{
        background-color: {COLORS["status.short_bg"]};
        color: {COLORS["status.short_loss"]};
        border: 1px solid {COLORS["status.short_loss"]};
        border-radius: 3px;
        padding: 2px 6px;
        font-family: {FONT_MONO};
        font-size: 11px;
        font-weight: 600;
    }}

    QLabel.badge-warning {{
        background-color: {COLORS["status.warning_bg"]};
        color: {COLORS["status.warning"]};
        border: 1px solid {COLORS["status.warning"]};
        border-radius: 3px;
        padding: 2px 6px;
        font-family: {FONT_MONO};
        font-size: 11px;
        font-weight: 600;
    }}

    QLabel.badge-info {{
        background-color: {COLORS["status.info_bg"]};
        color: {COLORS["status.info"]};
        border: 1px solid {COLORS["status.info"]};
        border-radius: 3px;
        padding: 2px 6px;
        font-family: {FONT_MONO};
        font-size: 11px;
        font-weight: 600;
    }}

    /* Tab Bars */
    QTabWidget::pane {{
        border: 1px solid {COLORS["border.subtle"]};
        background-color: {COLORS["bg.panel"]};
        border-radius: 4px;
    }}

    QTabBar::tab {{
        background-color: {COLORS["bg.canvas"]};
        color: {COLORS["text.secondary"]};
        border: 1px solid {COLORS["border.subtle"]};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 6px 14px;
        margin-right: 2px;
        font-size: 12px;
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS["bg.panel"]};
        color: {COLORS["accent.primary"]};
        font-weight: 600;
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {COLORS["bg.elevated"]};
        color: {COLORS["text.primary"]};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {COLORS["bg.canvas"]};
        width: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {COLORS["border.control"]};
        min-height: 20px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {COLORS["accent.primary"]};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {COLORS["bg.canvas"]};
        height: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: {COLORS["border.control"]};
        min-width: 20px;
        border-radius: 4px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {COLORS["accent.primary"]};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Splitters */
    QSplitter::handle {{
        background-color: {COLORS["bg.canvas"]};
    }}

    QSplitter::handle:hover {{
        background-color: {COLORS["accent.primary"]};
    }}

    /* Group Box */
    QGroupBox {{
        border: 1px solid {COLORS["border.subtle"]};
        border-radius: 6px;
        margin-top: 12px;
        padding: 14px;
        font-weight: 600;
        color: {COLORS["text.primary"]};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0px 4px;
        background-color: {COLORS["bg.panel"]};
    }}
    """
