// *****************************************************************************
/*
 * Copyright (C) 2006 Olivier Tilloy <olivier@tilloy.net>
 *
 * This program is part of the pyexiv2 distribution.
 *
 * pyexiv2 is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, 5th Floor, Boston, MA 02110-1301 USA.
 */
/*
  File:      libpyexiv2_wrapper.cpp
  Author(s): Olivier Tilloy <olivier@tilloy.net>
  History:   28-Dec-06, Olivier Tilloy: created
             30-Dec-06, Olivier Tilloy: added IPTC-related methods
 */
// *****************************************************************************

#include "libpyexiv2.hpp"

#include <boost/python.hpp>

using namespace boost::python;

using namespace LibPyExiv2;

BOOST_PYTHON_MODULE(libpyexiv2)
{
	class_<Image>("Image", init<std::string>())
		.def("readMetadata", &Image::readMetadata)
		.def("writeMetadata", &Image::writeMetadata)
		.def("getAvailableExifTags", &Image::getAvailableExifTags)
		.def("getExifTag", &Image::getExifTag)
		.def("getExifTagToString", &Image::getExifTagToString)
		.def("setExifTag", &Image::setExifTag)
		.def("deleteExifTag", &Image::deleteExifTag)
		.def("getAvailableIptcTags", &Image::getAvailableIptcTags)
		.def("getIptcTag", &Image::getIptcTag)
		.def("setIptcTag", &Image::setIptcTag)
		.def("deleteIptcTag", &Image::deleteIptcTag)
	;
}
