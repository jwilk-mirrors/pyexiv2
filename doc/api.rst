API documentation
=================

pyexiv2
#######

.. module:: pyexiv2
.. autodata:: pyexiv2.version_info
.. autodata:: pyexiv2.__version__
.. autodata:: pyexiv2.exiv2_version_info
.. autodata:: pyexiv2.__exiv2_version__

pyexiv2.metadata
################

.. module:: pyexiv2.metadata
.. autoclass:: pyexiv2.metadata.ImageMetadata
   :members: read, write, dimensions, mime_type, exif_keys, iptc_keys,
             xmp_keys, __getitem__, __setitem__, __delitem__, previews, copy

pyexiv2.exif
############

.. module:: pyexiv2.exif
.. autoexception:: pyexiv2.exif.ExifValueError
.. autoclass:: pyexiv2.exif.ExifTag
   :members: key, type, name, label, description, section_name,
             section_description, raw_value, value, human_value

