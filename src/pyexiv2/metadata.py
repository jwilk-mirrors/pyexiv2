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
Provide the ImageMetadata class.
"""

import os
import sys
from errno import ENOENT

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
    It also provides access to the previews embedded in an image.
    """

    def __init__(self, filename):
        """
        :param filename: path to an image file
        :type filename: string
        """
        self.filename = filename
        if filename is not None:
            self.filename = filename.encode(sys.getfilesystemencoding())
        self._image = None
        self._keys = {'exif': None, 'iptc': None, 'xmp': None}
        self._tags = {'exif': {}, 'iptc': {}, 'xmp': {}}

    def _instantiate_image(self, filename):
        # This method is meant to be overridden in unit tests to easily replace
        # the internal image reference by a mock.
        if not os.path.exists(filename) or not os.path.isfile(filename):
            raise IOError(ENOENT, "%s: '%s'" % (os.strerror(ENOENT), filename))
        return libexiv2python._Image(filename)

    @classmethod
    def from_buffer(cls, buffer):
        """
        Instantiate an image container from an image buffer.

        :param buffer: a buffer containing image data
        :type buffer: string
        """
        obj = cls(None)
        obj._image = libexiv2python._Image(buffer, len(buffer))
        return obj

    def read(self):
        """
        Read the metadata embedded in the associated image.
        It is necessary to call this method once before attempting to access
        the metadata (an exception will be raised if trying to access metadata
        before calling this method).
        """
        if self._image is None:
            self._image = self._instantiate_image(self.filename)
        self._image._readMetadata()

    def write(self):
        """
        Write the metadata back to the image.
        """
        self._image._writeMetadata()

    @property
    def dimensions(self):
        """A tuple containing the width and height of the image, expressed in
        pixels."""
        return (self._image._getPixelWidth(), self._image._getPixelHeight())

    @property
    def mime_type(self):
        """The mime type of the image, as a string."""
        return self._image._getMimeType()

    @property
    def exif_keys(self):
        """List of the keys of the available EXIF tags."""
        if self._keys['exif'] is None:
            self._keys['exif'] = self._image._exifKeys()
        return self._keys['exif']

    @property
    def iptc_keys(self):
        """List of the keys of the available IPTC tags."""
        if self._keys['iptc'] is None:
            self._keys['iptc'] = self._image._iptcKeys()
        return self._keys['iptc']

    @property
    def xmp_keys(self):
        """List of the keys of the available XMP tags."""
        if self._keys['xmp'] is None:
            self._keys['xmp'] = self._image._xmpKeys()
        return self._keys['xmp']

    def _get_exif_tag(self, key):
        # Return the EXIF tag for the given key.
        # Throw a KeyError if the tag doesn't exist.
        try:
            return self._tags['exif'][key]
        except KeyError:
            _tag = self._image._getExifTag(key)
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
            _tag = self._image._getIptcTag(key)
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
            _tag = self._image._getXmpTag(key)
            tag = XmpTag._from_existing_tag(_tag)
            tag.metadata = self
            self._tags['xmp'][key] = tag
            return tag

    def __getitem__(self, key):
        """
        Get a metadata tag for a given key.

        :param key: metadata key in the dotted form
                    ``familyName.groupName.tagName`` where ``familyName`` may
                    be one of ``exif``, ``iptc`` or ``xmp``.
        :type key: string

        :raise KeyError: if the tag doesn't exist
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_get_%s_tag' % family)(key)
        except AttributeError:
            raise KeyError(key)

    def _set_exif_tag(self, key, tag_or_value):
        # Set an EXIF tag. If the tag already exists, its value is overwritten.
        if isinstance(tag_or_value, ExifTag):
            tag = tag_or_value
        else:
            # As a handy shortcut, accept direct value assignment.
            tag = ExifTag(key, tag_or_value)
        self._image._setExifTagValue(tag.key, tag.raw_value)
        self._tags['exif'][tag.key] = tag
        if tag.key not in self.exif_keys:
            self._keys['exif'].append(tag.key)
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
        self._image._setExifTagValue(key, value)

    def _set_iptc_tag(self, key, tag_or_values):
        # Set an IPTC tag. If the tag already exists, its values are
        # overwritten.
        if isinstance(tag_or_values, IptcTag):
            tag = tag_or_values
        else:
            # As a handy shortcut, accept direct value assignment.
            tag = IptcTag(key, tag_or_values)
        self._image._setIptcTagValues(tag.key, tag.raw_values)
        self._tags['iptc'][tag.key] = tag
        if tag.key not in self.iptc_keys:
            self._keys['iptc'].append(tag.key)
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
        self._image._setIptcTagValues(key, values)

    def _set_xmp_tag(self, key, tag_or_value):
        # Set an XMP tag. If the tag already exists, its value is overwritten.
        if isinstance(tag_or_value, XmpTag):
            tag = tag_or_value
        else:
            # As a handy shortcut, accept direct value assignment.
            tag = XmpTag(key, tag_or_value)
        type = tag._tag._getExiv2Type()
        if type == 'XmpText':
            self._image._setXmpTagTextValue(tag.key, tag.raw_value)
        elif type in ('XmpAlt', 'XmpBag', 'XmpSeq'):
            self._image._setXmpTagArrayValue(tag.key, tag.raw_value)
        elif type == 'LangAlt':
            self._image._setXmpTagLangAltValue(tag.key, tag.raw_value)
        self._tags['xmp'][tag.key] = tag
        if tag.key not in self.xmp_keys:
            self._keys['xmp'].append(tag.key)
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
            self._image._setXmpTagTextValue(key, value)
        elif type in ('XmpAlt', 'XmpBag', 'XmpSeq') and isinstance(value, (list, tuple)):
            self._image._setXmpTagArrayValue(key, value)
        elif type == 'LangAlt' and isinstance(value, dict):
            self._image._setXmpTagLangAltValue(key, value)
        else:
            raise TypeError('Expecting either a string, a list, a tuple or a dict')

    def __setitem__(self, key, tag_or_value):
        """
        Set a metadata tag for a given key.
        If the tag was previously set, it is overwritten.
        As a handy shortcut, a value may be passed instead of a fully formed
        tag. The corresponding tag object will be instantiated.

        :param key: metadata key in the dotted form
                    ``familyName.groupName.tagName`` where ``familyName`` may
                    be one of ``exif``, ``iptc`` or ``xmp``.
        :type key: string
        :param tag_or_value: an instance of the corresponding family of metadata
                             tag, or a value
        :type tag_or_value: :class:`pyexiv2.exif.ExifTag` or
                            :class:`pyexiv2.iptc.IptcTag` or
                            :class:`pyexiv2.xmp.XmpTag` or any valid value type

        :raise KeyError: if the key is invalid
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_set_%s_tag' % family)(key, tag_or_value)
        except AttributeError:
            raise KeyError(key)

    def _delete_exif_tag(self, key):
        # Delete an EXIF tag.
        # Throw a KeyError if the tag doesn't exist.
        if key not in self.exif_keys:
            raise KeyError('Cannot delete an inexistent tag')
        self._image._deleteExifTag(key)
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
        self._image._deleteIptcTag(key)
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
        self._image._deleteXmpTag(key)
        try:
            del self._tags['xmp'][key]
        except KeyError:
            # The tag was not cached.
            pass

    def __delitem__(self, key):
        """
        Delete a metadata tag for a given key.

        :param key: metadata key in the dotted form
                    ``familyName.groupName.tagName`` where ``familyName`` may
                    be one of ``exif``, ``iptc`` or ``xmp``.
        :type key: string

        :raise KeyError: if the tag with the given key doesn't exist
        """
        family = key.split('.')[0].lower()
        try:
            return getattr(self, '_delete_%s_tag' % family)(key)
        except AttributeError:
            raise KeyError(key)

    @property
    def previews(self):
        """List of the previews available in the image, sorted by increasing
        size."""
        return self._image._previews()

    def copy(self, other, exif=True, iptc=True, xmp=True):
        """
        Copy the metadata to another image.
        The metadata in the destination is overridden. In particular, if the
        destination contains e.g. EXIF data and the source doesn't, it will be
        erased in the destination, unless explicitly omitted.

        :param other: the destination metadata to copy to (it must have been
                      :meth:`.read` beforehand)
        :type other: :class:`pyexiv2.metadata.ImageMetadata`
        :param exif: whether to copy the EXIF metadata
        :type exif: boolean
        :param iptc: whether to copy the IPTC metadata
        :type iptc: boolean
        :param xmp: whether to copy the XMP metadata
        :type xmp: boolean
        """
        self._image._copyMetadata(other._image, exif, iptc, xmp)
        # Empty the cache where needed
        if exif:
            other._keys['exif'] = None
            other._tags['exif'] = {}
        if iptc:
            other._keys['iptc'] = None
            other._tags['iptc'] = {}
        if xmp:
            other._keys['xmp'] = None
            other._tags['xmp'] = {}

    @property
    def buffer(self):
        """
        The image buffer as a string.
        If metadata has been modified, the data won't be up-to-date until
        :meth:`.write` has been called.
        """
        return self._image._getDataBuffer()

