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
  File:      libpyexiv2.cpp
  Author(s): Olivier Tilloy <olivier@tilloy.net>
  History:   28-Dec-06, Olivier Tilloy: created
             30-Dec-06, Olivier Tilloy: implemented IPTC-related methods
 */
// *****************************************************************************

#include "libpyexiv2.hpp"

namespace LibPyExiv2
{

	// Base constructor
	Image::Image(std::string filename)
	{
		_filename = filename;
		try
		{
			_image = Exiv2::ImageFactory::open(filename);
			assert(_image.get() != 0);
		}
		catch(Exiv2::AnyError & e)
		{
			std::cerr << ">>> Image::Image(): caught Exiv2 exception '" << e << "'!";
		}
		_dataRead = false;
	}

	// Copy constructor
	Image::Image(const Image & image)
	{
		_filename = image._filename;
		try
		{
			_image = Exiv2::ImageFactory::open(_filename);
			assert(_image.get() != 0);
		}
		catch(Exiv2::AnyError & e)
		{
			std::cerr << ">>> Image::Image(): caught Exiv2 exception '" << e << "'!";
		}
		_dataRead = false;
	}

	void Image::readMetadata()
	{
		try
		{
			_image->readMetadata();
			_exifData = _image->exifData();
			_iptcData = _image->iptcData();
			_dataRead = true;
		}
		catch(Exiv2::Error & e)
		{
			// An error occured while reading the metadata
			_dataRead = false;
			std::cerr << ">>> Image::readMetadata(): caught Exiv2 exception '" << e << "'!";
		}
	}

	void Image::writeMetadata()
	{
		if(_dataRead)
		{
			try
			{
				_image->setExifData(_exifData);
				_image->setIptcData(_iptcData);
				_image->writeMetadata();
			}
			catch(Exiv2::Error & e)
			{
				// An error occured while writing the metadata
				std::cerr << ">>> Image::writeMetadata(): caught Exiv2 exception '" << e << "'!";
			}
		}
	}

	boost::python::list Image::getAvailableExifTags()
	{
		boost::python::list list;
		if(_dataRead)
		{
			for(Exiv2::ExifMetadata::iterator i = _exifData.begin() ; i != _exifData.end() ; ++i)
			{
				list.append(i->key());
			}
			return list;
		}
		else
		{
			std::cerr << ">>> Image::getAvailableExifTags(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			// The returned list is empty
			return list;
		}
	}

	boost::python::tuple Image::getExifTag(std::string key)
	{
		if(_dataRead)
		{
			try
			{
				Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
				Exiv2::ExifMetadata::iterator i = _exifData.findKey(exifKey);
				if(i != _exifData.end())
				{
					Exiv2::Exifdatum exifDatum = _exifData[key];
					return boost::python::make_tuple(exifDatum.typeName(), exifDatum.toString());
				}
				else
				{
					// The key was not found
					std::cerr << ">>> Image::getExifTag(): tag '" << key << "' not found" << std::endl;
					return boost::python::make_tuple(std::string(""), std::string(""));
				}
			}
			catch(Exiv2::Error & e)
			{
				// The key is not a valid Exif tag key
				std::cerr << ">>> Image::getExifTag(): unknown key '" << key << "'" << std::endl;
				return boost::python::make_tuple(std::string(""), std::string(""));
			}
		}
		else
		{
			std::cerr << ">>> Image::getExifTag(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			return boost::python::make_tuple(std::string(""), std::string(""));
		}
	}

	std::string Image::getExifTagToString(std::string key)
	{
		if(_dataRead)
		{
			try
			{
				Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
				Exiv2::ExifMetadata::iterator i = _exifData.findKey(exifKey);
				if(i != _exifData.end())
				{
					Exiv2::Exifdatum exifDatum = _exifData[key];
					std::ostringstream buffer;
					buffer << exifDatum;
					return buffer.str();
				}
				else
				{
					// The key was not found
					std::cerr << ">>> Image::getExifTagToString(): tag '" << key << "' not found" << std::endl;
					return std::string("");
				}
			}
			catch(Exiv2::Error & e)
			{
				// The key is not a valid Exif tag key
				std::cerr << ">>> Image::getExifTagToString(): unknown key '" << key << "'" << std::endl;
				return std::string("");
			}
		}
		else
		{
			std::cerr << ">>> Image::getExifTagToString(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			return std::string("");
		}
	}

	boost::python::tuple Image::setExifTag(std::string key, std::string value)
	{
		boost::python::tuple returnValue;
		if(_dataRead)
		{
			try
			{
				Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
				Exiv2::ExifMetadata::iterator i = _exifData.findKey(exifKey);
				if(i != _exifData.end())
				{
					Exiv2::Exifdatum exifDatum = _exifData[key];
					returnValue = boost::python::make_tuple(exifDatum.typeName(), exifDatum.toString());
					// First erase the existing tag: in some case (and
					// I don't know why), the new value won't replace
					// the old one if not previously erased...
					_exifData.erase(i);
				}
				else
				{
					// The key was not found
					std::cerr << ">>> Image::setExifTag(): tag '" << key << "' not found" << std::endl;
					returnValue = boost::python::make_tuple(std::string(""), std::string(""));
				}
				_exifData[key] = value;
				return returnValue;
			}
			catch(Exiv2::Error & e)
			{
				// The key is not a valid Exif tag key
				std::cerr << ">>> Image::setExifTag(): unknown key '" << key << "'" << std::endl;
				return boost::python::make_tuple(std::string(""), std::string(""));
			}
		}
		else
		{
			std::cerr << ">>> Image::setExifTag(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			return boost::python::make_tuple(std::string(""), std::string(""));
		}
	}

	boost::python::tuple Image::deleteExifTag(std::string key)
	{
		boost::python::tuple returnValue;
		if(_dataRead)
		{
			try
			{
				Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
				Exiv2::ExifMetadata::iterator i = _exifData.findKey(exifKey);
				if(i != _exifData.end())
				{
					Exiv2::Exifdatum exifDatum = _exifData[key];
					returnValue = boost::python::make_tuple(exifDatum.typeName(), exifDatum.toString());
					_exifData.erase(i);
				}
				else
				{
					// The key was not found
					std::cerr << ">>> Image::deleteExifTag(): tag '" << key << "' not found" << std::endl;
					returnValue = boost::python::make_tuple(std::string(""), std::string(""));
				}
				return returnValue;
			}
			catch(Exiv2::Error & e)
			{
				// The key is not a valid Exif tag key
				std::cerr << ">>> Image::deleteExifTag(): unknown key '" << key << "'" << std::endl;
				return boost::python::make_tuple(std::string(""), std::string(""));
			}
		}
		else
		{
			std::cerr << ">>> Image::deleteExifTag(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			return boost::python::make_tuple(std::string(""), std::string(""));
		}
	}

	// returns a list containing the keys of all the IPTC tags available in
	// the image
	boost::python::list Image::getAvailableIptcTags()
	{
		boost::python::list list;
		if(_dataRead)
		{
			for(Exiv2::IptcMetadata::iterator i = _iptcData.begin() ; i != _iptcData.end() ; i++)
			{
				list.append(i->key());
			}
			return list;
		}
		else
		{
			std::cerr << ">>> Image::getAvailableIptcTags(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			// The returned list is empty
			return list;
		}
	}

	boost::python::tuple Image::getIptcTag(std::string key)
	{
		if(_dataRead)
		{
			try
			{
				Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
				Exiv2::IptcMetadata::iterator i = _iptcData.findKey(iptcKey);
				if(i != _iptcData.end())
				{
					Exiv2::Iptcdatum iptcDatum = _iptcData[key];
					return boost::python::make_tuple(iptcDatum.typeName(), iptcDatum.toString());
				}
				else
				{
					// The key was not found
					std::cerr << ">>> Image::getIptcTag(): tag '" << key << "' not found" << std::endl;
					return boost::python::make_tuple(std::string(""), std::string(""));
				}
			}
			catch(Exiv2::Error & e)
			{
				// The key is not a valid Iptc tag key
				std::cerr << ">>> Image::getIptcTag(): unknown key '" << key << "'" << std::endl;
				return boost::python::make_tuple(std::string(""), std::string(""));
			}
		}
		else
		{
			std::cerr << ">>> Image::getIptcTag(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			return boost::python::make_tuple(std::string(""), std::string(""));
		}
	}

	boost::python::tuple Image::setIptcTag(std::string key, std::string value)
	{
		boost::python::tuple returnValue;
		if(_dataRead)
		{
			try
			{
				Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
				Exiv2::IptcMetadata::iterator i = _iptcData.findKey(iptcKey);
				if(i != _iptcData.end())
				{
					Exiv2::Iptcdatum iptcDatum = _iptcData[key];
					returnValue = boost::python::make_tuple(iptcDatum.typeName(), iptcDatum.toString());
					// First erase the existing tag
					_iptcData.erase(i);
				}
				else
				{
					// The key was not found
					std::cerr << ">>> Image::setIptcTag(): tag '" << key << "' not found" << std::endl;
					returnValue = boost::python::make_tuple(std::string(""), std::string(""));
				}
				_iptcData[key] = value;
				return returnValue;
			}
			catch(Exiv2::Error & e)
			{
				// The key is not a valid Iptc tag key
				std::cerr << ">>> Image::setIptcTag(): unknown key '" << key << "'" << std::endl;
				return boost::python::make_tuple(std::string(""), std::string(""));
			}
		}
		else
		{
			std::cerr << ">>> Image::setIptcTag(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			return boost::python::make_tuple(std::string(""), std::string(""));
		}
	}

	boost::python::tuple Image::deleteIptcTag(std::string key)
	{
		boost::python::tuple returnValue;
		if(_dataRead)
		{
			try
			{
				Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
				Exiv2::IptcMetadata::iterator i = _iptcData.findKey(iptcKey);
				if(i != _iptcData.end())
				{
					Exiv2::Iptcdatum iptcDatum = _iptcData[key];
					returnValue = boost::python::make_tuple(iptcDatum.typeName(), iptcDatum.toString());
					_iptcData.erase(i);
				}
				else
				{
					// The key was not found
					std::cerr << ">>> Image::deleteIptcTag(): tag '" << key << "' not found" << std::endl;
					returnValue = boost::python::make_tuple(std::string(""), std::string(""));
				}
				return returnValue;
			}
			catch(Exiv2::Error & e)
			{
				// The key is not a valid Iptc tag key
				std::cerr << ">>> Image::deleteIptcTag(): unknown key '" << key << "'" << std::endl;
				return boost::python::make_tuple(std::string(""), std::string(""));
			}
		}
		else
		{
			std::cerr << ">>> Image::deleteIptcTag(): metadata not read yet, call Image::readMetadata() first" << std::endl;
			return boost::python::make_tuple(std::string(""), std::string(""));
		}
	}

	boost::python::tuple Image::getThumbnailData()
	{
		//TODO
		return boost::python::make_tuple(std::string(""), std::string(""));
	}

	bool Image::setThumbnailData(boost::python::tuple data)
	{
		//TODO
		return true;
	}

} // End of namespace LibPyExiv2
