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
# File:      TestsRunner.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest

# Test cases to run
from RationalTestCase import RationalTestCase
from ReadMetadataTestCase import ReadMetadataTestCase
from Bug146313_TestCase import Bug146313_TestCase

if __name__ == '__main__':
    # Instantiate a test suite containing all the test cases
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(RationalTestCase))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(ReadMetadataTestCase))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(Bug146313_TestCase))
    # Run the test suite
    unittest.TextTestRunner(verbosity=2).run(suite)

