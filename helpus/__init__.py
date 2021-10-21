import logging.config
import os


# Do not Import Stuff from 'module' here because will raise ImportError because of Circular import

def not_used(item):
    """
    Just to make PyLint happy.
    :param item:
    :return:
    """
    assert item == item


# Define Icon Path
icon_file_path = os.path.join(os.path.dirname(__file__), 'resources', 'ico', 'snake.ico')
# Define Log File
helpus_log_file = os.path.join(os.path.dirname(__file__), ' HelpUs.log')

# CleanUp Existing LogFile
if os.path.exists(helpus_log_file):
    try:
        os.remove(helpus_log_file)
    except Exception as don_t_care:
        not_used(don_t_care)

try:
    # Try to restore files
    from stringify import unstringify
    from .resources.resources import snake_ico as ico_data

    # Restore Files
    if not os.path.exists(os.path.dirname(icon_file_path)):
        os.makedirs(os.path.dirname(icon_file_path))
    with open(icon_file_path, 'wb+') as fp_w:
        fp_w.write(
            unstringify(ico_data)
        )
except ImportError as e:
    print('HelpUs Import Error !0!')
    pass

else:
    # Module Imports
    from .version import __version__
    from .core import (
        HelpUs,
        setup_breakpoint_hook,
        get_qtconsole_object
    )

    # ------------------------------------

    # Config Logger
    LOGGING_CONFIGURATION = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {'format': '%(name)s[%(levelname)s]: %(message)s'},
            'simple': {'format': '%(name)s[%(levelname)s]: %(message)s'}
        },
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': helpus_log_file,
                'formatter': 'verbose'
            }
        },
        'loggers': {
            'HelpUs': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': False
            }
        }
    }
    logging.config.dictConfig(LOGGING_CONFIGURATION)

    # ------------------------------------

    # Export Visible Items
    __all__ = [
        '__version__',
        'icon_file_path',
        'HelpUs',
        'get_qtconsole_object',
        'setup_breakpoint_hook',
    ]
