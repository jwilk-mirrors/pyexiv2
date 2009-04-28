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
# Author: Olivier Tilloy <olivier@tilloy.net>
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


class Rational(object):

    """
    A class representing a rational number.
    """

    _format_re = re.compile(r'(?P<numerator>-?\d+)/(?P<denominator>\d+)')

    def __init__(self, numerator, denominator):
        """
        Constructor.

        @param numerator:   the numerator
        @type numerator:    C{long}
        @param denominator: the denominator
        @type denominator:  C{long}

        @raise C{ZeroDivisionError}: if the denominator equals zero
        """
        if denominator == 0:
            msg = 'Denominator of a rational number cannot be zero.'
            raise ZeroDivisionError(msg)
        self.numerator = long(numerator)
        self.denominator = long(denominator)

    @staticmethod
    def from_string(string):
        """
        Instantiate a Rational from a string formatted as
        C{[-]numerator/denominator}.

        @param string: a string representation of a rational number
        @type string:  C{str}

        @return: the rational number parsed
        @rtype:  L{Rational}

        @raise ValueError: if the format of the string is invalid
        """
        match = Rational._format_re.match(string)
        if match is None:
            raise ValueError('Invalid format for a rational: %s' % string)
        gd = match.groupdict()
        return Rational(long(gd['numerator']), long(gd['denominator']))

    def __eq__(self, other):
        """
        Compare two rational numbers for equality.

        Two rational numbers are equal if their reduced forms are equal.

        @param other: the rational number to compare to self for equality
        @type other:  L{Rational}
        
        @return: C{True} if equal, C{False} otherwise
        @rtype:  C{bool}
        """
        return (self.numerator * other.denominator) == \
               (other.numerator * self.denominator)

    def __str__(self):
        """
        Return a string representation of the rational number.
        """
        return '%d/%d' % (self.numerator, self.denominator)


class ListenerInterface(object):
    # Define an interface that an object that wants to listen to changes on a
    # notifying list should implement.

    def item_changed(self, index, item):
        raise NotImplementedError()

    def item_deleted(self, index):
        raise NotImplementedError()

    def item_appended(self, item):
        raise NotImplementedError()

    # TODO: define other methods.


class NotifyingList(list):

    """
    DOCME
    Not asynchronous.
    """

    # file:///usr/share/doc/python2.5/html/lib/typesseq-mutable.html
    # http://docs.python.org/reference/datamodel.html#additional-methods-for-emulation-of-sequence-types

    def __init__(self, items=[]):
        super(NotifyingList, self).__init__(items)
        self._listeners = set()

    def register_listener(self, listener):
        self._listeners.add(listener)

    def unregister_listener(self, listener):
        self._listeners.remove(listener)

    def _notify_listeners(self, method_name, *args):
        for listener in self._listeners:
            getattr(listener, method_name)(*args)

    def __setitem__(self, index, item):
        # FIXME: support slice arguments
        super(NotifyingList, self).__setitem__(index, item)
        self._notify_listeners('item_changed', index, item)

    def __delitem__(self, index):
        # FIXME: support slice arguments
        super(NotifyingList, self).__delitem__(index)
        self._notify_listeners('item_deleted', index)

    def append(self, item):
        super(NotifyingList, self).append(item)
        self._notify_listeners('item_appended', item)


class MetadataTag(object):

    """
    A generic metadata tag.
    DOCME
    """

    def __init__(self, key, name, label, description, xtype, value):
        """
        Constructor.
        """
        self.key = key
        self.name = name
        self.label = label
        self.description = description
        self.xtype = xtype
        self.raw_value = value
        # Reference to the containing ImageMetadata object
        self.metadata = None

    def __str__(self):
        """
        Return a string representation of the metadata tag.
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.xtype + os.linesep + \
            'Raw value = ' + str(self.raw_value)
        return r


class ExifValueError(ValueError):
    def __init__(self, value, xtype):
        self.value = value
        self.xtype = xtype

    def __str__(self):
        return 'Invalid value for EXIF type [%s]: [%s]' % \
               (self.xtype, self.value)


class ExifTag(MetadataTag):

    """
    An EXIF metadata tag has an additional field that contains the value
    of the tag formatted as a human readable string.
    """

    # According to the EXIF specification, the only accepted format for an Ascii
    # value representing a datetime is '%Y:%m:%d %H:%M:%S', but it seems that
    # others formats can be found in the wild.
    _datetime_formats = ('%Y:%m:%d %H:%M:%S',
                         '%Y-%m-%d %H:%M:%S',
                         '%Y-%m-%dT%H:%M:%SZ')

    def __init__(self, key, name, label, description, xtype, value, fvalue):
        """
        Constructor.
        """
        super(ExifTag, self).__init__(key, name, label, description, xtype, value)
        self.fvalue = fvalue
        if xtype in ('Short', 'Long', 'SLong', 'Rational', 'SRational'):
            # May contain multiple values
            values = value.split()
            if len(values) > 1:
                self._value = map(lambda x: ExifTag._convert_to_python(x, xtype), values)
                return
        self._value = ExifTag._convert_to_python(value, xtype, fvalue)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if self.metadata is not None:
            raw_value = ExifTag._convert_to_string(new_value, self.xtype)
            self.metadata._set_exif_tag_value(self.key, raw_value)
        self._value = new_value

    def _del_value(self):
        if self.metadata is not None:
            self.metadata._delete_exif_tag(self.key)
        del self._value

    # DOCME
    value = property(fget=_get_value, fset=_set_value, fdel=_del_value,
                     doc=None)

    @staticmethod
    def _convert_to_python(value, xtype, fvalue):
        """
        Convert a value to its corresponding python type.

        @param value:  the value to be converted, as a string
        @type value:   C{str}
        @param xtype:  the EXIF type of the value
        @type xtype:   C{str}
        @param fvalue: the value formatted as a human-readable string by exiv2
        @type fvalue:  C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on xtype (DOCME)

        @raise L{ExifValueError}: if the conversion fails
        """
        if xtype == 'Ascii':
            # The value may contain a Datetime
            for format in ExifTag._datetime_formats:
                try:
                    t = time.strptime(value, format)
                except ValueError:
                    continue
                else:
                    return datetime.datetime(*t[:6])
            # Default to string
            try:
                return unicode(value, 'utf-8')
            except TypeError:
                raise ExifValueError(value, xtype)

        elif xtype == 'Byte':
            return value

        elif xtype == 'Short':
            try:
                return int(value)
            except ValueError:
                raise ExifValueError(value, xtype)

        elif xtype in ('Long', 'SLong'):
            try:
                return long(value)
            except ValueError:
                raise ExifValueError(value, xtype)

        elif xtype in ('Rational', 'SRational'):
            try:
                r = Rational.from_string(value)
            except (ValueError, ZeroDivisionError):
                raise ExifValueError(value, xtype)
            else:
                if xtype == 'Rational' and r.numerator < 0:
                    raise ExifValueError(value, xtype)
                return r

        elif xtype == 'Undefined':
            try:
                return unicode(fvalue, 'utf-8')
            except TypeError:
                raise ExifValueError(fvalue, xtype)

        raise ExifValueError(value, xtype)

    @staticmethod
    def _convert_to_string(value, xtype):
        """
        Convert a value to its corresponding string representation.

        @param value: the value to be converted
        @type value:  depends on xtype (DOCME)
        @param xtype: the EXIF type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise L{ExifValueError}: if the conversion fails
        """
        if xtype == 'Ascii':
            if type(value) is datetime.datetime:
                return value.strftime('%Y:%m:%d %H:%M:%S')
            elif type(value) is datetime.date:
                return value.strftime('%Y:%m:%d 00:00:00')
            elif type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise ExifValueError(value, xtype)
            elif type(value) is str:
                return value
            else:
                raise ExifValueError(value, xtype) 

        elif xtype == 'Byte':
            if type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise ExifValueError(value, xtype)
            elif type(value) is str:
                return value
            else:
                raise ExifValueError(value, xtype)

        elif xtype == 'Short':
            if type(value) is int and value >= 0:
                return str(value)
            else:
                raise ExifValueError(value, xtype)

        elif xtype == 'Long':
            if type(value) in (int, long) and value >= 0:
                return str(value)
            else:
                raise ExifValueError(value, xtype)

        elif xtype == 'SLong':
            if type(value) in (int, long):
                return str(value)
            else:
                raise ExifValueError(value, xtype)

        elif xtype == 'Rational':
            if type(value) is Rational and value.numerator >= 0:
                return str(value)
            else:
                raise ExifValueError(value, xtype)

        elif xtype == 'SRational':
            if type(value) is Rational:
                return str(value)
            else:
                raise ExifValueError(value, xtype)

        elif xtype == 'Undefined':
            if type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise ExifValueError(value, xtype)
            elif type(value) is str:
                return value
            else:
                raise ExifValueError(value, xtype)

        raise ExifValueError(value, xtype)

    def to_string(self):
        """
        Return a string representation of the EXIF tag suitable to pass to
        libexiv2 to set the value of the tag.
        DOCME
        """
        return ExifTag._convert_to_string(self.value, self.xtype)

    def __str__(self):
        """
        Return a string representation of the EXIF tag.
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.xtype + os.linesep + \
            'Value = ' + str(self.value) + os.linesep + \
            'Formatted value = ' + self.fvalue
        return r


class IptcValueError(ValueError):
    def __init__(self, value, xtype):
        self.value = value
        self.xtype = xtype

    def __str__(self):
        return 'Invalid value for IPTC type [%s]: [%s]' % \
               (self.xtype, self.value)


class IptcTag(MetadataTag, ListenerInterface):

    """
    An IPTC metadata tag can have several values (tags that have the repeatable
    property).
    """

    # strptime is not flexible enough to handle all valid Time formats, we use a
    # custom regular expression
    _time_zone_re = r'(?P<sign>\+|-)(?P<ohours>\d{2}):(?P<ominutes>\d{2})'
    _time_re = re.compile(r'(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})(?P<tzd>%s)' % _time_zone_re)

    def __init__(self, key, name, label, description, xtype, values):
        """
        Constructor.
        """
        super(IptcTag, self).__init__(key, name, label, description, xtype, values)
        self._values = NotifyingList(map(lambda x: IptcTag._convert_to_python(x, xtype), values))
        self._values.register_listener(self)

    def _get_values(self):
        return self._values

    def _set_values(self, new_values):
        if self.metadata is not None:
            raw_values = map(lambda x: IptcTag._convert_to_string(x, self.xtype), new_values)
            self.metadata._set_iptc_tag_values(self.key, raw_values)
        self._values = new_values

    def _del_values(self):
        if self.metadata is not None:
            self.metadata._delete_iptc_tag(self.key)
        self._values.unregister_listener(self)
        del self._values

    # DOCME
    values = property(fget=_get_values, fset=_set_values, fdel=_del_values,
                     doc=None)

    # Implement the listener interface.

    def item_changed(self, index, item):
        # An item of self._values was changed.
        # The following is a quick, non optimal solution.
        # FIXME: do not update the whole list, only the item that changed.
        self._set_values(self._values)


    @staticmethod
    def _convert_to_python(value, xtype):
        """
        Convert a value to its corresponding python type.

        @param value: the value to be converted, as a string
        @type value:  C{str}
        @param xtype: the IPTC type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on xtype (DOCME)

        @raise L{IptcValueError}: if the conversion fails
        """
        if xtype == 'Short':
            try:
                return int(value)
            except ValueError:
                raise IptcValueError(value, xtype)

        elif xtype == 'String':
            try:
                return unicode(value, 'utf-8')
            except TypeError:
                raise IptcValueError(value, xtype)

        elif xtype == 'Date':
            # According to the IPTC specification, the format for a string field
            # representing a date is '%Y%m%d'. However, the string returned by
            # exiv2 using method DateValue::toString() is formatted using
            # pattern '%Y-%m-%d'.
            format = '%Y-%m-%d'
            try:
                t = time.strptime(value, format)
                return datetime.date(*t[:3])
            except ValueError:
                raise IptcValueError(value, xtype)

        elif xtype == 'Time':
            # According to the IPTC specification, the format for a string field
            # representing a time is '%H%M%S±%H%M'. However, the string returned
            # by exiv2 using method TimeValue::toString() is formatted using
            # pattern '%H:%M:%S±%H:%M'.
            match = IptcTag._time_re.match(value)
            if match is None:
                raise IptcValueError(value, xtype)
            gd = match.groupdict()
            try:
                tzinfo = FixedOffset(gd['sign'], int(gd['ohours']),
                                     int(gd['ominutes']))
            except TypeError:
                raise IptcValueError(value, xtype)
            try:
                return datetime.time(int(gd['hours']), int(gd['minutes']),
                                     int(gd['seconds']), tzinfo=tzinfo)
            except (TypeError, ValueError):
                raise IptcValueError(value, xtype)

        elif xtype == 'Undefined':
            # Binary data, return it unmodified
            return value

        raise IptcValueError(value, xtype)

    @staticmethod
    def _convert_to_string(value, xtype):
        """
        Convert a value to its corresponding string representation.

        @param value: the value to be converted
        @type value:  depends on xtype (DOCME)
        @param xtype: the IPTC type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise L{IptcValueError}: if the conversion fails
        """
        if xtype == 'Short':
            if type(value) is int:
                return str(value)
            else:
                raise IptcValueError(value, xtype)

        elif xtype == 'String':
            if type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise IptcValueError(value, xtype)
            elif type(value) is str:
                return value
            else:
                raise IptcValueError(value, xtype)

        elif xtype == 'Date':
            if type(value) in (datetime.date, datetime.datetime):
                # ISO 8601 date format
                return value.strftime('%Y%m%d')
            else:
                raise IptcValueError(value, xtype)

        elif xtype == 'Time':
            if type(value) in (datetime.time, datetime.datetime):
                r = value.strftime('%H%M%S')
                if value.tzinfo is not None:
                    r += value.strftime('%z')
                else:
                    r += '+0000'
                return r
            else:
                raise IptcValueError(value, xtype)

        elif xtype == 'Undefined':
            if type(value) is str:
                return value
            else:
                raise IptcValueError(value, xtype)

        raise IptcValueError(value, xtype)

    def to_string(self):
        """
        Return a list of string representations of the IPTC tag values suitable
        to pass to libexiv2 to set the values of the tag.
        DOCME
        """
        return map(lambda x: IptcTag._convert_to_string(x, self.xtype), self.values)

    def __str__(self):
        """
        Return a string representation of the IPTC tag.
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.xtype + os.linesep + \
            'Values = ' + str(self.values)
        return r


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

    def __init__(self, key, name, label, description, xtype, value):
        """
        Constructor.
        """
        super(XmpTag, self).__init__(key, name, label, description, xtype, value)
        self._value = XmpTag._convert_to_python(value, xtype)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if self.metadata is not None:
            raw_value = XmpTag._convert_to_string(new_value, self.xtype)
            self.metadata._set_xmp_tag_value(self.key, raw_value)
        self._value = new_value

    def _del_value(self):
        if self.metadata is not None:
            self.metadata._delete_xmp_tag(self.key)
        del self._value

    # DOCME
    value = property(fget=_get_value, fset=_set_value, fdel=_del_value,
                     doc=None)

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
            if value == '':
                return []
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
        if xtype.startswith('bag '):
            if type(value) in (list, tuple):
                return ', '.join(map(lambda x: XmpTag._convert_to_string(x, xtype[4:]), value))
            else:
                raise XmpValueError(value, xtype)

        elif xtype == 'Boolean':
            if type(value) is bool:
                return str(value)
            else:
                raise XmpValueError(value, xtype)

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

        elif xtype in ('ProperName', 'Text', 'URI', 'URL'):
            if type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise XmpValueError(value, xtype)
            elif type(value) is str:
                return value
            else:
                raise XmpValueError(value, xtype)

        raise NotImplementedError('XMP conversion for type [%s]' % xtype)

    def to_string(self):
        """
        Return a string representation of the XMP tag suitable to pass to
        libexiv2 to set the value of the tag.
        DOCME
        """
        return XmpTag._convert_to_string(self.value, self.xtype)

    def __str__(self):
        """
        Return a string representation of the XMP tag.
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.xtype + os.linesep + \
            'Values = ' + str(self.values)
        return r


class ImageMetadata(object):

    """
    DOCME
    """

    def __init__(self, filename):
        self.filename = filename
        if type(filename) is unicode:
            self.filename = filename.encode('utf-8')
        self._image = None
        self._keys = {'exif': None, 'iptc': None, 'xmp': None}
        self._tags = {'exif': {}, 'iptc': {}, 'xmp': {}}

    def _instantiate_image(self, filename):
        # This method is meant to be overridden in unit tests to easily replace
        # the internal image reference by a mock.
        return libexiv2python.Image(filename)

    def read(self):
        """
        DOCME
        """
        if self._image is None:
            self._image = self._instantiate_image(self.filename)
        self._image.readMetadata()

    def write(self):
        """
        DOCME
        """
        self._image.writeMetadata()

    @property
    def exif_keys(self):
        if self._keys['exif'] is None:
            self._keys['exif'] = self._image.exifKeys()
        return self._keys['exif']

    @property
    def iptc_keys(self):
        if self._keys['iptc'] is None:
            self._keys['iptc'] = self._image.iptcKeys()
        return self._keys['iptc']

    @property
    def xmp_keys(self):
        if self._keys['xmp'] is None:
            self._keys['xmp'] = self._image.xmpKeys()
        return self._keys['xmp']

    def _get_exif_tag(self, key):
        try:
            return self._tags['exif'][key]
        except KeyError:
            tag = ExifTag(*self._image.getExifTag(key))
            tag.metadata = self
            self._tags['exif'][key] = tag
            return tag

    def _get_iptc_tag(self, key):
        try:
            return self._tags['iptc'][key]
        except KeyError:
            tag = IptcTag(*self._image.getIptcTag(key))
            tag.metadata = self
            self._tags['iptc'][key] = tag
            return tag

    def _get_xmp_tag(self, key):
        try:
            return self._tags['xmp'][key]
        except KeyError:
            tag = XmpTag(*self._image.getXmpTag(key))
            tag.metadata = self
            self._tags['xmp'][key] = tag
            return tag

    def __getitem__(self, key):
        """
        Get a metadata tag for a given key.
        DOCME
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_get_%s_tag' % family)(key)
        except AttributeError:
            raise KeyError(key)

    def _set_exif_tag(self, tag):
        if type(tag) is not ExifTag:
            raise TypeError('Expecting an ExifTag')
        self._image.setExifTagValue(tag.key, tag.to_string())
        self._tags['exif'][tag.key] = tag
        tag.metadata = self

    def _set_exif_tag_value(self, key, value):
        # Overwrite the tag value for an already existing tag.
        # The tag is already in cache.
        # Warning: this is not meant to be called directly as it doesn't update
        # the internal cache (which would leave the object in an inconsistent
        # state).
        if key not in self.exif_keys:
            raise KeyError('Cannot set the value of an inexistent tag')
        if type(value) is not str:
            raise TypeError('Expecting a string')
        self._image.setExifTagValue(key, value)

    def _set_iptc_tag(self, tag):
        if type(tag) is not IptcTag:
            raise TypeError('Expecting an IptcTag')
        self._image.setIptcTagValues(tag.key, tag.to_string())
        self._tags['iptc'][tag.key] = tag
        tag.metadata = self

    def _set_iptc_tag_values(self, key, values):
        # Overwrite the tag values for an already existing tag.
        # The tag is already in cache.
        # Warning: this is not meant to be called directly as it doesn't update
        # the internal cache (which would leave the object in an inconsistent
        # state).
        # FIXME: this is sub-optimal as it sets all the values regardless of how
        # many of them really changed. Need to implement the same method with an
        # index/range parameter (here and in the C++ wrapper).
        if key not in self.iptc_keys:
            raise KeyError('Cannot set the value of an inexistent tag')
        if type(values) is not list or not \
            reduce(lambda x, y: x and type(y) is str, values, True):
            raise TypeError('Expecting a list of strings')
        self._image.setIptcTagValues(key, values)

    def _set_xmp_tag(self, tag):
        if type(tag) is not XmpTag:
            raise TypeError('Expecting an XmpTag')
        self._image.setXmpTagValue(tag.key, tag.to_string())
        self._tags['xmp'][tag.key] = tag
        tag.metadata = self

    def _set_xmp_tag_value(self, key, value):
        # Overwrite the tag value for an already existing tag.
        # The tag is already in cache.
        # Warning: this is not meant to be called directly as it doesn't update
        # the internal cache (which would leave the object in an inconsistent
        # state).
        # TODO
        if key not in self.xmp_keys:
            raise KeyError('Cannot set the value of an inexistent tag')
        if type(value) is not str:
            raise TypeError('Expecting a string')
        self._image.setXmpTagValue(key, value)

    def __setitem__(self, key, tag):
        """
        Set a metadata tag for a given key.
        Override existing values.
        DOCME.
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_set_%s_tag' % family)(tag)
        except AttributeError:
            raise KeyError(key)

    def _delete_exif_tag(self, key):
        if key not in self.exif_keys:
            raise KeyError('Cannot delete an inexistent tag')
        self._image.deleteExifTag(key)
        try:
            del self._tags['exif'][key]
        except KeyError:
            # The tag was not cached.
            pass

    def _delete_iptc_tag(self, key):
        if key not in self.iptc_keys:
            raise KeyError('Cannot delete an inexistent tag')
        self._image.deleteIptcTag(key)
        try:
            del self._tags['iptc'][key]
        except KeyError:
            # The tag was not cached.
            pass

    def _delete_xmp_tag(self, key):
        if key not in self.xmp_keys:
            raise KeyError('Cannot delete an inexistent tag')
        self._image.deleteXmpTag(key)
        try:
            del self._tags['xmp'][key]
        except KeyError:
            # The tag was not cached.
            pass

    def __delitem__(self, key):
        """
        Delete a metadata tag with a given key.
        DOCME.
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_delete_%s_tag' % family)(key)
        except AttributeError:
            raise KeyError(key)


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
