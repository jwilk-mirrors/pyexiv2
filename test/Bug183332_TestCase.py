#!/usr/bin/python
# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2008 Olivier Tilloy <olivier@tilloy.net>
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
# File:      Bug183332_TestCase.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
import testutils
import os.path
import pyexiv2

class Bug183332_TestCase(unittest.TestCase):

    """
    Test case for bug #183332.

    Summary: Cached metadata is not converted to its correct type.
    Description: When setting the value of a tag, its value is automatically
    converted to the correct type, but the value held in the internal cache is
    not.
    """

    def testSetEXIFTagValue(self):
        """
        Test the value type of the internally cached metadata after setting an
        EXIF tag.
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'smiley1.jpg')
        md5sum = 'c066958457c685853293058f9bf129c1'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        image = pyexiv2.Image(filename)
        image.readMetadata()
        key = 'Exif.Image.Artist'
        self.assert_(key in image.exifKeys())
        value = 12
        # EXIF artist is a string, voluntarily pass an integer as argument
        image[key] = value
        self.assertEqual(image[key], str(value))

    def testSetIPTCTagValue(self):
        """
        Test the value type of the internally cached metadata after setting an
        IPTC tag.
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'smiley1.jpg')
        md5sum = 'c066958457c685853293058f9bf129c1'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        image = pyexiv2.Image(filename)
        image.readMetadata()
        key = 'Iptc.Application2.Keywords'
        self.assert_(key in image.iptcKeys())
        values = (5, 6)
        # IPTC keywords are strings, voluntarily pass integers as arguments
        image[key] = values
        self.assertEqual(image[key], tuple([str(v) for v in values]))

    def testSetNotSetEXIFTagValue(self):
        """
        Test the value type of the internally cached metadata after setting an
        EXIF tag that was not previously set.
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'smiley1.jpg')
        md5sum = 'c066958457c685853293058f9bf129c1'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        image = pyexiv2.Image(filename)
        image.readMetadata()
        key = 'Exif.Image.Model'
        self.assert_(key not in image.exifKeys())
        value = 34L
        # EXIF model is a string, voluntarily pass a long as argument
        image[key] = value
        self.assertEqual(image[key], str(value))

