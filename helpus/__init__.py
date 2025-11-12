import logging.config
import os

# Ensure QT_API is set early
os.environ.setdefault("QT_API", "pyside6")


# Do not Import Stuff from 'module' here because will raise ImportError because of Circular import
def not_used(item):
    """
    Just to make PyLint happy.
    :param item:
    :return:
    """
    assert item == item


# Define Log File
helpus_log_file = os.path.join(os.path.dirname("__file__"), "HelpUs.log")

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
