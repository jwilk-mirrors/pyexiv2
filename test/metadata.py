# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2009-2010 Olivier Tilloy <olivier@tilloy.net>
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

import unittest

from pyexiv2.metadata import ImageMetadata
from pyexiv2.exif import ExifTag
from pyexiv2.iptc import IptcTag
from pyexiv2.xmp import XmpTag
from pyexiv2.utils import FixedOffset, Rational

import datetime


class _TagMock(object):

    def __init__(self, key, type, value):
        self.key = key
        self.type = type
        self.value = value

    def _getKey(self):
        return self.key

    def _getType(self):
        return self.type

    def _getRawValue(self):
        return self.value


class _ExifTagMock(_TagMock):

    def __init__(self, key, type, value, human_value=None):
        super(_ExifTagMock, self).__init__(key, type, value)
        self.human_value = human_value

    def _getHumanValue(self):
        return self.human_value

    def _setRawValue(self, value):
        pass


class _IptcTagMock(_TagMock):

    def _getRawValues(self):
        return self.value

    def _setRawValues(self, values):
        pass


class _XmpTagMock(_TagMock):

    def __init__(self, key, type, exiv2_type, value):
        super(_XmpTagMock, self).__init__(key, type, value)
        self.exiv2_type = exiv2_type

    def _getExiv2Type(self):
        return self.exiv2_type

    def _getTextValue(self):
        return self.value

    def _getArrayValue(self):
        return self.value


class ImageMock(object):

    def __init__(self, filename):
        self.filename = filename
        self.read = False
        self.written = False
        self.tags = {'exif': {}, 'iptc': {}, 'xmp': {}}

    def readMetadata(self):
        self.read = True

    def writeMetadata(self):
        self.written = True

    def exifKeys(self):
        return self.tags['exif'].keys()

    def getExifTag(self, key):
        return self.tags['exif'][key]

    def setExifTagValue(self, key, value):
        self.tags['exif'][key] = value

    def deleteExifTag(self, key):
        try:
            del self.tags['exif'][key]
        except KeyError:
            pass

    def iptcKeys(self):
        return self.tags['iptc'].keys()

    def getIptcTag(self, key):
        return self.tags['iptc'][key]

    def setIptcTagValues(self, key, values):
        self.tags['iptc'][key] = values

    def deleteIptcTag(self, key):
        try:
            del self.tags['iptc'][key]
        except KeyError:
            pass

    def xmpKeys(self):
        return self.tags['xmp'].keys()

    def getXmpTag(self, key):
        return self.tags['xmp'][key]

    def setXmpTagTextValue(self, key, value):
        self.tags['xmp'][key] = value

    def setXmpTagArrayValue(self, key, value):
        self.tags['xmp'][key] = value

    def setXmpTagLangAltValue(self, key, value):
        self.tags['xmp'][key] = value

    def deleteXmpTag(self, key):
        try:
            del self.tags['xmp'][key]
        except KeyError:
            pass


class TestImageMetadata(unittest.TestCase):

    def setUp(self):
        self.metadata = ImageMetadata('nofile')
        self.metadata._instantiate_image = lambda filename: ImageMock(filename)

    def _set_exif_tags(self):
        tags = {}
        tags['Exif.Image.Make'] = _ExifTagMock('Exif.Image.Make', 'Ascii', 'EASTMAN KODAK COMPANY')
        tags['Exif.Image.DateTime'] = _ExifTagMock('Exif.Image.DateTime', 'Ascii', '2009:02:09 13:33:20')
        tags['Exif.Photo.ExifVersion'] = _ExifTagMock('Exif.Photo.ExifVersion', 'Undefined', '48 50 50 49 ')
        self.metadata._image.tags['exif'] = tags

    def _set_iptc_tags(self):
        tags = {}
        tags['Iptc.Application2.Caption'] = _IptcTagMock('Iptc.Application2.Caption', 'String', ['blabla'])
        tags['Iptc.Application2.DateCreated'] = _IptcTagMock('Iptc.Application2.DateCreated', 'Date', ['2004-07-13'])
        self.metadata._image.tags['iptc'] = tags

    def _set_xmp_tags(self):
        tags = {}
        tags['Xmp.dc.format'] = _XmpTagMock('Xmp.dc.format', 'MIMEType', 'XmpText', 'image/jpeg')
        tags['Xmp.dc.subject'] = _XmpTagMock('Xmp.dc.subject', 'bag Text', 'XmpBag', 'image, test, pyexiv2')
        tags['Xmp.xmp.CreateDate'] = _XmpTagMock('Xmp.xmp.CreateDate', 'Date', 'XmpText', '2005-09-07T15:07:40-07:00')
        tags['Xmp.xmpMM.DocumentID'] = _XmpTagMock('Xmp.xmpMM.DocumentID', 'URI', 'XmpText', 'uuid:9A3B7F52214211DAB6308A7391270C13')
        self.metadata._image.tags['xmp'] = tags

    ######################
    # Test general methods
    ######################

    def test_read(self):
        self.assertEqual(self.metadata._image, None)
        self.metadata.read()
        self.failIfEqual(self.metadata._image, None)
        self.failUnless(self.metadata._image.read)

    def test_write(self):
        self.metadata.read()
        self.failIf(self.metadata._image.written)
        self.metadata.write()
        self.failUnless(self.metadata._image.written)

    ###########################
    # Test EXIF-related methods
    ###########################

    def test_exif_keys(self):
        self.metadata.read()
        self._set_exif_tags()
        self.assertEqual(self.metadata._keys['exif'], None)
        keys = self.metadata.exif_keys
        self.assertEqual(len(keys), 3)
        self.assertEqual(self.metadata._keys['exif'], keys)

    def test_get_exif_tag(self):
        self.metadata.read()
        self._set_exif_tags()
        self.assertEqual(self.metadata._tags['exif'], {})
        # Get an existing tag
        key = 'Exif.Image.Make'
        tag = self.metadata._get_exif_tag(key)
        self.assertEqual(type(tag), ExifTag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['exif'][key], tag)
        # Try to get an nonexistent tag
        key = 'Exif.Photo.Sharpness'
        self.failUnlessRaises(KeyError, self.metadata._get_exif_tag, key)

    def test_set_exif_tag_wrong(self):
        self.metadata.read()
        self._set_exif_tags()
        self.assertEqual(self.metadata._tags['exif'], {})
        # Try to set a tag with wrong type
        tag = 'Not an exif tag'
        self.failUnlessRaises(TypeError, self.metadata._set_exif_tag, tag)
        self.assertEqual(self.metadata._tags['exif'], {})

    def test_set_exif_tag_create(self):
        self.metadata.read()
        self._set_exif_tags()
        self.assertEqual(self.metadata._tags['exif'], {})
        # Create a new tag
        tag = ExifTag('Exif.Thumbnail.Orientation', 1)
        self.assertEqual(tag.metadata, None)
        self.metadata._set_exif_tag(tag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['exif'], {tag.key: tag})
        self.assert_(self.metadata._image.tags['exif'].has_key(tag.key))
        self.assertEqual(self.metadata._image.tags['exif'][tag.key],
                         tag.raw_value)

    def test_set_exif_tag_overwrite(self):
        self.metadata.read()
        self._set_exif_tags()
        self.assertEqual(self.metadata._tags['exif'], {})
        # Overwrite an existing tag
        tag = ExifTag('Exif.Image.DateTime', datetime.datetime(2009, 3, 20, 20, 32, 0))
        self.assertEqual(tag.metadata, None)
        self.metadata._set_exif_tag(tag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['exif'], {tag.key: tag})
        self.assert_(self.metadata._image.tags['exif'].has_key(tag.key))
        self.assertEqual(self.metadata._image.tags['exif'][tag.key],
                         tag.raw_value)

    def test_set_exif_tag_overwrite_already_cached(self):
        self.metadata.read()
        self._set_exif_tags()
        self.assertEqual(self.metadata._tags['exif'], {})
        # Overwrite an existing tag already cached
        key = 'Exif.Photo.ExifVersion'
        tag = self.metadata._get_exif_tag(key)
        self.assertEqual(self.metadata._tags['exif'][key], tag)
        new_tag = ExifTag(key, '48 50 50 48 ', _tag=_ExifTagMock(key, 'Undefined', '48 50 50 48 ', '2.20'))
        self.assertEqual(new_tag.metadata, None)
        self.metadata._set_exif_tag(new_tag)
        self.assertEqual(new_tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['exif'], {key: new_tag})
        self.assert_(self.metadata._image.tags['exif'].has_key(key))
        # Special case where the formatted value is used instead of the raw
        # value.
        self.assertEqual(self.metadata._image.tags['exif'][key], new_tag.raw_value)

    def test_set_exif_tag_value_inexistent(self):
        self.metadata.read()
        self._set_exif_tags()
        key = 'Exif.Photo.ExposureTime'
        value = '1/500'
        self.failUnlessRaises(KeyError, self.metadata._set_exif_tag_value,
                              key, value)

    def test_set_exif_tag_value_wrong_type(self):
        self.metadata.read()
        self._set_exif_tags()
        key = 'Exif.Image.DateTime'
        value = datetime.datetime(2009, 3, 24, 9, 37, 36)
        self.failUnlessRaises(TypeError, self.metadata._set_exif_tag_value,
                              key, value)

    def test_set_exif_tag_value(self):
        self.metadata.read()
        self._set_exif_tags()
        key = 'Exif.Image.DateTime'
        tag = self.metadata._get_exif_tag(key)
        value = '2009:03:24 09:37:36'
        self.failIfEqual(self.metadata._image.tags['exif'][key], value)
        self.metadata._set_exif_tag_value(key, value)
        self.assertEqual(self.metadata._image.tags['exif'][key], value)

    def test_delete_exif_tag_inexistent(self):
        self.metadata.read()
        self._set_exif_tags()
        key = 'Exif.Image.Artist'
        self.failUnlessRaises(KeyError, self.metadata._delete_exif_tag, key)

    def test_delete_exif_tag_not_cached(self):
        self.metadata.read()
        self._set_exif_tags()
        key = 'Exif.Image.DateTime'
        self.assertEqual(self.metadata._tags['exif'], {})
        self.assert_(self.metadata._image.tags['exif'].has_key(key))
        self.metadata._delete_exif_tag(key)
        self.assertEqual(self.metadata._tags['exif'], {})
        self.failIf(self.metadata._image.tags['exif'].has_key(key))

    def test_delete_exif_tag_cached(self):
        self.metadata.read()
        self._set_exif_tags()
        key = 'Exif.Image.DateTime'
        self.assert_(self.metadata._image.tags['exif'].has_key(key))
        tag = self.metadata._get_exif_tag(key)
        self.assertEqual(self.metadata._tags['exif'][key], tag)
        self.metadata._delete_exif_tag(key)
        self.assertEqual(self.metadata._tags['exif'], {})
        self.failIf(self.metadata._image.tags['exif'].has_key(key))

    ###########################
    # Test IPTC-related methods
    ###########################

    def test_iptc_keys(self):
        self.metadata.read()
        self._set_iptc_tags()
        self.assertEqual(self.metadata._keys['iptc'], None)
        keys = self.metadata.iptc_keys
        self.assertEqual(len(keys), 2)
        self.assertEqual(self.metadata._keys['iptc'], keys)

    def test_get_iptc_tag(self):
        self.metadata.read()
        self._set_iptc_tags()
        self.assertEqual(self.metadata._tags['iptc'], {})
        # Get an existing tag
        key = 'Iptc.Application2.DateCreated'
        tag = self.metadata._get_iptc_tag(key)
        self.assertEqual(type(tag), IptcTag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['iptc'][key], tag)
        # Try to get an nonexistent tag
        key = 'Iptc.Application2.Copyright'
        self.failUnlessRaises(KeyError, self.metadata._get_iptc_tag, key)

    def test_set_iptc_tag_wrong(self):
        self.metadata.read()
        self._set_iptc_tags()
        self.assertEqual(self.metadata._tags['iptc'], {})
        # Try to set a tag with wrong type
        tag = 'Not an iptc tag'
        self.failUnlessRaises(TypeError, self.metadata._set_iptc_tag, tag)
        self.assertEqual(self.metadata._tags['iptc'], {})

    def test_set_iptc_tag_create(self):
        self.metadata.read()
        self._set_iptc_tags()
        self.assertEqual(self.metadata._tags['iptc'], {})
        # Create a new tag
        tag = IptcTag('Iptc.Application2.Writer', ['Nobody'])
        self.assertEqual(tag.metadata, None)
        self.metadata._set_iptc_tag(tag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['iptc'], {tag.key: tag})
        self.assert_(self.metadata._image.tags['iptc'].has_key(tag.key))
        self.assertEqual(self.metadata._image.tags['iptc'][tag.key],
                         tag.raw_values)

    def test_set_iptc_tag_overwrite(self):
        self.metadata.read()
        self._set_iptc_tags()
        self.assertEqual(self.metadata._tags['iptc'], {})
        # Overwrite an existing tag
        tag = IptcTag('Iptc.Application2.Caption', ['A picture.'])
        self.assertEqual(tag.metadata, None)
        self.metadata._set_iptc_tag(tag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['iptc'], {tag.key: tag})
        self.assert_(self.metadata._image.tags['iptc'].has_key(tag.key))
        self.assertEqual(self.metadata._image.tags['iptc'][tag.key],
                         tag.raw_values)

    def test_set_iptc_tag_overwrite_already_cached(self):
        self.metadata.read()
        self._set_iptc_tags()
        self.assertEqual(self.metadata._tags['iptc'], {})
        # Overwrite an existing tag already cached
        key = 'Iptc.Application2.Caption'
        tag = self.metadata._get_iptc_tag(key)
        self.assertEqual(self.metadata._tags['iptc'][key], tag)
        new_tag = IptcTag(key, ['A picture.'])
        self.assertEqual(new_tag.metadata, None)
        self.metadata._set_iptc_tag(new_tag)
        self.assertEqual(new_tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['iptc'], {key: new_tag})
        self.assert_(self.metadata._image.tags['iptc'].has_key(key))
        self.assertEqual(self.metadata._image.tags['iptc'][key],
                         new_tag.raw_values)

    def test_set_iptc_tag_values_inexistent(self):
        self.metadata.read()
        self._set_iptc_tags()
        key = 'Iptc.Application2.Urgency'
        values = ['1']
        self.failUnlessRaises(KeyError, self.metadata._set_iptc_tag_values,
                              key, values)

    def test_set_iptc_tag_values_wrong_type(self):
        self.metadata.read()
        self._set_iptc_tags()
        key = 'Iptc.Application2.DateCreated'
        value = '20090324'
        self.failUnlessRaises(TypeError, self.metadata._set_iptc_tag_values,
                              key, value)
        values = [datetime.date(2009, 3, 24)]
        self.failUnlessRaises(TypeError, self.metadata._set_iptc_tag_values,
                              key, values)

    def test_set_iptc_tag_values(self):
        self.metadata.read()
        self._set_iptc_tags()
        key = 'Iptc.Application2.DateCreated'
        tag = self.metadata._get_iptc_tag(key)
        values = ['2009-04-07']
        self.failIfEqual(self.metadata._image.tags['iptc'][key], values)
        self.metadata._set_iptc_tag_values(key, values)
        self.assertEqual(self.metadata._image.tags['iptc'][key], values)

    def test_delete_iptc_tag_inexistent(self):
        self.metadata.read()
        self._set_iptc_tags()
        key = 'Iptc.Application2.LocationCode'
        self.failUnlessRaises(KeyError, self.metadata._delete_iptc_tag, key)

    def test_delete_iptc_tag_not_cached(self):
        self.metadata.read()
        self._set_iptc_tags()
        key = 'Iptc.Application2.Caption'
        self.assertEqual(self.metadata._tags['iptc'], {})
        self.assert_(self.metadata._image.tags['iptc'].has_key(key))
        self.metadata._delete_iptc_tag(key)
        self.assertEqual(self.metadata._tags['iptc'], {})
        self.failIf(self.metadata._image.tags['iptc'].has_key(key))

    def test_delete_iptc_tag_cached(self):
        self.metadata.read()
        self._set_iptc_tags()
        key = 'Iptc.Application2.Caption'
        self.assert_(self.metadata._image.tags['iptc'].has_key(key))
        tag = self.metadata._get_iptc_tag(key)
        self.assertEqual(self.metadata._tags['iptc'][key], tag)
        self.metadata._delete_iptc_tag(key)
        self.assertEqual(self.metadata._tags['iptc'], {})
        self.failIf(self.metadata._image.tags['iptc'].has_key(key))

    ##########################
    # Test XMP-related methods
    ##########################

    def test_xmp_keys(self):
        self.metadata.read()
        self._set_xmp_tags()
        self.assertEqual(self.metadata._keys['xmp'], None)
        keys = self.metadata.xmp_keys
        self.assertEqual(len(keys), 4)
        self.assertEqual(self.metadata._keys['xmp'], keys)

    def test_get_xmp_tag(self):
        self.metadata.read()
        self._set_xmp_tags()
        self.assertEqual(self.metadata._tags['xmp'], {})
        # Get an existing tag
        key = 'Xmp.dc.subject'
        tag = self.metadata._get_xmp_tag(key)
        self.assertEqual(type(tag), XmpTag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['xmp'][key], tag)
        # Try to get an nonexistent tag
        key = 'Xmp.xmp.Label'
        self.failUnlessRaises(KeyError, self.metadata._get_xmp_tag, key)

    def test_set_xmp_tag_wrong(self):
        self.metadata.read()
        self._set_xmp_tags()
        self.assertEqual(self.metadata._tags['xmp'], {})
        # Try to set a tag with wrong type
        tag = 'Not an xmp tag'
        self.failUnlessRaises(TypeError, self.metadata._set_xmp_tag, tag)
        self.assertEqual(self.metadata._tags['xmp'], {})

    def test_set_xmp_tag_create(self):
        self.metadata.read()
        self._set_xmp_tags()
        self.assertEqual(self.metadata._tags['xmp'], {})
        # Create a new tag
        tag = XmpTag('Xmp.dc.title', {'x-default': 'This is not a title',
                                      'fr-FR': "Ceci n'est pas un titre"})
        self.assertEqual(tag.metadata, None)
        self.metadata._set_xmp_tag(tag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['xmp'], {tag.key: tag})
        self.assert_(self.metadata._image.tags['xmp'].has_key(tag.key))
        self.assertEqual(self.metadata._image.tags['xmp'][tag.key],
                         tag.raw_value)

    def test_set_xmp_tag_overwrite(self):
        self.metadata.read()
        self._set_xmp_tags()
        self.assertEqual(self.metadata._tags['xmp'], {})
        # Overwrite an existing tag
        tag = XmpTag('Xmp.dc.format', ('image', 'png'))
        self.assertEqual(tag.metadata, None)
        self.metadata._set_xmp_tag(tag)
        self.assertEqual(tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['xmp'], {tag.key: tag})
        self.assert_(self.metadata._image.tags['xmp'].has_key(tag.key))
        self.assertEqual(self.metadata._image.tags['xmp'][tag.key],
                         tag.raw_value)

    def test_set_xmp_tag_overwrite_already_cached(self):
        self.metadata.read()
        self._set_xmp_tags()
        self.assertEqual(self.metadata._tags['xmp'], {})
        # Overwrite an existing tag already cached
        key = 'Xmp.xmp.CreateDate'
        tag = self.metadata._get_xmp_tag(key)
        self.assertEqual(self.metadata._tags['xmp'][key], tag)
        new_tag = XmpTag(key, datetime.datetime(2009, 4, 21, 20, 7, 0, tzinfo=FixedOffset('+', 1, 0)))
        self.assertEqual(new_tag.metadata, None)
        self.metadata._set_xmp_tag(new_tag)
        self.assertEqual(new_tag.metadata, self.metadata)
        self.assertEqual(self.metadata._tags['xmp'], {key: new_tag})
        self.assert_(self.metadata._image.tags['xmp'].has_key(key))
        self.assertEqual(self.metadata._image.tags['xmp'][key],
                         new_tag.raw_value)

    def test_set_xmp_tag_value_inexistent(self):
        self.metadata.read()
        self._set_xmp_tags()
        key = 'Xmp.xmp.Nickname'
        value = 'oSoMoN'
        self.failUnlessRaises(KeyError, self.metadata._set_xmp_tag_value,
                              key, value)

    def test_set_xmp_tag_value_wrong_type(self):
        self.metadata.read()
        self._set_xmp_tags()
        key = 'Xmp.xmp.CreateDate'
        tag = self.metadata[key]
        value = datetime.datetime(2009, 4, 21, 20, 11, 0)
        self.failUnlessRaises(TypeError, self.metadata._set_xmp_tag_value,
                              key, value)

    def test_set_xmp_tag_value(self):
        self.metadata.read()
        self._set_xmp_tags()
        key = 'Xmp.xmp.CreateDate'
        tag = self.metadata._get_xmp_tag(key)
        value = '2009-04-21T20:12:47+01:00'
        self.failIfEqual(self.metadata._image.tags['xmp'][key], value)
        self.metadata._set_xmp_tag_value(key, value)
        self.assertEqual(self.metadata._image.tags['xmp'][key], value)

    def test_delete_xmp_tag_inexistent(self):
        self.metadata.read()
        self._set_xmp_tags()
        key = 'Xmp.xmp.CreatorTool'
        self.failUnlessRaises(KeyError, self.metadata._delete_xmp_tag, key)

    def test_delete_xmp_tag_not_cached(self):
        self.metadata.read()
        self._set_xmp_tags()
        key = 'Xmp.dc.subject'
        self.assertEqual(self.metadata._tags['xmp'], {})
        self.assert_(self.metadata._image.tags['xmp'].has_key(key))
        self.metadata._delete_xmp_tag(key)
        self.assertEqual(self.metadata._tags['xmp'], {})
        self.failIf(self.metadata._image.tags['xmp'].has_key(key))

    def test_delete_xmp_tag_cached(self):
        self.metadata.read()
        self._set_xmp_tags()
        key = 'Xmp.dc.subject'
        self.assert_(self.metadata._image.tags['xmp'].has_key(key))
        tag = self.metadata._get_xmp_tag(key)
        self.assertEqual(self.metadata._tags['xmp'][key], tag)
        self.metadata._delete_xmp_tag(key)
        self.assertEqual(self.metadata._tags['xmp'], {})
        self.failIf(self.metadata._image.tags['xmp'].has_key(key))

    ###########################
    # Test dictionary interface
    ###########################

    def test_getitem(self):
        self.metadata.read()
        self._set_exif_tags()
        self._set_iptc_tags()
        self._set_xmp_tags()
        # Get existing tags
        key = 'Exif.Photo.ExifVersion'
        tag = self.metadata[key]
        self.assertEqual(type(tag), ExifTag)
        key = 'Iptc.Application2.Caption'
        tag = self.metadata[key]
        self.assertEqual(type(tag), IptcTag)
        key = 'Xmp.xmp.CreateDate'
        tag = self.metadata[key]
        self.assertEqual(type(tag), XmpTag)
        # Try to get nonexistent tags
        keys = ('Exif.Image.SamplesPerPixel', 'Iptc.Application2.FixtureId',
                'Xmp.xmp.Rating', 'Wrong.Noluck.Raise')
        for key in keys:
            self.failUnlessRaises(KeyError, self.metadata.__getitem__, key)

    def test_setitem(self):
        self.metadata.read()
        self._set_exif_tags()
        self._set_iptc_tags()
        self._set_xmp_tags()
        # Set new tags
        key = 'Exif.Photo.ExposureBiasValue'
        tag = ExifTag(key, Rational(0, 3))
        self.metadata[key] = tag
        self.failUnless(key in self.metadata._tags['exif'])
        self.failUnlessEqual(self.metadata._tags['exif'][key], tag)
        key = 'Iptc.Application2.City'
        tag = IptcTag(key, ['Barcelona'])
        self.metadata[key] = tag
        self.failUnless(key in self.metadata._tags['iptc'])
        self.failUnlessEqual(self.metadata._tags['iptc'][key], tag)
        key = 'Xmp.dc.description'
        tag = XmpTag(key, {'x-default': 'Sunset picture.'})
        self.metadata[key] = tag
        self.failUnless(key in self.metadata._tags['xmp'])
        self.failUnlessEqual(self.metadata._tags['xmp'][key], tag)
        # Replace existing tags
        key = 'Exif.Photo.ExifVersion'
        tag = ExifTag(key, '48 50 50 48 ')
        self.metadata[key] = tag
        self.failUnless(key in self.metadata._tags['exif'])
        self.failUnlessEqual(self.metadata._tags['exif'][key], tag)
        key = 'Iptc.Application2.Caption'
        tag = IptcTag(key, ['Sunset on Barcelona.'])
        self.metadata[key] = tag
        self.failUnless(key in self.metadata._tags['iptc'])
        self.failUnlessEqual(self.metadata._tags['iptc'][key], tag)
        key = 'Xmp.dc.subject'
        tag = XmpTag(key, ['sunset', 'Barcelona', 'beautiful', 'beach'])
        self.metadata[key] = tag
        self.failUnless(key in self.metadata._tags['xmp'])
        self.failUnlessEqual(self.metadata._tags['xmp'][key], tag)

    def test_delitem(self):
        self.metadata.read()
        self._set_exif_tags()
        self._set_iptc_tags()
        self._set_xmp_tags()
        # Delete existing tags
        key = 'Exif.Photo.ExifVersion'
        del self.metadata[key]
        self.failIf(key in self.metadata._tags['exif'])
        key = 'Iptc.Application2.Caption'
        del self.metadata[key]
        self.failIf(key in self.metadata._tags['iptc'])
        key = 'Xmp.xmp.CreateDate'
        del self.metadata[key]
        self.failIf(key in self.metadata._tags['xmp'])
        # Try to delete nonexistent tags
        keys = ('Exif.Image.SamplesPerPixel', 'Iptc.Application2.FixtureId',
                'Xmp.xmp.Rating', 'Wrong.Noluck.Raise')
        for key in keys:
            self.failUnlessRaises(KeyError, self.metadata.__delitem__, key)

