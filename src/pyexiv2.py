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
Manipulation of EXIF, IPTC and XMP metadata and thumbnails embedded in images.

The L{ImageMetadata} class provides read/write access to all the metadata and
the various thumbnails embedded in an image file such as JPEG and TIFF files.

Metadata is accessed through subclasses of L{MetadataTag} and the tag values are
conveniently wrapped in python objects.
A tag containing a date/time information for the image
(e.g. C{Exif.Photo.DateTimeOriginal}) will be represented by a python
C{datetime.datetime} object.

This module is a python layer on top of the low-level python binding of the
C++ library Exiv2, libpyexiv2.

A typical use of this binding would be:

>>> import pyexiv2
>>> metadata = pyexiv2.ImageMetadata('test/smiley.jpg')
>>> metadata.read()
>>> print metadata.exif_keys
['Exif.Image.ImageDescription', 'Exif.Image.XResolution',
 'Exif.Image.YResolution', 'Exif.Image.ResolutionUnit', 'Exif.Image.Software',
 'Exif.Image.DateTime', 'Exif.Image.Artist', 'Exif.Image.Copyright',
 'Exif.Image.ExifTag', 'Exif.Photo.Flash', 'Exif.Photo.PixelXDimension',
 'Exif.Photo.PixelYDimension']
>>> print metadata['Exif.Image.DateTime'].value
2004-07-13 21:23:44
>>> import datetime
>>> metadata['Exif.Image.DateTime'].value = datetime.datetime.today()
>>> metadata.write()
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
    Fixed positive or negative offset from a local time east from UTC.

    @ivar sign:    the sign of the offset ('+' or '-')
    @type sign:    C{str}
    @ivar hours:   the absolute number of hours of the offset
    @type hours:   C{int}
    @ivar minutes: the absolute number of minutes of the offset
    @type minutes: C{int}

    """

    def __init__(self, sign='+', hours=0, minutes=0):
        """
        Initialize an offset from a sign ('+' or '-') and an absolute value
        expressed in hours and minutes.
        No check on the validity of those values is performed, it is the
        responsibility of the caller to pass valid values.

        @param sign:    the sign of the offset ('+' or '-')
        @type sign:     C{str}
        @param hours:   an absolute number of hours
        @type hours:    C{int}
        @param minutes: an absolute number of minutes
        @type minutes:  C{int}
        """
        self.sign = sign
        self.hours = hours
        self.minutes = minutes

    def utcoffset(self, dt):
        """
        Return offset of local time from UTC, in minutes east of UTC.
        If local time is west of UTC, this value will be negative.

        @param dt: the local time
        @type dt:  C{datetime.time}

        @return: a whole number of minutes in the range -1439 to 1439 inclusive
        @rtype:  C{datetime.timedelta}
        """
        total = self.hours * 60 + self.minutes
        if self.sign == '-':
            total = -total
        return datetime.timedelta(minutes = total)

    def dst(self, dt):
        """
        Return the daylight saving time (DST) adjustment.
        In this implementation, it is always nil.

        @param dt: the local time
        @type dt:  C{datetime.time}

        @return: the DST adjustment (always nil)
        @rtype:  C{datetime.timedelta}
        """
        return datetime.timedelta(0)

    def tzname(self, dt):
        """
        Return a string representation of the offset in the format '±%H:%M'.
        If the offset is nil, the representation is, by convention, 'Z'.

        @param dt: the local time
        @type dt:  C{datetime.time}

        @return: a human-readable representation of the offset
        @rtype:  C{str}
        """
        if self.hours == 0 and self.minutes == 0:
            return 'Z'
        else:
            return '%s%02d:%02d' % (self.sign, self.hours, self.minutes)

    def __equal__(self, other):
        """
        Test equality between this offset and another offset.

        @param other: another offset
        @type other:  L{FixedOffset}

        @return: C{True} if the offset are equal, C{False} otherwise
        @rtype:  C{bool}
        """
        return (self.sign == other.sign) and (self.hours == other.hours) and \
            (self.minutes == other.minutes)


def UndefinedToString(undefined):
    """
    Convert an undefined string into its corresponding sequence of bytes.
    The undefined string must contain the ascii codes of a sequence of bytes,
    each followed by a blank space (e.g. "48 50 50 49 " will be converted into
    "0221").
    The Undefined type is part of the EXIF specification.

    @param undefined: an undefined string
    @type undefined:  C{str}

    @return: the corresponding decoded string
    @rtype:  C{str}
    """
    return ''.join(map(lambda x: chr(int(x)), undefined.rstrip().split(' ')))


def StringToUndefined(sequence):
    """
    Convert a string into its undefined form.
    The undefined form contains a sequence of ascii codes, each followed by a
    blank space (e.g. "0221" will be converted into "48 50 50 49 ").
    The Undefined type is part of the EXIF specification.

    @param sequence: a sequence of bytes
    @type sequence:  C{str}

    @return: the corresponding undefined string
    @rtype:  C{str}
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

        @raise ZeroDivisionError: if the denominator equals zero
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

    def to_float(self):
        """
        @return: a floating point number approximation of the value
        @rtype:  C{float}
        """
        return float(self.numerator) / self.denominator

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

    """
    Interface that an object that wants to listen to changes on another object
    should implement.
    """

    def contents_changed(self):
        """
        React on changes on the object observed.
        Override to implement specific bejaviours.
        """
        raise NotImplementedError()


class NotifyingList(list):

    """
    A simplistic implementation of a notifying list.
    Any changes to the list are notified in a synchronous way to all previously
    registered listeners. A listener must implement the L{ListenerInterface}.
    """

    # Useful documentation:
    # file:///usr/share/doc/python2.5/html/lib/typesseq-mutable.html
    # http://docs.python.org/reference/datamodel.html#additional-methods-for-emulation-of-sequence-types

    def __init__(self, items=[]):
        super(NotifyingList, self).__init__(items)
        self._listeners = set()

    def register_listener(self, listener):
        """
        Register a new listener to be notified of changes.

        @param listener: any object that listens for changes
        @type listener:  any class that implements the L{ListenerInterface}
        """
        self._listeners.add(listener)

    def unregister_listener(self, listener):
        """
        Unregister a previously registered listener.

        @param listener: a previously registered listener
        @type listener:  any class that implements the L{ListenerInterface}

        @raise KeyError: if the listener was not previously registered
        """
        self._listeners.remove(listener)

    def _notify_listeners(self, *args):
        for listener in self._listeners:
            listener.contents_changed(*args)

    def __setitem__(self, index, item):
        # FIXME: support slice arguments for extended slicing
        super(NotifyingList, self).__setitem__(index, item)
        self._notify_listeners()

    def __delitem__(self, index):
        # FIXME: support slice arguments for extended slicing
        super(NotifyingList, self).__delitem__(index)
        self._notify_listeners()

    def append(self, item):
        super(NotifyingList, self).append(item)
        self._notify_listeners()

    def extend(self, items):
        super(NotifyingList, self).extend(items)
        self._notify_listeners()

    def insert(self, index, item):
        super(NotifyingList, self).insert(index, item)
        self._notify_listeners()

    def pop(self, index=None):
        if index is None:
            item = super(NotifyingList, self).pop()
        else:
            item = super(NotifyingList, self).pop(index)
        self._notify_listeners()
        return item

    def remove(self, item):
        super(NotifyingList, self).remove(item)
        self._notify_listeners()

    def reverse(self):
        super(NotifyingList, self).reverse()
        self._notify_listeners()

    def sort(self, cmp=None, key=None, reverse=False):
        super(NotifyingList, self).sort(cmp, key, reverse)
        self._notify_listeners()

    def __iadd__(self, other):
        self = super(NotifyingList, self).__iadd__(other)
        self._notify_listeners()
        return self

    def __imul__(self, coefficient):
        self = super(NotifyingList, self).__imul__(coefficient)
        self._notify_listeners()
        return self

    def __setslice__(self, i, j, items):
        # __setslice__ is deprecated but needs to be overridden for completeness
        super(NotifyingList, self).__setslice__(i, j, items)
        self._notify_listeners()

    def __delslice__(self, i, j):
        # __delslice__ is deprecated but needs to be overridden for completeness
        deleted = self[i:j]
        super(NotifyingList, self).__delslice__(i, j)
        if deleted:
            self._notify_listeners()


class MetadataTag(object):

    """
    A generic metadata tag.
    It is meant to be subclassed to implement specific tag types behaviours.

    @ivar key:         a unique key that identifies the tag
    @type key:         C{str}
    @ivar name:        the short internal name that identifies the tag within
                       its scope
    @type name:        C{str}
    @ivar label:       a human readable label for the tag
    @type label:       C{str}
    @ivar description: a description of the function of the tag
    @type description: C{str}
    @ivar type:        the data type name
    @type type:        C{str}
    @ivar raw_value:   the raw value of the tag as provided by exiv2
    @type raw_value:   C{str}
    @ivar metadata:    reference to the containing metadata if any
    @type metadata:    L{pyexiv2.ImageMetadata}
    """

    def __init__(self, key, name, label, description, type, value):
        self.key = key
        self.name = name
        # FIXME: all attributes that may contain a localized string should be
        #        unicode.
        self.label = label
        self.description = description
        self.type = type
        self.raw_value = value
        self.metadata = None

    def __str__(self):
        """
        Return a string representation of the tag for debugging purposes.

        @rtype: C{str}
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.type + os.linesep + \
            'Raw value = ' + str(self.raw_value)
        return r


class ExifValueError(ValueError):

    """
    Exception raised when failing to parse the value of an EXIF tag.

    @ivar value: the value that fails to be parsed
    @type value: C{str}
    @ivar type:  the EXIF type of the tag
    @type type:  C{str}
    """

    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __str__(self):
        return 'Invalid value for EXIF type [%s]: [%s]' % \
               (self.type, self.value)


class ExifTag(MetadataTag):

    """
    An EXIF metadata tag.
    This tag has an additional field that contains the value of the tag
    formatted as a human readable string.

    @ivar fvalue: the value of the tag formatted as a human readable string
    @type fvalue: C{str}
    """

    # According to the EXIF specification, the only accepted format for an Ascii
    # value representing a datetime is '%Y:%m:%d %H:%M:%S', but it seems that
    # others formats can be found in the wild.
    _datetime_formats = ('%Y:%m:%d %H:%M:%S',
                         '%Y-%m-%d %H:%M:%S',
                         '%Y-%m-%dT%H:%M:%SZ')

    def __init__(self, key, name, label, description, type, value, fvalue):
        super(ExifTag, self).__init__(key, name, label,
                                      description, type, value)
        self.fvalue = fvalue
        self._init_values()

    def _init_values(self):
        # Initial conversion of the raw values to their corresponding python
        # types.
        if self.type in ('Short', 'Long', 'SLong', 'Rational', 'SRational'):
            # May contain multiple values
            values = self.raw_value.split()
            if len(values) > 1:
                self._value = map(self._convert_to_python, values)
                return
        self._value = self._convert_to_python(self.raw_value)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if self.metadata is not None:
            raw_value = ExifTag._convert_to_string(new_value, self.type)
            self.metadata._set_exif_tag_value(self.key, raw_value)
        self._value = new_value

    def _del_value(self):
        if self.metadata is not None:
            self.metadata._delete_exif_tag(self.key)
        del self._value

    """the value of the tag converted to its corresponding python type"""
    value = property(fget=_get_value, fset=_set_value, fdel=_del_value,
                     doc=None)

    def _convert_to_python(self, value):
        """
        Convert a raw value to its corresponding python type.

        @param value:  the raw value to be converted
        @type value:   C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on C{self.type} (DOCME)

        @raise ExifValueError: if the conversion fails
        """
        if self.type == 'Ascii':
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
                raise ExifValueError(value, self.type)

        elif self.type == 'Byte':
            return value

        elif self.type == 'Short':
            try:
                return int(value)
            except ValueError:
                raise ExifValueError(value, self.type)

        elif self.type in ('Long', 'SLong'):
            try:
                return long(value)
            except ValueError:
                raise ExifValueError(value, self.type)

        elif self.type in ('Rational', 'SRational'):
            try:
                r = Rational.from_string(value)
            except (ValueError, ZeroDivisionError):
                raise ExifValueError(value, self.type)
            else:
                if self.type == 'Rational' and r.numerator < 0:
                    raise ExifValueError(value, self.type)
                return r

        elif self.type == 'Undefined':
            try:
                return unicode(self.fvalue, 'utf-8')
            except TypeError:
                raise ExifValueError(self.fvalue, self.type)

        raise ExifValueError(value, self.type)

    @staticmethod
    def _convert_to_string(value, xtype):
        """
        Convert a value to its corresponding string representation, suitable to
        pass to libexiv2.

        @param value: the value to be converted
        @type value:  depends on xtype (DOCME)
        @param xtype: the EXIF type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise ExifValueError: if the conversion fails
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

        @rtype: C{str}
        """
        return ExifTag._convert_to_string(self.value, self.type)

    def __str__(self):
        """
        Return a string representation of the EXIF tag for debugging purposes.

        @rtype: C{str}
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.type + os.linesep + \
            'Value = ' + str(self.value) + os.linesep + \
            'Formatted value = ' + self.fvalue
        return r


class IptcValueError(ValueError):

    """
    Exception raised when failing to parse the value of an IPTC tag.

    @ivar value: the value that fails to be parsed
    @type value: C{str}
    @ivar type:  the IPTC type of the tag
    @type type:  C{str}
    """

    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __str__(self):
        return 'Invalid value for IPTC type [%s]: [%s]' % \
               (self.type, self.value)


class IptcTag(MetadataTag):

    """
    An IPTC metadata tag.
    This tag can have several values (tags that have the repeatable property).
    """

    # strptime is not flexible enough to handle all valid Time formats, we use a
    # custom regular expression
    _time_zone_re = r'(?P<sign>\+|-)(?P<ohours>\d{2}):(?P<ominutes>\d{2})'
    _time_re = re.compile(r'(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})(?P<tzd>%s)' % _time_zone_re)

    def __init__(self, key, name, label, description, type, values):
        super(IptcTag, self).__init__(key, name, label,
                                      description, type, values)
        # Make values a notifying list
        values = map(lambda x: IptcTag._convert_to_python(x, type), values)
        self._values = NotifyingList(values)
        self._values.register_listener(self)

    def _get_values(self):
        return self._values

    def _set_values(self, new_values):
        if self.metadata is not None:
            raw_values = map(lambda x: IptcTag._convert_to_string(x, self.type), new_values)
            self.metadata._set_iptc_tag_values(self.key, raw_values)
        # Make values a notifying list if needed
        if isinstance(new_values, NotifyingList):
            self._values = new_values
        else:
            self._values = NotifyingList(new_values)

    def _del_values(self):
        if self.metadata is not None:
            self.metadata._delete_iptc_tag(self.key)
        del self._values

    """the list of values of the tag converted to their corresponding python
    type"""
    values = property(fget=_get_values, fset=_set_values, fdel=_del_values,
                     doc=None)

    def contents_changed(self):
        """
        Implementation of the L{ListenerInterface}.
        React on changes to the list of values of the tag.
        """
        # The contents of self._values was changed.
        # The following is a quick, non optimal solution.
        self._set_values(self._values)

    @staticmethod
    def _convert_to_python(value, xtype):
        """
        Convert a raw value to its corresponding python type.

        @param value: the raw value to be converted
        @type value:  C{str}
        @param xtype: the IPTC type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on xtype (DOCME)

        @raise IptcValueError: if the conversion fails
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
        Convert a value to its corresponding string representation, suitable to
        pass to libexiv2.

        @param value: the value to be converted
        @type value:  depends on xtype (DOCME)
        @param xtype: the IPTC type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise IptcValueError: if the conversion fails
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
        to pass to libexiv2 to set the value of the tag.

        @rtype: C{list} of C{str}
        """
        return map(lambda x: IptcTag._convert_to_string(x, self.type),
                   self.values)

    def __str__(self):
        """
        Return a string representation of the IPTC tag for debugging purposes.

        @rtype: C{str}
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.type + os.linesep + \
            'Values = ' + str(self.values)
        return r


class XmpValueError(ValueError):

    """
    Exception raised when failing to parse the value of an XMP tag.

    @ivar value: the value that fails to be parsed
    @type value: C{str}
    @ivar type: the XMP type of the tag
    @type type: C{str}
    """
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __str__(self):
        return 'Invalid value for XMP type [%s]: [%s]' % \
               (self.type, self.value)


class XmpTag(MetadataTag):

    """
    An XMP metadata tag.
    """

    # strptime is not flexible enough to handle all valid Date formats, we use a
    # custom regular expression
    _time_zone_re = r'Z|((?P<sign>\+|-)(?P<ohours>\d{2}):(?P<ominutes>\d{2}))'
    _time_re = r'(?P<hours>\d{2})(:(?P<minutes>\d{2})(:(?P<seconds>\d{2})(.(?P<decimal>\d+))?)?(?P<tzd>%s))?' % _time_zone_re
    _date_re = re.compile(r'(?P<year>\d{4})(-(?P<month>\d{2})(-(?P<day>\d{2})(T(?P<time>%s))?)?)?' % _time_re)

    def __init__(self, key, name, label, description, type, value):
        super(XmpTag, self).__init__(key, name, label, description, type, value)
        self._value = XmpTag._convert_to_python(value, type)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if self.metadata is not None:
            raw_value = XmpTag._convert_to_string(new_value, self.type)
            self.metadata._set_xmp_tag_value(self.key, raw_value)
        self._value = new_value

    def _del_value(self):
        if self.metadata is not None:
            self.metadata._delete_xmp_tag(self.key)
        del self._value

    """the value of the tag converted to its corresponding python type"""
    value = property(fget=_get_value, fset=_set_value, fdel=_del_value,
                     doc=None)

    @staticmethod
    def _convert_to_python(value, xtype):
        """
        Convert a raw value to its corresponding python type.

        @param value: the raw value to be converted
        @type value:  C{str}
        @param xtype: the XMP type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on xtype (DOCME)

        @raise XmpValueError: if the conversion fails
        """
        if xtype.startswith('bag '):
            # FIXME: make the value a notifying list.
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
        Convert a value to its corresponding string representation, suitable to
        pass to libexiv2.

        @param value: the value to be converted
        @type value:  depends on xtype (DOCME)
        @param xtype: the XMP type of the value
        @type xtype:  C{str}

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise XmpValueError: if the conversion fails
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

        @rtype: C{str}
        """
        return XmpTag._convert_to_string(self.value, self.type)

    def __str__(self):
        """
        Return a string representation of the XMP tag for debugging purposes.

        @rtype: C{str}
        """
        r = 'Key = ' + self.key + os.linesep + \
            'Name = ' + self.name + os.linesep + \
            'Label = ' + self.label + os.linesep + \
            'Description = ' + self.description + os.linesep + \
            'Type = ' + self.type + os.linesep + \
            'Values = ' + str(self.values)
        return r


class ImageMetadata(object):

    """
    A container for all the metadata attached to an image.

    It provides convenient methods for the manipulation of EXIF, IPTC and XMP
    metadata embedded in image files such as JPEG and TIFF files, using Python
    types.
    It also provides access to the thumbnails embedded in an image.
    """

    def __init__(self, filename):
        """
        @param filename: absolute path to an image file
        @type filename:  C{str} or C{unicode}
        """
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
        Read the metadata embedded in the associated image file.
        It is necessary to call this method once before attempting to access
        the metadata (an exception will be raised if trying to access metadata
        before calling this method).
        """
        if self._image is None:
            self._image = self._instantiate_image(self.filename)
        self._image.readMetadata()

    def write(self):
        """
        Write the metadata back to the associated image file.
        """
        self._image.writeMetadata()

    """List the keys of the available EXIF tags embedded in the image."""
    @property
    def exif_keys(self):
        if self._keys['exif'] is None:
            self._keys['exif'] = self._image.exifKeys()
        return self._keys['exif']

    """List the keys of the available IPTC tags embedded in the image."""
    @property
    def iptc_keys(self):
        if self._keys['iptc'] is None:
            self._keys['iptc'] = self._image.iptcKeys()
        return self._keys['iptc']

    """List the keys of the available XMP tags embedded in the image."""
    @property
    def xmp_keys(self):
        if self._keys['xmp'] is None:
            self._keys['xmp'] = self._image.xmpKeys()
        return self._keys['xmp']

    def _get_exif_tag(self, key):
        # Return the EXIF tag for the given key.
        # Throw a KeyError if the tag doesn't exist.
        try:
            return self._tags['exif'][key]
        except KeyError:
            tag = ExifTag(*self._image.getExifTag(key))
            tag.metadata = self
            self._tags['exif'][key] = tag
            return tag

    def _get_iptc_tag(self, key):
        # Return the IPTC tag for the given key.
        # Throw a KeyError if the tag doesn't exist.
        try:
            return self._tags['iptc'][key]
        except KeyError:
            tag = IptcTag(*self._image.getIptcTag(key))
            tag.metadata = self
            self._tags['iptc'][key] = tag
            return tag

    def _get_xmp_tag(self, key):
        # Return the XMP tag for the given key.
        # Throw a KeyError if the tag doesn't exist.
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

        @param key: a metadata key in the dotted form C{family.group.tag} where
                    family may be C{exif}, C{iptc} or C{xmp}.
        @type key:  C{str}

        @return: the metadata tag corresponding to the key
        @rtype:  a subclass of L{pyexiv2.MetadataTag}

        @raise KeyError: if the tag doesn't exist
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_get_%s_tag' % family)(key)
        except AttributeError:
            raise KeyError(key)

    def _set_exif_tag(self, tag):
        # Set an EXIF tag. If the tag already exists, its value is overwritten.
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
        # Set an IPTC tag. If the tag already exists, its values are
        # overwritten.
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
        # Set an XMP tag. If the tag already exists, its value is overwritten.
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
        if key not in self.xmp_keys:
            raise KeyError('Cannot set the value of an inexistent tag')
        if type(value) is not str:
            raise TypeError('Expecting a string')
        self._image.setXmpTagValue(key, value)

    def __setitem__(self, key, tag):
        """
        Set a metadata tag for a given key.
        If the tag was previously set, it is overwritten.

        @param key: a metadata key in the dotted form C{family.group.tag} where
                    family may be C{exif}, C{iptc} or C{xmp}.
        @type key:  C{str}
        @param tag: a metadata tag
        @type tag:  a subclass of L{pyexiv2.MetadataTag}

        @raise KeyError: if the key is invalid
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_set_%s_tag' % family)(tag)
        except AttributeError:
            raise KeyError(key)

    def _delete_exif_tag(self, key):
        # Delete an EXIF tag.
        # Throw a KeyError if the tag doesn't exist.
        if key not in self.exif_keys:
            raise KeyError('Cannot delete an inexistent tag')
        self._image.deleteExifTag(key)
        try:
            del self._tags['exif'][key]
        except KeyError:
            # The tag was not cached.
            pass

    def _delete_iptc_tag(self, key):
        # Delete an IPTC tag.
        # Throw a KeyError if the tag doesn't exist.
        if key not in self.iptc_keys:
            raise KeyError('Cannot delete an inexistent tag')
        self._image.deleteIptcTag(key)
        try:
            del self._tags['iptc'][key]
        except KeyError:
            # The tag was not cached.
            pass

    def _delete_xmp_tag(self, key):
        # Delete an XMP tag.
        # Throw a KeyError if the tag doesn't exist.
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
        Delete a metadata tag for a given key.

        @param key: a metadata key in the dotted form C{family.group.tag} where
                    family may be C{exif}, C{iptc} or C{xmp}.
        @type key:  C{str}

        @raise KeyError: if the tag with the given key doesn't exist
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_delete_%s_tag' % family)(key)
        except AttributeError:
            raise KeyError(key)

