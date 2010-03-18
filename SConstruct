# -*- coding: utf-8 -*-

def build_lib():
    try:
        from site import USER_SITE
    except ImportError:
        # Installing in the user site directory requires Python ≥ 2.6.
        pass
    else:
        AddOption('--user', action='store_true')
    SConscript('src/SConscript', variant_dir='build', duplicate=0)

def build_doc():
    SConscript('doc/SConscript')

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

