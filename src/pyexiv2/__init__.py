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

"""
Manipulation of EXIF, IPTC and XMP metadata and thumbnails embedded in images.

The L{ImageMetadata} class provides read/write access to all the metadata and
the various thumbnails embedded in an image file such as JPEG and TIFF files.

Metadata is accessed through subclasses of L{MetadataTag} and the tag values are
conveniently wrapped in python objects.
A tag containing a date/time information for the image
(e.g. C{Exif.Photo.DateTimeOriginal}) will be represented by a python
C{datetime.datetime} object.

This module is a python layer on top of the low-level python binding of the
C++ library Exiv2, libexiv2python.

A typical use of this binding would be:

>>> import pyexiv2
>>> metadata = pyexiv2.ImageMetadata('test/smiley.jpg')
>>> metadata.read()
>>> print metadata.exif_keys
['Exif.Image.ImageDescription', 'Exif.Image.XResolution',
 'Exif.Image.YResolution', 'Exif.Image.ResolutionUnit', 'Exif.Image.Software',
 'Exif.Image.DateTime', 'Exif.Image.Artist', 'Exif.Image.Copyright',
 'Exif.Image.ExifTag', 'Exif.Photo.Flash', 'Exif.Photo.PixelXDimension',
 'Exif.Photo.PixelYDimension']
>>> print metadata['Exif.Image.DateTime'].value
2004-07-13 21:23:44
>>> import datetime
>>> metadata['Exif.Image.DateTime'].value = datetime.datetime.today()
>>> metadata.write()
"""

import libexiv2python

from pyexiv2.metadata import ImageMetadata
from pyexiv2.exif import ExifValueError, ExifTag
from pyexiv2.iptc import IptcValueError, IptcTag
from pyexiv2.xmp import XmpValueError, XmpTag
from pyexiv2.utils import FixedOffset, UndefinedToString, StringToUndefined, \
                          Rational, NotifyingList


__version__ =  (0, 2, 1)

__exiv2_version__ = libexiv2python.__exiv2_version__

