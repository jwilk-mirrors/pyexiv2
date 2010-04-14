# -*- coding: utf-8 -*-

import os
import sys

def _fiddle_with_pythonpath():
    # Fiddle with the pythonpath to allow builders to locate pyexiv2
    # (see https://bugs.launchpad.net/pyexiv2/+bug/549398).
    curdir = os.path.abspath(os.curdir)
    sys.path.insert(0, os.path.join(curdir, 'build'))
    sys.path.insert(0, os.path.join(curdir, 'src'))

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
    _fiddle_with_pythonpath()
    SConscript('doc/SConscript')

def run_tests():
    _fiddle_with_pythonpath()
    from test.TestsRunner import run_unit_tests
    # FIXME: this is not really well integrated as scons is not informed
    # whether the unit tests passed or failed.
    # http://www.scons.org/wiki/UnitTests may be of use.
    run_unit_tests()

if not BUILD_TARGETS:
    # Default target: lib
    build_lib()
else:
    if 'lib' in BUILD_TARGETS or 'install' in BUILD_TARGETS:
        build_lib()
    if 'doc' in BUILD_TARGETS:
        # Note: building the doc requires the lib to be built and the pyexiv2
        # module to be in the python path.
        build_doc()
    if 'test' in BUILD_TARGETS:
        run_tests()

