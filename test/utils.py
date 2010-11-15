# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2010 Olivier Tilloy <olivier@tilloy.net>
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

from pyexiv2.utils import undefined_to_string, string_to_undefined


class TestConversions(unittest.TestCase):

    def test_undefined_to_string(self):
        self.assertEqual(undefined_to_string("48 50 50 49"), "0221")
        self.assertEqual(undefined_to_string("48 50 50 49 "), "0221")
        self.assertRaises(ValueError, undefined_to_string, "")
        self.assertRaises(ValueError, undefined_to_string, "foo")
        self.assertRaises(ValueError, undefined_to_string, "48 50  50 49")

    def test_string_to_undefined(self):
        self.assertEqual(string_to_undefined("0221"), "48 50 50 49")
        self.assertEqual(string_to_undefined(""), "")

    def test_identity(self):
        value = "0221"
        self.assertEqual(undefined_to_string(string_to_undefined(value)), value)
        value = "48 50 50 49"
        self.assertEqual(string_to_undefined(undefined_to_string(value)), value)

