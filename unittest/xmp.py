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
from pyexiv2 import XmpTag, FixedOffset
import datetime

class TestXmpTag(unittest.TestCase):

    def test_convert_to_python_boolean(self):
        xtype = 'Boolean'
        # Valid values
        self.assertEqual(XmpTag._convert_to_python('True', xtype), True)
        self.assertEqual(XmpTag._convert_to_python('False', xtype), False)
        # Invalid values: not converted
        self.assertEqual(XmpTag._convert_to_python('invalid', xtype), 'invalid')

    def test_convert_to_python_choice(self):
        pass

    def test_convert_to_python_colorant(self):
        pass

    def test_convert_to_python_date(self):
        xtype = 'Date'
        # Valid values
        self.assertEqual(XmpTag._convert_to_python('1999', xtype),
                         datetime.date(1999, 1, 1))
        self.assertEqual(XmpTag._convert_to_python('1999-10', xtype),
                         datetime.date(1999, 10, 1))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13', xtype),
                         datetime.date(1999, 10, 13))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03Z', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset()),
                         datetime.timedelta(0))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03+06:00', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset('+', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03-06:00', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, tzinfo=FixedOffset('-', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03:54Z', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, tzinfo=FixedOffset()),
                         datetime.timedelta(0))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03:54+06:00', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, tzinfo=FixedOffset('+', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03:54-06:00', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, tzinfo=FixedOffset('-', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03:54.721Z', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, 721000, tzinfo=FixedOffset()),
                         datetime.timedelta(0))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03:54.721+06:00', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, 721000, tzinfo=FixedOffset('+', 6, 0)),
                         datetime.timedelta(0))
        self.assertEqual(XmpTag._convert_to_python('1999-10-13T05:03:54.721-06:00', xtype) - \
                         datetime.datetime(1999, 10, 13, 5, 3, 54, 721000, tzinfo=FixedOffset('-', 6, 0)),
                         datetime.timedelta(0))
        # Invalid values
        self.assertEqual(XmpTag._convert_to_python('invalid', xtype), 'invalid')
        self.assertEqual(XmpTag._convert_to_python('11/10/1983', xtype), '11/10/1983')

        # FIXME: the following test should not fail: having hours without minutes is not a valid syntax.
        self.assertEqual(XmpTag._convert_to_python('2009-01-22T21', xtype), '2009-01-22T21')

    def test_convert_to_python_integer(self):
        xtype = 'Integer'
        # Valid values
        self.assertEqual(XmpTag._convert_to_python('23', xtype), 23)
        self.assertEqual(XmpTag._convert_to_python('+5628', xtype), 5628)
        self.assertEqual(XmpTag._convert_to_python('-4', xtype), -4)
        # Invalid values
        self.assertEqual(XmpTag._convert_to_python('abc', xtype), 'abc')
        self.assertEqual(XmpTag._convert_to_python('5,64', xtype), '5,64')
        self.assertEqual(XmpTag._convert_to_python('47.0001', xtype), '47.0001')
        self.assertEqual(XmpTag._convert_to_python('1E3', xtype), '1E3')

    def test_convert_to_python_langalt(self):
        xtype = 'Lang Alt'
        # Valid values
        self.assertEqual(XmpTag._convert_to_python('lang="x-default" some text', xtype),
                         {'x-default': 'some text'})
        self.assertEqual(XmpTag._convert_to_python('lang="x-default" some text, lang="fr-FR" du texte', xtype),
                         {'x-default': 'some text', 'fr-FR': 'du texte'})
        self.assertEqual(XmpTag._convert_to_python('lang="x-default" some text   ,    lang="fr-FR"   du texte  ', xtype),
                         {'x-default': 'some text   ', 'fr-FR': '  du texte  '})
        self.assertEqual(XmpTag._convert_to_python('lang="x-default" some text, lang="fr-FR" du texte, lang="es-ES" un texto', xtype),
                         {'x-default': 'some text', 'fr-FR': 'du texte', 'es-ES': 'un texto'})
        # Invalid values
        self.assertEqual(XmpTag._convert_to_python('invalid', xtype), 'invalid')
        self.assertEqual(XmpTag._convert_to_python('lang="malformed', xtype), 'lang="malformed')
        self.assertEqual(XmpTag._convert_to_python('xlang="x-default" some text', xtype), 'xlang="x-default" some text')
        self.assertEqual(XmpTag._convert_to_python('lang="x-default" some text, xlang="fr-FR" du texte', xtype), 'lang="x-default" some text, xlang="fr-FR" du texte')

    def test_convert_to_python_mimetype(self):
        xtype = 'MIMEType'
        # Valid values
        self.assertEqual(XmpTag._convert_to_python('image/jpeg', xtype),
                         {'type': 'image', 'subtype': 'jpeg'})
        self.assertEqual(XmpTag._convert_to_python('video/ogg', xtype),
                         {'type': 'video', 'subtype': 'ogg'})
        # Invalid values
        self.assertEqual(XmpTag._convert_to_python('invalid', xtype), 'invalid')
        self.assertEqual(XmpTag._convert_to_python('image-jpeg', xtype), 'image-jpeg')

    def test_convert_to_python_text(self):
        xtype = 'Text'
        # Valid values
        self.assertEqual(XmpTag._convert_to_python('Some text.', xtype), u'Some text.')
        self.assertEqual(XmpTag._convert_to_python(u'Some text.', xtype), u'Some text.')
        self.assertEqual(XmpTag._convert_to_python('Some text with exotic chàräctérʐ.', xtype),
                         u'Some text with exotic chàräctérʐ.')
        self.assertEqual(XmpTag._convert_to_python(u'Some text with exotic chàräctérʐ.', xtype),
                         u'Some text with exotic chàräctérʐ.')
        # Invalid values
        self.assertEqual(XmpTag._convert_to_python(12, xtype), 12)
        self.assertEqual(XmpTag._convert_to_python(3.14, xtype), 3.14)

    def test_convert_to_python_uri(self):
        xtype = 'URI'
        # Valid values
        self.assertEqual(XmpTag._convert_to_python('http://example.com', xtype), 'http://example.com')
        self.assertEqual(XmpTag._convert_to_python('https://example.com', xtype), 'https://example.com')
        self.assertEqual(XmpTag._convert_to_python('http://localhost:8000/resource', xtype),
                         'http://localhost:8000/resource')
        self.assertEqual(XmpTag._convert_to_python('uuid:9A3B7F52214211DAB6308A7391270C13', xtype),
                         'uuid:9A3B7F52214211DAB6308A7391270C13')

    def test_convert_to_python_url(self):
        xtype = 'URL'
        # Valid values
        self.assertEqual(XmpTag._convert_to_python('http://example.com', xtype), 'http://example.com')
        self.assertEqual(XmpTag._convert_to_python('https://example.com', xtype), 'https://example.com')
        self.assertEqual(XmpTag._convert_to_python('http://localhost:8000/resource', xtype),
                         'http://localhost:8000/resource')

    # TODO: other types
