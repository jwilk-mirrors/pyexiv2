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

import libexiv2python

from pyexiv2.utils import ListenerInterface, NotifyingList, FixedOffset

import time
import datetime
import re


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


class IptcTag(ListenerInterface):

    """
    An IPTC metadata tag.
    This tag can have several values (tags that have the repeatable property).
    """

    # strptime is not flexible enough to handle all valid Time formats, we use a
    # custom regular expression
    _time_zone_re = r'(?P<sign>\+|-)(?P<ohours>\d{2}):(?P<ominutes>\d{2})'
    _time_re = re.compile(r'(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})(?P<tzd>%s)' % _time_zone_re)

    def __init__(self, key, values=None, _tag=None):
        """
        DOCME
        """
        super(IptcTag, self).__init__()
        if _tag is not None:
            self._tag = _tag
        else:
            self._tag = libexiv2python._IptcTag(key)
        self.metadata = None
        self._raw_values = None
        self._values = None
        if values is not None:
            self._set_values(values)

    @staticmethod
    def _from_existing_tag(_tag):
        # Build a tag from an already existing _IptcTag
        tag = IptcTag(_tag._getKey(), _tag=_tag)
        tag.raw_values = _tag._getRawValues()
        return tag

    @property
    def key(self):
        return self._tag._getKey()

    @property
    def type(self):
        return self._tag._getType()

    @property
    def name(self):
        return self._tag._getName()

    @property
    def title(self):
        return self._tag._getTitle()

    @property
    def description(self):
        return self._tag._getDescription()

    @property
    def photoshop_name(self):
        return self._tag._getPhotoshopName()

    @property
    def repeatable(self):
        return self._tag._isRepeatable()

    @property
    def record_name(self):
        return self._tag._getRecordName()

    @property
    def record_description(self):
        return self._tag._getRecordDescription()

    def _get_raw_values(self):
        return self._raw_values

    def _set_raw_values(self, values):
        if not isinstance(values, (list, tuple)):
            raise TypeError('Expecting a list of values')
        self._raw_values = values
        self._values = NotifyingList(map(self._convert_to_python, values))
        self._values.register_listener(self)

    raw_values = property(fget=_get_raw_values, fset=_set_raw_values, doc=None)

    def _get_values(self):
        return self._values

    def _set_values(self, values):
        if not isinstance(values, (list, tuple)):
            raise TypeError('Expecting a list of values')

        self._raw_values = map(self._convert_to_string, values)
        self._tag._setRawValues(self._raw_values)

        if self.metadata is not None:
            self.metadata._set_iptc_tag_values(self.key, self._raw_values)

        if isinstance(self._values, NotifyingList):
            self._values.unregister_listener(self)

        if isinstance(values, NotifyingList):
            # Already a notifying list
            self._values = values
        else:
            # Make the values a notifying list 
            self._values = NotifyingList(values)

        self._values.register_listener(self)

    values = property(fget=_get_values, fset=_set_values, doc=None)

    def contents_changed(self):
        """
        Implementation of the L{ListenerInterface}.
        React on changes to the list of values of the tag.
        """
        # The contents of self._values was changed.
        # The following is a quick, non optimal solution.
        self._set_values(self._values)

    def _convert_to_python(self, value):
        """
        Convert one raw value to its corresponding python type.

        @param value: the raw value to be converted
        @type value:  C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on C{self.type} (DOCME)

        @raise IptcValueError: if the conversion fails
        """
        if self.type == 'Short':
            try:
                return int(value)
            except ValueError:
                raise IptcValueError(value, self.type)

        elif self.type == 'String':
            # There is currently no charset conversion.
            # TODO: guess the encoding and decode accordingly into unicode
            # where relevant.
            return value

        elif self.type == 'Date':
            # According to the IPTC specification, the format for a string field
            # representing a date is '%Y%m%d'. However, the string returned by
            # exiv2 using method DateValue::toString() is formatted using
            # pattern '%Y-%m-%d'.
            format = '%Y-%m-%d'
            try:
                t = time.strptime(value, format)
                return datetime.date(*t[:3])
            except ValueError:
                raise IptcValueError(value, self.type)

        elif self.type == 'Time':
            # According to the IPTC specification, the format for a string field
            # representing a time is '%H%M%S±%H%M'. However, the string returned
            # by exiv2 using method TimeValue::toString() is formatted using
            # pattern '%H:%M:%S±%H:%M'.
            match = IptcTag._time_re.match(value)
            if match is None:
                raise IptcValueError(value, self.type)
            gd = match.groupdict()
            try:
                tzinfo = FixedOffset(gd['sign'], int(gd['ohours']),
                                     int(gd['ominutes']))
            except TypeError:
                raise IptcValueError(value, self.type)
            try:
                return datetime.time(int(gd['hours']), int(gd['minutes']),
                                     int(gd['seconds']), tzinfo=tzinfo)
            except (TypeError, ValueError):
                raise IptcValueError(value, self.type)

        elif self.type == 'Undefined':
            # Binary data, return it unmodified
            return value

        raise IptcValueError(value, self.type)

    def _convert_to_string(self, value):
        """
        Convert one value to its corresponding string representation, suitable
        to pass to libexiv2.

        @param value: the value to be converted
        @type value:  depends on C{self.type} (DOCME)

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise IptcValueError: if the conversion fails
        """
        if self.type == 'Short':
            if type(value) is int:
                return str(value)
            else:
                raise IptcValueError(value, self.type)

        elif self.type == 'String':
            if type(value) is unicode:
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise IptcValueError(value, self.type)
            elif type(value) is str:
                return value
            else:
                raise IptcValueError(value, self.type)

        elif self.type == 'Date':
            if type(value) in (datetime.date, datetime.datetime):
                # ISO 8601 date format.
                # According to the IPTC specification, the format for a string
                # field representing a date is '%Y%m%d'. However, the string
                # expected by exiv2's DateValue::read(string) should be
                # formatted using pattern '%Y-%m-%d'.
                return value.strftime('%Y-%m-%d')
            else:
                raise IptcValueError(value, self.type)

        elif self.type == 'Time':
            if type(value) in (datetime.time, datetime.datetime):
                r = value.strftime('%H%M%S')
                if value.tzinfo is not None:
                    r += value.strftime('%z')
                else:
                    r += '+0000'
                return r
            else:
                raise IptcValueError(value, self.type)

        elif self.type == 'Undefined':
            if type(value) is str:
                return value
            else:
                raise IptcValueError(value, self.type)

        raise IptcValueError(value, self.type)

    def to_string_list(self):
        """
        Return a list of string representations of the values of the IPTC tag
        suitable to pass to libexiv2 to set it.

        @rtype: C{list} of C{str}
        """
        return map(self._convert_to_string, self._values)

    def __str__(self):
        """
        Return a string representation of the values of the IPTC tag.

        @rtype: C{str}
        """
        return ', '.join(self.to_string_list())

    def __repr__(self):
        """
        Return a string representation of the IPTC tag for debugging purposes.

        @rtype: C{str}
        """
        left = '%s [%s]' % (self.key, self.type)
        if self._values is None:
            right = '(No values)'
        else:
             right = str(self)
        return '<%s = %s>' % (left, right)

