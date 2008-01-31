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
# File:      Bug175070_TestCase.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
import testutils
import os.path
import pyexiv2

class Bug175070_TestCase(unittest.TestCase):

    """
    Test case for bug #175070.

    Summary: Deleting a tag not previously accessed raises a KeyError exception.
    Description: When trying to delete a tag present in an image but not
    previously accessed, a KeyError exception is raised.
    Fix: fixed with revision 78.
    """

    def testDeleteExifTag(self):
        """
        Test deleting an EXIF tag not previously accessed.
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'smiley1.jpg')
        md5sum = 'c066958457c685853293058f9bf129c1'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        image = pyexiv2.Image(filename)
        image.readMetadata()
        key = 'Exif.Image.ImageDescription'
        self.assert_(key in image.exifKeys())
        del image[key]

    def testDeleteIptcTag(self):
        """
        Test deleting an IPTC tag not previously accessed. The IPTC tag is a
        multiple values field, and the deletion is performed by assigning its
        value an empty list.
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'smiley1.jpg')
        md5sum = 'c066958457c685853293058f9bf129c1'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        image = pyexiv2.Image(filename)
        image.readMetadata()
        key = 'Iptc.Application2.Keywords'
        self.assert_(key in image.iptcKeys())
        image[key] = []

