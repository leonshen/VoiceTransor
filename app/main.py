# -*- coding: utf-8 -*-
"""Application entry point with i18n bootstrap."""
from PySide6.QtWidgets import QApplication
from app.ui.main_window import VoiceTransorMainWindow
from app.i18n.manager import I18nManager
from app._version import __version__
import sys

import logging, os, sys
from pathlib import Path

# ---- logging setup ----
LOGGER_NAME = "voicetransor"          # one place to reuse
log = logging.getLogger(LOGGER_NAME)  # module-level logger

def _fix_stdout_for_frozen_app() -> None:
    """
    Fix stdout/stderr for PyInstaller GUI apps.
    When console=False, sys.stdout/stderr are None, causing crashes.
    """
    if sys.stdout is None or sys.stderr is None:
        # Redirect to log file in user's temp directory
        log_dir = Path.home() / ".voicetransor" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"

        # Open in append mode so we keep history
        sys.stdout = open(log_file, "a", encoding="utf-8", buffering=1)
        sys.stderr = sys.stdout

def _setup_logging() -> None:
    level_name = os.getenv("VOICETRANSOR_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Choose output stream: stdout for dev, file for frozen app
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        log_dir = Path.home() / ".voicetransor" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "voicetransor.log"

        # Keep last 5 log files
        import glob
        log_files = sorted(glob.glob(str(log_dir / "voicetransor.*.log")))
        if len(log_files) >= 5:
            for old_log in log_files[:-4]:
                try:
                    os.remove(old_log)
                except:
                    pass

        # Rotate current log if it exists
        if log_file.exists():
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file.rename(log_dir / f"voicetransor.{timestamp}.log")

        handler = logging.FileHandler(log_file, encoding="utf-8")
    else:
        # Running from source
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%H:%M:%S"
    ))

    logging.basicConfig(
        level=level,
        handlers=[handler]
    )


def main() -> int:
    # Must fix stdout BEFORE any logging or print statements
    _fix_stdout_for_frozen_app()
    _setup_logging()

    # log.debug("hello debug")
    # log.info("hello info")
    # log.warning("hello warn")

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
