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
# File:      Bug173387_TestCase.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
import testutils
import os.path
import pyexiv2

class Bug173387_TestCase(unittest.TestCase):

    """
    Test case for bug #173387.

    Summary: Error reading Exif.Photo.UserComment.
    Description: Trying to read the value of EXIF tag 'Exif.Photo.UserComment'
    fails if the comment is not encoded as an ASCII string.
    Fix: fixed with revision 77.
    """

    def testEmptyUserComment(self):
        """
        Test reading a so-called "empty" user comment (full of \x00 characters).
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'bug173387_empty_usercomment.jpg')
        md5sum = '75e5f18aece0955b518cefe1ffd30b7c'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        image = pyexiv2.Image(filename)
        image.readMetadata()
        self.assertEqual(image['Exif.Photo.UserComment'], '\x00' * 256)

    def testCorruptedUserComment(self):
        """
        Test reading a corrupted user comment (full of non printable
        characters).
        """
        # Check that the reference file is not corrupted
        filename = os.path.join('data', 'bug173387_corrupted_usercomment.jpg')
        md5sum = '8007ac7357213fd2787bc817a6d7cd1d'
        self.assert_(testutils.CheckFileSum(filename, md5sum))

        image = pyexiv2.Image(filename)
        image.readMetadata()
        evalue = 'charset="InvalidCharsetId" \xff\xff\xaa\x00X\x00@\x00a\x00@\xff\xbb\x00x\x14F9\x05\x00\x08\xff\xcc\xff\xff\xff\xff\xff\xff\xff\xff\xff\xdd\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00<\x00\x00\x00\x00\x00\x00\x00X\x02\x00\x00s\x00\x00\x00\x00\x00\x00\x00@\xb2#\x8c\x00\x00\x00\x01J\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8c\x1e\x00\x00p:\xac\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00<R\x14\x8cx$\x03\x8cDR\x14\x8c\xa8+\x14\x8c\x00\x00\x00\x00x.\x14\x8c\x00\x00\x00\x00\x00\x00\x00\x00\x98s\x01\x00\x10\x00\x00\x00\x18\x08\x15\x8c `\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18\x03\xe7\x00\x08\x00\x00\x02\x00@\x00\x00\t\x05\x00\x00\x19\x03\x00\x00\x03\x06\x10\x01\x80\x84\x1a\x8c\x08O\x1a\x8c\xf0L\x1a\x8c\x00\x00\x00\x00\x00\x00\x00\x00\x80D\x1a\x8c\x01\x00\x00\x00\xf0\x94\x15\xac'
        self.assertEqual(image['Exif.Photo.UserComment'], evalue)

