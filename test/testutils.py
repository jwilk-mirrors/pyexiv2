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
# File:      testutils.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import hashlib

def CheckFileSum(filename, md5sum):
    """
    Test the MD5 sum of a given file against the expected value.

    Keyword arguments:
    filename -- the name of the file to test
    md5sum -- the expected value of the MD5 sum of the file
    """
    f = open(filename)
    return (hashlib.md5(f.read()).hexdigest() == md5sum)

