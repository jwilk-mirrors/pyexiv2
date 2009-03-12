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
from pyexiv2 import ImageMetadata, ExifTag


class ImageMock(object):

    def __init__(self, filename):
        self.filename = filename
        self.read = False
        self.written = False
        self.tags = {'exif': {}, 'iptc': {}, 'xmp': {}}

    def readMetadata(self):
        self.read = True

    def writeMetadata(self):
        self.written = True

    def exifKeys(self):
        return self.tags['exif'].keys()

    def getExifTag(self, key):
        return self.tags['exif'][key]

    def iptcKeys(self):
        return self.tags['iptc'].keys()

    def getIptcTag(self, key):
        return self.tags['iptc'][key]

    def xmpKeys(self):
        return self.tags['xmp'].keys()

    def getXmpTag(self, key):
        return self.tags['xmp'][key]


class TestImageMetadata(unittest.TestCase):

    def setUp(self):
        self.metadata = ImageMetadata('nofile')
        self.metadata._instantiate_image = lambda filename: ImageMock(filename)

    def _set_exif_tags(self):
        tags = {}
        tags['Exif.Image.Make'] = \
            ('Exif.Image.Make', 'Make', 'Manufacturer', 'blabla', 'Ascii',
             'EASTMAN KODAK COMPANY', 'EASTMAN KODAK COMPANY')
        tags['Exif.Image.DateTime'] = \
            ('Exif.Image.DateTime', 'DateTime', 'Date and Time', 'blabla',
             'Ascii', '2009:02:09 13:33:20', '2009:02:09 13:33:20')
        tags['Exif.Photo.ExifVersion'] = \
            ('Exif.Photo.ExifVersion', 'ExifVersion', 'Exif Version', 'blabla',
             'Undefined', '48 50 50 49 ', '2.21')
        self.metadata._image.tags['exif'] = tags

    def test_read(self):
        self.assertEqual(self.metadata._image, None)
        self.metadata.read()
        self.failIfEqual(self.metadata._image, None)
        self.failUnless(self.metadata._image.read)

    def test_write(self):
        self.metadata.read()
        self.failIf(self.metadata._image.written)
        self.metadata.write()
        self.failUnless(self.metadata._image.written)

    def test_exif_keys(self):
        self.metadata.read()
        self._set_exif_tags()
        self.assertEqual(self.metadata._keys['exif'], None)
        keys = self.metadata.exif_keys
        self.assertEqual(len(keys), 3)
        self.assertEqual(self.metadata._keys['exif'], keys)

    def test_get_exif_tag(self):
        self.metadata.read()
        self._set_exif_tags()
        self.assertEqual(self.metadata._tags['exif'], {})
        key = 'Exif.Image.Make'
        tag = self.metadata._get_exif_tag(key)
        self.assertEqual(type(tag), ExifTag)
        self.assertEqual(self.metadata._tags['exif'][key], tag)
