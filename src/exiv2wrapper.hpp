// *****************************************************************************
/*
 * Copyright (C) 2006-2008 Olivier Tilloy <olivier@tilloy.net>
 *
 * This file is part of the pyexiv2 distribution.
 *
 * pyexiv2 is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * pyexiv2 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with pyexiv2; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, 5th Floor, Boston, MA 02110-1301 USA.
 */
/*
  File:      exiv2wrapper.hpp
  Author(s): Olivier Tilloy <olivier@tilloy.net>
 */
// *****************************************************************************

#ifndef __exiv2wrapper__
#define __exiv2wrapper__

#include <string>

#include "exiv2/image.hpp"
//#include "exiv2/exif.hpp"
//#include "exiv2/iptc.hpp"

#include "boost/python.hpp"

namespace exiv2wrapper
{

class Image
{
public:
    // Constructors
    Image(const std::string& filename);
    Image(const Image& image);

    void readMetadata();
    //void writeMetadata();

    // Read and write access to the EXIF tags.
    // For a complete list of the available EXIF tags, see
    // libexiv2's documentation (http://exiv2.org/tags.html).

    // Return a list of all the keys of available EXIF tags set in the
    // image.
    boost::python::list exifKeys();

    // Return a tuple containing the type (as a string) and the value
    // (as a string as well) of the required EXIF tag.
    // Throw an exception if the tag is not set.
    // key
    // tagname
    // taglabel
    // tagdesc
    // type
    // tagvalue
    // tagvalue (human-readable)
    boost::python::tuple getExifTag(std::string key);

    // Return a human-readable string containing the value of the
    // required EXIF tag.
    // Throw an exception if the tag is not set.
    //std::string getExifTagToString(std::string key);

    // Set the EXIF tag's value and return a tuple containing the
    // type and previous value of the tag (empty strings if not previously
    // set). If the tag was not previously set, it is created.
    //boost::python::tuple setExifTag(std::string key, std::string value);

    // Delete the required EXIF tag and return a tuple containing the
    // type and previous value.
    // Throw an exception if the tag was not set.
    //boost::python::tuple deleteExifTag(std::string key);

    // Read and write access to the IPTC tags.
    // For a complete list of the available IPTC tags, see
    // libexiv2's documentation (http://exiv2.org/iptc.html).

    // Returns a list of all the keys of available IPTC tags set in the
    // image. This list has no duplicates: each of its items is unique,
    // even if a tag is present more than once.
    boost::python::list iptcKeys();

    // Return a tuple containing the type (as a string) and the value
    // (as a string as well) of the required IPTC tag.
    // Throw an exception if the tag is not set.
    // key
    // tagname
    // taglabel
    // tagdesc
    // type
    // tagvalue (list)
    // tagvalue (human-readable) (list)
    boost::python::tuple getIptcTag(std::string key);

    // Set the IPTC tag's value and return a tuple containing the
    // type and previous value of the tag (empty strings if not previously
    // set). If the tag was not previously set, it is created.
    // If the key references a repeatable tag, the parameter index (starting
    // from 0 like a list index) is used to determine which of the
    // repetitions is to be set. In case of an index greater than the
    // highest existing one, adds a repetition of the tag.
    //boost::python::tuple setIptcTag(std::string key, std::string value, unsigned int index);

    // Delete the required IPTC tag and return a tuple containing the
    // type and previous value.
    // If the key references a repeatable tag, the parameter index (starting
    // from 0 like a list index) is used to determine which of the
    // repetitions is to be deleted.
    // Throw an exception if the tag was not set or if the index is greater
    // than the highest existing one.
    //boost::python::tuple deleteIptcTag(std::string key, unsigned int index);

    boost::python::list xmpKeys();

    // Return a tuple containing the name of the tag and its description.
    //boost::python::tuple tagDetails(std::string key);

    // Read and write access to the thumbnail embedded in the image.

    // Return a tuple containing the format of the thumbnail ("TIFF" or
    // "JPEG") and the thumbnail raw data as a string buffer.
    // Throw an exception if the thumbnail data cannot be accessed.
    //boost::python::tuple getThumbnailData();

    // Set the thumbnail of the image. The parameter is the thumbnail raw
    // jpeg data as a string buffer.
    //void setThumbnailData(std::string data);

    // Delete the thumbnail embedded in the image.
    //void deleteThumbnail();

    // Write the thumbnail to an image file.
    // A filename extension is appended to the given path according to the
    // image type of the thumbnail, so it should not include an extension.
    // Throw an exception if the image does not contain a thumbnail.
    //void dumpThumbnailToFile(const std::string path);

    // Set the image contained in the jpeg file passed as a parameter as
    // the thumbnail of the image.
    //void setThumbnailFromJpegFile(const std::string path);

private:
    std::string _filename;
    Exiv2::Image::AutoPtr _image;
    Exiv2::ExifData _exifData;
    Exiv2::IptcData _iptcData;
    Exiv2::XmpData _xmpData;

    // true if the image's internal metadata has already been read,
    // false otherwise
    bool _dataRead;
};

// Translate an Exiv2 generic exception into a Python exception
void translateExiv2Error(Exiv2::Error const& error);

} // End of namespace exiv2wrapper

#endif

