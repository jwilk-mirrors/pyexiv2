# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2008-2009 Olivier Tilloy <olivier@tilloy.net>
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
from pyexiv2 import Rational


class TestRational(unittest.TestCase):

    def test_constructor(self):
        r = Rational(2, 1)
        self.assertEqual(r.numerator, 2)
        self.assertEqual(r.denominator, 1)
        self.assertRaises(ZeroDivisionError, Rational, 1, 0)

    def test_equality(self):
        r1 = Rational(2, 1)
        r2 = Rational(2, 1)
        r3 = Rational(8, 4)
        r4 = Rational(3, 2)
        self.assertEqual(r1, r2)
        self.assertEqual(r1, r3)
        self.assertNotEqual(r1, r4)
