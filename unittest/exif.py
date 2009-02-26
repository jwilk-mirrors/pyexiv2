# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2009 Olivier Tilloy <olivier@tilloy.net>
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
# Author: Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
from pyexiv2 import ExifTag, ExifValueError


class TestExifTag(unittest.TestCase):

    def test_convert_to_python_short(self):
        xtype = 'Short'
        # Valid values
        self.assertEqual(ExifTag._convert_to_python('23', xtype), 23)
        self.assertEqual(ExifTag._convert_to_python('+5628', xtype), 5628)
        # Invalid values
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, 'abc', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '5,64', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '47.0001', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '1E3', xtype)

    def test_convert_to_string_short(self):
        xtype = 'Short'
        # Valid values
        self.assertEqual(ExifTag._convert_to_string(123, xtype), '123')
        # Invalid values
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_string, -57, xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_string, 'invalid', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_string, 3.14, xtype)

    def test_convert_to_python_long(self):
        xtype = 'Long'
        # Valid values
        self.assertEqual(ExifTag._convert_to_python('23', xtype), 23)
        self.assertEqual(ExifTag._convert_to_python('+5628', xtype), 5628)
        # Invalid values
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, 'abc', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '5,64', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '47.0001', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '1E3', xtype)

    def test_convert_to_string_long(self):
        xtype = 'Long'
        # Valid values
        self.assertEqual(ExifTag._convert_to_string(123, xtype), '123')
        self.assertEqual(ExifTag._convert_to_string(678024, xtype), '678024')
        # Invalid values
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_string, -57, xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_string, 'invalid', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_string, 3.14, xtype)

    def test_convert_to_python_slong(self):
        xtype = 'SLong'
        # Valid values
        self.assertEqual(ExifTag._convert_to_python('23', xtype), 23)
        self.assertEqual(ExifTag._convert_to_python('+5628', xtype), 5628)
        self.assertEqual(ExifTag._convert_to_python('-437', xtype), -437)
        # Invalid values
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, 'abc', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '5,64', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '47.0001', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_python, '1E3', xtype)

    def test_convert_to_string_slong(self):
        xtype = 'SLong'
        # Valid values
        self.assertEqual(ExifTag._convert_to_string(123, xtype), '123')
        self.assertEqual(ExifTag._convert_to_string(678024, xtype), '678024')
        self.assertEqual(ExifTag._convert_to_string(-437, xtype), '-437')
        # Invalid values
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_string, 'invalid', xtype)
        self.failUnlessRaises(ExifValueError, ExifTag._convert_to_string, 3.14, xtype)
