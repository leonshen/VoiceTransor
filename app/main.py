# -*- coding: utf-8 -*-
"""Application entry point with i18n bootstrap."""
from PySide6.QtWidgets import QApplication
from app.ui.main_window import VoiceTransorMainWindow
from app.i18n.manager import I18nManager
from app._version import __version__
import sys

import logging, os, sys

# ---- logging setup ----
LOGGER_NAME = "voicetransor"          # one place to reuse
log = logging.getLogger(LOGGER_NAME)  # module-level logger

def _setup_logging() -> None:
    level_name = os.getenv("VOICETRANSOR_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,  # set to logging.DEBUG to see debug logs
        stream=sys.stdout,  # send to the VS Code terminal
        format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    _setup_logging()

    log.debug("hello debug")
    log.info("hello info")
    log.warning("hello warn")

    app = QApplication(sys.argv)

    # Load preferred locale before constructing UI.
    i18n = I18nManager()
    preferred = i18n.read_locale_from_settings()
    i18n.install(preferred)

    win = VoiceTransorMainWindow(version=__version__, i18n=i18n)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
