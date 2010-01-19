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
Utilitary classes and functions.
"""

import datetime
import re


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


def undefined_to_string(undefined):
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


def string_to_undefined(sequence):
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

    Its numerator and denominator are read-only properties.
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
        self._numerator = long(numerator)
        self._denominator = long(denominator)

    @property
    def numerator(self):
        return self._numerator

    @property
    def denominator(self):
        return self._denominator

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
        return float(self._numerator) / self._denominator

    def __eq__(self, other):
        """
        Compare two rational numbers for equality.

        Two rational numbers are equal if their reduced forms are equal.

        @param other: the rational number to compare to self for equality
        @type other:  L{Rational}
        
        @return: C{True} if equal, C{False} otherwise
        @rtype:  C{bool}
        """
        return (self._numerator * other._denominator) == \
               (other._numerator * self._denominator)

    def __str__(self):
        """
        Return a string representation of the rational number.
        """
        return '%d/%d' % (self._numerator, self._denominator)


class ListenerInterface(object):

    """
    Interface that an object that wants to listen to changes on another object
    should implement.
    """

    def contents_changed(self):
        """
        React on changes on the object observed.
        Override to implement specific behaviours.
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


class GPSCoordinate(object):

    """
    A class representing GPS coordinates (e.g. a latitude or a longitude).

    Its attributes (degrees, minutes, seconds, direction) are read-only
    properties.
    """

    _format_re = \
        re.compile(r'(?P<degrees>-?\d+),'
                    '(?P<minutes>\d+)(,(?P<seconds>\d+)|\.(?P<fraction>\d+))'
                    '(?P<direction>[NSEW])')

    def __init__(self, degrees, minutes, seconds, direction):
        """
        Constructor.

        @param degrees:   degrees
        @type degrees:    C{int}
        @param minutes:   minutes
        @type minutes:    C{int}
        @param seconds:   seconds
        @type seconds:    C{int}
        @param direction: direction ('N', 'S', 'E' or 'W')
        @type direction:  C{str}
        """
        if degrees < 0 or degrees > 90:
            raise ValueError('Invalid value for degrees: %d' % degrees)
        self._degrees = degrees
        if minutes < 0 or minutes > 60:
            raise ValueError('Invalid value for minutes: %d' % minutes)
        self._minutes = minutes
        if seconds < 0 or seconds > 60:
            raise ValueError('Invalid value for seconds: %d' % seconds)
        self._seconds = seconds
        if direction not in ('N', 'S', 'E', 'W'):
            raise ValueError('Invalid direction: %s' % direction)
        self._direction = direction

    @property
    def degrees(self):
        return self._degrees

    @property
    def minutes(self):
        return self._minutes

    @property
    def seconds(self):
        return self._seconds

    @property
    def direction(self):
        return self._direction

    @staticmethod
    def from_string(string):
        """
        Instantiate a GPSCoordinate from a string formatted as C{DDD,MM,SSk} or
        C{DDD,MM.mmk} where C{DDD} is a number of degrees, C{MM} is a number of
        minutes, C{SS} is a number of seconds, C{mm} is a fraction of minutes,
        and C{k} is a single character C{N}, C{S}, C{E}, or C{W} indicating a
        direction (north, south, east, west).

        @param string: a string representation of a GPS coordinate
        @type string:  C{str}

        @return: the GPS coordinate parsed
        @rtype:  L{GPSCoordinate}

        @raise ValueError: if the format of the string is invalid
        """
        match = GPSCoordinate._format_re.match(string)
        if match is None:
            raise ValueError('Invalid format for a GPS coordinate: %s' % string)
        gd = match.groupdict()
        fraction = gd['fraction']
        if fraction is not None:
            seconds = int(round(int(fraction[:2]) * 0.6))
        else:
            seconds = int(gd['seconds'])
        return GPSCoordinate(int(gd['degrees']), int(gd['minutes']), seconds,
                             gd['direction'])

    def __eq__(self, other):
        """
        Compare two GPS coordinates for equality.

        @param other: the GPS coordinate to compare to self for equality
        @type other:  L{GPSCoordinate}
        
        @return: C{True} if equal, C{False} otherwise
        @rtype:  C{bool}
        """
        return (self._degrees == other._degrees) and \
               (self._minutes == other._minutes) and \
               (self._seconds == other._seconds) and \
               (self._direction == other._direction)

    def __str__(self):
        """
        Return a string representation of the GPS coordinate conforming to the
        XMP specification.
        """
        return '%d,%d,%d%s' % (self._degrees, self._minutes, self._seconds,
                               self._direction)

