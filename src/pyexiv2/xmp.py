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

import libexiv2python

from pyexiv2.utils import FixedOffset, Rational, GPSCoordinate

import datetime
import re


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


class XmpTag(object):

    # FIXME: should inherit from ListenerInterface and implement observation of
    # changes on list/dict values.

    """
    An XMP tag.

    Here is a correspondance table between the XMP types and the possible
    python types the value of a tag may take:
     - alt, bag, seq: C{list} of the contained simple type
     - lang alt: C{dict} of (language-code: value)
     - Boolean: C{bool}
     - Colorant: [not implemented yet]
     - Date: C{datetime.date}, C{datetime.datetime}
     - Dimensions: [not implemented yet]
     - Font: [not implemented yet]
     - GPSCoordinate: L{pyexiv2.utils.GPSCoordinate}
     - Integer: C{int}
     - Locale: [not implemented yet]
     - MIMEType: C{tuple}
     - Rational: L{pyexiv2.utils.Rational}
     - Real: [not implemented yet]
     - AgentName, ProperName, Text: C{unicode}
     - Thumbnail: [not implemented yet]
     - URI, URL: C{str}
     - XPath: [not implemented yet]

    @ivar metadata: the parent metadata if any, or C{None}
    @type metadata: L{pyexiv2.metadata.ImageMetadata}
    """

    # strptime is not flexible enough to handle all valid Date formats, we use a
    # custom regular expression
    _time_zone_re = r'Z|((?P<sign>\+|-)(?P<ohours>\d{2}):(?P<ominutes>\d{2}))'
    _time_re = r'(?P<hours>\d{2})(:(?P<minutes>\d{2})(:(?P<seconds>\d{2})(.(?P<decimal>\d+))?)?(?P<tzd>%s))?' % _time_zone_re
    _date_re = re.compile(r'(?P<year>\d{4})(-(?P<month>\d{2})(-(?P<day>\d{2})(T(?P<time>%s))?)?)?' % _time_re)

    def __init__(self, key, value=None, _tag=None):
        """
        The tag can be initialized with an optional value which expected type
        depends on the XMP type of the tag.

        @param key:   the key of the tag
        @type key:    C{str}
        @param value: the value of the tag
        """
        super(XmpTag, self).__init__()
        if _tag is not None:
            self._tag = _tag
        else:
            self._tag = libexiv2python._XmpTag(key)
        self.metadata = None
        self._raw_value = None
        self._value = None
        self._value_cookie = False
        if value is not None:
            self._set_value(value)

    @staticmethod
    def _from_existing_tag(_tag):
        # Build a tag from an already existing libexiv2python._XmpTag
        tag = XmpTag(_tag._getKey(), _tag=_tag)
        type = _tag._getExiv2Type()
        if type == 'XmpText':
            tag.raw_value = _tag._getTextValue()
        elif type in ('XmpAlt', 'XmpBag', 'XmpSeq'):
            tag.raw_value = _tag._getArrayValue()
        elif type == 'LangAlt':
            tag.raw_value = _tag._getLangAltValue()
        return tag

    @property
    def key(self):
        """The key of the tag in the form 'familyName.groupName.tagName'."""
        return self._tag._getKey()

    @property
    def type(self):
        """The XMP type of the tag."""
        return self._tag._getType()

    @property
    def name(self):
        """The name of the tag (this is also the third part of the key)."""
        return self._tag._getName()

    @property
    def title(self):
        """The title (label) of the tag."""
        return self._tag._getTitle()

    @property
    def description(self):
        """The description of the tag."""
        return self._tag._getDescription()

    def _get_raw_value(self):
        return self._raw_value

    def _set_raw_value(self, value):
        type = self._tag._getExiv2Type()
        if type == 'XmpText':
            self._tag._setTextValue(value)
        elif type in ('XmpAlt', 'XmpBag', 'XmpSeq'):
            if not value:
                raise ValueError('Empty array')
            self._tag._setArrayValue(value)
        elif type == 'LangAlt':
            if not value:
                raise ValueError('Empty LangAlt')
            self._tag._setLangAltValue(value)

        if self.metadata is not None:
            self.metadata._set_xmp_tag_value(self.key, value)
        self._raw_value = value
        self._value_cookie = True

    raw_value = property(fget=_get_raw_value, fset=_set_raw_value,
                         doc='The raw value of the tag as a [list of] ' \
                             'string(s).')

    def _compute_value(self):
        # Lazy computation of the value from the raw value
        if self.type.startswith(('seq', 'bag', 'alt')):
            type = self.type[4:]
            if type.lower().startswith('closed choice of'):
                type = type[17:]
            self._value = map(lambda x: self._convert_to_python(x, type), self._raw_value)
        elif self.type == 'Lang Alt':
            self._value = {}
            for k, v in self._raw_value.iteritems():
                try:
                    self._value[unicode(k, 'utf-8')] = unicode(v, 'utf-8')
                except TypeError:
                    raise XmpValueError(self._raw_value, type)
        elif self.type.lower().startswith('closed choice of'):
            self._value = self._convert_to_python(self._raw_value, self.type[17:])
        elif self.type == '':
            self._value = self._raw_value
        else:
            self._value = self._convert_to_python(self._raw_value, self.type)

        self._value_cookie = False

    def _get_value(self):
        if self._value_cookie:
            self._compute_value()
        return self._value

    def _set_value(self, value):
        type = self._tag._getExiv2Type()
        if type == 'XmpText':
            stype = self.type
            if stype.lower().startswith('closed choice of'):
                stype = stype[17:]
            self.raw_value = self._convert_to_string(value, stype)
        elif type in ('XmpAlt', 'XmpBag', 'XmpSeq'):
            stype = self.type[4:]
            if stype.lower().startswith('closed choice of'):
                stype = stype[17:]
            self.raw_value = map(lambda x: self._convert_to_string(x, stype), value)
        elif type == 'LangAlt':
            raw_value = {}
            for k, v in value.iteritems():
                try:
                    raw_value[k.encode('utf-8')] = v.encode('utf-8')
                except TypeError:
                    raise XmpValueError(value, type)
            self.raw_value = raw_value

        self._value = value
        self._value_cookie = False

    value = property(fget=_get_value, fset=_set_value,
                     doc='The value of the tag as a [list of] python ' \
                         'object(s).')

    def _convert_to_python(self, value, type):
        """
        Convert a raw value to its corresponding python type.

        @param value: the raw value to be converted
        @type value:  C{str}
        @param type:  the simple type of the raw value
        @type type:   C{str}

        @return: the value converted to its corresponding python type
        @rtype:  depends on C{type}

        @raise XmpValueError: if the conversion fails
        """
        if type == 'Boolean':
            if value == 'True':
                return True
            elif value == 'False':
                return False
            else:
                raise XmpValueError(value, type)

        elif type == 'Colorant':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % type)

        elif type == 'Date':
            match = self._date_re.match(value)
            if match is None:
                raise XmpValueError(value, type)
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
                    raise XmpValueError(value, type)
            else:
                if gd['minutes'] is None:
                    # Malformed time
                    raise XmpValueError(value, type)
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
                    raise XmpValueError(value, type)

        elif type == 'Dimensions':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % type)

        elif type == 'Font':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % type)

        elif type == 'GPSCoordinate':
            try:
                return GPSCoordinate.from_string(value)
            except ValueError:
                raise XmpValueError(value, type)

        elif type == 'Integer':
            try:
                return int(value)
            except ValueError:
                raise XmpValueError(value, type)

        elif type == 'Locale':
            # TODO
            # See RFC 3066
            raise NotImplementedError('XMP conversion for type [%s]' % type)

        elif type == 'MIMEType':
            if value.count('/') != 1:
                raise XmpValueError(value, type)
            try:
                return tuple(value.split('/', 1))
            except ValueError:
                raise XmpValueError(value, type)

        elif type == 'Rational':
            try:
                return Rational.from_string(value)
            except (ValueError, ZeroDivisionError):
                raise XmpValueError(value, type)

        elif type == 'Real':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % type)

        elif type in ('AgentName', 'ProperName', 'Text'):
            try:
                return unicode(value, 'utf-8')
            except TypeError:
                raise XmpValueError(value, type)

        elif type == 'Thumbnail':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % type)

        elif type in ('URI', 'URL'):
            return value

        elif type == 'XPath':
            # TODO
            raise NotImplementedError('XMP conversion for type [%s]' % type)

        raise NotImplementedError('XMP conversion for type [%s]' % type)

    def _convert_to_string(self, value, type):
        """
        Convert a value to its corresponding string representation, suitable to
        pass to libexiv2.

        @param value: the value to be converted
        @type value:  depends on C{type}
        @param type:  the simple type of the value
        @type type:   C{str}

        @return: the value converted to its corresponding string representation
        @rtype:  C{str}

        @raise XmpValueError: if the conversion fails
        """
        if type == 'Boolean':
            if isinstance(value, bool):
                return str(value)
            else:
                raise XmpValueError(value, type)

        elif type == 'Date':
            if isinstance(value, datetime.datetime):
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
            elif isinstance(value, datetime.date):
                return value.isoformat()
            else:
                raise XmpValueError(value, type)

        elif type == 'GPSCoordinate':
            if isinstance(value, GPSCoordinate):
                return str(value)
            else:
                raise XmpValueError(value, type)

        elif type == 'Integer':
            if isinstance(value, (int, long)):
                return str(value)
            else:
                raise XmpValueError(value, type)

        elif type == 'MIMEType':
            if isinstance(value, tuple) and len(value) == 2:
                return '/'.join(value)
            else:
                raise XmpValueError(value, type)

        elif type in ('AgentName', 'ProperName', 'Text', 'URI', 'URL'):
            if isinstance(value, unicode):
                try:
                    return value.encode('utf-8')
                except UnicodeEncodeError:
                    raise XmpValueError(value, type)
            elif isinstance(value, str):
                return value
            else:
                raise XmpValueError(value, type)

        elif type == 'Rational':
            if isinstance(value, Rational):
                return str(value)
            else:
                raise XmpValueError(value, type)

        raise NotImplementedError('XMP conversion for type [%s]' % type)

    def __str__(self):
        """
        Return a string representation of the XMP tag for debugging purposes.

        @rtype: C{str}
        """
        left = '%s [%s]' % (self.key, self.type)
        if self._raw_value is None:
            right = '(No value)'
        else:
             right = self._raw_value
        return '<%s = %s>' % (left, right)

