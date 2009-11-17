#!//usr/bin/python
# -*- coding: utf-8 -*-

from pyexiv2 import ImageMetadata, ExifTag

import sys
from datetime import datetime


if __name__ == '__main__':
    # Read an image file's metadata
    image_file = sys.argv[1]
    metadata = ImageMetadata(image_file)
    metadata.read()

    # Print a list of all the keys of the EXIF tags in the image
    print metadata.exif_keys

    # Print the value of the Exif.Image.DateTime tag
    print metadata['Exif.Image.DateTime']

    # Set the value of the Exif.Image.DateTime tag
    metadata['Exif.Image.DateTime'].value = datetime.now()

    # Add a new tag
    metadata['Exif.Image.Orientation'] = ExifTag('Exif.Image.Orientation', 1)

    # Write back the metadata to the file
    metadata.write()

