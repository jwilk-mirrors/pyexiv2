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

from pyexiv2.exif import ExifTag, ExifValueError
from pyexiv2.utils import Rational

import datetime


class ExifTagMock(ExifTag):

    def __init__(self, key, type, fvalue=''):
        super(ExifTagMock, self).__init__(key, '', '', '', type, '', fvalue)

    def _init_values(self):
        pass


class ImageMetadataMock(object):

    tags = {}

    def _set_exif_tag_value(self, key, value):
        self.tags[key] = value

    def _delete_exif_tag(self, key):
        try:
            del self.tags[key]
        except KeyError:
            pass


class TestExifTag(unittest.TestCase):

    def test_convert_to_python_ascii(self):
        type = 'Ascii'

        # Valid values: datetimes
        tag = ExifTagMock('Exif.Image.DateTime', type)
        self.assertEqual(tag._convert_to_python('2009-03-01 12:46:51'),
                         datetime.datetime(2009, 03, 01, 12, 46, 51))
        self.assertEqual(tag._convert_to_python('2009:03:01 12:46:51'),
                         datetime.datetime(2009, 03, 01, 12, 46, 51))
        self.assertEqual(tag._convert_to_python('2009-03-01T12:46:51Z'),
                         datetime.datetime(2009, 03, 01, 12, 46, 51))

        # Valid values: dates
        tag = ExifTagMock('Exif.GPSInfo.GPSDateStamp', type)
        self.assertEqual(tag._convert_to_python('2009:08:04'),
                         datetime.date(2009, 8, 4))

        # Valid values: strings
        tag = ExifTagMock('Exif.Image.Copyright', type)
        self.assertEqual(tag._convert_to_python('Some text.'), 'Some text.')
        self.assertEqual(tag._convert_to_python(u'Some text with exotic chàräctérʐ.'),
                         u'Some text with exotic chàräctérʐ.')

        # Invalid values: datetimes
        tag = ExifTagMock('Exif.Image.DateTime', type)
        self.assertEqual(tag._convert_to_python('2009-13-01 12:46:51'),
                         u'2009-13-01 12:46:51')
        self.assertEqual(tag._convert_to_python('2009-12-01'), u'2009-12-01')

        # Invalid values: dates
        tag = ExifTagMock('Exif.GPSInfo.GPSDateStamp', type)
        self.assertEqual(tag._convert_to_python('2009:13:01'), u'2009:13:01')
        self.assertEqual(tag._convert_to_python('2009-12-01'), u'2009-12-01')

    def test_convert_to_string_ascii(self):
        type = 'Ascii'

        # Valid values: datetimes
        tag = ExifTagMock('Exif.Image.DateTime', type)
        self.assertEqual(tag._convert_to_string(datetime.datetime(2009, 03, 01, 12, 54, 28)),
                         '2009:03:01 12:54:28')
        self.assertEqual(tag._convert_to_string(datetime.date(2009, 03, 01)),
                         '2009:03:01 00:00:00')

        # Valid values: dates
        tag = ExifTagMock('Exif.GPSInfo.GPSDateStamp', type)
        self.assertEqual(tag._convert_to_string(datetime.date(2009, 03, 01)),
                         '2009:03:01')

        # Valid values: strings
        tag = ExifTagMock('Exif.Image.Copyright', type)
        self.assertEqual(tag._convert_to_string(u'Some text'), 'Some text')
        self.assertEqual(tag._convert_to_string(u'Some text with exotic chàräctérʐ.'),
                         'Some text with exotic chàräctérʐ.')
        self.assertEqual(tag._convert_to_string('Some text with exotic chàräctérʐ.'),
                         'Some text with exotic chàräctérʐ.')

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, None)

    def test_convert_to_python_byte(self):
        type = 'Byte'

        # Valid values
        tag = ExifTagMock('Exif.GPSInfo.GPSVersionID', type)
        self.assertEqual(tag._convert_to_python('D'), 'D')

    def test_convert_to_string_byte(self):
        type = 'Byte'

        # Valid values
        tag = ExifTagMock('Exif.GPSInfo.GPSVersionID', type)
        self.assertEqual(tag._convert_to_string('Some text'), 'Some text')
        self.assertEqual(tag._convert_to_string(u'Some text'), 'Some text')

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, None)

    def test_convert_to_python_short(self):
        type = 'Short'

        # Valid values
        tag = ExifTagMock('Exif.Image.BitsPerSample', type)
        self.assertEqual(tag._convert_to_python('8'), 8)
        self.assertEqual(tag._convert_to_python('+5628'), 5628)

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, 'abc')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '5,64')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '47.0001')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '1E3')

    def test_convert_to_string_short(self):
        type = 'Short'

        # Valid values
        tag = ExifTagMock('Exif.Image.BitsPerSample', type)
        self.assertEqual(tag._convert_to_string(123), '123')

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, -57)
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 'invalid')
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 3.14)

    def test_convert_to_python_long(self):
        type = 'Long'

        # Valid values
        tag = ExifTagMock('Exif.Image.ImageWidth', type)
        self.assertEqual(tag._convert_to_python('8'), 8)
        self.assertEqual(tag._convert_to_python('+5628'), 5628)

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, 'abc')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '5,64')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '47.0001')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '1E3')

    def test_convert_to_string_long(self):
        type = 'Long'

        # Valid values
        tag = ExifTagMock('Exif.Image.ImageWidth', type)
        self.assertEqual(tag._convert_to_string(123), '123')
        self.assertEqual(tag._convert_to_string(678024), '678024')

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, -57)
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 'invalid')
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 3.14)

    def test_convert_to_python_slong(self):
        type = 'SLong'

        # Valid values
        tag = ExifTagMock('Exif.OlympusCs.ManometerReading', type)
        self.assertEqual(tag._convert_to_python('23'), 23)
        self.assertEqual(tag._convert_to_python('+5628'), 5628)
        self.assertEqual(tag._convert_to_python('-437'), -437)

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, 'abc')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '5,64')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '47.0001')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '1E3')

    def test_convert_to_string_slong(self):
        type = 'SLong'

        # Valid values
        tag = ExifTagMock('Exif.OlympusCs.ManometerReading', type)
        self.assertEqual(tag._convert_to_string(123), '123')
        self.assertEqual(tag._convert_to_string(678024), '678024')
        self.assertEqual(tag._convert_to_string(-437), '-437')

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 'invalid')
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 3.14)

    def test_convert_to_python_rational(self):
        type = 'Rational'

        # Valid values
        tag = ExifTagMock('Exif.Image.XResolution', type)
        self.assertEqual(tag._convert_to_python('5/3'), Rational(5, 3))

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, 'invalid')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '-5/3')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '5 / 3')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '5/-3')

    def test_convert_to_string_rational(self):
        type = 'Rational'

        # Valid values
        tag = ExifTagMock('Exif.Image.XResolution', type)
        self.assertEqual(tag._convert_to_string(Rational(5, 3)), '5/3')

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 'invalid')
        self.failUnlessRaises(ExifValueError,
                              tag._convert_to_string, Rational(-5, 3))

    def test_convert_to_python_srational(self):
        type = 'SRational'

        # Valid values
        tag = ExifTagMock('Exif.Image.BaselineExposure', type)
        self.assertEqual(tag._convert_to_python('5/3'), Rational(5, 3))
        self.assertEqual(tag._convert_to_python('-5/3'), Rational(-5, 3))

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, 'invalid')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '5 / 3')
        self.failUnlessRaises(ExifValueError, tag._convert_to_python, '5/-3')

    def test_convert_to_string_srational(self):
        type = 'SRational'

        # Valid values
        tag = ExifTagMock('Exif.Image.BaselineExposure', type)
        self.assertEqual(tag._convert_to_string(Rational(5, 3)), '5/3')
        self.assertEqual(tag._convert_to_string(Rational(-5, 3)), '-5/3')

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 'invalid')

    def test_convert_to_python_undefined(self):
        type = 'Undefined'

        # Valid values
        tag = ExifTagMock('Exif.Photo.ExifVersion', type, '1.00')
        self.assertEqual(tag._convert_to_python('48 49 48 48 '), u'1.00')
        tag = ExifTagMock('Exif.Photo.DeviceSettingDescription', type, 'Digital still camera')
        self.assertEqual(tag._convert_to_python('3 '), u'Digital still camera')

    def test_convert_to_string_undefined(self):
        type = 'Undefined'

        # Valid values
        tag = ExifTagMock('Exif.Photo.ExifVersion', type)
        self.assertEqual(tag._convert_to_string('48 49 48 48 '), '48 49 48 48 ')
        self.assertEqual(tag._convert_to_string(u'48 49 48 48 '), '48 49 48 48 ')

        # Invalid values
        self.failUnlessRaises(ExifValueError, tag._convert_to_string, 3)

    def test_set_value_no_metadata(self):
        tag = ExifTag('Exif.Thumbnail.Orientation', 'Orientation',
                      'Orientation', 'The image orientation viewed in terms ' \
                      'of rows and columns.', 'Short', '1', 'top, left')
        old_value = tag.value
        tag.value = 2
        self.failIfEqual(tag.value, old_value)

    def test_set_value_with_metadata(self):
        tag = ExifTag('Exif.Thumbnail.Orientation', 'Orientation',
                      'Orientation', 'The image orientation viewed in terms ' \
                      'of rows and columns.', 'Short', '1', 'top, left')
        tag.metadata = ImageMetadataMock()
        old_value = tag.value
        tag.value = 2
        self.failIfEqual(tag.value, old_value)
        self.assertEqual(tag.metadata.tags[tag.key], '2')

    def test_del_value_no_metadata(self):
        tag = ExifTag('Exif.Thumbnail.Orientation', 'Orientation',
                      'Orientation', 'The image orientation viewed in terms ' \
                      'of rows and columns.', 'Short', '1', 'top, left')
        del tag.value
        self.failIf(hasattr(tag, 'value'))

    def test_del_value_with_metadata(self):
        tag = ExifTag('Exif.Thumbnail.Orientation', 'Orientation',
                      'Orientation', 'The image orientation viewed in terms ' \
                      'of rows and columns.', 'Short', '1', 'top, left')
        tag.metadata = ImageMetadataMock()
        tag.metadata._set_exif_tag_value(tag.key, str(tag))
        self.assertEqual(tag.metadata.tags, {tag.key: '1'})
        del tag.value
        self.failIf(hasattr(tag, 'value'))
        self.failIf(tag.metadata.tags.has_key(tag.key))
