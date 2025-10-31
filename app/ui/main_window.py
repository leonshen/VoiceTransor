# -*- coding: utf-8 -*-
"""Main window for VoiceTransor with i18n and full pipeline integration.

Layout:
    - Top dock: waveform placeholder (future: rendering + playback).
    - Left dock: audio-info (toggleable).
    - Central (right): transcript + result (vertical splitter).

Features:
    - Import → Transcribe (Whisper, local) → Text operations  → Export (TXT/PDF).
    - Thread pool with safe lifetime management to avoid random crashes.
    - i18n: Language menu (System/English/简体中文) with live retranslation.

Text Operations:
    - Uses Ollama for local LLM text processing (privacy-focused, offline).
    - OpenAI integration code is preserved for developer extensibility but hidden from end users.
    - The OpenAI Settings menu item is commented out in the UI (see lines ~373, ~887, ~1735).
"""
from __future__ import annotations
from pathlib import Path
import os
import datetime as dt
from typing import Optional

from PySide6.QtCore import Qt, QSettings, QSize, QThreadPool
from PySide6.QtGui import QAction, QFont, QFontDatabase, QActionGroup
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLabel,
    QToolBar, QMessageBox, QStatusBar, QSplitter, QFrame,
    QStyle, QFileDialog, QGroupBox, QFormLayout, QDockWidget, QDialog, QProgressBar,
    QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QPushButton, QInputDialog

)
from PySide6.QtCore import Qt, QSettings, QSize, QThreadPool, QCoreApplication,QTimer

from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QFont, QFontDatabase, QPageLayout, QPageSize
from PySide6.QtCore import QMarginsF
from PySide6.QtWidgets import QFileDialog, QMessageBox
import os

from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

# reg resources, import once 
import app.ui.resources.resources_rc as _qrc # VERY IMPORTANT

from PySide6.QtGui import QActionGroup, QFont, QKeySequence
from PySide6.QtWidgets import QApplication
from app.ui.theme import apply_theme, pick_monospace_family

from app.core.audio.ffprobe_utils import (
    ffprobe_info, summarize_info, FFprobeError
)
from app.core.common.workers import TaskSpec, FunctionRunnable, WorkerSignals
from app.core.stt.whisper_runner import transcribe, default_models_dir, is_model_cached, pick_device
# from app.core.summarize.openai_summarizer import summarize_with_openai
from app.core.export.pdf_exporter import export_result_to_pdf
from app.core.ai.openai_textops import run_text_op
from app.ui.options_dialogs import TranscribeOptionsDialog, OpenAISettingsDialog
from app.i18n.manager import I18nManager

from app.core.audio.chunker import ChunkConfig
from app.core.stt.chunked_transcriber import transcribe_chunked, TranscribeOptions
from app.core.system.thermal import ThermalConfig
import threading
import time
import inspect
import json
import sys
from app.utils.icon_tint import svg_icon

import logging
log = logging.getLogger(__name__)

ICON_PX = 28  # requested icon size

def set_action_icon_with_fallback(action: QAction, resource_name: str, icon_color: str,
                                  fallback_std_icon: QStyle.StandardPixmap | None = None):
    # icon = QIcon(f":/icons/{resource_name}")
    # icon_color = "#FFFFFF" if is_dark() else "#000000"
    size = QSize(ICON_PX, ICON_PX)  # small than toolbar height
    icon = svg_icon(f":/icons/{resource_name}", color=icon_color, size=size)
    if icon.isNull() and fallback_std_icon is not None:
        icon = QApplication.style().standardIcon(fallback_std_icon)
    action.setIcon(icon)

def _assert_resource(path: str):
    from PySide6.QtCore import QFile
    assert QFile(path).exists(), f"QRC not found: {path}"

def _apply_windows_titlebar_theme(widget, dark: bool) -> None:
    """
    Best-effort: enable/disable immersive dark title bar, then repaint non-client.
    Safe no-op on non-Windows or missing APIs.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes as wt

        hwnd = int(widget.winId())
        build = sys.getwindowsversion().build

        # 1) Try legacy uxtheme toggles (older Win10 need this to honor dark mode)
        try:
            uxtheme = ctypes.WinDLL("uxtheme")
            # ordinal exports: SetPreferredAppMode (135 or 135?) varies; use names if available in your build
            # Many builds export by ordinal; below is defensive: ignore if not present.
            # 1: Default, 2: AllowDark, 3: ForceDark, 4: ForceLight, 5: Max
            SetPreferredAppMode = getattr(uxtheme, "SetPreferredAppMode", None)
            AllowDarkModeForWindow = getattr(uxtheme, "AllowDarkModeForWindow", None)
            if SetPreferredAppMode and AllowDarkModeForWindow:
                SetPreferredAppMode(ctypes.c_int(2 if dark else 4))
                AllowDarkModeForWindow(wt.HWND(hwnd), ctypes.c_bool(bool(dark)))
        except Exception:
            pass

        # 2) DWM immersive dark flag (Win10 1809+)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20 if build >= 18985 else 19
        val = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wt.HWND(hwnd),
            wt.DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE),
            ctypes.byref(val),
            ctypes.sizeof(val),
        )

    except Exception:
        # Ignore on unsupported systems
        pass


def _force_titlebar_refresh(widget) -> None:
    """
    Force Windows to repaint the non-client title bar immediately.
    Strategy:
      - If not maximized: 1px geometry nudge (no visual change).
      - If maximized: showNormal() then showMaximized() on next tick (tiny flicker).
    """
    from PySide6.QtCore import Qt, QTimer

    if sys.platform != "win32":
        return

    try:
        state = widget.windowState()
        if state & Qt.WindowMaximized:
            # Briefly restore then re-maximize on the next cycle
            widget.showNormal()
            QTimer.singleShot(0, widget.showMaximized)
        else:
            g = widget.geometry()
            # 1px widen then revert—forces a non-client frame recalculation
            widget.setGeometry(g.x(), g.y(), g.width() + 1, g.height())
            widget.setGeometry(g)
    except Exception:
        pass



def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M")


class VoiceTransorMainWindow(QMainWindow):
    """Main GUI window."""

    from app._version import __version__
    def __init__(self, version: str = __version__, i18n: Optional[I18nManager] = None) -> None:
        super().__init__()

        _assert_resource(":/icons/vt2-app-icon.svg")

        self.version = version
        self.i18n = i18n or I18nManager()
        self.setWindowTitle(f"VoiceTransor {self.version}")
        self.resize(1200, 800)
        self._current_theme = ""

        # State
        self.settings = QSettings("VoiceTransor", "VoiceTransor")
        self.current_audio_path: Optional[Path] = None
        self.last_dir = self.settings.value("last_dir", str(Path.home()))
        self.pool = QThreadPool.globalInstance()
        self._active_tasks: list[FunctionRunnable] = []  # pin runnables to avoid premature deletion

        # STT defaults
        self.opt_model = self.settings.value("stt/model", "base")
        self.opt_lang = self.settings.value("stt/lang", "")
        self.opt_device = self.settings.value("stt/device", "auto")
        self.opt_models_dir = Path(self.settings.value("stt/models_dir", str(default_models_dir())))
        self._stop_flag = None # type: Optional[threading.Event]

        # OpenAI settings
        self.openai_key = os.getenv("OPENAI_API_KEY", self.settings.value("openai/api_key", ""))
        self.openai_model = self.settings.value("openai/model", "gpt-4o-mini")
        self.openai_project = self.settings.value("openai/project", os.getenv("OPENAI_PROJECT", ""))
        self.textops_style = self.settings.value("textops/style", "normal")

        # PDF
        self.pdf_font_path = self.settings.value("pdf/font_path", "")

        self._create_actions()
        self._create_menus_and_toolbar()
        self._create_central()       # right: transcript/text operations
        self._create_statusbar()
        self._apply_light_qss()

        # comment audio replay & waveform
        # self._create_wave_dock()     # top: waveform
        self._create_info_dock()     # left: audio info
        self._create_prompt_dock()   # left: prompt dock

        # read zoom percent (default 100)
        self._zoom_pct = int(self.settings.value("ui/zoom_pct", 100))

        # Initial translation of texts
        self.retranslate_ui()
        self._apply_saved_theme()
        QTimer.singleShot(0, lambda: self._apply_saved_theme())  # apply theme again to ensure the text color of QGroupBox



    # -------------------------
    # Actions / Menus / Toolbar
    # -------------------------
    def _create_actions(self) -> None:
        st = self.style()

        # File / Tools
        self.act_import = QAction(self)
        self.act_import.setIcon(st.standardIcon(QStyle.SP_DialogOpenButton))
        self.act_import.triggered.connect(self.on_import_audio)

        # comment audio replay & waveform
        # self.act_play_pause = QAction(self)
        # self.act_play_pause.setIcon(st.standardIcon(QStyle.SP_MediaPlay))
        # self.act_play_pause.triggered.connect(self.on_play_pause)

        self.act_transcribe = QAction(self)
        self.act_transcribe.setIcon(st.standardIcon(QStyle.SP_DialogApplyButton))
        self.act_transcribe.triggered.connect(self.on_transcribe)

        self.act_save_txt = QAction(self)
        self.act_save_txt.setIcon(st.standardIcon(QStyle.SP_DialogSaveButton))
        self.act_save_txt.triggered.connect(self.on_save_transcript_txt)

        self.act_textops = QAction(self)
        self.act_textops.setIcon(st.standardIcon(QStyle.SP_FileDialogInfoView))
        self.act_textops.triggered.connect(self.on_run_textops)

        self.act_export_pdf = QAction(self)
        self.act_export_pdf.setIcon(st.standardIcon(QStyle.SP_DialogSaveButton))
        self.act_export_pdf.triggered.connect(self.on_export_pdf)

        self.act_save_result_as_txt = QAction(self)
        self.act_save_result_as_txt.setIcon(st.standardIcon(QStyle.SP_DialogSaveButton))
        self.act_save_result_as_txt.triggered.connect(self.on_save_result_txt)

        self.act_about = QAction(self)
        self.act_about.setIcon(st.standardIcon(QStyle.SP_MessageBoxInformation))
        self.act_about.triggered.connect(self.on_about)

        self.act_contact = QAction(self)
        self.act_contact.triggered.connect(self.on_contact)

        self.act_exit = QAction(self)
        self.act_exit.setIcon(st.standardIcon(QStyle.SP_DialogCloseButton))
        self.act_exit.triggered.connect(self.close)

        # View
        self.act_show_info_dock = QAction(self, checkable=True, checked=True)
        self.act_show_info_dock.triggered.connect(self.on_toggle_info_dock)

        self.act_show_prompt_dock = QAction(self, checkable=True, checked=True)
        self.act_show_prompt_dock.triggered.connect(self.on_toggle_prompt_dock)

        self.act_wrap = QAction(self, checkable=True, checked=True)
        self.act_wrap.triggered.connect(self.on_toggle_wrap)

        self.act_mono_transcript = QAction(self, checkable=True, checked=True)
        self.act_mono_transcript.triggered.connect(self.on_toggle_mono_transcript)

        # Zoom actions
        self.act_zoom_in = QAction(self.tr("Zoom In"), self)
        self.act_zoom_in.setShortcut(QKeySequence.ZoomIn)   #  Ctrl + + / Ctrl + =

        # Ctrl+=、Ctrl+Shift+=Ctrl+“+”、 + 
        if sys.platform == "darwin":
            self.act_zoom_in.setShortcuts([
                QKeySequence(QKeySequence.ZoomIn),                 # ⌘+= 
                QKeySequence(Qt.MetaModifier | Qt.Key_Equal),      # ⌘=
                QKeySequence(Qt.MetaModifier | Qt.ShiftModifier | Qt.Key_Equal),  # ⌘+
                QKeySequence(Qt.MetaModifier | Qt.Key_Plus),       # ⌘+
            ])
        else:
            self.act_zoom_in.setShortcuts([
                QKeySequence(QKeySequence.ZoomIn),                 # Ctrl+= 
                QKeySequence(Qt.ControlModifier | Qt.Key_Equal),   # Ctrl=
                QKeySequence(Qt.ControlModifier | Qt.ShiftModifier | Qt.Key_Equal),  # Ctrl+ 
                QKeySequence(Qt.ControlModifier | Qt.Key_Plus),    # Ctrl+ +
            ])

        self.act_zoom_in.triggered.connect(self.on_zoom_in)

        self.act_zoom_out = QAction(self.tr("Zoom Out"), self)
        self.act_zoom_out.setShortcut(QKeySequence.ZoomOut) # Windows Ctrl + -
        self.act_zoom_out.triggered.connect(self.on_zoom_out)        

        self.act_zoom_reset = QAction(self.tr("Zoom Reset"),self)
        seq_reset = QKeySequence("Meta+0") if sys.platform == "darwin" else QKeySequence("Ctrl+0")
        self.act_zoom_reset.setShortcut(seq_reset)
        self.act_zoom_reset.triggered.connect(self.on_zoom_reset)

        # OpenAI Settings
        self.act_openai_settings = QAction(self)
        self.act_openai_settings.triggered.connect(self.on_openai_settings)

        # Language actions (radio-style)
        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusive(True)
        self.act_lang_system = QAction(self, checkable=True)
        self.act_lang_en = QAction(self, checkable=True)
        self.act_lang_zh = QAction(self, checkable=True)

        for a in (self.act_lang_system, self.act_lang_en, self.act_lang_zh):
            self.lang_group.addAction(a)
        self.act_lang_system.triggered.connect(lambda: self.on_change_language("system"))
        self.act_lang_en.triggered.connect(lambda: self.on_change_language("en"))
        self.act_lang_zh.triggered.connect(lambda: self.on_change_language("zh_CN"))

        # Cancel
        self.act_cancel = QAction(self)
        self.act_cancel.setEnabled(False)
        self.act_cancel.triggered.connect(self.on_cancel_transcription)

        #theme
        self.act_theme_dark = QAction(self)
        self.act_theme_light = QAction(self)
        self.act_theme_dark.setCheckable(True)
        self.act_theme_light.setCheckable(True)

        grp = QActionGroup(self)
        grp.setExclusive(True)
        grp.addAction(self.act_theme_dark)
        grp.addAction(self.act_theme_light)

        self.act_theme_dark.triggered.connect(lambda: self._apply_theme("dark"))
        self.act_theme_light.triggered.connect(lambda: self._apply_theme("light"))
        
    def _create_menus_and_toolbar(self) -> None:
        # Menus
        self.menu_file = self.menuBar().addMenu("")     # text set in retranslate_ui
        # comment audio replay & waveform
        # self.menu_play = self.menuBar().addMenu("")
        self.menu_tools = self.menuBar().addMenu("")
        self.menu_view = self.menuBar().addMenu("")
        self.menu_lang = self.menu_view.addMenu("")     # Language submenu
        self.menu_theme = self.menu_view.addMenu("")    # text set in retranslate_ui
        self.menu_help = self.menuBar().addMenu("")

        self.menu_file.addAction(self.act_import)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_save_txt)
        self.menu_file.addAction(self.act_export_pdf)
        self.menu_file.addAction(self.act_save_result_as_txt)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_exit)

        # comment audio replay & waveform
        # self.menu_play.addAction(self.act_play_pause)

        self.menu_tools.addAction(self.act_transcribe)
        self.menu_tools.addAction(self.act_textops)
        self.menu_tools.addSeparator()
        # OpenAI Settings menu item hidden from end users (code preserved for developer extensibility)
        # self.menu_tools.addAction(self.act_openai_settings)

        self.menu_view.addAction(self.act_show_info_dock)
        self.menu_view.addAction(self.act_show_prompt_dock)
        self.menu_view.addAction(self.act_wrap)
        self.menu_view.addAction(self.act_mono_transcript)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.act_zoom_in)
        self.menu_view.addAction(self.act_zoom_out)
        self.menu_view.addAction(self.act_zoom_reset)

        # Language submenu items
        self.menu_lang.addAction(self.act_lang_system)
        self.menu_lang.addAction(self.act_lang_en)
        self.menu_lang.addAction(self.act_lang_zh)

        # theme submenu items
        self.menu_theme.addAction(self.act_theme_dark)
        self.menu_theme.addAction(self.act_theme_light)        

        self.menu_help.addAction(self.act_about)
        self.menu_help.addAction(self.act_contact)

        # Toolbar
        self.build_toolbar()


    def build_toolbar(self):
        """Create a top toolbar with 36px icons and solid (non-dashed) top/bottom borders."""
        PAD_V   = 2  # vertical padding inside the toolbar
        PAD_H   = 4  # horizontal padding
        SPACING = 4  # space between tool buttons

        # Even min-height avoids half-pixel rounding on HiDPI (prevents broken border lines)
        MIN_H   = ICON_PX + PAD_V * 2        # 36 + 12 = 48 (even)

        # BORDER  = "#2a2a2a"
        # BG      = "#1b1d20"
        # color   = "#FFFFFF" if self._is_dark() else "#000000"

        tb = QToolBar(self.tr("Main Toolbar"), self)
        tb.setMovable(False)
        tb.setObjectName("mainToolbar")      # so we can target via QSS
        tb.setIconSize(QSize(ICON_PX, ICON_PX))
        self.addToolBar(Qt.TopToolBarArea, tb)

        # Style: add padding so icons do not touch top/bottom edges; draw continuous borders here.
            # border-top: 1px solid;
            # border-bottom: 1px solid;
        tb.setStyleSheet(f"""
        QToolBar#mainToolbar {{
            padding: {PAD_V}px {PAD_H}px;
            min-height: {MIN_H}px;
            spacing: {SPACING}px;
        }}
        QToolButton {{
            /* keep buttons away from the toolbar edges to avoid clipping the border */
            padding: 4px;
            margin: 2px;
            background: transparent;   /* do not paint per-button background over the border */
            border: none;
        }}
        QToolButton:hover {{
            background: rgba(255,255,255,0.4);
            border-radius: 8px;
        }}
        QToolButton:pressed {{
            background: rgba(255,255,255,0.10);
            border-radius: 8px;
        }}
        """)

        tb.addAction(self.act_import)
        # tb.addAction(self.act_play_pause)
        tb.addSeparator()
        tb.addAction(self.act_transcribe)
        tb.addAction(self.act_cancel)
        tb.addSeparator()
        tb.addAction(self.act_textops)
        tb.addSeparator()
        tb.addAction(self.act_save_txt)
        tb.addAction(self.act_export_pdf)
        tb.addAction(self.act_save_result_as_txt)
        self._set_icons()



    def _is_dark(self) -> bool:
        return self._current_theme == "dark"
    
    def _set_icons(self) -> None :
        # set all 8 icons
        icon_color = "#FFFFFF" if self._is_dark() else "#000000"
        log.debug(f"icon_color: {icon_color}")
        self.setWindowIcon(svg_icon(":/icons/vt2-app-icon.svg", icon_color, QSize(22, 22)))

        set_action_icon_with_fallback(self.act_import,            "vt2-import-audio.svg",icon_color,QStyle.SP_DialogOpenButton)
        set_action_icon_with_fallback(self.act_transcribe,        "vt2-transcribe.svg",icon_color,       None)
        set_action_icon_with_fallback(self.act_cancel,            "vt2-cancel-transcribe.svg",icon_color,QStyle.SP_DialogCancelButton)
        set_action_icon_with_fallback(self.act_textops,           "vt2-ai-text.svg",icon_color,          None)
        set_action_icon_with_fallback(self.act_save_txt,          "vt2-save-transcript-txt.svg",icon_color, QStyle.SP_DialogSaveButton)
        set_action_icon_with_fallback(self.act_export_pdf,        "vt2-export-pdf.svg",icon_color,       None)
        set_action_icon_with_fallback(self.act_save_result_as_txt,"vt2-save-result-txt.svg",icon_color,  QStyle.SP_DialogSaveButton)

    # -------------
    # Central Area
    # -------------
    def _create_central(self) -> None:
        self.grp_transcript = QGroupBox(self)
        trans_lay = QVBoxLayout(self.grp_transcript)
        self.txt_transcript = QPlainTextEdit(self)
        self._set_editor_defaults(self.txt_transcript, mono=True, wrap=True)
        trans_lay.addWidget(self.txt_transcript)

        self.grp_result = QGroupBox(self)
        result_lay = QVBoxLayout(self.grp_result)
        self.txt_result = QTextEdit(self)
        self.txt_result.setAcceptRichText(True)
        self.txt_result.setReadOnly(True)
        # self.txt_result.setPlaceholderText(self.tr("Result will appear here (Markdown will be rendered when possible)."))
        result_lay.addWidget(self.txt_result)


        splitter = QSplitter(Qt.Vertical, self)
        splitter.addWidget(self.grp_transcript)
        splitter.addWidget(self.grp_result)
        splitter.setSizes([520, 280])

        self.setCentralWidget(splitter)

    # -----------
    # Top Waveform Dock (placeholder)
    # -----------
    def _create_wave_dock(self) -> None:
        self.dock_wave = QDockWidget(self)
        self.dock_wave.setAllowedAreas(Qt.TopDockWidgetArea)
        self.dock_wave.setFeatures(QDockWidget.NoDockWidgetFeatures)

        wrap = QWidget(self.dock_wave)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(8, 8, 8, 8)

        self.wave_placeholder = QFrame(wrap)
        self.wave_placeholder.setFrameShape(QFrame.StyledPanel)
        self.wave_placeholder.setMinimumHeight(180)
        lbl = QLabel(self.tr("Waveform placeholder (to be implemented: rendering/transport)"), self.wave_placeholder)
        lbl.setAlignment(Qt.AlignCenter)
        inner = QVBoxLayout(self.wave_placeholder)
        inner.addWidget(lbl)

        lay.addWidget(self.wave_placeholder)
        self.dock_wave.setWidget(wrap)
        self.addDockWidget(Qt.TopDockWidgetArea, self.dock_wave)

    # -----------
    # Left Audio-Info Dock (toggleable)
    # -----------
    def _create_info_dock(self) -> None:
        self.dock_info = QDockWidget(self)
        self.dock_info.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dock_info.setFeatures(
            QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )

        host = QWidget(self.dock_info)
        form = QFormLayout(host)
        form.setLabelAlignment(Qt.AlignRight)

        self.lbl_info_file = QLabel("-", host)
        self.lbl_info_path = QLabel("-", host)
        self.lbl_info_container = QLabel("-", host)
        self.lbl_info_codec = QLabel("-", host)
        self.lbl_info_channels = QLabel("-", host)
        self.lbl_info_sr = QLabel("-", host)
        self.lbl_info_bitrate = QLabel("-", host)
        self.lbl_info_duration = QLabel("-", host)
        self.lbl_info_size = QLabel("-", host)

        form.addRow(self.tr("File:"), self.lbl_info_file)
        form.addRow(self.tr("Path:"), self.lbl_info_path)
        form.addRow(self.tr("Container:"), self.lbl_info_container)
        form.addRow(self.tr("Codec:"), self.lbl_info_codec)
        form.addRow(self.tr("Channels:"), self.lbl_info_channels)
        form.addRow(self.tr("Sample rate:"), self.lbl_info_sr)
        form.addRow(self.tr("Bitrate:"), self.lbl_info_bitrate)
        form.addRow(self.tr("Duration:"), self.lbl_info_duration)
        form.addRow(self.tr("Size:"), self.lbl_info_size)

        host.setMinimumWidth(280)
        self.dock_info.setWidget(host)
        self.dock_info.visibilityChanged.connect(lambda vis: self.act_show_info_dock.setChecked(bool(vis)))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_info)

    # -----------
    # Left prompt Dock (toggleable)
    # -----------
    def _create_prompt_dock(self) -> None:
        self.dock_prompt = QDockWidget(self)
        self.dock_prompt.setObjectName("dockPrompt")
        self.dock_prompt.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dock_prompt.setFeatures(
            QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        self.dock_prompt.setWindowTitle(self.tr("Prompt"))

        host = QWidget(self.dock_prompt)
        vbox = QVBoxLayout(host)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(6)

        # Preset row
        row = QHBoxLayout()
        row.addWidget(QLabel(self.tr("Preset:")))
        self.cmb_prompt_preset = QComboBox(host)
        row.addWidget(self.cmb_prompt_preset, 1)
        vbox.addLayout(row)

        # Prompt editor
        self.txt_prompt = QTextEdit(host)
        self.txt_prompt.setAcceptRichText(False)
        self.txt_prompt.setPlaceholderText(
            self.tr("Describe what to do with the transcript (e.g., summarize, translate, extract action items)…")
        )
        vbox.addWidget(self.txt_prompt, 1)

        self.dock_prompt.setWidget(host)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_prompt)
        try:
            self.splitDockWidget(self.dock_info, self.dock_prompt, Qt.Vertical)
        except Exception:
            pass

        # Build presets and connect
        self._refresh_prompt_preset_combo()
        self.cmb_prompt_preset.currentIndexChanged.connect(self._on_prompt_preset_changed)

        self.dock_prompt.visibilityChanged.connect(lambda vis: self.act_show_prompt_dock.setChecked(bool(vis)))


    def _builtin_prompt_templates(self):
        """Return list of (display_name, prompt_text) for built-in presets."""
        srt_zh = (
            "You are translating an SRT subtitle file.\n"
            "Follow these NON-NEGOTIABLE rules:\n"
            "1) Preserve each block's structure EXACTLY:\n"
            "   - Line 1: the block number (unchanged).\n"
            "   - Line 2: the time range (unchanged).\n"
            "   - Line 3..N: text lines (translate ONLY these lines).\n"
            "2) Do not merge or split blocks or lines. Keep the SAME number of lines per block.\n"
            "3) Output MUST be valid SRT. No extra commentary or trailing blank lines.\n"
            "Translate the text lines into Simplified Chinese. Keep punctuation natural.\n"
            "Return ONLY the translated SRT blocks."
        )

        return [
            (self.tr("— Select preset —"), ""),  # index 0: placeholder
            (self.tr("Summarize"),
            "Summarize the source text into 5–8 concise bullet points. Keep key facts, dates, names."),
            # (self.tr("Translate to English"),
            # "Translate the source text into natural, fluent English. Preserve meaning and tone."),
            (self.tr("Translate to Chinese"),
            "Translate the source text into Simplified Chinese with natural wording."),
            # (self.tr("Bullet notes"),
            # "Extract concise bullet notes from the source text. Use nested lists and keep structure."),
            # (self.tr("Action items"),
            # "Extract action items with: assignee (if any), action, due date (if mentioned), and priority."),
            (self.tr("Meeting minutes"),
            "Produce meeting minutes: agenda, decisions, action items (with owners and due dates), open questions."),
            (self.tr("Translate SRT to Chinese (preserve timestamps)"),
            srt_zh),
        ]

    def _load_custom_prompt_presets(self):
        """Load custom presets from QSettings (JSON array)."""
        raw = self.settings.value("prompt/custom_presets", "")
        if not raw:
            return []
        try:
            arr = json.loads(raw)
            out = []
            for it in arr:
                name = (it.get("name") or "").strip()
                text = (it.get("text") or "").strip()
                if name and text:
                    out.append((name, text))
            return out
        except Exception:
            return []

    def _save_custom_prompt_presets(self, items):
        """Persist custom presets list [(name, text), ...] as JSON."""
        arr = [{"name": n, "text": t} for (n, t) in items]
        self.settings.setValue("prompt/custom_presets", json.dumps(arr, ensure_ascii=False))

    def _refresh_prompt_preset_combo(self):
        """Rebuild the combo box with builtins + separator + customs + 'Save…' + 'Delete…'."""
        builtins = self._builtin_prompt_templates()      # [(name, text)]
        customs  = self._load_custom_prompt_presets()    # [(name, text)]

        self.cmb_prompt_preset.blockSignals(True)
        self.cmb_prompt_preset.clear()

        # Map: combo index -> preset text (only for selectable preset items)
        self._preset_texts_by_index = {}
        self._save_item_index = -1
        self._delete_item_index = -1

        # 0) Placeholder (no text mapping)
        self.cmb_prompt_preset.addItem(self.tr("— Select preset —"))

        # 1) Built-ins (skip index 0 placeholder)
        for name, text in builtins[1:]:
            idx = self.cmb_prompt_preset.count()
            self.cmb_prompt_preset.addItem(name)
            self._preset_texts_by_index[idx] = text

        # Separator
        self.cmb_prompt_preset.insertSeparator(self.cmb_prompt_preset.count())

        # 2) Custom presets
        for name, text in customs:
            idx = self.cmb_prompt_preset.count()
            self.cmb_prompt_preset.addItem(name)
            self._preset_texts_by_index[idx] = text

        # Separator + Save item
        self.cmb_prompt_preset.insertSeparator(self.cmb_prompt_preset.count())
        self._save_item_index = self.cmb_prompt_preset.count()
        self.cmb_prompt_preset.addItem(self.tr("➕ Save current as preset…"))

        # Separator + Delete item
        self.cmb_prompt_preset.insertSeparator(self.cmb_prompt_preset.count())
        self._delete_item_index = self.cmb_prompt_preset.count()
        self.cmb_prompt_preset.addItem(self.tr("🗑 Delete a custom preset…"))

        # Default back to placeholder
        self.cmb_prompt_preset.setCurrentIndex(0)
        self.cmb_prompt_preset.blockSignals(False)


    def _on_prompt_preset_changed(self, idx: int):
        """When user selects a preset: auto replace editor text; if 'save…' selected -> ask and save."""
        if idx <= 0:
            return

        # 'Save current as preset…'
        if idx == getattr(self, "_save_item_index", -1):
            self._ask_save_prompt_as_preset()
            # keep current editor content and reset combo to placeholder
            self.cmb_prompt_preset.blockSignals(True)
            self.cmb_prompt_preset.setCurrentIndex(0)
            self.cmb_prompt_preset.blockSignals(False)
            return

        # Delete a custom preset…
        if idx == getattr(self, "_delete_item_index", -1):
            self._ask_delete_prompt_preset()
            self.cmb_prompt_preset.blockSignals(True)
            self.cmb_prompt_preset.setCurrentIndex(0)
            self.cmb_prompt_preset.blockSignals(False)
            return

        # Regular preset (builtin or custom): apply text
        text = getattr(self, "_preset_texts_by_index", {}).get(idx)
        if text is not None:
            self.txt_prompt.setPlainText(text)
        
        # Separators or invalid index: ignore

    def _ask_save_prompt_as_preset(self):
        """Save current editor content as a named custom preset."""
        text = self.txt_prompt.toPlainText().strip()
        if not text:
            QMessageBox.information(self, self.tr("Info"), self.tr("Prompt is empty. Nothing to save."))
            return
        name, ok = QInputDialog.getText(self, self.tr("Save Prompt Preset"), self.tr("Preset name:"))
        if not ok or not name.strip():
            return
        name = name.strip()

        # check duplicate name -> replace，otherwise append
        custom = self._load_custom_prompt_presets()
        replaced = False
        for i, (n, t) in enumerate(custom):
            if n == name:
                custom[i] = (name, text)
                replaced = True
                break
        if not replaced:
            custom.append((name, text))
        self._save_custom_prompt_presets(custom)
        self._refresh_prompt_preset_combo()
        QMessageBox.information(self, self.tr("Saved"), self.tr("Preset saved: {name}").format(name=name))

    def _ask_delete_prompt_preset(self):
        """Prompt user to select a custom preset to delete; update settings."""
        customs = self._load_custom_prompt_presets()  # [(name, text)]
        if not customs:
            QMessageBox.information(self, self.tr("Info"), self.tr("No custom presets to delete."))
            return

        # Try to preselect a name by matching current editor content
        current_text = self.txt_prompt.toPlainText().strip()
        names = [n for (n, _t) in customs]
        default_name = names[0]
        for n, t in customs:
            if t.strip() == current_text:
                default_name = n
                break

        name, ok = QInputDialog.getItem(
            self,
            self.tr("Delete Prompt Preset"),
            self.tr("Select a preset to delete:"),
            names,
            current=names.index(default_name) if default_name in names else 0,
            editable=False
        )
        if not ok or not name:
            return

        # Confirm
        ret = QMessageBox.question(
            self,
            self.tr("Confirm Delete"),
            self.tr("Delete preset “{name}”? This cannot be undone.").format(name=name)
        )
        if ret != QMessageBox.Yes:
            return

        # Remove and save
        filtered = [(n, t) for (n, t) in customs if n != name]
        self._save_custom_prompt_presets(filtered)
        self._refresh_prompt_preset_combo()
        QMessageBox.information(self, self.tr("Deleted"), self.tr("Preset deleted: {name}").format(name=name))


    # -----------
    # Status Bar
    # -----------
    def _create_statusbar(self) -> None:
        sb = QStatusBar(self)
        self.setStatusBar(sb)
        self.lbl_status = QLabel("", self)

        # mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        # self.lbl_time_current = QLabel("Current 00:00", self)
        # self.lbl_time_current.setFont(mono)

        # self.lbl_time_remaining = QLabel("Remaining -00:00", self)
        # self.lbl_time_remaining.setFont(mono)

        # --- NEW: progress bar & ETA ---
        self.pb = QProgressBar(self)
        self.pb.setMinimum(0); self.pb.setMaximum(100); self.pb.setValue(0)
        self.pb.setVisible(False)
        self.lbl_eta = QLabel("", self)
        self.lbl_eta.setVisible(False)

        # sb.addWidget(self.lbl_time_current)
        sb.addWidget(self.lbl_status, 1)
        sb.addWidget(self.pb)
        sb.addWidget(self.lbl_eta)
        # sb.addPermanentWidget(self.lbl_time_remaining)

    # -----------
    # Stylesheet (light)
    # -----------
    def _apply_light_qss(self) -> None:
        self.setStyleSheet("""
        QGroupBox {
            font-weight: 600;
            border: 1px solid palette(mid);
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
        }
        QPlainTextEdit {
            padding: 6px;
        }
        QToolBar { spacing: 6px; }
        QDockWidget::title {
            text-align: left;
            padding-left: 8px;
            padding-top: 3px;
            padding-bottom: 3px;
            font-size: 8pt;
            min-height: 20px;
        }
        """)

    # -----------
    # Helpers
    # -----------
    def _set_editor_defaults(self, editor: QPlainTextEdit, mono: bool, wrap: bool) -> None:
        if mono:
            editor.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        else:
            editor.setFont(QFont())
        editor.setLineWrapMode(QPlainTextEdit.WidgetWidth if wrap else QPlainTextEdit.NoWrap)

    def _update_audio_info_fields(self, d: dict[str, str]) -> None:
        self.lbl_info_file.setText(d.get("File", "-"))
        self.lbl_info_path.setText(d.get("Path", "-"))
        self.lbl_info_container.setText(d.get("Container", "-"))
        self.lbl_info_codec.setText(d.get("Codec", "-"))
        self.lbl_info_channels.setText(d.get("Channels", "-"))
        self.lbl_info_sr.setText(d.get("Sample rate", "-"))
        self.lbl_info_bitrate.setText(d.get("Bitrate", "-"))
        self.lbl_info_duration.setText(d.get("Duration", "-"))
        self.lbl_info_size.setText(d.get("File size", "-"))

    def _disable_actions_for_task(self, busy: bool) -> None:
        for act in [
            self.act_import, self.act_transcribe, # self.act_play_pause,
            self.act_save_txt, self.act_textops, self.act_export_pdf,
            self.act_save_result_as_txt,
            # self.act_openai_settings  # Hidden from end users
        ]:
            act.setEnabled(not busy)

    def _run_task(self, fn, **kwargs) -> WorkerSignals:
        """
        Run a function in the thread pool and wire it to GUI-safe signals.

        Returns:
            WorkerSignals: the same signals object passed into the background function.
        """
        signals = WorkerSignals()

        # Build kwargs to pass into the background function
        kwargs_to_pass = dict(kwargs)

        # Inject signals only if the function can accept it (or has **kwargs)
        params = inspect.signature(fn).parameters
        accepts_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        if 'signals' in params or accepts_var_kw:
            kwargs_to_pass['signals'] = signals

        # Ensure the background function receives the same signals instance.
        # kwargs.setdefault("signals", signals)

        task = TaskSpec(fn=fn, args=tuple(), kwargs=kwargs_to_pass)
        runnable = FunctionRunnable(task, signals)

        # GUI-safe wrapper to avoid crashing the UI thread if a slot raises.
        def safe(slot):
            def wrapper(*a, **k):
                try:
                    return slot(*a, **k)
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        QCoreApplication.translate("VoiceTransorMainWindow", "Error"),
                        str(e),
                    )
            return wrapper

        @safe
        def on_started():
            self._disable_actions_for_task(True)
            self._show_progress(True)
            self.lbl_status.setText(
                QCoreApplication.translate("VoiceTransorMainWindow", "Working…")
            )

        @safe
        def on_message(msg: str):
            if msg:
                self.lbl_status.setText(msg)

        @safe
        def on_progress(percent: int, secs_done: float, secs_total: float, eta_secs: float):
            self.pb.setValue(max(0, min(100, int(percent))))
            mm = int(eta_secs // 60)
            ss = int(eta_secs % 60)
            self.lbl_eta.setText(
                QCoreApplication.translate("VoiceTransorMainWindow", "ETA {mm:02d}:{ss:02d}")
                .format(mm=mm, ss=ss)
            )

        @safe
        def on_result(_res):
            # Result is handled by the caller (they connect signals.result).
            pass

        @safe
        def on_error(err: str):
            self._disable_actions_for_task(False)
            self._show_progress(False)
            self.act_cancel.setEnabled(False)
            self._stop_flag = None
            self.lbl_status.setText("")
            if err.strip() == "__CANCELLED__":
                QMessageBox.information(
                    self,
                    QCoreApplication.translate("VoiceTransorMainWindow", "Cancelled"),
                    QCoreApplication.translate("VoiceTransorMainWindow", "Transcription was cancelled."),
                )
            else:
                QMessageBox.critical(
                    self,
                    QCoreApplication.translate("VoiceTransorMainWindow", "Error"),
                    err,
                )

        @safe
        def on_finished():
            # CRITICAL: Only process finish if this task is still active
            # This prevents delayed signals from old tasks interfering with new ones
            if runnable not in self._active_tasks:
                log.warning("Received finished signal from non-active task, ignoring")
                return

            try:
                self._active_tasks.remove(runnable)
            except ValueError:
                pass

            # Only reset UI if no other tasks are running
            if len(self._active_tasks) == 0:
                self._disable_actions_for_task(False)
                self._show_progress(False)
                self.act_cancel.setEnabled(False)
                self._stop_flag = None
                self.lbl_status.setText("")
            else:
                log.debug(f"Other tasks still running ({len(self._active_tasks)}), keeping UI state")

        # Wire signals
        signals.started.connect(on_started)
        signals.message.connect(on_message)
        signals.progress.connect(on_progress)
        signals.result.connect(on_result)
        signals.error.connect(on_error)
        signals.finished.connect(on_finished)

        # Submit to the pool and track lifetime
#        self.thread_pool.start(runnable)
        self.pool.start(runnable)
        self._active_tasks.append(runnable)
        return signals


    def _default_txt_name(self, base_dir: Path) -> Path:
        return base_dir / f"VoiceTransor_transcript_{timestamp()}.txt"

    def _default_pdf_name(self, base_dir: Path) -> Path:
        return base_dir / f"VoiceTransor_result_{timestamp()}.pdf"

    def _show_progress(self, vis: bool) -> None:
        self.pb.setVisible(vis)
        self.lbl_eta.setVisible(vis)
        if not vis:
            self.pb.setValue(0)
            self.lbl_eta.setText("")


    def _refresh_info_and_status_colors(self, theme: str) -> None:
        """
        Re-apply the current app palette to:
        1) the auto-created QLabel(s) in the Audio Info form (left-hand labels),
        2) the status bar and its child labels.
        This fixes cases where those widgets kept an old palette after theme switch.
        """
        pal = QApplication.instance().palette()

        # 1) Audio Info form labels (auto-created by QFormLayout.addRow(str, widget))
        try:
            host = self.dock_info.widget()
            if host is not None:
                lay = host.layout()
                if isinstance(lay, QFormLayout):
                    for row in range(lay.rowCount()):
                        item = lay.itemAt(row, QFormLayout.ItemRole.LabelRole)
                        lbl = item.widget() if item is not None else None
                        if isinstance(lbl, QLabel):
                            lbl.setPalette(pal)
                    # Right-side value labels we created explicitly:
                    for item_role in (QFormLayout.ItemRole.FieldRole,):
                        for row in range(lay.rowCount()):
                            item = lay.itemAt(row, item_role)
                            w = item.widget() if item is not None else None
                            if isinstance(w, QLabel):
                                w.setPalette(pal)
        except Exception:
            pass

        # 2) Status bar and its children
        try:
            sb = self.statusBar()
            if sb is not None:
                sb.setPalette(pal)
                for child in sb.findChildren(QLabel):
                    child.setPalette(pal)
        except Exception:
            pass

    def _apply_saved_theme(self) -> None:
        """Read 'ui/theme' from settings and apply."""
        theme = str(self.settings.value("ui/theme", "dark"))
        self._apply_theme(theme, save=False)



    def _apply_theme(self, theme: str, save: bool = True) -> None:
        """Apply theme and update fonts similar to VS Code."""
        app = QApplication.instance()
        apply_theme(app, theme)
        self._current_theme = theme

        # VS Code–like fonts
        mono_family = pick_monospace_family()
        mono_font = QFont(mono_family, 10)
        self.txt_transcript.setFont(mono_font)
        self.txt_result.setFont(mono_font)

        # Refresh palettes of text widgets (transcript, result, audio info)
        text_widgets = []
        text_widgets += self.findChildren(QPlainTextEdit)
        text_widgets += self.findChildren(QTextEdit)
        text_widgets += self.findChildren(QTextBrowser)

        # choose palette per theme
        pal = app.palette() if theme == "dark" else app.style().standardPalette()

        for w in text_widgets:
            w.setPalette(pal)
            if hasattr(w, "viewport"):
                w.viewport().update()

        # Audio Info auto-created labels and our value labels
        try:
            host = self.dock_info.widget()
            if host and host.layout():
                for lbl in host.findChildren(QLabel):
                    lbl.setPalette(pal)
        except Exception:
            pass

        # Status bar labels
        sb = self.statusBar()
        if sb:
            sb.setPalette(pal)
            for lbl in sb.findChildren(QLabel):
                lbl.setPalette(pal)

        # Group boxes (ensure titles repaint after theme switch)
        for gb in self.findChildren(QGroupBox):
            gb.setPalette(pal)
            gb.update()

        # Ensure editors refresh their palette after a theme switch
        for w in (self.txt_transcript, self.txt_result):
            w.setPalette(pal)
            w.viewport().update()

        self._refresh_info_and_status_colors(theme)

        # Sync Windows system title bar to theme and force immediate repaint
        _apply_windows_titlebar_theme(self, theme == "dark")
        _force_titlebar_refresh(self)

        self.act_theme_dark.setChecked(theme == "dark")
        self.act_theme_light.setChecked(theme != "dark")
        if save:
            self.settings.setValue("ui/theme", theme)

        # Apply light theme QSS for dock widget titles
        if theme != "dark":
            self._apply_light_qss()

        self._apply_zoom() # ensure zoom ok after change theme
        self._set_icons()

    def _apply_zoom(self) -> None:
        """Apply current zoom percent to editor panes."""
        # Base size you prefer; align with the 10pt given to the editor in the theme
        base_pt = 12
        size_pt = max(8, int(round(base_pt * (self._zoom_pct / 100.0))))

        # Choose a monospace font (already have pick_monospace_family available)
        # try:
        #     from app.ui.theme import pick_monospace_family
        #     family = pick_monospace_family()
        # except Exception:
        family = self.font().family()

        f = QFont(family, size_pt)

        # Which controls participate in scaling?
        targets = []
        if hasattr(self, "txt_transcript"): targets.append(self.txt_transcript)
        if hasattr(self, "txt_result"):     targets.append(self.txt_result)
        if hasattr(self, "txt_prompt"):     targets.append(self.txt_prompt)

        for w in targets:
            w.setFont(f)
            # Make the view refresh immediately
            if hasattr(w, "viewport"):
                w.viewport().update()
            w.update()

    def _set_zoom(self, pct: int) -> None:
        """Clamp+save+apply zoom."""
        pct = max(80, min(300, int(pct)))  # limit to 80%~300%
        if pct == getattr(self, "_zoom_pct", 100):
            return
        self._zoom_pct = pct
        self.settings.setValue("ui/zoom_pct", pct)
        self._apply_zoom()



    # -----------
    # Slots / Handlers
    # -----------
    def on_import_audio(self) -> None:
        # Check if a task is running and ask user whether to stop it
        if len(self._active_tasks) > 0:
            reply = QMessageBox.question(
                self,
                self.tr("Warning"),
                self.tr("A task is running. Do you want to stop it and load new audio?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Stop current task
                if self._stop_flag is not None:
                    self._stop_flag.set()
                # Wait for task to finish (max 3 seconds)
                self.pool.waitForDone(3000)
                # Clear task list
                self._active_tasks.clear()
            else:
                return

        filters = self.tr("Audio files (*.wav *.mp3 *.m4a *.flac *.ogg *.aac);;All files (*.*)")
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Select Audio File"), self.last_dir, filters)
        if not file_path:
            return
        self._load_audio_file(Path(file_path))

    def _load_audio_file(self, p: Path) -> None:
        if not p.exists():
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"File does not exist: {Path}").format(path=p))
            return

        self.current_audio_path = p
        self.last_dir = str(p.parent)
        self.settings.setValue("last_dir", self.last_dir)

        try:
            info = ffprobe_info(p)
            summary = summarize_info(info, p)
        except FFprobeError as e:
            QMessageBox.critical(self, self.tr("ffprobe Error"), str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, self.tr("Unknown Error"), self.tr(f"Failed to read audio info: {e}").format(err=e))
            return

        self._update_audio_info_fields(summary)
        self.setWindowTitle(f"VoiceTransor {self.version} — {p.name}")
        self.statusBar().showMessage(self.tr(f"Loaded: {p.name}").format(name=p.name), 3000)

    # comment audio replay & waveform
    # def on_play_pause(self) -> None:
    #     QMessageBox.information(self, self.tr("Play/Pause"), self.tr("To be implemented."))

    def on_transcribe(self) -> None:
        if not self.current_audio_path:
            QMessageBox.information(self, self.tr("Info"), self.tr("Please import an audio file first."))
            return

        # Check if a transcription task is already running
        if len(self._active_tasks) > 0:
            QMessageBox.warning(
                self,
                self.tr("Busy"),
                self.tr("A transcription task is already running. Please wait for it to complete.")
            )
            return

        dlg = TranscribeOptionsDialog(
            self,
            model=str(self.opt_model),
            language=str(self.opt_lang),
            device=str(self.opt_device),
            models_dir=str(self.opt_models_dir),
        )
        if dlg.exec() != QDialog.Accepted:
            return
        model, language, device, models_dir, include_ts = dlg.values()

        # Save settings
        self.opt_model, self.opt_lang, self.opt_device, self.opt_models_dir = model, language, device, models_dir
        self.settings.setValue("stt/model", model)
        self.settings.setValue("stt/lang", language)
        self.settings.setValue("stt/device", device)
        self.settings.setValue("stt/models_dir", str(models_dir))

        # First-time download notice
        if not is_model_cached(model, models_dir):
            ok = QMessageBox.question(
                self, self.tr("Download Model"),
                self.tr(f"Model '{model}' is not cached yet.\nDownload to:\n{models_dir}\n\nStart now?"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if ok != QMessageBox.Yes:
                return

        # Prepare options/configs
        t_opt = TranscribeOptions(
            model=model,
            language=(language or None),
            device=device,
            models_dir=models_dir,
            include_timestamps=bool(include_ts),
        )
        c_cfg = ChunkConfig(
            target_s=float(self.settings.value("chunk/target_s", 30.0)),
            search_window_s=float(self.settings.value("chunk/search_window_s", 5.0)),
            min_chunk_s=float(self.settings.value("chunk/min_chunk_s", 15.0)),
            max_chunk_s=float(self.settings.value("chunk/max_chunk_s", 40.0)),
            min_silence_len_ms=int(self.settings.value("chunk/min_silence_len_ms", 300)),
            silence_thresh_dbfs=int(self.settings.value("chunk/silence_thresh_dbfs", -35)),
        )
        th_cfg = ThermalConfig(
            enabled=bool(self.settings.value("thermal/enabled", True)),
            high_c=float(self.settings.value("thermal/high_c", 85.0)),
            critical_c=float(self.settings.value("thermal/critical_c", 95.0)),
            cooldown_ms_base=int(self.settings.value("thermal/cooldown_ms_base", 200)),
            cooldown_ms_hot=int(self.settings.value("thermal/cooldown_ms_hot", 800)),
            poll_ms=int(self.settings.value("thermal/poll_ms", 1000)),
            fallback_use_cpu_percent=bool(self.settings.value("thermal/fallback_use_cpu_percent", True)),
            cpu_hot_pct=int(self.settings.value("thermal/cpu_hot_pct", 85)),
        )

        # Stop flag & UI wiring
        self._stop_flag = threading.Event()
        self.act_cancel.setEnabled(True)
        self._show_progress(True)

        # CRITICAL: Process all pending Qt events before starting new transcription
        # This ensures any delayed signals from previous transcription are handled
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

        # CRITICAL: Force GPU cleanup before starting new transcription
        try:
            import torch
            import gc
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                gc.collect()
                log.debug("GPU memory cleared before new transcription")
        except Exception as e:
            log.warning(f"Failed to clear GPU memory: {e}")

        # AGGRESSIVE RESET: Clear text box completely
        try:
            self.txt_transcript.clear()
            self.txt_transcript.setPlainText("")
            log.debug("Text box cleared for new transcription")
        except Exception as e:
            log.warning(f"Failed to clear text box: {e}")

        QCoreApplication.processEvents()  # Process clear events

        signals = self._run_task(
            transcribe_chunked,
            audio_path=self.current_audio_path,
            t_opt=t_opt,
            c_cfg=c_cfg,
            th_cfg=th_cfg,
            stop_flag=self._stop_flag,
            # signals=None,       # run-task creates fresh signals; we still get them wired
            resume=True,
        )

        # Connect signals immediately after _run_task but before task actually runs
        signals.partial_text.connect(self._on_partial_transcript)
        signals.bootstrap_text.connect(self._on_bootstrap_transcript)

        def on_res(text: str):
            # log.debug("on_res() of transcribe, got text:")
            # log.debug(text)
            # if text.strip() :
            #     self.txt_transcript.setPlainText(text)
            
            # txt_transcript should be filled by above 2 signals: partial & bootstrap
            # so, no need to update here again to avoid update with only last part(if resume).

            QMessageBox.information(
                self, QCoreApplication.translate("VoiceTransorMainWindow", "Transcription Finished"),
                QCoreApplication.translate("VoiceTransorMainWindow", "Completed with model '{model}' on device '{device}'.").format(
                    model=model, device=pick_device(device)
                )
            )
            self._disable_actions_for_task(False)
            self._show_progress(False)
            self.act_cancel.setEnabled(False)
            self.lbl_status.setText("")

        signals.result.connect(on_res)

    def _on_bootstrap_transcript(self, text: str) -> None:
        """Fill transcript with previously transcribed text when resuming."""
        try:
            log.debug("got previously trans text")
            log.debug(text)
            self.txt_transcript.setPlainText(text)
            # to end, cause error
            # self.txt_transcript.moveCursor(self.txt_transcript.textCursor().End)
        except Exception as e:
            log.debug(e)
            pass

    def _on_partial_transcript(self, text: str) -> None:
        """Append new chunk text to transcript in real time."""
        try:
            # Use insertPlainText instead of appendPlainText for better stability
            from PySide6.QtGui import QTextCursor
            cursor = self.txt_transcript.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(text)
            cursor.insertText("\n")
            self.txt_transcript.setTextCursor(cursor)
            # Ensure the update is processed
            self.txt_transcript.ensureCursorVisible()
        except Exception as e:
            log.error(f"Failed to append transcript text: {e}")

    def on_cancel_transcription(self) -> None:
        if self._stop_flag is not None:
            self._stop_flag.set()
            self.lbl_status.setText(QCoreApplication.translate("VoiceTransorMainWindow", "Cancelling…"))

    def on_save_transcript_txt(self) -> None:
        text = self.txt_transcript.toPlainText().strip()
        if not text:
            QMessageBox.information(self, self.tr("Info"), self.tr("No transcript text to save."))
            return

        base_dir = Path(self.last_dir or str(Path.home()))
        default_name = self._default_txt_name(base_dir)
        out_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Transcript as TXT"), str(default_name), self.tr("Text files (*.txt);;All files (*.*)")
        )
        if not out_path:
            return
        try:
            Path(out_path).write_text(text, encoding="utf-8")
            QMessageBox.information(self, self.tr("Saved"), self.tr("Saved to: {path}").format(path=out_path))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Write Failed"), str(e))

    def on_openai_settings(self) -> None:
        dlg = OpenAISettingsDialog(
            self,
            api_key=str(self.openai_key or ""),
            model=str(self.openai_model),
            project=str(self.openai_project or ""),
        )
        if dlg.exec() != QDialog.Accepted:
            return
        key, project, model = dlg.values()
        self.openai_key = key
        self.openai_project = project or ""
        self.openai_model = model or "gpt-4o-mini"
        self.settings.setValue("openai/api_key", self.openai_key)
        self.settings.setValue("openai/project", self.openai_project)
        self.settings.setValue("openai/model", self.openai_model)

    def on_run_textops(self) -> None:
        src = self.txt_transcript.toPlainText().strip()
        if not src:
            QMessageBox.information(self, self.tr("Info"), self.tr("Please transcribe or paste text first."))
            return

        # User instruction
        user_prompt = self.txt_prompt.toPlainText().strip()
        if not user_prompt:
            # fall back to classic summarize if empty
            user_prompt = "Summarize the source text into clear, concise bullet points."

        # Show options dialog for LLM model selection
        from app.ui.options_dialogs import TextOpsOptionsDialog
        current_model = self.settings.value("ollama/model", "llama3.1:8b")
        base_url = self.settings.value("ollama/base_url", "http://localhost:11434")

        dlg = TextOpsOptionsDialog(self, current_model, base_url)
        if dlg.exec() != QDialog.Accepted:
            return  # User canceled

        # Get selected model from dialog
        llm_model = dlg.values()
        if not llm_model:
            llm_model = "llama3.1:8b"

        # Save model selection
        self.settings.setValue("ollama/model", llm_model)

        # Double-check Ollama availability (in case it stopped after dialog opened)
        from app.core.ai.ollama_textops import check_ollama_available
        is_available, status_msg = check_ollama_available(base_url)
        if not is_available:
            QMessageBox.critical(
                self,
                self.tr("Ollama Not Available"),
                self.tr(
                    "Ollama service is not running.\n\n"
                    "{status}\n\n"
                    "Please ensure Ollama is started before running text operations."
                ).format(status=status_msg)
            )
            return

        # UI state
        self._stop_flag = threading.Event()
        self._show_progress(True)
        self.act_cancel.setEnabled(True)

        # background task - use Ollama
        from app.core.ai.ollama_textops import run_text_op
        signals = self._run_task(
            run_text_op,
            transcript=src,
            prompt=user_prompt,
            model=llm_model,
            base_url=self.settings.value("ollama/base_url", "http://localhost:11434"),
        )

        def _on_ok(res):
            log.debug(res)
            html = res.get("html")
            md = res.get("markdown") or ""
            plain = res.get("plain") or ""


            if html:
                self.txt_result.setHtml(html)
            elif md:
                # simple fallback: wrap as <pre> to avoid losing structure
                self.txt_result.setPlainText(md)
            else:
                self.txt_result.setPlainText(plain)

            self.statusBar().showMessage(self.tr("Text operation completed."), 5000)

        def _on_err(msg):
            QMessageBox.critical(self, self.tr("Error"), str(msg))

        def _on_fin():
            self._show_progress(False)
            self.act_cancel.setEnabled(False)

        signals.result.connect(_on_ok)
        signals.error.connect(_on_err)
        signals.finished.connect(_on_fin)

    def _pick_cjk_font_family(self) -> str:
        """
        Pick a CJK-friendly font to avoid missing glyphs in PDF.
        Tries several common families; falls back to the app font.
        """
        candidates = [
            "Microsoft YaHei UI", "Microsoft YaHei",   # Windows
            "PingFang SC", "Heiti SC",                # macOS
            "Noto Sans CJK SC", "Noto Sans CJK",      # cross-platform
            "SimSun", "SimHei",
            "Arial Unicode MS",
        ]
        db = QFontDatabase()
        for fam in candidates:
            if fam in db.families():
                return fam
        return self.font().family()

    def on_export_pdf(self) -> None:
        """Export the content of Result editor to a PDF (WYSIWYG)."""
        if not hasattr(self, "txt_result"):
            QMessageBox.information(self, self.tr("Info"), self.tr("No result to export."))
            return
        html = self.txt_result.toHtml().strip()
        if not html:
            QMessageBox.information(self, self.tr("Info"), self.tr("No result to export."))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Result as PDF"),
            self._last_dir_or_home("result.pdf"),
            self.tr("PDF Files (*.pdf)")
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        # Prepare printer
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageMargins(QMarginsF(18, 18, 18, 18), QPageLayout.Point)  # 18pt ≈ 0.25 inch

        # Prepare document (inject a CJK-capable font to avoid squares)
        from PySide6.QtGui import QTextDocument
        doc = QTextDocument()
        # inject default font & optional CSS
        family = self._pick_cjk_font_family()
        base_pt = 10.5
        doc.setDefaultFont(QFont(family, base_pt))
        # Ensure body uses our font even if original HTML didn't specify
        css = f"body {{ font-family: '{family}'; font-size: {base_pt}pt; }}"
        doc.setDefaultStyleSheet(css)
        doc.setHtml(html)

        # Print ()
        try:
            doc.print(printer)      # PySide6 
        except AttributeError:
            doc.print_(printer)     

        QMessageBox.information(self, self.tr("Exported"), self.tr("PDF saved: {path}").format(path=path))
        self._remember_last_dir(os.path.dirname(path))

    def on_save_result_txt(self) -> None:
        """Save Result as plain text (.txt)."""
        if not hasattr(self, "txt_result"):
            QMessageBox.information(self, self.tr("Info"), self.tr("No result to save."))
            return
        text = self.txt_result.toPlainText()
        if not text.strip():
            QMessageBox.information(self, self.tr("Info"), self.tr("No result to save."))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Result as Text"),
            self._last_dir_or_home("result.txt"),
            self.tr("Text Files (*.txt);;All Files (*.*)")
        )
        if not path:
            return
        if not os.path.splitext(path)[1]:
            path += ".txt"

        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        QMessageBox.information(self, self.tr("Exported"), self.tr("Text saved: {path}").format(path=path))
        self._remember_last_dir(os.path.dirname(path))

    def _last_dir_or_home(self, default_name: str) -> str:
        d = self.settings.value("paths/last_dir", "")
        if not d or not os.path.isdir(d):
            d = os.path.expanduser("~")
        return os.path.join(d, default_name)

    def _remember_last_dir(self, d: str) -> None:
        if d and os.path.isdir(d):
            self.settings.setValue("paths/last_dir", d)

    def on_about(self) -> None:
        QMessageBox.information(
            self,
            self.tr("About VoiceTransor"),
            self.tr(
                "VoiceTransor {version}\n"
                "Speech-to-Text & Text Assistant\n\n"
                "Features:\n"
                "- Import audio files\n"
                "- Local transcription (Whisper, with resume support)\n"
                "- AI-powered text processing \n"
                "- Export results (TXT / PDF)\n\n"
                "Supported Platforms: Windows, macOS"
            ).format(version=self.version),
        )

    def on_contact(self) -> None:
        contact_text = self.tr(
            "VoiceTransor is an open-source project.\n\n"
            "For support, feedback, or collaboration:\n"
            "- Email: voicetransor@gmail.com\n"
            "- GitHub: https://github.com/leonshen/VoiceTransor.git\n"
        )
            # "- Upwork: https://www.upwork.com/freelancers/yourprofile\n"

        QMessageBox.information(
            self,
            self.tr("Contact"),
            contact_text
        )

    # ---- View handlers ----
    def on_toggle_info_dock(self) -> None:
        want = self.act_show_info_dock.isChecked()
        if hasattr(self, "dock_info"):
            self.dock_info.setVisible(want)

    def on_toggle_prompt_dock(self) -> None:
        want = self.act_show_prompt_dock.isChecked()
        if hasattr(self, "dock_prompt"):
            self.dock_prompt.setVisible(want)

    def on_toggle_wrap(self) -> None:
        wrap = self.act_wrap.isChecked()
        self.txt_transcript.setLineWrapMode(QPlainTextEdit.WidgetWidth if wrap else QPlainTextEdit.NoWrap)
        self.txt_result.setLineWrapMode(QPlainTextEdit.WidgetWidth if wrap else QPlainTextEdit.NoWrap)

    def on_toggle_mono_transcript(self) -> None:
        mono = self.act_mono_transcript.isChecked()
        if mono:
            self.txt_transcript.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        else:
            self.txt_transcript.setFont(QFont())

    def on_zoom_in(self) -> None:
        self._set_zoom(self._zoom_pct + 10)

    def on_zoom_out(self) -> None:
        self._set_zoom(self._zoom_pct - 10)

    def on_zoom_reset(self) -> None:
        self._set_zoom(100)

    # ---- Language switching & retranslation ----
    def on_change_language(self, locale_code: str) -> None:
        actual = self.i18n.install(locale_code)
        self.i18n.write_locale_to_settings(locale_code)
        self.update_language_checks(actual)
        self.retranslate_ui()

    def update_language_checks(self, actual: str) -> None:
        if actual == "en":
            self.act_lang_en.setChecked(True)
        elif actual.lower().startswith("zh"):
            self.act_lang_zh.setChecked(True)
        else:
            self.act_lang_system.setChecked(True)

    def retranslate_ui(self) -> None:
        """Set all user-visible strings (called on startup and language change)."""
        # Menus
        self.menu_file.setTitle(self.tr("File"))
        # comment audio replay & waveform
        # self.menu_play.setTitle(self.tr("Playback"))
        self.menu_tools.setTitle(self.tr("Tools"))
        self.menu_view.setTitle(self.tr("View"))
        self.menu_lang.setTitle(self.tr("Language"))
        self.menu_help.setTitle(self.tr("Help"))

        # Menu actions
        self.act_import.setText(self.tr("Import Audio…"))
        # comment audio replay & waveform
        # self.act_play_pause.setText(self.tr("Play/Pause"))
        self.act_transcribe.setText(self.tr("Transcribe to Text"))

        self.act_cancel.setText(QCoreApplication.translate("VoiceTransorMainWindow", "Cancel Transcription"))

        self.act_save_txt.setText(self.tr("Save Transcript as TXT…"))
        self.act_textops.setText(self.tr("Run Text Operation"))
        self.act_export_pdf.setText(self.tr("Export result as PDF…"))
        self.act_save_result_as_txt.setText(self.tr("Save Result as TXT…"))
        # self.act_openai_settings.setText(self.tr("OpenAI Settings…"))  # Hidden from end users
        self.act_about.setText(self.tr("About VoiceTransor"))
        self.act_contact.setText(self.tr("Contact"))
        self.act_exit.setText(self.tr("Exit"))

        self.act_show_info_dock.setText(self.tr("Show Audio Info Dock"))
        self.act_show_prompt_dock.setText(self.tr("Show Prompt Dock"))
        self.act_wrap.setText(self.tr("Word Wrap (Transcript/Result)"))
        self.act_mono_transcript.setText(self.tr("Monospace Font for Transcript"))
        self.act_zoom_in.setText(self.tr("Zoom In"))
        self.act_zoom_out.setText(self.tr("Zoom Out"))
        self.act_zoom_reset.setText(self.tr("Reset Zoom"))

        # Language submenu actions
        self.act_lang_system.setText(self.tr("System Default"))
        self.act_lang_en.setText(self.tr("English"))
        self.act_lang_zh.setText(self.tr("简体中文"))

        self.menu_theme.setTitle(QCoreApplication.translate("VoiceTransorMainWindow", "Theme"))
        self.act_theme_dark.setText(QCoreApplication.translate("VoiceTransorMainWindow", "Dark"))
        self.act_theme_light.setText(QCoreApplication.translate("VoiceTransorMainWindow", "Light"))


        # Group titles & placeholders
        self.grp_transcript.setTitle(self.tr("Transcript"))
        self.txt_transcript.setPlaceholderText(self.tr("Transcript will appear here."))
        self.grp_result.setTitle(self.tr("Result"))
        self.txt_result.setPlaceholderText(self.tr("Result will appear here."))

        # Docks titles
        # self.dock_wave.setWindowTitle(self.tr("Waveform"))
        self.dock_info.setWindowTitle(self.tr("Audio Info"))

    def closeEvent(self, event):
        # If no background work, close immediately.
        if not getattr(self, "_active_tasks", []):
            return super().closeEvent(event)

        # Ask the user; you can skip the dialog if you prefer always-cancel
        resp = QMessageBox.question(
            self,
            QCoreApplication.translate("VoiceTransorMainWindow", "Quit"),
            QCoreApplication.translate(
                "VoiceTransorMainWindow",
                "There is a running task. Cancel and exit?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            event.ignore()
            return

        # Cooperatively stop current task(s)
        try:
            if getattr(self, "_stop_flag", None) is not None:
                self._stop_flag.set()
        except Exception:
            pass

        # Prevent new tasks, clear queue, and wait a bit for workers to finish
        try:
            self.pool.clear()
            self.pool.waitForDone(5000)  # 5s grace; adjust if you like
        except Exception:
            pass

        return super().closeEvent(event)