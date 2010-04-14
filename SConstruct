# -*- coding: utf-8 -*-

import os
import sys

def build_lib():
    try:
        from site import USER_SITE
    except ImportError:
        # Installing in the user site directory requires Python ≥ 2.6.
        pass
    else:
        AddOption('--user', action='store_true',
                  help='Install in the user site directory.')
    SConscript('src/SConscript', variant_dir='build', duplicate=0)

def build_doc():
    # Fiddle with the pythonpath to allow the doc builder to locate pyexiv2
    # (see https://bugs.launchpad.net/pyexiv2/+bug/549398).
    curdir = os.path.abspath(os.curdir)
    sys.path.insert(0, os.path.join(curdir, 'build'))
    sys.path.insert(0, os.path.join(curdir, 'src'))
    SConscript('doc/SConscript')

if not BUILD_TARGETS:
    # Default target: lib
    build_lib()
else:
    if 'lib' in BUILD_TARGETS or 'install' in BUILD_TARGETS:
        build_lib()
    if 'doc' in BUILD_TARGETS:
        # Note: building the doc requires the lib to be built.
        build_doc()

