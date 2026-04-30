import importlib.util
import logging.config
import os
import sys


# On Windows, register any shiboken6 / PySide6 directories found on sys.path as
# DLL search directories *before* importing Qt.  This is needed when helpus is
# imported inside a frozen executable (e.g. eval_tool) whose own DLL search path
# does not include the Qt DLLs that were passed via --py_libs / sys.path.
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    for _pkg in ("shiboken6", "PySide6"):
        _spec = importlib.util.find_spec(_pkg)
        if _spec and _spec.submodule_search_locations:
            for _loc in _spec.submodule_search_locations:
                try:
                    os.add_dll_directory(_loc)
                except Exception:
                    pass


# Ensure QT_API is set early so qtpy picks the right binding.
if not os.environ.get("QT_API"):
    os.environ.setdefault("QT_API", "pyside6")


# Do not Import Stuff from 'module' here because will raise ImportError because of Circular import
def not_used(item):
    """Suppress linter warnings for intentionally unused variables."""
    pass


# Define Log File
helpus_log_file = os.path.join(os.path.dirname(__file__) or ".", "HelpUs.log")

# CleanUp Existing LogFile
if os.path.exists(helpus_log_file):
    try:
        os.remove(helpus_log_file)
    except Exception as don_t_care:
        not_used(don_t_care)

__all__ = ["HelpUs", "get_qtconsole_object", "setup_breakpoint", "setup_breakpoint_hook"]


def _lazy_imports():
    try:
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
    except Exception:
        # Qt is not available in this environment (e.g. inside eval_tool frozen app).
        # Provide lightweight no-op fallbacks so that code calling
        # setup_breakpoint() in non-GUI contexts does not crash on import.

        def setup_breakpoint(*args, **kwargs):
            pass

        def setup_breakpoint_hook(parent, method, *args, **kwargs):
            return method

        def get_qtconsole_object():
            raise RuntimeError("HelpUs Qt console is not available in this environment.")

        globals().update(
            {
                "HelpUs": None,
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
