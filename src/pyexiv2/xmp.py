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

from pyexiv2.utils import FixedOffset

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
    An XMP metadata tag.
    """

    # strptime is not flexible enough to handle all valid Date formats, we use a
    # custom regular expression
    _time_zone_re = r'Z|((?P<sign>\+|-)(?P<ohours>\d{2}):(?P<ominutes>\d{2}))'
    _time_re = r'(?P<hours>\d{2})(:(?P<minutes>\d{2})(:(?P<seconds>\d{2})(.(?P<decimal>\d+))?)?(?P<tzd>%s))?' % _time_zone_re
    _date_re = re.compile(r'(?P<year>\d{4})(-(?P<month>\d{2})(-(?P<day>\d{2})(T(?P<time>%s))?)?)?' % _time_re)

    def __init__(self, key, value=None, _tag=None):
        """
        DOCME
        """
        super(XmpTag, self).__init__()
        if _tag is not None:
            self._tag = _tag
        else:
            self._tag = libexiv2python._XmpTag(key)
        self.metadata = None
        self._raw_value = None
        self._value = None
        if value is not None:
            self._set_value(value)

    @staticmethod
    def _from_existing_tag(_tag):
        # Build a tag from an already existing _XmpTag
        tag = XmpTag(_tag._getKey(), _tag=_tag)
        tag.raw_value = _tag._getRawValue()
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

    def _get_raw_value(self):
        return self._raw_value

    def _set_raw_value(self, value):
        self._raw_value = value
        # FIXME: handle bags and other complex values, make them notifying lists
        # if necessary
        self._value = self._convert_to_python(value)

    raw_value = property(fget=_get_raw_value, fset=_set_raw_value, doc=None)

    def _get_value(self):
        return self._value

    def _set_value(self, value):
        # FIXME: handle bags and other complex values
        self._raw_value = self._convert_to_string(value)
        self._tag._setRawValue(self._raw_value)

        if self.metadata is not None:
            self.metadata._set_xmp_tag_value(self.key, self._raw_value)

        self._value = value

    value = property(fget=_get_value, fset=_set_value, doc=None)

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

    def __str__(self):
        """
        Return a string representation of the value of the XMP tag suitable to
        pass to libexiv2 to set it.

        @rtype: C{str}
        """
        return self._convert_to_string(self._value)

    def __repr__(self):
        """
        Return a string representation of the XMP tag for debugging purposes.

        @rtype: C{str}
        """
        left = '%s [%s]' % (self.key, self.type)
        if self._value is None:
            right = '(No value)'
        else:
             right = str(self)
        return '<%s = %s>' % (left, right)

