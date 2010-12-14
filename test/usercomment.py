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

from pyexiv2.metadata import ImageMetadata

import unittest
import testutils
import os.path


class TestUserComment(unittest.TestCase):

    def _read_image(self, filename, checksum):
        filepath = testutils.get_absolute_file_path(os.path.join('data', filename))
        self.assert_(testutils.CheckFileSum(filepath, checksum))
        m = ImageMetadata(filepath)
        m.read()
        return m

    def test_read_ascii(self):
        m = self._read_image('usercomment-ascii.jpg', 'ad29ac65fb6f63c8361aaed6cb02f8c7')
        tag = m['Exif.Photo.UserComment']
        self.assertEqual(tag.raw_value, 'charset="Ascii" deja vu')
        self.assertEqual(tag.value, u'deja vu')

    def test_read_unicode_little_endian(self):
        m = self._read_image('usercomment-unicode-ii.jpg', '13b7cc09129a8677f2cf18634f5abd3c')
        tag = m['Exif.Photo.UserComment']
        self.assertEqual(tag.raw_value, 'charset="Unicode" d\x00\xe9\x00j\x00\xe0\x00 \x00v\x00u\x00')
        self.assertEqual(tag.value, u'déjà vu')

    def test_read_unicode_big_endian(self):
        m = self._read_image('usercomment-unicode-mm.jpg', '7addfed7823c556ba489cd4ab2037200')
        tag = m['Exif.Photo.UserComment']
        self.assertEqual(tag.raw_value, 'charset="Unicode" \x00d\x00\xe9\x00j\x00\xe0\x00 \x00v\x00u')
        self.assertEqual(tag.value, u'déjà vu')

    def test_write_ascii(self):
        m = self._read_image('usercomment-ascii.jpg', 'ad29ac65fb6f63c8361aaed6cb02f8c7')
        tag = m['Exif.Photo.UserComment']
        tag.value = 'foo bar'
        self.assertEqual(tag.raw_value, 'charset="Ascii" foo bar')
        self.assertEqual(tag.value, u'foo bar')

    def test_write_unicode_over_ascii(self):
        m = self._read_image('usercomment-ascii.jpg', 'ad29ac65fb6f63c8361aaed6cb02f8c7')
        tag = m['Exif.Photo.UserComment']
        tag.value = u'déjà vu'
        self.assertEqual(tag.raw_value, 'déjà vu')
        self.assertEqual(tag.value, u'déjà vu')

    def test_write_unicode_little_endian(self):
        m = self._read_image('usercomment-unicode-ii.jpg', '13b7cc09129a8677f2cf18634f5abd3c')
        tag = m['Exif.Photo.UserComment']
        tag.value = u'DÉJÀ VU'
        self.assertEqual(tag.raw_value, 'charset="Unicode" D\x00\xc9\x00J\x00\xc0\x00 \x00V\x00U\x00')
        self.assertEqual(tag.value, u'DÉJÀ VU')

    def test_write_unicode_big_endian(self):
        m = self._read_image('usercomment-unicode-mm.jpg', '7addfed7823c556ba489cd4ab2037200')
        tag = m['Exif.Photo.UserComment']
        tag.value = u'DÉJÀ VU'
        self.assertEqual(tag.raw_value, 'charset="Unicode" \x00D\x00\xc9\x00J\x00\xc0\x00 \x00V\x00U')
        self.assertEqual(tag.value, u'DÉJÀ VU')

