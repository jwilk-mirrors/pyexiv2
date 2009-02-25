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
from pyexiv2 import IptcTag, IptcValueError, FixedOffset
import datetime


class TestIptcTag(unittest.TestCase):

    def test_convert_to_python_short(self):
        xtype = 'Short'
        # Valid values
        self.assertEqual(IptcTag._convert_to_python('23', xtype), 23)
        self.assertEqual(IptcTag._convert_to_python('+5628', xtype), 5628)
        self.assertEqual(IptcTag._convert_to_python('-4', xtype), -4)
        # Invalid values
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, 'abc', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '5,64', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '47.0001', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '1E3', xtype)

    def test_convert_to_string_short(self):
        xtype = 'Short'
        # Valid values
        self.assertEqual(IptcTag._convert_to_string(123, xtype), '123')
        self.assertEqual(IptcTag._convert_to_string(-57, xtype), '-57')
        # Invalid values
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_string, 'invalid', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_string, '3.14', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_string, '1E3', xtype)

    def test_convert_to_python_string(self):
        xtype = 'String'
        # Valid values
        self.assertEqual(IptcTag._convert_to_python('Some text.', xtype), u'Some text.')
        self.assertEqual(IptcTag._convert_to_python('Some text with exotic chàräctérʐ.', xtype),
                         u'Some text with exotic chàräctérʐ.')
        # Invalid values
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, None, xtype)

    def test_convert_to_string_string(self):
        xtype = 'String'
        # Valid values
        self.assertEqual(IptcTag._convert_to_string(u'Some text', xtype), 'Some text')
        self.assertEqual(IptcTag._convert_to_string(u'Some text with exotic chàräctérʐ.', xtype),
                         'Some text with exotic chàräctérʐ.')
        self.assertEqual(IptcTag._convert_to_string('Some text with exotic chàräctérʐ.', xtype),
                         'Some text with exotic chàräctérʐ.')
        # Invalid values
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_string, None, xtype)

    def test_convert_to_python_date(self):
        xtype = 'Date'
        # Valid values
        self.assertEqual(IptcTag._convert_to_python('1999-10-13', xtype),
                         datetime.date(1999, 10, 13))
        # Invalid values
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, 'invalid', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '11/10/1983', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '-1000', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '2009-02', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '2009-10-32', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '2009-02-24T22:12:54', xtype)

    def test_convert_to_string_date(self):
        xtype = 'Date'
        # Valid values
        self.assertEqual(IptcTag._convert_to_string(datetime.date(2009, 2, 4), xtype),
                         '20090204')
        self.assertEqual(IptcTag._convert_to_string(datetime.datetime(1999, 10, 13), xtype),
                         '19991013')
        self.assertEqual(IptcTag._convert_to_string(datetime.datetime(2009, 2, 4), xtype),
                         '20090204')
        self.assertEqual(IptcTag._convert_to_string(datetime.datetime(2009, 2, 4, 10, 52, 37), xtype),
                         '20090204')
        # Invalid values
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_string, 'invalid', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_string, None, xtype)

    def test_convert_to_python_time(self):
        xtype = 'Time'
        # Valid values
        self.assertEqual(IptcTag._convert_to_python('05:03:54+00:00', xtype),
                         datetime.time(5, 3, 54, tzinfo=FixedOffset()))
        self.assertEqual(IptcTag._convert_to_python('05:03:54+06:00', xtype),
                         datetime.time(5, 3, 54, tzinfo=FixedOffset('+', 6, 0)))
        self.assertEqual(IptcTag._convert_to_python('05:03:54-10:30', xtype),
                         datetime.time(5, 3, 54, tzinfo=FixedOffset('-', 10, 30)))
        # Invalid values
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, 'invalid', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '23:12:42', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '25:12:42+00:00', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '21:77:42+00:00', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '21:12:98+00:00', xtype)
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, '081242+0000', xtype)

    def test_convert_to_string_time(self):
        xtype = 'Time'
        # Valid values
        self.assertEqual(IptcTag._convert_to_string(datetime.time(10, 52, 4), xtype),
                         '105204+0000')
        self.assertEqual(IptcTag._convert_to_string(datetime.time(10, 52, 4, 574), xtype),
                         '105204+0000')
        self.assertEqual(IptcTag._convert_to_string(datetime.time(10, 52, 4, tzinfo=FixedOffset()), xtype),
                         '105204+0000')
        self.assertEqual(IptcTag._convert_to_string(datetime.time(10, 52, 4, tzinfo=FixedOffset('+', 5, 30)), xtype),
                         '105204+0530')
        self.assertEqual(IptcTag._convert_to_string(datetime.time(10, 52, 4, tzinfo=FixedOffset('-', 4, 0)), xtype),
                         '105204-0400')
        self.assertEqual(IptcTag._convert_to_string(datetime.datetime(2007, 2, 7, 10, 52, 4), xtype),
                         '105204+0000')
        self.assertEqual(IptcTag._convert_to_string(datetime.datetime(2007, 2, 7, 10, 52, 4, 478), xtype),
                         '105204+0000')
        self.assertEqual(IptcTag._convert_to_string(datetime.datetime(2007, 2, 7, 10, 52, 4, tzinfo=FixedOffset()), xtype),
                         '105204+0000')
        self.assertEqual(IptcTag._convert_to_string(datetime.datetime(2007, 2, 7, 10, 52, 4, tzinfo=FixedOffset('+', 5, 30)), xtype),
                         '105204+0530')
        self.assertEqual(IptcTag._convert_to_string(datetime.datetime(2007, 2, 7, 10, 52, 4, tzinfo=FixedOffset('-', 4, 0)), xtype),
                         '105204-0400')
        # Invalid values
        self.failUnlessRaises(IptcValueError, IptcTag._convert_to_python, 'invalid', xtype)

    def test_convert_to_python_undefined(self):
        xtype = 'Undefined'
        # Valid values
        self.assertEqual(IptcTag._convert_to_python('Some binary data.', xtype),
                         'Some binary data.')
        self.assertEqual(IptcTag._convert_to_python('�lj1�eEϟ�u����ᒻ;C(�SpI]���QI�}', xtype),
                         '�lj1�eEϟ�u����ᒻ;C(�SpI]���QI�}')
