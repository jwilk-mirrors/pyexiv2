Developers
==========

If you are a developer and use pyexiv2 in your project, you will find here
useful information.

Getting the code
################

pyexiv2's source code is versioned with
`bazaar <http://bazaar.canonical.com/>`_, and all the branches, including the
main development focus (sometimes referred to as *trunk*), are hosted on
`Launchpad <https://code.launchpad.net/pyexiv2>`_.

To get a working copy of the latest revision of the development branch, just
issue the following command in a terminal::

  bzr branch lp:pyexiv2

If you need to get a specific revision identified by a tag (all releases of
pyexiv2 are tagged), use the following command::

  bzr branch -r tag:tag_name lp:pyexiv2

A list of all the available tags can be obtained using the ``bzr tags``
command::

  osomon@granuja:~/dev/pyexiv2$ bzr tags
  release-0.1          60
  release-0.1.1        73
  release-0.1.2        99
  release-0.1.3        99.1.6

Dependencies
############

You will need the following dependencies installed on your system to build and
use pyexiv2:

* `Python <http://python.org/download/>`_ ≥ 2.5
* `boost.python <http://www.boost.org/libs/python/doc/>`_ ≥ 1.35
* `libexiv2 <http://exiv2.org/>`_ ≥ 0.19
* `SCons <http://scons.org/>`_

For Python, boost.python and libexiv2, the development files are needed
(-dev packages).
A typical list of packages to install on a Debian/Ubuntu system is::

  python-all-dev libboost-python-dev libexiv2-dev scons

Building and installing
#######################

Linux
+++++

Building pyexiv2 is as simple as invoking ``scons`` in the top-level directory::

  osomon@granuja:~/dev/pyexiv2$ scons
  scons: Reading SConscript files ...
  scons: done reading SConscript files.
  scons: Building targets ...
  g++ -o build/exiv2wrapper.os -c -fPIC -I/usr/include/python2.6 src/exiv2wrapper.cpp
  g++ -o build/exiv2wrapper_python.os -c -fPIC -I/usr/include/python2.6 src/exiv2wrapper_python.cpp
  g++ -o build/libexiv2python.so -shared build/exiv2wrapper.os build/exiv2wrapper_python.os -lboost_python -lexiv2
  scons: done building targets.

The result of the build process is a shared library, ``libexiv2python.so``, in
the build directory::

  osomon@granuja:~/dev/pyexiv2$ ls build/
  exiv2wrapper.os  exiv2wrapper_python.os  libexiv2python.so

To install pyexiv2 system-wide, just invoke ``scons install``.
You will most likely need administrative privileges to proceed.
The ``--user`` switch will install pyexiv2 in the current
`user site directory <http://www.python.org/dev/peps/pep-0370/>`_
(Python ≥ 2.6 is required).

Note to packagers:
if `DESTDIR <http://www.gnu.org/prep/standards/html_node/DESTDIR.html>`_ is
specified on the command line when invoking ``scons install``, its value will be
prepended to each installed target file.

Windows
+++++++

The top-level directory of the development branch contains a shell script named
``cross-compile.sh`` that retrieves all the dependencies required and
cross-compiles pyexiv2 for Windows on a Linux host.
Read the comments in the header of the script to know the pre-requisites.

The result of the compilation is a DLL, ``libexiv2python.pyd``, in the build
directory. This file and the ``pyexiv2`` folder in ``src`` should be copied to
the system-wide site directory of a Python 2.6 setup
(typically ``C:\Python26\Lib\site-packages\``) or to the user site directory
(``%APPDATA%\Python\Python26\site-packages\``).

The top-level directory of the branch also contains an
`NSIS <http://nsis.sourceforge.net/>`_ installer script named
``win32-installer.nsi``.
From the top-level directory of the branch, run the following command::

  makensis win32-installer.nsi

This will generate a ready-to-distribute installer executable named
``pyexiv2-0.2-setup.exe``.

Documentation
#############

The present documentation is generated using
`Sphinx <http://sphinx.pocoo.org/>`_ from reStructuredText sources found in the
doc/ directory. Invoke ``scons doc`` to (re)build the HTML documentation.
Alternatively, you can issue the following command::

  sphinx-build -b html doc/ doc/_build/

The index of the documentation will then be found under doc/_build/index.html.
Note that you will need pyexiv2 to be installed system-wide or to be found on
the ``PYTHONPATH`` for the documentation to build successfully.

Unit tests
##########

pyexiv2's source comes with a battery of unit tests, in the test/ directory.
To run them, ``cd`` to this directory and execute the ``TestsRunner.py``
script, making sure that pyexiv2 is installed system-wide or can be found on
the ``PYTHONPATH``.

Contributing
############

pyexiv2 is Free Software, meaning that you are encouraged to use it, modify it
to suit your needs, contribute back improvements, and redistribute it.

`Bugs <https://bugs.launchpad.net/pyexiv2>`_ are tracked on Launchpad.
There is a team called
`pyexiv2-developers <https://launchpad.net/~pyexiv2-developers>`_ open to anyone
interested in following development on pyexiv2. Don't hesitate to subscribe to
the team (you don't need to actually contribute!) and to the associated mailing
list.

There are several ways in which you can contribute to improve pyexiv2:

* Use it;
* Give your feedback and discuss issues and feature requests on the
  mailing list;
* Report bugs, write patches;
* Package it for your favorite distribution/OS.

When reporting a bug, don't forget to include the following information in the
report:

* version of pyexiv2
* version of libexiv2 it was compiled against
* a minimal script that reliably reproduces the issue
* a sample image file with which the bug can reliably be reproduced

