# Copyright (C) 2014 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

try:
    import py2exe
    HAVE_PY2EXE=True
except:
    HAVE_PY2EXE=False

import glob

here = path.abspath(path.dirname(__file__))

setup(
    name='l5rcm',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='3.10.0',

    description='L5R RPG character manager',

    # Author details
    author='Daniele Simonetti',
    author_email='oppifjellet@gmail.com',

    license='GPLv3',

    # The project's main homepage.
    url='https://github.com/OpenNingia/l5r-character-manager-3',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        'Intended Audience :: End Users/Desktop',

        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: Qt',

        'Topic :: Games/Entertainment :: Role-Playing',
        'Topic :: Utilities',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2 :: Only',
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    keywords='l5r rpg legend of the five rings character manager',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['asq'],

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'l5r.share.l5rcm': ['*.pdf', '*.txt', '*.png'],
        'l5r.share.l5rcm.i18n': ['*.qm'],
        'l5r.share.icons.l5rcm': ['*.png'],
        'l5r.share.icons.l5rcm.tabs': ['*.png'],
        'l5r.share.icons.l5rcm.16x16': ['*.png'],
        'l5r.share.icons.l5rcm.32x32': ['*.png'],
        'l5r.share.icons.l5rcm.48x48': ['*.png'],
        'l5r.share.icons.l5rcm.64x64': ['*.png'],
        'l5r.share.icons.l5rcm.128x128': ['*.png'],
        'l5r.share.icons.l5rcm.256x256': ['*.png'],
        'l5r.tools': ['*.*'],
        #'tools': glob.glob('../tools/pdftk/*')
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    #data_files=[
    #    ('share/icons/l5rcm/256x256', glob.glob('l5rcm/share/icons/l5rcm/256x256/*')),
    #    ('share/icons/l5rcm/128x128', glob.glob('l5rcm/share/icons/l5rcm/128x128/*')),
    #    ('share/icons/l5rcm/64x64', glob.glob('l5rcm/share/icons/l5rcm/64x64/*')),
    #    ('share/icons/l5rcm/48x48', glob.glob('l5rcm/share/icons/l5rcm/48x48/*')),
    #    ('share/icons/l5rcm/32x32', glob.glob('l5rcm/share/icons/l5rcm/32x32/*')),
    #    ('share/icons/l5rcm/16x16', glob.glob('l5rcm/share/icons/l5rcm/16x16/*')),
    #    ('share/icons/l5rcm/tabs', glob.glob('l5rcm/share/icons/l5rcm/tabs/*')),
    #    ('share/icons/l5rcm', glob.glob('l5rcm/share/icons/l5rcm/*.*')),
    #
    #    ('share/l5rcm/i18n', glob.glob('l5rcm/share/l5rcm/i18n/*')),
    #    ('share/l5rcm', glob.glob('l5rcm/share/l5rcm/*.*')),
    #
    #    ('tools', glob.glob('tools/pdftk/*.*')),
    #],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'l5rcm=l5r.main:main',
        ],

        'gui_scripts': [
            'l5rcm_win=l5r.main:main',
        ]

    },

    windows=[
        {
            "script": "main.py",
            "icon_resources": [(0, "tools/deploy/windows/l5rcm.ico"), (1, "tools/deploy/windows/l5rcmpack.ico")]
        }
    ],
    options={
        "py2exe": {"includes": ["PyQt4.QtGui", 'lxml.etree', 'lxml._elementpath', 'sip']}},
)
