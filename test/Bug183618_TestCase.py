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
# File:      Bug183618_TestCase.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
import testutils
import os.path
import pyexiv2

class Bug183618_TestCase(unittest.TestCase):

    """
    Test case for bug #183618.

    Summary: Exif.GPSInfo.{GPSLongitude,Latitude} are not decoded.
    Description: The GPS latitude and longitude data is not correctly decoded
    because multiple value fields for EXIF tags are not correctly dealt with:
    only the first value is extracted and returned.
    Fix: fixed with revision 79, behaviour changed with revision 82.
    """

    def checkTypeAndValue(self, tag, etype, evalue):
        """
        Check the type and the value of a metadata tag against expected values.

        Keyword arguments:
        tag -- the full name of the tag (eg. 'Exif.Image.DateTime')
        etype -- the expected type of the tag value
        evalue -- the expected value of the tag
        """
        self.assertEqual(tag.__class__, etype)
        self.assertEqual(tag, evalue)

    def testReadGPSMetadata(self):
        """
        Test the extraction of the GPS metadata from a file.
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'bug183618.jpg')
        md5sum = 'ccddff432b0a2dc8f544f0f380e1fa6d'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        # Read the image metadata
        image = pyexiv2.Image(filename)
        image.readMetadata()

        # Exhaustive tests on the values of EXIF GPS metadata
        gpsTags = [('Exif.Image.GPSTag', long, 1313L),
                   ('Exif.GPSInfo.GPSVersionID', str, '2 0 0 0 '),
                   ('Exif.GPSInfo.GPSLatitudeRef', str, 'N'),
                   ('Exif.GPSInfo.GPSLatitude', tuple, (pyexiv2.Rational(47, 1), pyexiv2.Rational(3817443, 1000000), pyexiv2.Rational(0, 1))),
                   ('Exif.GPSInfo.GPSLongitudeRef', str, 'E'),
                   ('Exif.GPSInfo.GPSLongitude', tuple, (pyexiv2.Rational(8, 1), pyexiv2.Rational(41359940, 1000000), pyexiv2.Rational(0, 1))),
                   ('Exif.GPSInfo.GPSAltitudeRef', str, '0 '),
                   ('Exif.GPSInfo.GPSAltitude', pyexiv2.Rational, pyexiv2.Rational(1908629, 1250)),
                   ('Exif.GPSInfo.GPSMapDatum', str, 'WGS-84')]
        self.assertEqual([tag for tag in image.exifKeys() if tag.find('GPS') != -1], [tag[0] for tag in gpsTags])
        for tag in gpsTags:
            self.checkTypeAndValue(image[tag[0]], tag[1], tag[2])

