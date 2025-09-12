# -*- coding: utf-8 -*-
"""Thin i18n manager for installing/uninstalling Qt translators.

This module centralizes:
- Reading/writing locale preference via QSettings.
- Installing a QTranslator for specific locale (if a .qm exists).
- Graceful fallback to English (source language) when .qm missing.

Supported locale codes:
- "system" : follow OS locale (resolve to e.g., "zh_CN", "en_US"...)
- "en"     : force English (no translator needed, because source text is English)
- "zh_CN"  : Simplified Chinese (requires app/i18n/locales/voicetransor_zh_CN.qm)
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QCoreApplication, QLocale, QTranslator, QSettings


class I18nManager:
    """Manage a single QTranslator instance for the app."""

    def __init__(self) -> None:
        self.translator: Optional[QTranslator] = None
        # Where compiled .qm files live
        self.locales_dir = Path(__file__).resolve().parent / "locales"

    # ---------------- Settings ----------------
    def read_locale_from_settings(self) -> str:
        """Return stored locale code or default 'system'."""
        s = QSettings("VoiceTransor", "VoiceTransor")
        return str(s.value("ui/locale", "system"))

    def write_locale_to_settings(self, locale_code: str) -> None:
        """Persist preferred locale code."""
        s = QSettings("VoiceTransor", "VoiceTransor")
        s.setValue("ui/locale", locale_code)

    # ---------------- Install/Uninstall ----------------
    def install(self, locale_code: str) -> str:
        """Install translator for the given locale code.

        Args:
            locale_code: "system" | "en" | "zh_CN"

        Returns:
            The actual installed locale code (may differ if fallback applied).
        """
        if self.translator:
            QCoreApplication.instance().removeTranslator(self.translator)
            self.translator = None

        if locale_code == "system":
            qloc = QLocale.system().name()  # e.g., "zh_CN"
            locale_code = qloc if qloc else "en"

        # English is source language → no translator needed.
        if locale_code.lower().startswith("en"):
            return "en"

        # Try to load .qm for non-English.
        qm_name = f"voicetransor_{locale_code}.qm"
        qm_path = self.locales_dir / qm_name
        if qm_path.exists():
            tr = QTranslator()
            if tr.load(str(qm_path)):
                QCoreApplication.instance().installTranslator(tr)
                self.translator = tr
                return locale_code

        # Fallback to English (no translator).
        return "en"
