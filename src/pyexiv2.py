#!/usr/bin/python
# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2006-2009 Olivier Tilloy <olivier@tilloy.net>
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
Manipulation of EXIF, IPTC and XMP metadata embedded in image files.

This module provides a single class, Image, and utility functions to manipulate
EXIF, IPTC and XMP metadata embedded in image files such as JPEG and TIFF files.
EXIF, IPTC and XMP metadata can be accessed in both read and write modes.

This module is a higher-level interface to the Python binding of the excellent
C++ library Exiv2, libpyexiv2.
Its only class, Image, inherits from libpyexiv2.Image and provides convenient
methods for the manipulation of EXIF and IPTC metadata using Python's built-in
types and modules such as datetime.
These methods should be preferred to the ones directly provided by
libpyexiv2.Image.

A typical use of this binding would be:

>>> import pyexiv2
>>> import datetime
>>> image = pyexiv2.Image('test/smiley.jpg')
>>> image.readMetadata()
>>> print image.exifKeys()
['Exif.Image.ImageDescription', 'Exif.Image.XResolution', 'Exif.Image.YResolution', 'Exif.Image.ResolutionUnit', 'Exif.Image.Software', 'Exif.Image.DateTime', 'Exif.Image.Artist', 'Exif.Image.Copyright', 'Exif.Image.ExifTag', 'Exif.Photo.Flash', 'Exif.Photo.PixelXDimension', 'Exif.Photo.PixelYDimension']
>>> print image['Exif.Image.DateTime']
2004-07-13 21:23:44
>>> image['Exif.Image.DateTime'] = datetime.datetime.today()
>>> image.writeMetadata()

"""

import libexiv2python

import os
import time
import datetime
import re


__version__ =  (0, 2, 1)

__exiv2_version__ = libexiv2python.__exiv2_version__


class FixedOffset(datetime.tzinfo):

    """
    Fixed offset from a local time east from UTC.

    Represent a fixed (positive or negative) offset from a local time in hours
    and minutes.

    Public methods:
    utcoffset -- return offset of local time from UTC, in minutes east of UTC
    dst -- return the daylight saving time (DST) adjustment, here always 0
    tzname -- return a string representation of the offset with format '±%H:%M'
    """

    def __init__(self, sign='+', hours=0, minutes=0):
        """
        Constructor.

        Construct a FixedOffset object from an offset sign ('+' or '-') and an
        offset absolute value expressed in hours and minutes.
        No check on the validity of those values is performed, it is the
        responsibility of the caller to pass correct values to the constructor.

        Keyword arguments:
        sign -- the sign of the offset ('+' or '-')
        hours -- the absolute number of hours of the offset
        minutes -- the absolute number of minutes of the offset
        """
        self.sign = sign
        self.hours = hours
        self.minutes = minutes

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
        total = self.hours * 60 + self.minutes
        if self.sign == '-':
            total = -total
        return datetime.timedelta(minutes = total)

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
        if self.hours == 0 and self.minutes == 0:
            return 'Z'
        else:
            return '%s%02d:%02d' % (self.sign, self.hours, self.minutes)

    def __equal__(self, other):
        return (self.sign == other.sign) and (self.hours == other.hours) and \
            (self.minutes == other.minutes)


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
    sequence of ascii codes, each followed by a blank space (e.g. "0221" will
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
    # TODO: move the declaration of this list at module level
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

class Rational:

    """
    A class representing a rational number.
    """

    def __init__(self, numerator, denominator):
        """
        Constructor.

        Construct a rational number from its numerator and its denominator.

        Keyword arguments:
        numerator -- the numerator
        denominator -- the denominator (if zero, will raise a ZeroDivisionError)
        """
        if int(denominator) == 0:
            raise ZeroDivisionError('Denominator of a rational number cannot be zero')
        self.numerator = long(numerator)
        self.denominator = long(denominator)

    def __eq__(self, other):
        """
        Compare two rational numbers for equality.

        Two rational numbers are equal if and only if their numerators are equal
        and their denominators are equal.

        Keyword arguments:
        other -- the rational number to compare to self for equality
        """
        return ((self.numerator == other.numerator) and
                (self.denominator == other.denominator))

    def __str__(self):
        """
        Return a string representation of the rational number.
        """
        return str(self.numerator) + '/' + str(self.denominator)

def StringToRational(string):
    """
    Try to convert a string containing a rational number to a Rational object.

    Try to convert a string containing a rational number to the corresponding
    Rational object.
    The conversion is done by matching a regular expression.
    If the pattern does not match, the Rational object with numerator=0 and
    denominator=1 is returned.

    Keyword arguments:
    string -- the string potentially containing a rational number
    """
    pattern = re.compile("(-?[0-9]+)/(-?[1-9][0-9]*)")
    match = pattern.match(string)
    if match == None:
        return Rational(0, 1)
    else:
        return Rational(*map(long, match.groups()))


class MetadataTag(object):

    """
    A generic metadata tag.

    TODO: determine which attributes are common to all types of tags (EXIF,
          IPTC and XMP), and which are specific.
    """

    def __init__(self, key, name, label, description, type, value):
        """
        Constructor.
        """
        self.key = key
        self.name = name
        self.label = label
        self.description = description
        self.type = type
        self._value = value
        self.value = value

    def __str__(self):
        """
        Return a string representation of the metadata tag.
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.type + os.linesep + \
            'Raw value = ' + str(self._value)
        return r


class ExifTag(MetadataTag):

    """
    An EXIF metadata tag has an additional field that contains the value
    of the tag formatted as a human readable string.
    """

    def __init__(self, key, name, label, description, type, value, fvalue):
        """
        Constructor.
        """
        MetadataTag.__init__(self, key, name, label, description, type, value)
        self.fvalue = fvalue
        self.__convert_value_to_python_type()

    def __convert_value_to_python_type(self):
        """
        Convert the stored value from a string to the matching Python type.
        """
        if self.type == 'Byte':
            pass
        elif self.type == 'Ascii':
            # try to guess if the value is a datetime
            self.value = StringToDateTime(self._value)
        elif self.type == 'Short':
            self.value = int(self._value)
        elif self.type == 'Long' or self.type == 'SLong':
            self.value = long(self._value)
        elif self.type == 'Rational' or self.type == 'SRational':
            self.value = StringToRational(self._value)
        elif self.type == 'Undefined':
            # self.value is a sequence of bytes whose codes are written as a
            # string, each code being followed by a blank space (e.g.
            # "48 50 50 49 " for "0221" in the "Exif.Photo.ExifVersion" tag).
            try:
                self.value = UndefinedToString(self._value)
            except ValueError:
                # Some tags such as "Exif.Photo.UserComment" are marked as
                # Undefined but do not store their value as expected.
                # This should fix bug #173387.
                pass

    def __str__(self):
        """
        Return a string representation of the EXIF tag.
        """
        r = MetadataTag.__str__(self)
        r += os.linesep + 'Formatted value = ' + self.fvalue
        return r


class IptcTag(MetadataTag):

    """
    An IPTC metadata tag can have several values (tags that have the repeatable
    property).
    """

    def __init__(self, key, name, label, description, type, values):
        """
        Constructor.
        """
        MetadataTag.__init__(self, key, name, label, description, type, values)
        self.__convert_values_to_python_type()

    def __convert_values_to_python_type(self):
        """
        Convert the stored values from strings to the matching Python type.
        """
        if self.type == 'Short':
            self.value = map(int, self._value)
        elif self.type == 'String':
            pass
        elif self.type == 'Date':
            self.value = map(StringToDate, self._value)
        elif self.type == 'Time':
            self.value = map(StringToTime, self._value)
        elif self.type == 'Undefined':
            pass

    def __str__(self):
        """
        Return a string representation of the IPTC tag.
        """
        r = MetadataTag.__str__(self)
        return r.replace('Raw value = ', 'Raw values = ')


class XmpValueError(ValueError):
    def __init__(self, value, xtype):
        self.value = value
        self.xtype = xtype

    def __str__(self):
        return 'Invalid value for XMP type [%s]: [%s]' % \
               (self.xtype, self.value)


class XmpTag(MetadataTag):

    """
    An XMP metadata tag can have several values.
    """

    # strptime is not flexible enough to handle all valid Date formats, we use a
    # custom regular expression
    _time_zone_re = r'Z|((?P<sign>\+|-)(?P<ohours>\d{2}):(?P<ominutes>\d{2}))'
    _time_re = r'(?P<hours>\d{2})(:(?P<minutes>\d{2})(:(?P<seconds>\d{2})(.(?P<decimal>\d+))?)?(?P<tzd>%s))?' % _time_zone_re
    _date_re = re.compile(r'(?P<year>\d{4})(-(?P<month>\d{2})(-(?P<day>\d{2})(T(?P<time>%s))?)?)?' % _time_re)

    def __init__(self, key, name, label, description, type, values):
        """
        Constructor.
        """
        MetadataTag.__init__(self, key, name, label, description, type, values)
        self.value = map(lambda x: XmpTag._convert_to_python(x, self.type), self.value)

    @staticmethod
    def _convert_to_python(value, xtype):
        """
        Convert a value to its corresponding python type.

        @param value: the value to be converted, as a string
        @type value:  C{str}
        @param xtype: the XMP type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on xtype (DOCME)

        @raise L{XmpValueError}: if the conversion fails
        """
        if xtype.startswith('bag '):
            values = value.split(', ')
            return map(lambda x: XmpTag._convert_to_python(x, xtype[4:]), values)

        elif xtype == 'Boolean':
            if value == 'True':
                return True
            elif value == 'False':
                return False
            else:
                raise XmpValueError(value, xtype)

        elif xtype == 'Choice':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % xtype)

        elif xtype == 'Colorant':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % xtype)

        elif xtype == 'Date':
            match = XmpTag._date_re.match(value)
            if match is None:
                raise XmpValueError(value, xtype)
            gd = match.groupdict()
            if gd['month'] is not None:
                month = int(gd['month'])
            else:
                month = 1
            if gd['day'] is not None:
                day = int(gd['day'])
            else:
                day = 1
            if gd['time'] is None:
                try:
                    return datetime.date(int(gd['year']), month, day)
                except ValueError:
                    raise XmpValueError(value, xtype)
            else:
                if gd['minutes'] is None:
                    # Malformed time
                    raise XmpValueError(value, xtype)
                if gd['seconds'] is not None:
                    seconds = int(gd['seconds'])
                else:
                    seconds = 0
                if gd['decimal'] is not None:
                    microseconds = int(float('0.%s' % gd['decimal']) * 1E6)
                else:
                    microseconds = 0
                if gd['tzd'] == 'Z':
                    tzinfo = FixedOffset()
                else:
                    tzinfo = FixedOffset(gd['sign'], int(gd['ohours']),
                                         int(gd['ominutes']))
                try:
                    return datetime.datetime(int(gd['year']), month, day,
                                             int(gd['hours']), int(gd['minutes']),
                                             seconds, microseconds, tzinfo)
                except ValueError:
                    raise XmpValueError(value, xtype)

        elif xtype == 'Dimensions':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % xtype)

        elif xtype == 'Font':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % xtype)

        elif xtype == 'Integer':
            try:
                return int(value)
            except ValueError:
                raise XmpValueError(value, xtype)

        elif xtype == 'Lang Alt':
            matches = value.split('lang="')
            nb = len(matches)
            if nb < 2 or matches[0] != '':
                raise XmpValueError(value, xtype)
            result = {}
            for i, match in enumerate(matches[1:]):
                try:
                    qualifier, text = match.split('" ', 1)
                except ValueError:
                    raise XmpValueError(value, xtype)
                else:
                    if not text.rstrip().endswith(','):
                        if (i < nb - 2):
                            # If not the last match, it should end with a comma
                            raise XmpValueError(value, xtype)
                        else:
                            result[qualifier] = text
                            try:
                                result[qualifier] = unicode(text, 'utf-8')
                            except TypeError:
                                raise XmpValueError(value, xtype)
                    else:
                        try:
                            result[qualifier] = unicode(text.rstrip()[:-1], 'utf-8')
                        except TypeError:
                            raise XmpValueError(value, xtype)
            return result

        elif xtype == 'Locale':
            # TODO
            # See RFC 3066
            raise NotImplementedError('XMP conversion for type [%s]' % xtype)

        elif xtype == 'MIMEType':
            try:
                mtype, msubtype = value.split('/', 1)
            except ValueError:
                raise XmpValueError(value, xtype)
            else:
                return {'type': mtype, 'subtype': msubtype}

        elif xtype == 'Real':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % xtype)

        elif xtype in ('ProperName', 'Text'):
            try:
                return unicode(value, 'utf-8')
            except TypeError:
                raise XmpValueError(value, xtype)

        elif xtype == 'Thumbnail':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % xtype)

        elif xtype in ('URI', 'URL'):
            return value

        elif xtype == 'XPath':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % xtype)

        raise NotImplementedError('XMP conversion for type [%s]' % xtype)

    @staticmethod
    def _convert_to_string(value, xtype):
        """
        Convert a value to its corresponding string representation.

        @param value: the value to be converted
        @type value:  depends on xtype (DOCME)
        @param xtype: the XMP type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise L{XmpValueError}: if the conversion fails
        """
        if xtype == 'Boolean' and type(value) is bool:
            return str(value)

        elif xtype == 'Date':
            if type(value) is datetime.date:
                return value.isoformat()
            elif type(value) is datetime.datetime:
                if value.hour == 0 and value.minute == 0 and \
                    value.second == 0 and value.microsecond == 0 and \
                    (value.tzinfo is None or value.tzinfo == FixedOffset()):
                    return value.strftime('%Y-%m-%d')
                elif value.second == 0 and value.microsecond == 0:
                    return value.strftime('%Y-%m-%dT%H:%M%Z')
                elif value.microsecond == 0:
                    return value.strftime('%Y-%m-%dT%H:%M:%S%Z')
                else:
                    r = value.strftime('%Y-%m-%dT%H:%M:%S.')
                    r += str(int(value.microsecond) / 1E6)[2:]
                    r += value.strftime('%Z')
                    return r
            else:
                raise XmpValueError(value, xtype)

        elif xtype == 'Integer':
            if type(value) in (int, long):
                return str(value)
            else:
                raise XmpValueError(value, xtype)

        elif xtype == 'Lang Alt':
            if type(value) is dict and len(value) > 0:
                r = ''
                for key, avalue in value.iteritems():
                    if type(key) is unicode:
                        try:
                            rkey = key.encode('utf-8')
                        except UnicodeEncodeError:
                            raise XmpValueError(value, xtype)
                    elif type(key) is str:
                        rkey = key
                    else:
                        raise XmpValueError(value, xtype)
                    if type(avalue) is unicode:
                        try:
                            ravalue = avalue.encode('utf-8')
                        except UnicodeEncodeError:
                            raise XmpValueError(value, xtype)
                    elif type(avalue) is str:
                        ravalue = avalue
                    else:
                        raise XmpValueError(value, xtype)
                    r += 'lang="%s" %s, ' % (rkey, ravalue)
                return r[:-2]
            else:
                raise XmpValueError(value, xtype)

        elif xtype == 'MIMEType':
            if type(value) is dict:
                try:
                    return '%s/%s' % (value['type'], value['subtype'])
                except KeyError:
                    raise XmpValueError(value, xtype)
            else:
                raise XmpValueError(value, xtype)

        elif xtype in ('ProperName', 'Text'):
            if type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise XmpValueError(value, xtype)
            elif type(value) is str:
                return value
            else:
                raise XmpValueError(value, xtype)

        raise XmpValueError(value, xtype)

    def __str__(self):
        """
        Return a string representation of the XMP tag.
        """
        r = MetadataTag.__str__(self)
        return r.replace('Raw value = ', 'Raw values = ')


class Image(libexiv2python.Image):

    """
    Provide convenient methods for the manipulation of EXIF, IPTC and XMP
    metadata.

    Provide convenient methods for the manipulation of EXIF, IPTC and XMP
    metadata embedded in image files such as JPEG and TIFF files, using Python's
    built-in types and modules such as datetime.
    """

    def __init__(self, filename):
        f = filename
        if f.__class__ is unicode:
            f = f.encode('utf-8')
        libexiv2python.Image.__init__(self, f)
        self.__exifTagsDict = {}
        self.__iptcTagsDict = {}
        self.__exifCached = False
        self.__iptcCached = False

    def __get_exif_tag(self, key):
        """
        DOCME
        """
        tag = ExifTag(*self.__getExifTag(key))
        return tag

    def __get_iptc_tag(self, key):
        """
        DOCME
        """
        tag = IptcTag(*self.__getIptcTag(key))
        return tag

    def __getExifTagValue(self, key):
        """
        Get the value associated to a key in EXIF metadata.

        Get the value associated to a key in EXIF metadata.
        Whenever possible, the value is typed using Python's built-in types or
        modules such as datetime when the value is composed of a date and a time
        (e.g. the EXIF tag 'Exif.Photo.DateTimeOriginal').

        Keyword arguments:
        key -- the EXIF key of the requested metadata tag
        """
        tagType, tagValue = self.__getExifTag(key)
        if tagType not in ('Byte', 'Ascii', 'Undefined'):
            values = [ConvertToPythonType('Exif', tagType, x) for x in tagValue.split()]
            if len(values) == 1:
                return values[0]
            else:
                return tuple(values)
        else:
            return ConvertToPythonType('Exif', tagType, tagValue)

    def __setExifTagValue(self, key, value):
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
        elif valueType == list or valueType == tuple:
            strVal = ' '.join([str(x) for x in value])
        else:
            # Value must already be a string.
            # Warning: no distinction is possible between values that really are
            # strings (type 'Ascii') and those that are supposed to be sequences
            # of bytes (type 'Undefined'), in which case value must be passed as
            # a string correctly formatted, using utility function
            # StringToUndefined().
            strVal = str(value)
        typeName, oldValue = self.__setExifTag(key, strVal)
        return typeName

    def __getIptcTagValue(self, key):
        """
        Get the value(s) associated to a key in IPTC metadata.

        Get the value associated to a key in IPTC metadata.
        Whenever possible, the value is typed using Python's built-in types or
        modules such as date when the value represents a date (e.g. the IPTC tag
        'Iptc.Application2.DateCreated').
        If key represents a repeatable tag, a list of several values is
        returned. If not, or if it has only one repetition, the list simply has
        one element.

        Keyword arguments:
        key -- the IPTC key of the requested metadata tag
        """
        return [ConvertToPythonType('Iptc', *x) for x in self.__getIptcTag(key)]

    def __setIptcTagValue(self, key, value, index=0):
        """
        Set the value associated to a key in IPTC metadata.

        Set the value associated to a key in IPTC metadata.
        The new value passed should be typed using Python's built-in types or
        modules such as datetime when the value contains a date or a time
        (e.g. the IPTC tags 'Iptc.Application2.DateCreated' and
        'Iptc.Application2.TimeCreated'), the method takes care
        of converting it before setting the internal IPTC tag value.
        If key references a repeatable tag, the parameter index (starting from
        0 like a list index) is used to determine which of the repetitions is to
        be set. In case of an index greater than the highest existing one, adds
        a repetition of the tag. index defaults to 0 for (the majority of)
        non-repeatable tags.

        Keyword arguments:
        key -- the IPTC key of the requested metadata tag
        value -- the new value for the requested metadata tag
        index -- the index of the tag repetition to set (default value: 0)
        """
        if (index < 0):
            raise IndexError('Index must be greater than or equal to zero')
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
        typeName, oldValue = self.__setIptcTag(key, strVal, index)
        return typeName

    def __getitem__(self, key):
        """
        Read access implementation of the [] operator on Image objects.

        Get the value associated to a key in EXIF/IPTC metadata.
        The value is cached in an internal dictionary for later accesses.

        Whenever possible, the value is typed using Python's built-in types or
        modules such as datetime when the value is composed of a date and a time
        (e.g. the EXIF tag 'Exif.Photo.DateTimeOriginal') or date when the value
        represents a date (e.g. the IPTC tag 'Iptc.Application2.DateCreated').

        If key references a repeatable tag (IPTC only), a list of several values
        is returned. If not, or if it has only one repetition, the list simply
        has one element.

        Keyword arguments:
        key -- the [EXIF|IPTC] key of the requested metadata tag
        """
        if key.__class__ is not str:
            raise TypeError('Key must be of type string')
        tagFamily = key[:4]
        if tagFamily == 'Exif':
            try:
                return self.__exifTagsDict[key]
            except KeyError:
                value = self.__getExifTagValue(key)
                self.__exifTagsDict[key] = value
                return value
        elif tagFamily == 'Iptc':
            try:
                return self.__iptcTagsDict[key]
            except KeyError:
                value = self.__getIptcTagValue(key)
                if len(value) == 1:
                    value = value[0]
                elif len(value) > 1:
                    value = tuple(value)
                self.__iptcTagsDict[key] = value
                return value
        else:
            # This is exiv2's standard error message, all futures changes on
            # exiv2's side should be reflected here.
            # As a future development, consider i18n for error messages. 
            raise IndexError("Invalid key `" + key + "'")

    def __setitem__(self, key, value):
        """
        Write access implementation of the [] operator on Image objects.

        Set the value associated to a key in EXIF/IPTC metadata.
        The value is cached in an internal dictionary for later accesses.

        The new value passed should be typed using Python's built-in types or
        modules such as datetime when the value contains a date and a time
        (e.g. the EXIF tag 'Exif.Photo.DateTimeOriginal' or the IPTC tags
        'Iptc.Application2.DateCreated' and 'Iptc.Application2.TimeCreated'),
        the method takes care of converting it before setting the internal tag
        value.

        If key references a repeatable tag (IPTC only), value can be a list of
        values (the new values will overwrite the old ones, and an empty list of
        values will unset the tag).

        Keyword arguments:
        key -- the [EXIF|IPTC] key of the requested metadata tag
        value -- the new value for the requested metadata tag
        """
        if key.__class__ is not str:
            raise TypeError('Key must be of type string')
        tagFamily = key[:4]
        if tagFamily == 'Exif':
            if value is not None:
                # For datetime objects, microseconds are not supported by the
                # EXIF specification, so truncate them if present.
                if value.__class__ is datetime.datetime:
                    value = value.replace(microsecond=0)

                typeName = self.__setExifTagValue(key, value)
                self.__exifTagsDict[key] = ConvertToPythonType(tagFamily, typeName, str(value))
            else:
                self.__deleteExifTag(key)
                if self.__exifTagsDict.has_key(key):
                    del self.__exifTagsDict[key]
        elif tagFamily == 'Iptc':
            # The case of IPTC tags is a bit trickier since some tags are
            # repeatable. To simplify the process, parameter 'value' is
            # transformed into a tuple if it is not already one and then each of
            # its values is processed (set, that is) in a loop.
            newValues = value
            if newValues is None:
                # Setting the value to None does not really make sense, but can
                # in a way be seen as equivalent to deleting it, so this
                # behaviour is simulated by providing an empty list for 'value'.
                newValues = ()
            if newValues.__class__ is not tuple:
                if newValues.__class__ is list:
                    # For flexibility, passing a list instead of a tuple works
                    newValues = tuple(newValues)
                else:
                    # Interpret the value as a single element
                    newValues = (newValues,)
            try:
                oldValues = self.__iptcTagsDict[key]
                if oldValues.__class__ is not tuple:
                    oldValues = (oldValues,)
            except KeyError:
                # The tag is not cached yet
                try:
                    oldValues = self.__getitem__(key)
                except KeyError:
                    # The tag is not set
                    oldValues = ()

            # For time objects, microseconds are not supported by the IPTC
            # specification, so truncate them if present.
            tempNewValues = []
            for newValue in newValues:
                if newValue.__class__ is datetime.time:
                    tempNewValues.append(newValue.replace(microsecond=0))
                else:
                    tempNewValues.append(newValue)
            newValues = tuple(tempNewValues)

            # This loop processes the values one by one. There are 3 cases:
            #   * if the two tuples are of the exact same size, each item in
            #     oldValues is replaced by its new value in newValues;
            #   * if newValues is longer than oldValues, each item in oldValues
            #     is replaced by its new value in newValues and the new items
            #     are appended at the end of oldValues;
            #   * if newValues is shorter than oldValues, each item in newValues
            #     replaces the corresponding one in oldValues and the trailing
            #     extra items in oldValues are deleted.
            for i in xrange(max(len(oldValues), len(newValues))):
                try:
                    typeName = self.__setIptcTagValue(key, newValues[i], i)
                except IndexError:
                    try:
                        self.__deleteIptcTag(key, min(len(oldValues), len(newValues)))
                    except KeyError:
                        pass
            if len(newValues) > 0:
                if len(newValues) == 1:
                    newValues = newValues[0]
                self.__iptcTagsDict[key] = tuple([ConvertToPythonType(tagFamily, typeName, str(v)) for v in newValues])
            else:
                if self.__iptcTagsDict.has_key(key):
                    del self.__iptcTagsDict[key]
        else:
            raise IndexError("Invalid key `" + key + "'")

    def __delitem__(self, key):
        """
        Implementation of the del operator for deletion on Image objects.

        Delete the value associated to a key in EXIF/IPTC metadata.

        If key references a repeatable tag (IPTC only), all the associated
        values will be deleted.

        Keyword arguments:
        key -- the [EXIF|IPTC] key of the requested metadata tag
        """
        if key.__class__ is not str:
            raise TypeError('Key must be of type string')
        tagFamily = key[:4]
        if tagFamily == 'Exif':
            self.__deleteExifTag(key)
            if self.__exifTagsDict.has_key(key):
                del self.__exifTagsDict[key]
        elif tagFamily == 'Iptc':
            try:
                oldValues = self.__iptcTagsDict[key]
            except KeyError:
                oldValues = self.__getIptcTag(key)
            for i in xrange(len(oldValues)):
                self.__deleteIptcTag(key, 0)
            if self.__iptcTagsDict.has_key(key):
                del self.__iptcTagsDict[key]
        else:
            raise IndexError("Invalid key `" + key + "'")

    def cacheAllExifTags(self):
        """
        Cache the EXIF tag values for faster subsequent access.

        Read the values of all the EXIF tags in the image and cache them in an
        internal dictionary so as to speed up subsequent accesses.
        """
        if not self.__exifCached:
            for key in self.exifKeys():
                self[key]
            self.__exifCached = True

    def cacheAllIptcTags(self):
        """
        Cache the IPTC tag values for faster subsequent access.

        Read the values of all the IPTC tags in the image and cache them in an
        internal dictionary so as to speed up subsequent accesses.
        """
        if not self.__iptcCached:
            for key in self.iptcKeys():
                self[key]
            self.__iptcCached = True

    def interpretedExifValue(self, key):
        """
        Get the interpreted value of an EXIF tag as presented by the exiv2 tool.

        For EXIF tags, the exiv2 command-line tool is capable of displaying
        user-friendly interpreted values, such as 'top, left' for the
        'Exif.Image.Orientation' tag when it has value '1'. This method always
        returns a string containing this interpreted value for a given tag.
        Warning: calling this method will not cache the value in the internal
        dictionary.

        Keyword arguments:
        key -- the EXIF key of the requested metadata tag
        """
        # This method was added as a requirement tracked by bug #147534
        return self.__getExifTagToString(key)

    def copyMetadataTo(self, destImage):
        # TODO: add optional parameters exif=True, iptc=True, xmp=True, so that
        # one can choose to copy only part of the metadata.
        """
        Duplicate all the tags and the comment from this image to another one.

        Read all the values of the EXIF and IPTC tags and the comment and write
        them back to the new image.

        Keyword arguments:
        destImage -- the destination image to write the copied metadata back to
        """
        for key in self.exifKeys():
            destImage[key] = self[key]
        for key in self.iptcKeys():
            destImage[key] = self[key]
        destImage.setComment(self.getComment())

