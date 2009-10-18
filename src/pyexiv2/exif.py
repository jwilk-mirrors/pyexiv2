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

from pyexiv2.tag import MetadataTag
from pyexiv2.utils import ListenerInterface, NotifyingList, Rational

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


class ExifTag(MetadataTag, ListenerInterface):

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

    _date_formats = ('%Y:%m:%d',)

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
                # Make values a notifying list
                values = map(self._convert_to_python, values)
                self._value = NotifyingList(values)
                self._value.register_listener(self)
                return
        self._value = self._convert_to_python(self.raw_value)

    def _get_value(self):
        return self._value

    def _set_value(self, new_value):
        if self.metadata is not None:
            if isinstance(new_value, (list, tuple)):
                raw_values = map(self._convert_to_string, new_value)
                raw_value = ' '.join(raw_values)
            else:
                raw_value = self._convert_to_string(new_value)
            self.metadata._set_exif_tag_value(self.key, raw_value)

        if isinstance(self._value, NotifyingList):
            self._value.unregister_listener(self)

        if isinstance(new_value, NotifyingList):
            # Already a notifying list
            self._value = new_value
            self._value.register_listener(self)
        elif isinstance(new_value, (list, tuple)):
            # Make the values a notifying list 
            self._value = NotifyingList(new_value)
            self._value.register_listener(self)
        else:
            # Single value
            self._value = new_value

    def _del_value(self):
        if self.metadata is not None:
            self.metadata._delete_exif_tag(self.key)

        if isinstance(self._value, NotifyingList):
            self._value.unregister_listener(self)

        del self._value

    """the value of the tag converted to its corresponding python type"""
    value = property(fget=_get_value, fset=_set_value, fdel=_del_value,
                     doc=None)

    def contents_changed(self):
        """
        Implementation of the L{ListenerInterface}.
        React on changes to the list of values of the tag.
        """
        # self._value is a list of value and its contents changed.
        self._set_value(self._value)

    def _convert_to_python(self, value):
        """
        Convert one raw value to its corresponding python type.

        @param value:  the raw value to be converted
        @type value:   C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on C{self.type} (DOCME)

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
            # There is currently no charset conversion.
            # TODO: guess the encoding and decode accordingly into unicode
            # where relevant.
            return self.fvalue

        raise ExifValueError(value, self.type)

    def _convert_to_string(self, value):
        """
        Convert one value to its corresponding string representation, suitable
        to pass to libexiv2.

        @param value: the value to be converted
        @type value:  depends on C{self.type} (DOCME)

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

        elif self.type == 'Byte':
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
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise ExifValueError(value, self.type)
            elif type(value) is str:
                return value
            else:
                raise ExifValueError(value, self.type)

        raise ExifValueError(value, self.type)

    def __str__(self):
        """
        Return a string representation of the value of the EXIF tag suitable to
        pass to libexiv2 to set it.

        @rtype: C{str}
        """
        return self._convert_to_string(self.value)

    def __repr__(self):
        """
        Return a string representation of the EXIF tag for debugging purposes.

        @rtype: C{str}
        """
        left = '%s [%s]' % (self.key, self.type)
        if self.type == 'Undefined' and len(self._value) > 100:
            right = '(Binary value suppressed)'
        else:
            right = self.fvalue
        return '<%s = %s>' % (left, right)

