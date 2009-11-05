// *****************************************************************************
/*
 * Copyright (C) 2006-2009 Olivier Tilloy <olivier@tilloy.net>
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
  Author: Olivier Tilloy <olivier@tilloy.net>
 */
// *****************************************************************************

#include "exiv2wrapper.hpp"

#include "exiv2/exv_conf.h"
#include "exiv2/version.hpp"

#include <boost/python.hpp>

using namespace boost::python;

using namespace exiv2wrapper;

boost::python::tuple exiv2_version = \
    boost::python::make_tuple(EXIV2_MAJOR_VERSION,
                              EXIV2_MINOR_VERSION,
                              EXIV2_PATCH_VERSION);

BOOST_PYTHON_MODULE(libexiv2python)
{
    scope().attr("__exiv2_version__") = exiv2_version;

    register_exception_translator<Exiv2::Error>(&translateExiv2Error);

    class_<Image>("Image", init<std::string>())

        .def("readMetadata", &Image::readMetadata)
        .def("writeMetadata", &Image::writeMetadata)

        .def("exifKeys", &Image::exifKeys)
        .def("getExifTag", &Image::getExifTag)
        .def("setExifTagValue", &Image::setExifTagValue)
        .def("deleteExifTag", &Image::deleteExifTag)

        .def("iptcKeys", &Image::iptcKeys)
        .def("getIptcTag", &Image::getIptcTag)
        .def("setIptcTagValues", &Image::setIptcTagValues)
        .def("deleteIptcTag", &Image::deleteIptcTag)

        .def("xmpKeys", &Image::xmpKeys)
        .def("getXmpTag", &Image::getXmpTag)
        .def("setXmpTagValue", &Image::setXmpTagValue)
        .def("deleteXmpTag", &Image::deleteXmpTag)

//        .def("getThumbnailData", &Image::getThumbnailData)
//        .def("setThumbnailData", &Image::setThumbnailData)
//        .def("deleteThumbnail", &Image::deleteThumbnail)
//        .def("dumpThumbnailToFile", &Image::dumpThumbnailToFile)
//        .def("setThumbnailFromJpegFile", &Image::setThumbnailFromJpegFile)

//        .def("getComment", &Image::getComment)
//        .def("setComment", &Image::setComment)
//        .def("clearComment", &Image::clearComment)
    ;

    class_<ExifTag>("ExifTag", init<std::string>())

        .def("_setRawValue", &ExifTag::setRawValue)

        .def("_getKey", &ExifTag::getKey)
        .def("_getType", &ExifTag::getType)
        .def("_getName", &ExifTag::getName)
        .def("_getTitle", &ExifTag::getTitle)
        .def("_getLabel", &ExifTag::getLabel)
        .def("_getDescription", &ExifTag::getDescription)
        .def("_getSectionName", &ExifTag::getSectionName)
        .def("_getSectionDescription", &ExifTag::getSectionDescription)
        .def("_getRawValue", &ExifTag::getRawValue)
    ;

    class_<IptcTag>("IptcTag", init<std::string>())

        .def("_setValue", &IptcTag::setValue)

        .def("_getKey", &IptcTag::getKey)
        .def("_getType", &IptcTag::getType)
        .def("_getName", &IptcTag::getName)
        .def("_getTitle", &IptcTag::getTitle)
        .def("_getDescription", &IptcTag::getDescription)
        .def("_getPhotoshopName", &IptcTag::getPhotoshopName)
        .def("_isRepeatable", &IptcTag::isRepeatable)
        .def("_getRecordName", &IptcTag::getRecordName)
        .def("_getRecordDescription", &IptcTag::getRecordDescription)
        .def("_getValue", &IptcTag::getValue)
    ;
}

