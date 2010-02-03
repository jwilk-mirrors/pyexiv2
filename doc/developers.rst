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

To install pyexiv2, just invoke ``scons install``. You will most likely need
administrative privileges to proceed.

Documentation
#############

The present documentation is generated using
`Sphinx <http://sphinx.pocoo.org/>`_ from reStructuredText sources found in the
doc/ directory. Issue the following command to (re)build the HTML
documentation::

  sphinx-build -b html doc/ doc/_build/

The index of the documentation will then be found under doc/_build/index.html.

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

