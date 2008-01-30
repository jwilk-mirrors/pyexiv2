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
# File:      RationalTestCase.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
import pyexiv2

class RationalTestCase(unittest.TestCase):

    """
    Test case on the pyexiv2.Rational class.
    """

    def testConstructor(self):
        """
        Test that the rational number constructor works as expected.
        """
        r = pyexiv2.Rational(2, 1)
        self.assertEqual(r.numerator, 2)
        self.assertEqual(r.denominator, 1)

    def testException(self):
        """
        Test that the constructor throws an exception when denominator is zero.
        """
        self.assertRaises(ZeroDivisionError, pyexiv2.Rational, 1, 0)

    def testEquality(self):
        """
        Test the (non) equality of two rational numbers.
        """
        r1 = pyexiv2.Rational(2, 1)
        r2 = pyexiv2.Rational(2, 1)
        r3 = pyexiv2.Rational(3, 1)
        self.assertEqual(r1, r2)
        self.assertNotEqual(r1, r3)

