#!/usr/bin/python
# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2006 Olivier Tilloy <olivier@tilloy.net>
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
# File:      pyexiv2.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

"""
Manipulation of EXIF and IPTC metadata embedded in image files.

This module provides a single class, Image, and utility functions to manipulate
EXIF and IPTC metadata embedded in image files such as JPEG and TIFF files.
EXIF and IPTC metadata can be accessed in both read and write modes.

This module is a higher-level interface to the Python binding of the excellent
C++ library Exiv2, libpyexiv2.
Its only class, Image, inherits from libpyexiv2.Image and provides convenient
methods for the manipulation of EXIF and IPTC metadata using Python's built-in
types and modules such as datetime.
These methods should be preferred to the ones directly provided by
libpyexiv2.Image.

A typical use of this binding is as follows:

	import pyexiv2
	import datetime
	image = pyexiv2.Image('path/to/imagefile')
	image.readMetadata()
	print image.getAvailableExifTags()
	print image.getExifTagValue('Exif.Photo.DateTimeOriginal')
	today = datetime.datetime.today()
	image.setExifTagValue('Exif.Photo.DateTimeOriginal', today)
	image.writeMetadata()
	...

"""

import libpyexiv2

import time
import datetime
import re

class FixedOffset(datetime.tzinfo):

	"""
	Fixed offset from a local time east from UTC.

	Represent a fixed (positive or negative) offset from a local time in hours
	and minutes.

	Public methods:
	utcoffset -- return offset of local time from UTC, in minutes east of UTC
	dst -- return the daylight saving time (DST) adjustment, here always 0
	tzname -- return a string representation of the offset with format '±%H%M'
	"""

	def __init__(self, offsetSign='+', offsetHours=0, offsetMinutes=0):
		"""
		Constructor.

		Construct a FixedOffset object from an offset sign ('+' or '-') and an
		offset absolute value expressed in hours and minutes.
		No check on the validity of those values is performed, it is the
		responsibility of the caller to pass correct values to the constructor.

		Keyword arguments:
		offsetSign -- the sign of the offset ('+' or '-')
		offsetHours -- the absolute number of hours of the offset
		offsetMinutes -- the absolute number of minutes of the offset
		"""
		self.offsetSign = offsetSign
		self.offsetHours = offsetHours
		self.offsetMinutes = offsetMinutes

	def utcoffset(self, dt):
		"""
		Return offset of local time from UTC, in minutes east of UTC.

		Return offset of local time from UTC, in minutes east of UTC.
		If local time is west of UTC, this should be negative.
		The value returned is a datetime.timedelta object specifying a whole
		number of minutes in the range -1439 to 1439 inclusive.

		Keyword arguments:
		dt -- the datetime.time object representing the local time
		"""
		totalOffsetMinutes = self.offsetHours * 60 + self.offsetMinutes
		if self.offsetSign == '-':
			totalOffsetMinutes = -totalOffsetMinutes
		return datetime.timedelta(minutes = totalOffsetMinutes)

	def dst(self, dt):
		"""
		Return the daylight saving time (DST) adjustment.

		Return the daylight saving time (DST) adjustment.
		In this implementation, it is always nil, and the method return
		datetime.timedelta(0).

		Keyword arguments:
		dt -- the datetime.time object representing the local time
		"""
		return datetime.timedelta(0)

	def tzname(self, dt):
		"""
		Return a string representation of the offset.

		Return a string representation of the offset with format '±%H:%M'.

		Keyword arguments:
		dt -- the datetime.time object representing the local time
		"""
		string = self.offsetSign
		string = string + ('%02d' % self.offsetHours) + ':'
		string = string + ('%02d' % self.offsetMinutes)
		return string

def UndefinedToString(undefined):
	"""
	Convert an undefined string into its corresponding sequence of bytes.

	Convert a string containing the ascii codes of a sequence of bytes, each
	followed by a blank space, into the corresponding string (e.g.
	"48 50 50 49 " will be converted into "0221").
	The Undefined type is defined in the EXIF specification.

	Keyword arguments:
	undefined -- the string containing the ascii codes of a sequence of bytes
	"""
	return ''.join(map(lambda x: chr(int(x)), undefined.rstrip().split(' ')))

def StringToUndefined(sequence):
	"""
	Convert a string containing a sequence of bytes into its undefined form.

	Convert a string containing a sequence of bytes into the corresponding
	sequence of ascii codes, each	followed by a blank space (e.g. "0221" will
	be converted into "48 50 50 49 ").
	The Undefined type is defined in the EXIF specification.

	Keyword arguments:
	sequence -- the string containing the sequence of bytes
	"""
	return ''.join(map(lambda x: '%d ' % ord(x), sequence))

def StringToDateTime(string):
	"""
	Try to convert a string containing a date and time to a datetime object.

	Try to convert a string containing a date and time to the corresponding
	datetime object. The conversion is done by trying several patterns for
	regular expression matching.
	If no pattern matches, the string is returned unchanged.

	Keyword arguments:
	string -- the string potentially containing a date and time
	"""
	# Possible formats to try
	# According to the EXIF specification [http://www.exif.org/Exif2-2.PDF], the
	# only accepted format for a string field representing a datetime is
	# '%Y-%m-%d %H:%M:%S', but it seems that others formats can be found in the
	# wild, so this list could be extended to include new exotic formats.
	formats = ['%Y-%m-%d %H:%M:%S', '%Y:%m:%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']

	for format in formats:
		try:
			t = time.strptime(string, format)
			return datetime.datetime(*t[:6])
		except ValueError:
			# the tested format does not match, do nothing
			pass

	# none of the tested formats matched, return the original string unchanged
	return string

def StringToDate(string):
	"""
	Try to convert a string containing a date to a date object.

	Try to convert a string containing a date to the corresponding date object.
	The conversion is done by matching a regular expression.
	If the pattern does not match, the string is returned unchanged.

	Keyword arguments:
	string -- the string potentially containing a date
	"""
	# According to the IPTC specification
	# [http://www.iptc.org/std/IIM/4.1/specification/IIMV4.1.pdf], the format
	# for a string field representing a date is '%Y%m%d'.
	# However, the string returned by exiv2 using method DateValue::toString()
	# is formatted using pattern '%Y-%m-%d'.
	format = '%Y-%m-%d'
	try:
		t = time.strptime(string, format)
		return datetime.date(*t[:3])
	except ValueError:
		# the tested format does not match, do nothing
		return string

def StringToTime(string):
	"""
	Try to convert a string containing a time to a time object.

	Try to convert a string containing a time to the corresponding time object.
	The conversion is done by matching a regular expression.
	If the pattern does not match, the string is returned unchanged.

	Keyword arguments:
	string -- the string potentially containing a time
	"""
	# According to the IPTC specification
	# [http://www.iptc.org/std/IIM/4.1/specification/IIMV4.1.pdf], the format
	# for a string field representing a time is '%H%M%S±%H%M'.
	# However, the string returned by exiv2 using method TimeValue::toString()
	# is formatted using pattern '%H:%M:%S±%H:%M'.

	if len(string) != 14:
		# the string is not correctly formatted, do nothing
		return string

	if (string[2] != ':') or (string[5] != ':') or (string[11] != ':'):
		# the string is not correctly formatted, do nothing
		return string

	offsetSign = string[8]
	if (offsetSign != '+') and (offsetSign != '-'):
		# the string is not correctly formatted, do nothing
		return string

	try:
		hours = int(string[:2])
		minutes = int(string[3:5])
		seconds = int(string[6:8])
		offsetHours = int(string[9:11])
		offsetMinutes = int(string[12:])
	except ValueError:
		# the string is not correctly formatted, do nothing
		return string

	try:
		offset = FixedOffset(offsetSign, offsetHours, offsetMinutes)
		localTime = datetime.time(hours, minutes, seconds, tzinfo=offset)
	except ValueError:
		# the values are out of range, do nothing
		return string

	return localTime

class Image(libpyexiv2.Image):

	"""
	Provide convenient methods for the manipulation of EXIF and IPTC metadata.

	Provide convenient methods for the manipulation of EXIF and IPTC metadata
	embedded in image files such as JPEG and TIFF files, using Python's built-in
	types and modules such as datetime.

	Public methods:
	getExifTagValue -- get the value associated to a key in EXIF metadata
	setExifTagValue -- set the value associated to a key in EXIF metadata
	getIptcTagValue -- get the value associated to a key in IPTC metadata
	setIptcTagValue -- set the value associated to a key in IPTC metadata
	"""

	def getExifTagValue(self, key):
		"""
		Get the value associated to a key in EXIF metadata.

		Get the value associated to a key in EXIF metadata.
		Whenever possible, the value is typed using Python's built-in types or
		modules such as datetime when the value is composed of a date and a time
		(e.g. the EXIF tag 'Exif.Photo.DateTimeOriginal').

		Keyword arguments:
		key -- the EXIF key of the requested metadata tag
		"""
		tagType, tagValue = self.getExifTag(key)
		if tagType == 'Byte':
			return tagValue
		elif tagType == 'Ascii':
			# try to guess if the value is a datetime
			return StringToDateTime(tagValue)
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
			# tagValue is a sequence of bytes whose codes are written as a
			# string, each code being followed by a blank space (e.g.
			# "48 50 50 49 " for "0221").
			# Note: in the case of tag "Exif.Photo.UserComment", it is better to
			# call method getExifTagToString() to obtain directly the value as a
			# human-readable string.
			return UndefinedToString(tagValue)

	def setExifTagValue(self, key, value):
		"""
		Set the value associated to a key in EXIF metadata.

		Set the value associated to a key in EXIF metadata.
		The new value passed should be typed using Python's built-in types or
		modules such as datetime when the value is composed of a date and a time
		(e.g. the EXIF tag 'Exif.Photo.DateTimeOriginal'), the method takes care
		of converting it before setting the internal EXIF tag value.

		Keyword arguments:
		key -- the EXIF key of the requested metadata tag
		value -- the new value for the requested metadata tag
		"""
		valueType = value.__class__
		if valueType == int or valueType == long:
			strVal = str(value)
		elif valueType == datetime.datetime:
			strVal = value.strftime('%Y:%m:%d %H:%M:%S')
		elif valueType == tuple:
			strVal = '%s/%s' % (str(value[0]), str(value[1]))
		else:
			# Value must already be a string.
			# Warning: no distinction is possible between values that really are
			# strings (type 'Ascii') and those that are supposed to be sequences
			# of bytes (type 'Undefined'), in which case value must be passed as
			# a string correctly formatted, using utility function
			# StringToUndefined().
			strVal = str(value)
		self.setExifTag(key, strVal)

	def getIptcTagValue(self, key):
		"""
		Get the value associated to a key in IPTC metadata.

		Get the value associated to a key in IPTC metadata.
		Whenever possible, the value is typed using Python's built-in types or
		modules such as date when the value represents a date (e.g. the IPTC tag
		'Iptc.Application2.DateCreated').

		Keyword arguments:
		key -- the IPTC key of the requested metadata tag
		"""
		tagType, tagValue = self.getIptcTag(key)
		if tagType == 'Short':
			return int(tagValue)
		elif tagType == 'String':
			return tagValue
		elif tagType == 'Date':
			return StringToDate(tagValue)
		elif tagType == 'Time':
			return StringToTime(tagValue)
		elif tagType == 'Undefined':
			return tagValue

	def setIptcTagValue(self, key, value):
		"""
		Set the value associated to a key in IPTC metadata.

		Set the value associated to a key in IPTC metadata.
		The new value passed should be typed using Python's built-in types or
		modules such as datetime when the value contains a date or a time
		(e.g. the IPTC tags 'Iptc.Application2.DateCreated' and
		'Iptc.Application2.TimeCreated'), the method takes care
		of converting it before setting the internal IPTC tag value.

		Keyword arguments:
		key -- the IPTC key of the requested metadata tag
		value -- the new value for the requested metadata tag
		"""
		valueType = value.__class__
		if valueType == int or valueType == long:
			strVal = str(value)
		elif valueType == datetime.date:
			strVal = value.strftime('%Y-%m-%d')
		elif valueType == datetime.time:
			# The only legal format for a time is '%H:%M:%S±%H:%M',
			# but if the UTC offset is absent (format '%H:%M:%S'), the time can
			# still be set (exiv2 is permissive).
			strVal = value.strftime('%H:%M:%S%Z')
		else:
			# Value must already be a string.
			# Warning: no distinction is possible between values that really are
			# strings (type 'String') and those that are of type 'Undefined'.
			# FIXME: for tags of type 'Undefined', this does not seem to work...
			strVal = str(value)
		self.setIptcTag(key, strVal)

def _test():
	print 'testing library pyexiv2...'
	# TODO: various tests
	print 'done.'

if __name__ == '__main__':
	_test()
