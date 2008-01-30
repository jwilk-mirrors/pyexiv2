#!/usr/bin/python
# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2006-2007 Olivier Tilloy <olivier@tilloy.net>
#
# This file is part of the pyexiv2 distribution.
#
# pyexiv2 is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# pyexiv2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyexiv2; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, 5th Floor, Boston, MA 02110-1301 USA.
#
#
# File:      Bug146313_TestCase.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
import os.path
import pyexiv2

class Bug146313_TestCase(unittest.TestCase):

    """
    Test case for bug #146313.

    Summary: Passing the filename to the Image constructor as unicode fails.
    Description: passing a unicode string to the constructor of pyexiv2.Image
    throws an exception of type Boost.Python.ArgumentError.
    Fix: fixed with revision 76.
    """

    def testNormalStringAscii(self):
        """
        Test passing the constructor a normal string with ascii characters only.
        """
        filename = os.path.join('data', 'smiley1.jpg')
        image = pyexiv2.Image(filename)

    def testNormalStringExotic(self):
        """
        Test passing the constructor a normal string with unicode characters.
        """
        filename = os.path.join('data', 'bug146313_šmiléŷ.jpg')
        image = pyexiv2.Image(filename)

    def testUnicodeStringAscii(self):
        """
        Test passing the constructor a unicode string with ascii characters
        only.
        """
        filename = unicode(os.path.join('data', 'smiley1.jpg'), 'utf-8')
        image = pyexiv2.Image(filename)

    def testUnicodeStringExotic(self):
        """
        Test passing the constructor a unicode string with unicode characters.
        """
        filename = unicode(os.path.join('data', 'bug146313_šmiléŷ.jpg'), 'utf-8')
        image = pyexiv2.Image(filename)

