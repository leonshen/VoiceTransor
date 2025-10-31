# -*- coding: utf-8 -*-
"""Application themes: VS Code–like dark and classic light."""
from __future__ import annotations
from PySide6.QtGui import QPalette, QColor, QFontDatabase, QFont
from PySide6.QtWidgets import QApplication, QStyleFactory


# ---- font helpers -----------------------------------------------------------
def pick_ui_font(size_pt: int = 10) -> QFont:
    """Pick a modern UI font similar to VS Code on Windows."""
    preferred = ["Segoe UI", "Inter", "Roboto", "Arial"]
    fams = set(QFontDatabase.families())
    for name in preferred:
        if name in fams:
            f = QFont(name, pointSize=size_pt)
            return f
    return QApplication.font()  # fallback

def pick_monospace_family() -> str:
    """Pick a VS Code–like editor font family."""
    preferred = ["Cascadia Code", "Consolas", "Courier New", "DejaVu Sans Mono"]
    fams = set(QFontDatabase.families())
    for name in preferred:
        if name in fams:
            return name
    return QApplication.font().family()


# ---- palettes ---------------------------------------------------------------
def _vscode_dark_palette() -> QPalette:
    # VS Code-ish colors
    bg  = QColor("#1e1e1e")
    base = QColor("#1e1e1e")
    alt  = QColor("#252526")
    text = QColor("#d4d4d4")
    mid  = QColor("#2d2d30")
    btn  = QColor("#2d2d30")
    acc  = QColor("#0e639c")  # VS Code blue
    dis  = QColor("#7f7f7f")

    pal = QPalette()
    pal.setColor(QPalette.Window, bg)
    pal.setColor(QPalette.WindowText, text)
    pal.setColor(QPalette.Base, base)
    pal.setColor(QPalette.AlternateBase, alt)
    pal.setColor(QPalette.ToolTipBase, alt)
    pal.setColor(QPalette.ToolTipText, text)
    pal.setColor(QPalette.Text, text)
    pal.setColor(QPalette.Button, btn)
    pal.setColor(QPalette.ButtonText, text)
    pal.setColor(QPalette.Highlight, acc)
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.PlaceholderText, dis)

    # Disabled
    pal.setColor(QPalette.Disabled, QPalette.Text, dis)
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, dis)
    pal.setColor(QPalette.Disabled, QPalette.WindowText, dis)
    pal.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#3d3d3d"))
    pal.setColor(QPalette.Disabled, QPalette.HighlightedText, dis)
    return pal

_DARK_QSS = r"""
/* Global base */
QWidget { background-color: #1e1e1e; color: #d4d4d4; }
QLabel { color: #d4d4d4; }
QToolTip { background-color: #252526; color: #d4d4d4; border: 1px solid #3f3f46; }

/* Menus / bars / docks */
QMenuBar, QMenu, QToolBar, QStatusBar, QDockWidget { background: #2d2d30; color: #d4d4d4; }
QMenuBar::item:selected, QMenu::item:selected { background: #094771; }

/* Dock title */
QDockWidget::title {
    background: #2d2d30;
    padding-left: 8px;
    padding-top: 3px;
    padding-bottom: 3px;
    color: #d4d4d4;
    font-size: 8pt;
    min-height: 20px;
    text-align: left;
}

/* Groups / frames */
QGroupBox {
  border: 1px solid #3f3f46;
  margin-top: 8px;
  color: #d4d4d4;                 /* <-- make group captions light */
}
QGroupBox::title {
  subcontrol-origin: margin;
  left: 8px;
  padding: 0 3px;
  color: #d4d4d4;                 /* <-- explicitly set title color */
  background: transparent;
}

/* Editors & scroll areas */
QAbstractScrollArea { background: #1e1e1e; }
QPlainTextEdit, QTextEdit, QTextBrowser, QListView, QTreeView, QTableView {
  background: #1e1e1e;
  color: #d4d4d4;
  selection-background-color: #264f78;
  selection-color: #ffffff;
  border: 1px solid #3f3f46;
}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {
  background: #252526;
  color: #d4d4d4;
  border: 1px solid #3f3f46;
  padding: 2px 4px;
}
QComboBox {
  background: #252526; color: #d4d4d4; border: 1px solid #3f3f46; padding: 2px 4px;
}
QComboBox QAbstractItemView {
  background: #252526; color: #d4d4d4; selection-background-color: #094771; selection-color: #ffffff;
}

/* Buttons */
QPushButton { background: #2d2d30; border: 1px solid #3f3f46; padding: 4px 8px; color: #d4d4d4; }
QPushButton:hover { background: #3a3a3d; }
QPushButton:pressed { background: #094771; }
QPushButton:disabled { color: #7f7f7f; border-color: #3a3a3d; }

/* Checkables */
QCheckBox, QRadioButton { spacing: 6px; }
QCheckBox::indicator, QRadioButton::indicator { background: #1e1e1e; border: 1px solid #3f3f46; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked { background: #0e639c; }

/* Progress / sliders */
QProgressBar { border: 1px solid #3f3f46; text-align: center; height: 10px; background: #1e1e1e; color: #d4d4d4; }
QProgressBar::chunk { background-color: #0e639c; }
QSlider::groove:horizontal { background: #3f3f46; height: 2px; }
QSlider::handle:horizontal { background: #0e639c; width: 10px; margin: -4px 0; }

/* Scrollbars */
QScrollBar:vertical { background: #1e1e1e; width: 10px; }
QScrollBar::handle:vertical { background: #3f3f46; min-height: 20px; }
QScrollBar:horizontal { background: #1e1e1e; height: 10px; }
QScrollBar::handle:horizontal { background: #3f3f46; min-width: 20px; }

/* Ensure all text inside docks inherits light color */
QDockWidget, QDockWidget * { color: #d4d4d4; }

/* Status bar text & its internal labels */
QStatusBar, QStatusBar * { color: #d4d4d4; }

/* Disabled colors */
*::disabled { color: #7f7f7f; }
"""


def apply_theme(app: QApplication, theme: str, ui_pt: int = 10) -> None:
    if theme == "dark":
        # Fusion gives reliable palette+QSS behavior
        app.setStyle(QStyleFactory.create("Fusion"))
        app.setPalette(_vscode_dark_palette())
        app.setStyleSheet(_DARK_QSS)
    else:
        # Use native Windows style if available; fallback to Fusion
        win = QStyleFactory.create("WindowsVista") or QStyleFactory.create("Windows")
        app.setStyle(win or QStyleFactory.create("Fusion"))
        app.setPalette(app.style().standardPalette())
        app.setStyleSheet("")

    app.setFont(pick_ui_font(ui_pt))

