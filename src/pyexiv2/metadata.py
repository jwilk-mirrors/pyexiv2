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

from pyexiv2.exif import ExifTag
from pyexiv2.iptc import IptcTag
from pyexiv2.xmp import XmpTag


class ImageMetadata(object):

    """
    A container for all the metadata embedded in an image.

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
        if isinstance(filename, unicode):
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

    @property
    def exif_keys(self):
        """Keys of the available EXIF tags embedded in the image."""
        if self._keys['exif'] is None:
            self._keys['exif'] = self._image.exifKeys()
        return self._keys['exif']

    @property
    def iptc_keys(self):
        """Keys of the available IPTC tags embedded in the image."""
        if self._keys['iptc'] is None:
            self._keys['iptc'] = self._image.iptcKeys()
        return self._keys['iptc']

    @property
    def xmp_keys(self):
        """Keys of the available XMP tags embedded in the image."""
        if self._keys['xmp'] is None:
            self._keys['xmp'] = self._image.xmpKeys()
        return self._keys['xmp']

    def _get_exif_tag(self, key):
        # Return the EXIF tag for the given key.
        # Throw a KeyError if the tag doesn't exist.
        try:
            return self._tags['exif'][key]
        except KeyError:
            _tag = self._image.getExifTag(key)
            tag = ExifTag._from_existing_tag(_tag)
            tag.metadata = self
            self._tags['exif'][key] = tag
            return tag

    def _get_iptc_tag(self, key):
        # Return the IPTC tag for the given key.
        # Throw a KeyError if the tag doesn't exist.
        try:
            return self._tags['iptc'][key]
        except KeyError:
            _tag = self._image.getIptcTag(key)
            tag = IptcTag._from_existing_tag(_tag)
            tag.metadata = self
            self._tags['iptc'][key] = tag
            return tag

    def _get_xmp_tag(self, key):
        # Return the XMP tag for the given key.
        # Throw a KeyError if the tag doesn't exist.
        try:
            return self._tags['xmp'][key]
        except KeyError:
            _tag = self._image.getXmpTag(key)
            tag = XmpTag._from_existing_tag(_tag)
            tag.metadata = self
            self._tags['xmp'][key] = tag
            return tag

    def __getitem__(self, key):
        """
        Get a metadata tag for a given key.

        @param key: a metadata key in the dotted form
                    C{familyName.groupName.tagName} where C{familyName} may be
                    C{exif}, C{iptc} or C{xmp}.
        @type key:  C{str}

        @return: the metadata tag corresponding to the key

        @raise KeyError: if the tag doesn't exist
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_get_%s_tag' % family)(key)
        except AttributeError:
            raise KeyError(key)

    def _set_exif_tag(self, tag):
        # Set an EXIF tag. If the tag already exists, its value is overwritten.
        if not isinstance(tag, ExifTag):
            raise TypeError('Expecting an ExifTag')
        self._image.setExifTagValue(tag.key, tag.raw_value)
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
        if not isinstance(tag, IptcTag):
            raise TypeError('Expecting an IptcTag')
        self._image.setIptcTagValues(tag.key, tag.to_string_list())
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
        if not isinstance(tag, XmpTag):
            raise TypeError('Expecting an XmpTag')
        type = tag._tag._getExiv2Type()
        if type == 'XmpText':
            self._image.setXmpTagTextValue(tag.key, tag.raw_value)
        elif type in ('XmpAlt', 'XmpBag', 'XmpSeq'):
            self._image.setXmpTagArrayValue(tag.key, tag.raw_value)
        elif type == 'LangAlt':
            self._image.setXmpTagLangAltValue(tag.key, tag.raw_value)
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
        type = self._tags['xmp'][key]._tag._getExiv2Type()
        if type == 'XmpText' and isinstance(value, str):
            self._image.setXmpTagTextValue(key, value)
        elif type in ('XmpAlt', 'XmpBag', 'XmpSeq') and isinstance(value, (list, tuple)):
            self._image.setXmpTagArrayValue(key, value)
        elif type == 'LangAlt' and isinstance(value, dict):
            self._image.setXmpTagLangAltValue(key, value)
        else:
            raise TypeError('Expecting either a string, a list, a tuple or a dict')

    def __setitem__(self, key, tag):
        """
        Set a metadata tag for a given key.
        If the tag was previously set, it is overwritten.

        @param key: a metadata key in the dotted form
                    C{familyName.groupName.tagName} where C{familyName} may be
                    C{exif}, C{iptc} or C{xmp}.
        @type key:  C{str}
        @param tag: a metadata tag

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

        @param key: a metadata key in the dotted form
                    C{familyName.groupName.tagName} where C{familyName} may be
                    C{exif}, C{iptc} or C{xmp}.
        @type key:  C{str}

        @raise KeyError: if the tag with the given key doesn't exist
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_delete_%s_tag' % family)(key)
        except AttributeError:
            raise KeyError(key)

    @property
    def previews(self):
        return self._image.previews()

