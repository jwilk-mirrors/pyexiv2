// *****************************************************************************
/*
 * Copyright (C) 2006 Olivier Tilloy <olivier@tilloy.net>
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
  File:      libpyexiv2.cpp
  Author(s): Olivier Tilloy <olivier@tilloy.net>
 */
// *****************************************************************************

#include "libpyexiv2.hpp"

#define METADATA_NOT_READ_CODE 101

namespace LibPyExiv2
{

	// Base constructor
	Image::Image(std::string filename)
	{
		_filename = filename;
		_image = Exiv2::ImageFactory::open(filename);
		assert(_image.get() != 0);
		_dataRead = false;
	}

	// Copy constructor
	Image::Image(const Image & image)
	{
		_filename = image._filename;
		_image = Exiv2::ImageFactory::open(_filename);
		assert(_image.get() != 0);
		_dataRead = false;
	}

	void Image::readMetadata()
	{
		_image->readMetadata();
		_exifData = _image->exifData();
		_iptcData = _image->iptcData();
		_dataRead = true;
	}

	void Image::writeMetadata()
	{
		if(_dataRead)
		{
			_image->setExifData(_exifData);
			_image->setIptcData(_iptcData);
			_image->writeMetadata();
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
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
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	boost::python::tuple Image::getExifTag(std::string key)
	{
		if(_dataRead)
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
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	std::string Image::getExifTagToString(std::string key)
	{
		if(_dataRead)
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
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	boost::python::tuple Image::setExifTag(std::string key, std::string value)
	{
		boost::python::tuple returnValue;
		if(_dataRead)
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
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	boost::python::tuple Image::deleteExifTag(std::string key)
	{
		boost::python::tuple returnValue;
		if(_dataRead)
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
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
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
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	boost::python::tuple Image::getIptcTag(std::string key)
	{
		if(_dataRead)
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
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	boost::python::tuple Image::setIptcTag(std::string key, std::string value)
	{
		boost::python::tuple returnValue;
		if(_dataRead)
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
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	boost::python::tuple Image::deleteIptcTag(std::string key)
	{
		boost::python::tuple returnValue;
		if(_dataRead)
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
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	boost::python::tuple Image::getThumbnailData()
	{
		if(_dataRead)
		{
			Exiv2::Thumbnail::AutoPtr thumbnail = _exifData.getThumbnail();
			if (thumbnail.get() != 0)
			{
				std::string format(_exifData.thumbnailFormat());
				// Copy the data buffer in a string. Since the data buffer can
				// contain null char ('\x00'), the string cannot be simply
				// constructed like that:
				//     std::string data((char*) dataBuffer.pData_);
				// because it would be truncated after the first occurence of a
				// null char. Therefore, it has to be copied char by char.
				Exiv2::DataBuf dataBuffer = _exifData.copyThumbnail();
				char* charData = (char*) dataBuffer.pData_;
				long dataLen = dataBuffer.size_;
				// First allocate the memory for the whole string...
				std::string data(dataLen, ' ');
				// ... then fill it with the raw jpeg data.
				for(long i = 0; i < dataLen; ++i)
				{
					data[i] = charData[i];
				}
				return boost::python::make_tuple(format, data);
			}
			else
			{
				std::cerr << ">>> Image::getThumbnailData(): cannot access thumbnail" << std::endl;
				return boost::python::make_tuple(std::string(""), std::string(""));
			}
		}
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	bool Image::setThumbnailData(std::string data)
	{
		if(_dataRead)
		{
			const Exiv2::byte* dataBuf = (const Exiv2::byte*) data.c_str();
			_exifData.setJpegThumbnail(dataBuf, data.size());
			return true;
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	void Image::deleteThumbnail()
	{
		if(_dataRead)
			_exifData.eraseThumbnail();
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	bool Image::dumpThumbnailToFile(const std::string path)
	{
		if(_dataRead)
		{
			int result = _exifData.writeThumbnail(path);
			if (result == 0)
			{
				return true;
			}
			else if (result == 8)
			{
				std::cerr << ">>> Image::dumpThumbnailToFile(): the EXIF data does not contain a thumbnail";
				return false;
			}
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	bool Image::setThumbnailFromJpegFile(const std::string path)
	{
		if(_dataRead)
		{
			_exifData.setJpegThumbnail(path);
			return true;
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ_CODE);
	}

	void translateExiv2Error(Exiv2::Error const& e)
	{
		// Use the Python 'C' API to set up an exception object
		const char* message = e.what().c_str();
		// The type of the Python exception depends on the error code
		// Warning: this piece of code should be updated in case the error codes
		// defined by Exiv2 (file 'src/error.cpp') are changed
		switch (e.code())
		{
			case -2:
			case -1:
			case 1:
			case 2:
				PyErr_SetString(PyExc_RuntimeError, message);
				break;
			case 3:
			case 9:
			case 10:
			case 11:
			case 12:
			case 13:
			case 14:
			case 15:
			case 17:
			case 18:
			case 20:
			case 21:
			case 23:
			case 31:
			case 32:
			case 33:
			case 36:
			case 37:
				PyErr_SetString(PyExc_IOError, message);
				break;
			case 6:
			case 7:
				PyErr_SetString(PyExc_KeyError, message);
				break;
			case 4:
			case 5:
			case 8:
			case 22:
			case 24:
			case 25:
			case 26:
			case 27:
			case 28:
			case 29:
			case 30:
			case 34:
				PyErr_SetString(PyExc_ValueError, message);
				break;
			case 16:
			case 19:
			case 35:
				PyErr_SetString(PyExc_MemoryError, message);
				break;

			// custom defined error codes
			case METADATA_NOT_READ_CODE:
				PyErr_SetString(PyExc_IOError, "Image metadata has not been read yet");
				break;

			default:
				PyErr_SetString(PyExc_RuntimeError, message);
		}
	}

} // End of namespace LibPyExiv2
