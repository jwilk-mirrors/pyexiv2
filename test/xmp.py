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

from pyexiv2.xmp import XmpTag, XmpValueError
from pyexiv2.utils import FixedOffset

import datetime


class ImageMetadataMock(object):

    tags = {}

    def _set_xmp_tag_value(self, key, value):
        self.tags[key] = value


class TestXmpTag(unittest.TestCase):

    def test_convert_to_python_bag(self):
        # Valid values
        tag = XmpTag('Xmp.dc.subject')
        self.assertEqual(tag.type, 'bag Text')
        self.assertEqual(tag._convert_to_python('', 'Text'), u'')
        self.assertEqual(tag._convert_to_python('One value only', 'Text'),
                         u'One value only')

    def test_convert_to_string_bag(self):
        # Valid values
        tag = XmpTag('Xmp.dc.subject')
        self.assertEqual(tag.type, 'bag Text')
        self.assertEqual(tag._convert_to_string(u'', 'Text'), '')
        self.assertEqual(tag._convert_to_string('One value only', 'Text'), 'One value only')
        self.assertEqual(tag._convert_to_string(u'One value only', 'Text'), 'One value only')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, [1, 2, 3], 'Text')

    def test_convert_to_python_boolean(self):
        # Valid values
        tag = XmpTag('Xmp.xmpRights.Marked')
        self.assertEqual(tag.type, 'Boolean')
        self.assertEqual(tag._convert_to_python('True', 'Boolean'), True)
        self.assertEqual(tag._convert_to_python('False', 'Boolean'), False)
        # Invalid values: not converted
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, 'invalid', 'Boolean')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, None, 'Boolean')

    def test_convert_to_string_boolean(self):
        # Valid values
        tag = XmpTag('Xmp.xmpRights.Marked')
        self.assertEqual(tag.type, 'Boolean')
        self.assertEqual(tag._convert_to_string(True, 'Boolean'), 'True')
        self.assertEqual(tag._convert_to_string(False, 'Boolean'), 'False')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, 'invalid', 'Boolean')
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, None, 'Boolean')

    def test_convert_to_python_date(self):
        # Valid values
        tag = XmpTag('Xmp.xmp.CreateDate')
        self.assertEqual(tag.type, 'Date')
        self.assertEqual(tag._convert_to_python('1999', 'Date'),
                         datetime.date(1999, 1, 1))
        self.assertEqual(tag._convert_to_python('1999-10', 'Date'),
                         datetime.date(1999, 10, 1))
        self.assertEqual(tag._convert_to_python('1999-10-13', 'Date'),
                         datetime.date(1999, 10, 13))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03Z', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset()),
                         datetime.timedelta(0))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03+06:00', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset('+', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03-06:00', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset('-', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03:54Z', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, tzinfo=FixedOffset()),
                         datetime.timedelta(0))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03:54+06:00', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, tzinfo=FixedOffset('+', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03:54-06:00', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, tzinfo=FixedOffset('-', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03:54.721Z', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, 721000, tzinfo=FixedOffset()),
                         datetime.timedelta(0))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03:54.721+06:00', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, 721000, tzinfo=FixedOffset('+', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(tag._convert_to_python('1999-10-13T05:03:54.721-06:00', 'Date') - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, 721000, tzinfo=FixedOffset('-', 6, 0)),
                         datetime.timedelta(0))
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, 'invalid', 'Date')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '11/10/1983', 'Date')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '-1000', 'Date')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '2009-13', 'Date')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '2009-10-32', 'Date')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '2009-10-30T25:12Z', 'Date')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '2009-10-30T23:67Z', 'Date')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '2009-01-22T21', 'Date')

    def test_convert_to_string_date(self):
        # Valid values
        tag = XmpTag('Xmp.xmp.CreateDate')
        self.assertEqual(tag.type, 'Date')
        self.assertEqual(tag._convert_to_string(datetime.date(2009, 2, 4), 'Date'),
                         '2009-02-04')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13), 'Date'),
                         '1999-10-13')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset()), 'Date'),
                         '1999-10-13T05:03Z')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset('+', 5, 30)), 'Date'),
                         '1999-10-13T05:03+05:30')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset('-', 11, 30)), 'Date'),
                         '1999-10-13T05:03-11:30')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, 27, tzinfo=FixedOffset()), 'Date'),
                         '1999-10-13T05:03:27Z')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, 27, tzinfo=FixedOffset('+', 5, 30)), 'Date'),
                         '1999-10-13T05:03:27+05:30')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, 27, tzinfo=FixedOffset('-', 11, 30)), 'Date'),
                         '1999-10-13T05:03:27-11:30')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, 27, 124300, tzinfo=FixedOffset()), 'Date'),
                         '1999-10-13T05:03:27.1243Z')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, 27, 124300, tzinfo=FixedOffset('+', 5, 30)), 'Date'),
                         '1999-10-13T05:03:27.1243+05:30')
        self.assertEqual(tag._convert_to_string(datetime.datetime(1999, 10, 13, 5, 3, 27, 124300, tzinfo=FixedOffset('-', 11, 30)), 'Date'),
                         '1999-10-13T05:03:27.1243-11:30')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, 'invalid', 'Date')
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, None, 'Date')

    def test_convert_to_python_integer(self):
        # Valid values
        tag = XmpTag('Xmp.xmpMM.SaveID')
        self.assertEqual(tag.type, 'Integer')
        self.assertEqual(tag._convert_to_python('23', 'Integer'), 23)
        self.assertEqual(tag._convert_to_python('+5628', 'Integer'), 5628)
        self.assertEqual(tag._convert_to_python('-4', 'Integer'), -4)
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, 'abc', 'Integer')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '5,64', 'Integer')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '47.0001', 'Integer')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, '1E3', 'Integer')

    def test_convert_to_string_integer(self):
        # Valid values
        tag = XmpTag('Xmp.xmpMM.SaveID')
        self.assertEqual(tag.type, 'Integer')
        self.assertEqual(tag._convert_to_string(123, 'Integer'), '123')
        self.assertEqual(tag._convert_to_string(-57, 'Integer'), '-57')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, 'invalid', 'Integer')
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, 3.14, 'Integer')

    def test_convert_to_python_mimetype(self):
        # Valid values
        tag = XmpTag('Xmp.dc.format')
        self.assertEqual(tag.type, 'MIMEType')
        self.assertEqual(tag._convert_to_python('image/jpeg', 'MIMEType'),
                         ('image', 'jpeg'))
        self.assertEqual(tag._convert_to_python('video/ogg', 'MIMEType'),
                         ('video', 'ogg'))
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, 'invalid', 'MIMEType')
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, 'image-jpeg', 'MIMEType')

    def test_convert_to_string_mimetype(self):
        # Valid values
        tag = XmpTag('Xmp.dc.format')
        self.assertEqual(tag.type, 'MIMEType')
        self.assertEqual(tag._convert_to_string(('image', 'jpeg'), 'MIMEType'), 'image/jpeg')
        self.assertEqual(tag._convert_to_string(('video', 'ogg'), 'MIMEType'), 'video/ogg')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, 'invalid', 'MIMEType')
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, ('image',), 'MIMEType')

    def test_convert_to_python_propername(self):
        # Valid values
        tag = XmpTag('Xmp.photoshop.CaptionWriter')
        self.assertEqual(tag.type, 'ProperName')
        self.assertEqual(tag._convert_to_python('Gérard', 'ProperName'), u'Gérard')
        self.assertEqual(tag._convert_to_python('Python Software Foundation', 'ProperName'), u'Python Software Foundation')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, None, 'ProperName')

    def test_convert_to_string_propername(self):
        # Valid values
        tag = XmpTag('Xmp.photoshop.CaptionWriter')
        self.assertEqual(tag.type, 'ProperName')
        self.assertEqual(tag._convert_to_string('Gérard', 'ProperName'), 'Gérard')
        self.assertEqual(tag._convert_to_string(u'Gérard', 'ProperName'), 'Gérard')
        self.assertEqual(tag._convert_to_string(u'Python Software Foundation', 'ProperName'), 'Python Software Foundation')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, None, 'ProperName')

    def test_convert_to_python_text(self):
        # Valid values
        tag = XmpTag('Xmp.dc.source')
        self.assertEqual(tag.type, 'Text')
        self.assertEqual(tag._convert_to_python('Some text.', 'Text'), u'Some text.')
        self.assertEqual(tag._convert_to_python('Some text with exotic chàräctérʐ.', 'Text'),
                         u'Some text with exotic chàräctérʐ.')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_python, None, 'Text')

    def test_convert_to_string_text(self):
        # Valid values
        tag = XmpTag('Xmp.dc.source')
        self.assertEqual(tag.type, 'Text')
        self.assertEqual(tag._convert_to_string(u'Some text', 'Text'), 'Some text')
        self.assertEqual(tag._convert_to_string(u'Some text with exotic chàräctérʐ.', 'Text'),
                         'Some text with exotic chàräctérʐ.')
        self.assertEqual(tag._convert_to_string('Some text with exotic chàräctérʐ.', 'Text'),
                         'Some text with exotic chàräctérʐ.')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, None, 'Text')

    def test_convert_to_python_uri(self):
        # Valid values
        tag = XmpTag('Xmp.xmpMM.DocumentID')
        self.assertEqual(tag.type, 'URI')
        self.assertEqual(tag._convert_to_python('http://example.com', 'URI'), 'http://example.com')
        self.assertEqual(tag._convert_to_python('https://example.com', 'URI'), 'https://example.com')
        self.assertEqual(tag._convert_to_python('http://localhost:8000/resource', 'URI'),
                         'http://localhost:8000/resource')
        self.assertEqual(tag._convert_to_python('uuid:9A3B7F52214211DAB6308A7391270C13', 'URI'),
                         'uuid:9A3B7F52214211DAB6308A7391270C13')

    def test_convert_to_string_uri(self):
        # Valid values
        tag = XmpTag('Xmp.xmpMM.DocumentID')
        self.assertEqual(tag.type, 'URI')
        self.assertEqual(tag._convert_to_string('http://example.com', 'URI'), 'http://example.com')
        self.assertEqual(tag._convert_to_string(u'http://example.com', 'URI'), 'http://example.com')
        self.assertEqual(tag._convert_to_string('https://example.com', 'URI'), 'https://example.com')
        self.assertEqual(tag._convert_to_string('http://localhost:8000/resource', 'URI'),
                         'http://localhost:8000/resource')
        self.assertEqual(tag._convert_to_string('uuid:9A3B7F52214211DAB6308A7391270C13', 'URI'),
                         'uuid:9A3B7F52214211DAB6308A7391270C13')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, None, 'URI')

    def test_convert_to_python_url(self):
        # Valid values
        tag = XmpTag('Xmp.xmp.BaseURL')
        self.assertEqual(tag.type, 'URL')
        self.assertEqual(tag._convert_to_python('http://example.com', 'URL'), 'http://example.com')
        self.assertEqual(tag._convert_to_python('https://example.com', 'URL'), 'https://example.com')
        self.assertEqual(tag._convert_to_python('http://localhost:8000/resource', 'URL'),
                         'http://localhost:8000/resource')

    def test_convert_to_string_url(self):
        # Valid values
        tag = XmpTag('Xmp.xmp.BaseURL')
        self.assertEqual(tag.type, 'URL')
        self.assertEqual(tag._convert_to_string('http://example.com', 'URL'), 'http://example.com')
        self.assertEqual(tag._convert_to_string(u'http://example.com', 'URL'), 'http://example.com')
        self.assertEqual(tag._convert_to_string('https://example.com', 'URL'), 'https://example.com')
        self.assertEqual(tag._convert_to_string('http://localhost:8000/resource', 'URL'),
                         'http://localhost:8000/resource')
        # Invalid values
        self.failUnlessRaises(XmpValueError, tag._convert_to_string, None, 'URL')

    # TODO: other types


    def test_set_value_no_metadata(self):
        tag = XmpTag('Xmp.xmp.ModifyDate', datetime.datetime(2005, 9, 7, 15, 9, 51, tzinfo=FixedOffset('-', 7, 0)))
        old_value = tag.value
        tag.value = datetime.datetime(2009, 4, 22, 8, 30, 27, tzinfo=FixedOffset())
        self.failIfEqual(tag.value, old_value)

    def test_set_value_with_metadata(self):
        tag = XmpTag('Xmp.xmp.ModifyDate', datetime.datetime(2005, 9, 7, 15, 9, 51, tzinfo=FixedOffset('-', 7, 0)))
        tag.metadata = ImageMetadataMock()
        old_value = tag.value
        tag.value = datetime.datetime(2009, 4, 22, 8, 30, 27, tzinfo=FixedOffset())
        self.failIfEqual(tag.value, old_value)
        self.assertEqual(tag.metadata.tags[tag.key], '2009-04-22T08:30:27Z')

