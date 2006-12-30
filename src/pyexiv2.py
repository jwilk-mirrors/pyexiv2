#!/usr/bin/python
# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2006 Olivier Tilloy <olivier@tilloy.net>
#
# This program is part of the pyexiv2 distribution.
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
# File:      pyexiv2.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
# History:   28-Dec-06, Olivier Tilloy: created
#
# ******************************************************************************

import libpyexiv2

import re
import datetime

def UndefinedToString(undefined):
	# undefined must be a string containing the ascii codes of a sequence of
	# bytes, each followed by a blank space (e.g. "48 50 50 49 " for "0221")
	return ''.join(map(lambda x: chr(int(x)), undefined.rstrip().split(' ')))

def StringToUndefined(string):
	# string must be a string containing a sequence of ascii representations
	# of bytes, to be converted in the suitable format for the type
	# 'Undefined' in EXIF specification (e.g. "0221" will be converted into
	# "48 50 50 49 ")
	return ''.join(map(lambda x: '%d ' % ord(x), string))

class Image(libpyexiv2.Image):
	"""
	A class that extends the methods of class libpyexiv2.Image with "higher
	level methods", making use of Python's built-in types and classes such as
	datetime.
	"""
	def getExifTagValue(self, key):
		tagType, tagValue = self.getExifTag(key)
		if tagType == 'Byte':
			return tagValue
		elif tagType == 'Ascii':
			# tries to guess if the value is a datetime
			pattern = re.compile("([0-9]{4}):([0-9]{2}):([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})")
			match = pattern.match(tagValue)
			if match == None:
				return tagValue.strip()
			else:
				v = map(int, match.groups())
				return datetime.datetime(v[0], v[1], v[2], v[3], v[4], v[5])
		elif tagType == 'Short':
			return int(tagValue)
		elif tagType == 'Long' or tagType == 'SLong':
			return long(tagValue)
		# for Rational and SRational types, we use tuples
		# TODO: define a rational type?
		elif tagType == 'Rational':
			pattern = re.compile("([0-9]+)/([1-9][0-9]*)")
			match = pattern.match(tagValue)
			if match == None:
				return long(0), long(1)
			else:
				v = map(long, match.groups())
				return v[0], v[1]
		elif tagType == 'SRational':
			pattern = re.compile("(-?[0-9]+)/(-?[1-9][0-9]*)")
			match = pattern.match(tagValue)
			if match == None:
				return long(0), long(1)
			else:
				v = map(long, match.groups())
				return v[0], v[1]
		elif tagType == 'Undefined':
			# tagValue is a sequence of bytes whose codes are written as
			# a string, each code being followed by a blank space
			# (e.g. "48 50 50 49 " for "0221")
			# Note: in the case of tag "Exif.Photo.UserComment", it is
			# better to call method getExifTagToString() to obtain
			# directly the value as a human-readable string
			return UndefinedToString(tagValue)
		else:
			# empty type and value
			return

	def setExifTagValue(self, key, value):
		valueType = value.__class__
		if valueType == int or valueType == long:
			strVal = str(value)
		elif valueType == datetime.datetime:
			strVal = value.strftime('%Y:%m:%d %H:%M:%S')
		elif valueType == tuple:
			strVal = '%s/%s' % (str(value[0]), str(value[1]))
		else:
			# value must already be a string
			# warning: no distinction is possible between values that
			# really are strings (type 'Ascii') and those that are
			# supposed to be sequences of bytes (type 'Undefined'), in
			# which case value must be passed as a string correctly
			# formatted, using function StringToUndefined()
			strVal = value
		self.setExifTag(key, strVal)
