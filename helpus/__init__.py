import logging.config
import os


def _detect_or_install_qt():
    """
    Return the QT_API name for the Qt binding already present in the environment.
    Priority: PyQt6 > PySide6 > PyQt5 > PySide2.
    If none is found, PySide6 is installed automatically.
    """
    import importlib.util

    candidates = [
        ("pyqt6",   "PyQt6"),
        ("pyside6", "PySide6"),
        ("pyqt5",   "PyQt5"),
        ("pyside2", "PySide2"),
    ]
    for api_name, module_name in candidates:
        if importlib.util.find_spec(module_name) is not None:
            return api_name

    # No Qt binding found — install PySide6 as the fallback.
    import subprocess
    import sys
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "PySide6-Essentials"],
        stdout=subprocess.DEVNULL,
    )
    return "pyside6"


# Respect an existing QT_API set by the host application; otherwise auto-detect.
os.environ.setdefault("QT_API", _detect_or_install_qt())


# Do not Import Stuff from 'module' here because will raise ImportError because of Circular import
def not_used(item):
    """Suppress linter warnings for intentionally unused variables."""
    pass


# Define Log File
helpus_log_file = os.path.join(os.path.dirname(__file__), "HelpUs.log")

# CleanUp Existing LogFile
if os.path.exists(helpus_log_file):
    try:
        os.remove(helpus_log_file)
    except Exception as don_t_care:
        not_used(don_t_care)

__all__ = ["HelpUs", "get_qtconsole_object", "setup_breakpoint", "setup_breakpoint_hook"]


def _lazy_imports():
    from helpus.source.core import (
        get_qtconsole_object,
        HelpUs,
        setup_breakpoint,
        setup_breakpoint_hook,
    )

    globals().update(
        {
            "HelpUs": HelpUs,
            "get_qtconsole_object": get_qtconsole_object,
            "setup_breakpoint": setup_breakpoint,
            "setup_breakpoint_hook": setup_breakpoint_hook,
        }
    )


_lazy_imports()

# ------------------------------------
# Config Logger
LOGGING_CONFIGURATION = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(name)s[%(levelname)s]: %(message)s"},
        "simple": {"format": "%(name)s[%(levelname)s]: %(message)s"},
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": helpus_log_file,
            "formatter": "verbose",
        }
    },
    "loggers": {"HelpUs": {"handlers": ["file"], "level": "DEBUG", "propagate": False}},
}
logging.config.dictConfig(LOGGING_CONFIGURATION)

# ------------------------------------
