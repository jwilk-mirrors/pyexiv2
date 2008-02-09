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
  File:      libpyexiv2.cpp
  Author(s): Olivier Tilloy <olivier@tilloy.net>
 */
// *****************************************************************************

#include "libpyexiv2.hpp"

// Custom error codes for Exiv2 exceptions
#define METADATA_NOT_READ 101
#define NON_REPEATABLE 102
#define KEY_NOT_FOUND 103
#define THUMB_ACCESS 104
#define NO_THUMBNAIL 105

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
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	boost::python::list Image::exifKeys()
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
			throw Exiv2::Error(METADATA_NOT_READ);
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
				return boost::python::make_tuple(std::string(exifDatum.typeName()), exifDatum.toString());
			}
			else
				throw Exiv2::Error(KEY_NOT_FOUND, key);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
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
				throw Exiv2::Error(KEY_NOT_FOUND, key);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	boost::python::tuple Image::setExifTag(std::string key, std::string value)
	{
		if(_dataRead)
		{
			std::string typeName;
			std::string oldValue("");
			Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
			Exiv2::ExifMetadata::iterator i = _exifData.findKey(exifKey);
			if(i != _exifData.end())
			{
				Exiv2::Exifdatum exifDatum = _exifData[key];
				oldValue = exifDatum.toString();
				// First erase the existing tag: in some case (and
				// I don't know why), the new value won't replace
				// the old one if not previously erased...
				_exifData.erase(i);
			}
			_exifData[key] = value;
			typeName = std::string(_exifData[key].typeName());
			return boost::python::make_tuple(typeName, oldValue);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	boost::python::tuple Image::deleteExifTag(std::string key)
	{
		if(_dataRead)
		{
			Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
			Exiv2::ExifMetadata::iterator i = _exifData.findKey(exifKey);
			if(i != _exifData.end())
			{
				Exiv2::Exifdatum exifDatum = _exifData[key];
				boost::python::tuple returnValue =
					boost::python::make_tuple(std::string(exifDatum.typeName()), exifDatum.toString());
				_exifData.erase(i);
				return returnValue;
			}
			else
				throw Exiv2::Error(KEY_NOT_FOUND, key);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	boost::python::list Image::iptcKeys()
	{
		boost::python::list list;
		if(_dataRead)
		{
			for(Exiv2::IptcMetadata::iterator i = _iptcData.begin() ; i != _iptcData.end() ; i++)
			{
				// The key is appended to the list if and only if it is not
				// already present.
				if (list.count(i->key()) == 0)
					list.append(i->key());
			}
			return list;
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	boost::python::list Image::getIptcTag(std::string key)
	{
		if(_dataRead)
		{
			boost::python::list valuesList;
			unsigned int valueOccurences = 0;
			Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
			for (Exiv2::IptcMetadata::iterator dataIterator = _iptcData.begin();
				dataIterator != _iptcData.end(); ++dataIterator)
			{
				if (dataIterator->key() == key)
				{
					valuesList.append(boost::python::make_tuple(std::string(dataIterator->typeName()), dataIterator->toString()));
					++valueOccurences;
				}
			}
			if (valueOccurences > 0)
				return valuesList;
			else
				throw Exiv2::Error(KEY_NOT_FOUND, key);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	boost::python::tuple Image::setIptcTag(std::string key, std::string value, unsigned int index=0)
	{
		if(_dataRead)
		{
			std::string typeName;
			std::string oldValue("");
			unsigned int indexCounter = index;
			Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
			Exiv2::IptcMetadata::iterator dataIterator = _iptcData.findKey(iptcKey);
			while ((indexCounter > 0) && (dataIterator != _iptcData.end()))
			{
				dataIterator = std::find_if(++dataIterator, _iptcData.end(),
					Exiv2::FindMetadatumById::FindMetadatumById(iptcKey.tag(), iptcKey.record()));
				--indexCounter;
			}
			if (dataIterator != _iptcData.end())
			{
				// The tag at given index already exists, override it
				dataIterator->setValue(value);
				typeName = std::string(dataIterator->typeName());
				oldValue = dataIterator->toString();
			}
			else
			{
				// Either index is greater than the index of the last repetition
				// of the tag, or the tag does not exist yet.
				// In both cases, it is created.
				Exiv2::Iptcdatum iptcDatum(iptcKey);
				typeName = std::string(iptcDatum.typeName());
				iptcDatum.setValue(value);
				int state = _iptcData.add(iptcDatum);
				if (state == 6)
					throw Exiv2::Error(NON_REPEATABLE);
			}
			return boost::python::make_tuple(typeName, oldValue);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	boost::python::tuple Image::deleteIptcTag(std::string key, unsigned int index=0)
	{
		if(_dataRead)
		{
			unsigned int indexCounter = index;
			Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
			Exiv2::IptcMetadata::iterator dataIterator = _iptcData.findKey(iptcKey);
			while ((indexCounter > 0) && (dataIterator != _iptcData.end()))
			{
				dataIterator = std::find_if(++dataIterator, _iptcData.end(),
					Exiv2::FindMetadatumById::FindMetadatumById(iptcKey.tag(), iptcKey.record()));
				--indexCounter;
			}
			if (dataIterator != _iptcData.end())
			{
				// The tag at given index already exists, delete it
				boost::python::tuple returnValue =
					boost::python::make_tuple(std::string(dataIterator->typeName()), dataIterator->toString());
				_iptcData.erase(dataIterator);
				return returnValue;
			}
			else
				throw Exiv2::Error(KEY_NOT_FOUND, key);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	boost::python::tuple Image::tagDetails(std::string key)
	{
		std::string keyFamily = key.substr(0, 4);
		if (keyFamily == "Exif")
		{
			Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
			std::string tagLabel = exifKey.tagLabel();
			std::string tagDesc =
				std::string(Exiv2::ExifTags::tagDesc(exifKey.tag(), exifKey.ifdId()));
			return boost::python::make_tuple(tagLabel, tagDesc);
		}
		else if (keyFamily == "Iptc")
		{
			Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
			std::string tagLabel = iptcKey.tagLabel();
			std::string tagDesc =
				std::string(Exiv2::IptcDataSets::dataSetDesc(iptcKey.tag(), iptcKey.record()));
			return boost::python::make_tuple(tagLabel, tagDesc);
		}
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
				throw Exiv2::Error(THUMB_ACCESS);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	void Image::setThumbnailData(std::string data)
	{
		if(_dataRead)
		{
			const Exiv2::byte* dataBuf = (const Exiv2::byte*) data.c_str();
			_exifData.setJpegThumbnail(dataBuf, data.size());
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	void Image::deleteThumbnail()
	{
		if(_dataRead)
			_exifData.eraseThumbnail();
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	void Image::dumpThumbnailToFile(const std::string path)
	{
		if(_dataRead)
		{
			int result = _exifData.writeThumbnail(path);
			if (result == 8)
				throw Exiv2::Error(NO_THUMBNAIL);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

	void Image::setThumbnailFromJpegFile(const std::string path)
	{
		if(_dataRead)
		{
			_exifData.setJpegThumbnail(path);
		}
		else
			throw Exiv2::Error(METADATA_NOT_READ);
	}

    const std::string Image::getComment() const
    {
        if(_dataRead)
        {
            return _image->comment();
        }
        else
            throw Exiv2::Error(METADATA_NOT_READ);
    }

    void Image::setComment(const std::string& comment)
    {
        if(_dataRead)
        {
            _image->setComment(comment);
        }
        else
            throw Exiv2::Error(METADATA_NOT_READ);
    }

    void Image::clearComment()
    {
        if(_dataRead)
        {
            _image->clearComment();
        }
        else
            throw Exiv2::Error(METADATA_NOT_READ);
    }

	void translateExiv2Error(Exiv2::Error const& e)
	{
		// Use the Python 'C' API to set up an exception object

		// Building a C++ string first allows this code to compile with all
		// versions of libexiv2 (< 0.13 and >= 0.13), because the way exceptions
		// are handled in libexiv2 was changed in 0.13.
		const std::string sMessage(e.what());
		const char* message = sMessage.c_str();

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
			case 4:
			case 5:
			case 6:
			case 7:
				PyErr_SetString(PyExc_IndexError, message);
				break;
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

			// custom error codes
			case METADATA_NOT_READ:
				PyErr_SetString(PyExc_IOError, "Image metadata has not been read yet");
				break;
			case NON_REPEATABLE:
				PyErr_SetString(PyExc_KeyError, "Tag is not repeatable");
				break;
			case KEY_NOT_FOUND:
				PyErr_SetString(PyExc_KeyError, "Tag not set");
				break;
			case THUMB_ACCESS:
				PyErr_SetString(PyExc_IOError, "Cannot access image thumbnail");
				break;
			case NO_THUMBNAIL:
				PyErr_SetString(PyExc_IOError, "The EXIF data does not contain a thumbnail");
				break;

			default:
				PyErr_SetString(PyExc_RuntimeError, message);
		}
	}

} // End of namespace LibPyExiv2
