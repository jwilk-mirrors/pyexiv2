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
        Return a string representation of the value of the tag suitable to pass
        to libexiv2 to set it.

        @rtype: C{str}
        """
        return self.raw_value

    def __repr__(self):
        """
        Return a string representation of the tag for debugging purposes.

        @rtype: C{str}
        """
        return '<%s [%s] = %s>' % (self.key, self.type, self.raw_value)
