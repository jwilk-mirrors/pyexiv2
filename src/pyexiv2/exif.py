# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2006-2010 Olivier Tilloy <olivier@tilloy.net>
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
EXIF specific code.
"""

import libexiv2python

from pyexiv2.utils import Rational, NotifyingList, ListenerInterface, \
                          undefined_to_string, string_to_undefined

import time
import datetime


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


class ExifTag(ListenerInterface):

    """
    An EXIF tag.

    Here is a correspondance table between the EXIF types and the possible
    python types the value of a tag may take:
     - Ascii: C{datetime.datetime}, C{datetime.date}, C{str}
     - Byte, SByte: C{str}
     - Comment: C{str}
     - Short, SShort: [list of] C{int}
     - Long, SLong: [list of] C{long}
     - Rational, SRational: [list of] L{pyexiv2.utils.Rational}
     - Undefined: C{str}

    @ivar metadata: the parent metadata if any, or C{None}
    @type metadata: L{pyexiv2.metadata.ImageMetadata}
    """

    # According to the EXIF specification, the only accepted format for an Ascii
    # value representing a datetime is '%Y:%m:%d %H:%M:%S', but it seems that
    # others formats can be found in the wild.
    _datetime_formats = ('%Y:%m:%d %H:%M:%S',
                         '%Y-%m-%d %H:%M:%S',
                         '%Y-%m-%dT%H:%M:%SZ')

    _date_formats = ('%Y:%m:%d',)

    def __init__(self, key, value=None, _tag=None):
        """
        The tag can be initialized with an optional value which expected type
        depends on the EXIF type of the tag.

        @param key:   the key of the tag
        @type key:    C{str}
        @param value: the value of the tag
        """
        super(ExifTag, self).__init__()
        if _tag is not None:
            self._tag = _tag
        else:
            self._tag = libexiv2python._ExifTag(key)
        self.metadata = None
        self._raw_value = None
        self._value = None
        self._value_cookie = False
        if value is not None:
            self._set_value(value)

    @staticmethod
    def _from_existing_tag(_tag):
        # Build a tag from an already existing libexiv2python._ExifTag.
        tag = ExifTag(_tag._getKey(), _tag=_tag)
        tag.raw_value = _tag._getRawValue()
        return tag

    @property
    def key(self):
        """The key of the tag in the form 'familyName.groupName.tagName'."""
        return self._tag._getKey()

    @property
    def type(self):
        """The EXIF type of the tag (one of Ascii, Byte, SByte, Comment, Short,
        SShort, Long, SLong, Rational, SRational, Undefined)."""
        return self._tag._getType()

    @property
    def name(self):
        """The name of the tag (this is also the third part of the key)."""
        return self._tag._getName()

    @property
    def label(self):
        """The title (label) of the tag."""
        return self._tag._getLabel()

    @property
    def description(self):
        """The description of the tag."""
        return self._tag._getDescription()

    @property
    def section_name(self):
        """The name of the tag's section."""
        return self._tag._getSectionName()

    @property
    def section_description(self):
        """The description of the tag's section."""
        return self._tag._getSectionDescription()

    def _get_raw_value(self):
        return self._raw_value

    def _set_raw_value(self, value):
        self._tag._setRawValue(value)
        if self.metadata is not None:
            self.metadata._set_exif_tag_value(self.key, value)
        self._raw_value = value
        self._value_cookie = True

    raw_value = property(fget=_get_raw_value, fset=_set_raw_value,
                         doc='The raw value of the tag as a string (C{str}).')

    def _compute_value(self):
        # Lazy computation of the value from the raw value.
        if self.type in \
            ('Short', 'SShort', 'Long', 'SLong', 'Rational', 'SRational'):
            # May contain multiple values
            values = self._raw_value.split()
            if len(values) > 1:
                # Make values a notifying list
                values = map(self._convert_to_python, values)
                self._value = NotifyingList(values)
                self._value.register_listener(self)
                self._value_cookie = False
                return

        self._value = self._convert_to_python(self._raw_value)
        self._value_cookie = False

    def _get_value(self):
        if self._value_cookie:
            self._compute_value() 
        return self._value

    def _set_value(self, value):
        if isinstance(value, (list, tuple)):
            raw_values = map(self._convert_to_string, value)
            self.raw_value = ' '.join(raw_values)
        else:
            self.raw_value = self._convert_to_string(value)

        if isinstance(self._value, NotifyingList):
            self._value.unregister_listener(self)

        if isinstance(value, NotifyingList):
            # Already a notifying list
            self._value = value
            self._value.register_listener(self)
        elif isinstance(value, (list, tuple)):
            # Make the values a notifying list 
            self._value = NotifyingList(value)
            self._value.register_listener(self)
        else:
            # Single value
            self._value = value

        self._value_cookie = False

    value = property(fget=_get_value, fset=_set_value,
                     doc='The value of the tag as a python object.')

    @property
    def human_value(self):
        """A human-readable representation of the value of the tag."""
        return self._tag._getHumanValue() or None

    # Implement the ListenerInterface
    def contents_changed(self):
        """
        Implementation of the L{ListenerInterface}.
        React on changes to the list of values of the tag.
        """
        # self._value is a list of values and its contents changed.
        self._set_value(self._value)

    def _convert_to_python(self, value):
        """
        Convert one raw value to its corresponding python type.

        @param value:  the raw value to be converted
        @type value:   C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on C{self.type}

        @raise ExifValueError: if the conversion fails
        """
        if self.type == 'Ascii':
            # The value may contain a Datetime
            for format in self._datetime_formats:
                try:
                    t = time.strptime(value, format)
                except ValueError:
                    continue
                else:
                    return datetime.datetime(*t[:6])
            # Or a Date (e.g. Exif.GPSInfo.GPSDateStamp)
            for format in self._date_formats:
                try:
                    t = time.strptime(value, format)
                except ValueError:
                    continue
                else:
                    return datetime.date(*t[:3])
            # Default to string.
            # There is currently no charset conversion.
            # TODO: guess the encoding and decode accordingly into unicode
            # where relevant.
            return value

        elif self.type in ('Byte', 'SByte'):
            return value

        elif self.type == 'Comment':
            # There is currently no charset conversion.
            # TODO: guess the encoding and decode accordingly into unicode
            # where relevant.
            return value

        elif self.type in ('Short', 'SShort'):
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
            # There is currently no charset conversion.
            # TODO: guess the encoding and decode accordingly into unicode
            # where relevant.
            return undefined_to_string(value)

        raise ExifValueError(value, self.type)

    def _convert_to_string(self, value):
        """
        Convert one value to its corresponding string representation, suitable
        to pass to libexiv2.

        @param value: the value to be converted
        @type value:  depends on C{self.type}

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise ExifValueError: if the conversion fails
        """
        if self.type == 'Ascii':
            if type(value) is datetime.datetime:
                return value.strftime(self._datetime_formats[0])
            elif type(value) is datetime.date:
                if self.key == 'Exif.GPSInfo.GPSDateStamp':
                    # Special case
                    return value.strftime(self._date_formats[0])
                else:
                    return value.strftime('%s 00:00:00' % self._date_formats[0])
            elif type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise ExifValueError(value, self.type)
            elif type(value) is str:
                return value
            else:
                raise ExifValueError(value, self.type)

        elif self.type in ('Byte', 'SByte'):
            if type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise ExifValueError(value, self.type)
            elif type(value) is str:
                return value
            else:
                raise ExifValueError(value, self.type)

        elif self.type == 'Comment':
            if type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise ExifValueError(value, self.type)
            elif type(value) is str:
                return value
            else:
                raise ExifValueError(value, self.type)

        elif self.type == 'Short':
            if type(value) is int and value >= 0:
                return str(value)
            else:
                raise ExifValueError(value, self.type)

        elif self.type == 'SShort':
            if type(value) is int:
                return str(value)
            else:
                raise ExifValueError(value, self.type)

        elif self.type == 'Long':
            if type(value) in (int, long) and value >= 0:
                return str(value)
            else:
                raise ExifValueError(value, self.type)

        elif self.type == 'SLong':
            if type(value) in (int, long):
                return str(value)
            else:
                raise ExifValueError(value, self.type)

        elif self.type == 'Rational':
            if type(value) is Rational and value.numerator >= 0:
                return str(value)
            else:
                raise ExifValueError(value, self.type)

        elif self.type == 'SRational':
            if type(value) is Rational:
                return str(value)
            else:
                raise ExifValueError(value, self.type)

        elif self.type == 'Undefined':
            if type(value) is unicode:
                try:
                    return string_to_undefined(value.encode('utf-8'))
                except UnicodeEncodeError:
                    raise ExifValueError(value, self.type)
            elif type(value) is str:
                return string_to_undefined(value)
            else:
                raise ExifValueError(value, self.type)

        raise ExifValueError(value, self.type)

    def __str__(self):
        """
        Return a string representation of the EXIF tag for debugging purposes.

        @rtype: C{str}
        """
        left = '%s [%s]' % (self.key, self.type)
        if self._raw_value is None:
            right = '(No value)'
        elif self.type == 'Undefined' and len(self._raw_value) > 100:
            right = '(Binary value suppressed)'
        else:
             right = self._raw_value
        return '<%s = %s>' % (left, right)

