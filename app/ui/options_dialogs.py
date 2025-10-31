# -*- coding: utf-8 -*-
"""Small option dialogs (Transcribe, OpenAI settings) with i18n-ready labels."""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QCoreApplication, QTimer
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QFileDialog, QWidget, QLabel, QHBoxLayout, QCheckBox
)

COMMON_LANGS = [
    ("Auto detect", ""),
    ("Chinese", "zh"),
    ("English", "en"),
    ("日本語", "ja"),
    ("한국어", "ko"),
    ("Español", "es"),
    ("Français", "fr"),
    ("Deutsch", "de"),
]


class TranscribeOptionsDialog(QDialog):
    """Dialog to select Whisper model/language/device/models-dir."""

    def __init__(self, parent: QWidget | None, model: str, language: str, device: str, models_dir: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Transcription Options"))
        self.setModal(True)

        lay = QVBoxLayout(self)

        form = QFormLayout()
        self.cmb_model = QComboBox(self)
        self.cmb_model.addItems(["tiny", "base", "small"])
        if model in ["tiny", "base", "small"]:
            self.cmb_model.setCurrentText(model)

        self.cmb_lang = QComboBox(self)
        for label, code in COMMON_LANGS:
            self.cmb_lang.addItem(self.tr(label), code)
        idx = next((i for i in range(self.cmb_lang.count()) if self.cmb_lang.itemData(i) == language), 0)
        self.cmb_lang.setCurrentIndex(idx)

        self.chk_srt = QCheckBox(QCoreApplication.translate("TranscribeOptionsDialog", "Include timestamps (SRT style)"), self)
        self.chk_srt.setChecked(False)

        self.cmb_device = QComboBox(self)
        self.cmb_device.addItems(["auto", "cpu", "cuda", "mps"])
        if device in ["auto", "cpu", "cuda", "mps"]:
            self.cmb_device.setCurrentText(device)

        self.ed_models_dir = QLineEdit(models_dir, self)
        btn_browse = QPushButton(self.tr("Browse…"), self)
        row_models = QHBoxLayout()
        row_models.addWidget(self.ed_models_dir, 1)
        row_models.addWidget(btn_browse, 0)

        form.addRow(self.tr("Model:"), self.cmb_model)
        form.addRow(self.tr("Device:"), self.cmb_device)
        form.addRow(self.tr("Language:"), self.cmb_lang)
        form.addRow(self.tr("srt:"), self.chk_srt)
        form.addRow(self.tr("Models directory:"), QWidget(self))
        lay.addLayout(form)
        lay.addLayout(row_models)

        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        lay.addWidget(self.btns)

        btn_browse.clicked.connect(self._on_browse)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)

    def _on_browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, self.tr("Select Models Directory"), self.ed_models_dir.text())
        if d:
            self.ed_models_dir.setText(d)

    def values(self) -> tuple[str, str, str, Path, bool]:
        """Return (model, language, device, models_dir, include_timestamps)."""
        model = self.cmb_model.currentText()
        language = self.cmb_lang.currentData() or ""
        device = self.cmb_device.currentText()
        models_dir = Path(self.ed_models_dir.text())
        include_ts = bool(self.chk_srt.isChecked())
        return model, language, device, models_dir, include_ts


class OpenAISettingsDialog(QDialog):
    """Dialog to configure OpenAI API key, Project ID, and model name."""

    def __init__(self, parent: QWidget | None, api_key: str, model: str, project: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("OpenAI Settings"))
        lay = QVBoxLayout(self)
        form = QFormLayout()

        # Input fields (order: Key -> Project -> Model)
        self.ed_key = QLineEdit(api_key, self)
        self.ed_key.setEchoMode(QLineEdit.Password)

        self.ed_project = QLineEdit(project or "", self)
        self.ed_project.setPlaceholderText(self.tr("e.g. proj_abc123 (leave empty to skip)"))

        self.ed_model = QLineEdit(model or "gpt-4o-mini", self)

        # Display order
        form.addRow(self.tr("API Key:"), self.ed_key)
        form.addRow(self.tr("Project ID:"), self.ed_project)
        form.addRow(self.tr("Model:"), self.ed_model)

        tip = QLabel(self.tr("Tip: You can also set OPENAI_API_KEY (and optional OPENAI_PROJECT) in environment."), self)
        tip.setStyleSheet("color: palette(mid);")

        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        lay.addLayout(form)
        lay.addWidget(tip)
        lay.addWidget(self.btns)

        # Tab order: key -> project -> model
        self.setTabOrder(self.ed_key, self.ed_project)
        self.setTabOrder(self.ed_project, self.ed_model)

        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)

    def values(self) -> tuple[str, str, str]:
        """Return (key, project, model) in that order."""
        return (
            self.ed_key.text().strip(),
            self.ed_project.text().strip(),
            self.ed_model.text().strip(),
        )


class TextOpsOptionsDialog(QDialog):
    """Dialog to configure text operations with Ollama (LLM model selection)."""

    def __init__(self, parent: QWidget | None, llm_model: str, base_url: str = "http://localhost:11434") -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Text Operations Options"))
        self.setModal(True)
        self.base_url = base_url

        lay = QVBoxLayout(self)
        form = QFormLayout()

        # LLM Model selection (editable ComboBox)
        self.cmb_llm_model = QComboBox(self)
        self.cmb_llm_model.setEditable(True)
        self.cmb_llm_model.addItems([
            "llama3.1:8b",
            "qwen2.5:7b",
            "gemma2:9b",
        ])
        self.cmb_llm_model.setCurrentText(llm_model)

        # Ollama status indicator row
        status_row = QHBoxLayout()
        self.lbl_ollama_status = QLabel("●")
        self.lbl_ollama_status.setStyleSheet("color: gray; font-size: 16px;")
        self.lbl_ollama_status.setToolTip(self.tr("Ollama service status"))
        self.lbl_status_text = QLabel(self.tr("Checking..."))
        self.lbl_status_text.setStyleSheet("color: palette(mid);")
        status_row.addWidget(self.lbl_ollama_status)
        status_row.addWidget(self.lbl_status_text, 1)

        # Help button
        btn_help = QPushButton(self.tr("? Setup Guide"))
        btn_help.clicked.connect(self._on_help)

        form.addRow(self.tr("LLM Model:"), self.cmb_llm_model)
        form.addRow(self.tr("Status:"), QWidget(self))

        lay.addLayout(form)
        lay.addLayout(status_row)
        lay.addWidget(btn_help)

        # Info label
        info = QLabel(
            self.tr("Note: Ensure Ollama is installed and running. See Setup Guide for details."),
            self
        )
        info.setStyleSheet("color: palette(mid);")
        info.setWordWrap(True)
        lay.addWidget(info)

        # Dialog buttons
        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        lay.addWidget(self.btns)

        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)

        # Check Ollama status on init and periodically
        self._check_ollama_status()
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._check_ollama_status)
        self._status_timer.start(3000)  # Check every 3 seconds

    def _check_ollama_status(self) -> None:
        """Check Ollama service status and update indicator."""
        try:
            from app.core.ai.ollama_textops import check_ollama_available
            is_available, status_msg = check_ollama_available(self.base_url)

            if is_available:
                self.lbl_ollama_status.setStyleSheet("color: green; font-size: 16px;")
                self.lbl_status_text.setText(self.tr("Ollama is running"))
                self.lbl_status_text.setStyleSheet("color: green;")
            else:
                self.lbl_ollama_status.setStyleSheet("color: red; font-size: 16px;")
                self.lbl_status_text.setText(self.tr("Ollama is not running"))
                self.lbl_status_text.setStyleSheet("color: red;")
        except Exception:
            self.lbl_ollama_status.setStyleSheet("color: gray; font-size: 16px;")
            self.lbl_status_text.setText(self.tr("Status unknown"))
            self.lbl_status_text.setStyleSheet("color: gray;")

    def _on_help(self) -> None:
        """Show Ollama setup guide."""
        from pathlib import Path
        import subprocess
        import sys

        # Try to find the guide file
        guide_file = Path("docs/OLLAMA_SETUP_GUIDE.md")
        guide_file_cn = Path("docs/OLLAMA_SETUP_GUIDE_CN.md")

        # Prefer language-specific version if available
        if guide_file_cn.exists():
            file_to_open = guide_file_cn
        elif guide_file.exists():
            file_to_open = guide_file
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                self.tr("Setup Guide Not Found"),
                self.tr("Could not find docs/OLLAMA_SETUP_GUIDE.md file.")
            )
            return

        # Open the guide file with default application
        try:
            if sys.platform == "win32":
                subprocess.Popen(["cmd", "/c", "start", "", str(file_to_open)], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(file_to_open)])
            else:
                subprocess.Popen(["xdg-open", str(file_to_open)])
        except Exception:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                self.tr("Setup Guide"),
                self.tr("Please open the file manually: {}").format(str(file_to_open))
            )

    def closeEvent(self, event) -> None:
        """Stop the status timer when dialog closes."""
        if hasattr(self, '_status_timer'):
            self._status_timer.stop()
        super().closeEvent(event)

    def values(self) -> str:
        """Return selected LLM model."""
        return self.cmb_llm_model.currentText().strip()
