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
# File:      ReadMetadataTestCase.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
import testutils
import os.path
import pyexiv2
import datetime

class ReadMetadataTestCase(unittest.TestCase):

    """
    Test case on reading the metadata contained in a file.
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

    def testReadMetadata(self):
        """
        Perform various tests on reading the metadata contained in a file.
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'smiley1.jpg')
        md5sum = 'c066958457c685853293058f9bf129c1'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        # Read the image metadata
        image = pyexiv2.Image(filename)
        image.readMetadata()

        # Exhaustive tests on the values of EXIF metadata
        exifTags = [('Exif.Image.ImageDescription', str, 'Well it is a smiley that happens to be green'),
                    ('Exif.Image.XResolution', pyexiv2.Rational, pyexiv2.Rational(72, 1)),
                    ('Exif.Image.YResolution', pyexiv2.Rational, pyexiv2.Rational(72, 1)),
                    ('Exif.Image.ResolutionUnit', int, 2),
                    ('Exif.Image.Software', str, 'ImageReady'),
                    ('Exif.Image.DateTime', datetime.datetime, datetime.datetime(2004, 7, 13, 21, 23, 44)),
                    ('Exif.Image.Artist', str, 'No one'),
                    ('Exif.Image.Copyright', str, ''),
                    ('Exif.Image.ExifTag', long, 226L),
                    ('Exif.Photo.Flash', int, 80),
                    ('Exif.Photo.PixelXDimension', long, 167L),
                    ('Exif.Photo.PixelYDimension', long, 140L)]
        self.assertEqual(image.exifKeys(), [tag[0] for tag in exifTags])
        for tag in exifTags:
            self.checkTypeAndValue(image[tag[0]], tag[1], tag[2])

        # Exhaustive tests on the values of IPTC metadata
        iptcTags = [('Iptc.Application2.Caption', str, 'yelimS green faced dude (iptc caption)'),
                    ('Iptc.Application2.Writer', str, 'Nobody'),
                    ('Iptc.Application2.Byline', str, 'Its me'),
                    ('Iptc.Application2.ObjectName', str, 'GreeenDude'),
                    ('Iptc.Application2.DateCreated', datetime.date, datetime.date(2004, 7, 13)),
                    ('Iptc.Application2.City', str, 'Seattle'),
                    ('Iptc.Application2.ProvinceState', str, 'WA'),
                    ('Iptc.Application2.CountryName', str, 'USA'),
                    ('Iptc.Application2.Category', str, 'Things'),
                    ('Iptc.Application2.Keywords', tuple, ('Green', 'Smiley', 'Dude')),
                    ('Iptc.Application2.Copyright', str, '\xa9 2004 Nobody')]
        self.assertEqual(image.iptcKeys(), [tag[0] for tag in iptcTags])
        for tag in iptcTags:
            self.checkTypeAndValue(image[tag[0]], tag[1], tag[2])

        # Test on the JPEG comment
        self.checkTypeAndValue(image.getComment(),
            str, 'This is a jpeg comment, about the green smiley.')

