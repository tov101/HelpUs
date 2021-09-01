import os

# Do not Import Stuff from 'module' here because will raise ImportError because of Circular import

# Define Icon Path
icon_file_path = os.path.join(os.path.dirname(__file__), 'resources', 'ico', 'snake.ico')

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
        MyBreakPoint,
        setup_breakpoint_hook,
        get_qtconsole_object
    )

    # ------------------------------------

    # Export Visible Items
    __all__ = [
        '__version__',
        'icon_file_path',
        'MyBreakPoint',
        'get_qtconsole_object',
        'setup_breakpoint_hook',
    ]
