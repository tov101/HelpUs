import glob
import os
import shutil
import sys

# To use a consistent encoding
from codecs import open
# Always prefer setuptools over distutils
from setuptools import setup

from helpus.version import __version__

here = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(here, "helpus"))

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Clean Pyc Files
try:
    for _item in glob.glob(os.path.join(here, 'helpus', '*.pyc')):
        print('CleanUp File: {}'.format(_item))
        os.remove(_item)
except PermissionError:
    pass

# Get requirements for current package
with open('requirements.txt') as f:
    required = f.read().splitlines()

# Collect/Store/Encrypt Data. Garbage Method. Hope it Works
resource_temp = os.path.join(here, 'helpus\\resources.py')
resource_dest = os.path.join(here, 'helpus\\resources\\resources.py')
try:
    from stringify.util import _bin_to_py_file

    if os.path.isfile(resource_dest):
        os.remove(resource_dest)
    if os.path.isfile(resource_temp):
        os.remove(resource_temp)

    _bin_to_py_file(
        source_file_path=os.path.join(here, 'helpus\\resources\\ico\\snake_ico.ico'),
        destination_file=resource_temp,
        overwrite=True
    )
    shutil.move(
        resource_temp,
        resource_dest,
    )
except ImportError:
    pass

data = [os.path.join(here, 'helpus\\resources')]

setup(
    name='helpus',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=__version__,

    description='Simple Gui to call Pdb in GUI Apps',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/tov101/HelpUs',

    # Author details
    author='Ovidiu Mihaila',
    author_email='ov.mihaila@gmail.com',

    # Choose your license
    license='',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Bug Tracking',

        # Pick your license as you wish (should match "license" above)
        'License :: Public Domain',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],

    # What does your project relate to?
    keywords='HelpUs -> BreakPoint In Execution Module',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['helpus'],

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=required,

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'HelpUs': data
    },
    include_package_data=True,
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    #    entry_points={
    #        'console_scripts': [
    #            'sample=sample:main',
    #        ],
    #    },
    download_url='https://github.com/tov101/HelpUs/archive/refs/tags/v0.0.1.tar.gz'
)
