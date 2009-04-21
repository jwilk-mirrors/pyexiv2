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

// Custom error codes for Exiv2 exceptions
#define METADATA_NOT_READ 101
#define NON_REPEATABLE 102
#define KEY_NOT_FOUND 103
#define THUMB_ACCESS 104
#define NO_THUMBNAIL 105

namespace exiv2wrapper
{

// Base constructor
Image::Image(const std::string& filename)
{
    _filename = filename;
    _image = Exiv2::ImageFactory::open(filename);
    assert(_image.get() != 0);
    _dataRead = false;
}

// Copy constructor
Image::Image(const Image& image)
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
    _xmpData = _image->xmpData();
    _dataRead = true;
}

void Image::writeMetadata()
{
    if(_dataRead)
    {
        _image->setExifData(_exifData);
        _image->setIptcData(_iptcData);
        _image->setXmpData(_xmpData);
        _image->writeMetadata();
    }
    else
        throw Exiv2::Error(METADATA_NOT_READ);
}

boost::python::list Image::exifKeys()
{
    boost::python::list keys;
    if(_dataRead)
    {
        for(Exiv2::ExifMetadata::iterator i = _exifData.begin();
            i != _exifData.end();
            ++i)
        {
            keys.append(i->key());
        }
        return keys;
    }
    else
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }
}

boost::python::tuple Image::getExifTag(std::string key)
{
    if(_dataRead)
    {
        Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
        if(_exifData.findKey(exifKey) != _exifData.end())
        {
            Exiv2::Exifdatum exifDatum = _exifData[key];
            std::string sTagName = exifDatum.tagName();
            std::string sTagLabel = exifDatum.tagLabel();
            std::string sTagDesc(Exiv2::ExifTags::tagDesc(exifKey.tag(), exifKey.ifdId()));
            std::string sTagType = exifDatum.typeName();
            std::string sTagValue = exifDatum.toString();
            std::ostringstream sTagStringValueBuffer;
            sTagStringValueBuffer << exifDatum;
            std::string sTagStringValue = sTagStringValueBuffer.str();
            return boost::python::make_tuple(key, sTagName, sTagLabel, sTagDesc, sTagType, sTagValue, sTagStringValue);
        }
        else
        {
            throw Exiv2::Error(KEY_NOT_FOUND, key);
        }
    }
    else
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }
}

void Image::setExifTagValue(std::string key, std::string value)
{
    if(_dataRead)
    {
        Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
        Exiv2::ExifMetadata::iterator i = _exifData.findKey(exifKey);
        if(i != _exifData.end())
        {
            // First erase the existing tag: in some case (and I don't know
            // why), the new value won't replace the old one if not previously
            // erased...
            // TODO: check if this is still valid with libexiv2 0.18
            _exifData.erase(i);
        }
        _exifData[key] = value;
    }
    else
        throw Exiv2::Error(METADATA_NOT_READ);
}

void Image::deleteExifTag(std::string key)
{
    if(_dataRead)
    {
        Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
        Exiv2::ExifMetadata::iterator i = _exifData.findKey(exifKey);
        if(i != _exifData.end())
        {
            _exifData.erase(i);
        }
        else
            throw Exiv2::Error(KEY_NOT_FOUND, key);
    }
    else
        throw Exiv2::Error(METADATA_NOT_READ);
}

boost::python::list Image::iptcKeys()
{
    boost::python::list keys;
    if(_dataRead)
    {
        for(Exiv2::IptcMetadata::iterator i = _iptcData.begin();
            i != _iptcData.end();
            ++i)
        {
            // The key is appended to the list if and only if it is not already
            // present.
            if (keys.count(i->key()) == 0)
            {
                keys.append(i->key());
            }
        }
        return keys;
    }
    else
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }
}

boost::python::tuple Image::getIptcTag(std::string key)
{
    if(_dataRead)
    {
        Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
        boost::python::list values;
        unsigned int occurences = 0;
        std::string sTagType;
        for (Exiv2::IptcMetadata::iterator i = _iptcData.begin();
             i != _iptcData.end();
             ++i)
        {
            if (i->key() == key)
            {
                values.append(i->toString());
                ++occurences;
                sTagType = i->typeName();
            }
        }
        if (occurences > 0)
        {
            std::string sTagName = iptcKey.tagName();
            std::string sTagLabel = iptcKey.tagLabel();
            std::string sTagDesc(Exiv2::IptcDataSets::dataSetDesc(iptcKey.tag(), iptcKey.record()));
            return boost::python::make_tuple(key, sTagName, sTagLabel, sTagDesc, sTagType, values);
        }
        else
        {
            throw Exiv2::Error(KEY_NOT_FOUND, key);
        }
    }
    else
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }
}

/*void Image::setIptcTag(std::string key, std::string value, unsigned int index=0)
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
            // The tag at given index already exists, override it
            dataIterator->setValue(value);
        }
        else
        {
            // Either index is greater than the index of the last repetition
            // of the tag, or the tag does not exist yet.
            // In both cases, it is created.
            Exiv2::Iptcdatum iptcDatum(iptcKey);
            iptcDatum.setValue(value);
            int state = _iptcData.add(iptcDatum);
            if (state == 6)
                throw Exiv2::Error(NON_REPEATABLE);
        }
    }
    else
        throw Exiv2::Error(METADATA_NOT_READ);
}*/

void Image::setIptcTagValues(std::string key, boost::python::tuple values)
{
    if (!_dataRead)
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }

    Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
    unsigned int index = 0;
    unsigned int max = len(values);
    Exiv2::IptcMetadata::iterator dataIterator = _iptcData.findKey(iptcKey);
    while (index < max)
    {
        std::string value = boost::python::extract<std::string>(values[index++]);
        if (dataIterator != _iptcData.end())
        {
            // Override an existing value
            dataIterator->setValue(value);
            dataIterator = std::find_if(++dataIterator, _iptcData.end(),
                Exiv2::FindMetadatumById::FindMetadatumById(iptcKey.tag(),
                                                            iptcKey.record()));
        }
        else
        {
            // Append a new value
            Exiv2::Iptcdatum iptcDatum(iptcKey);
            iptcDatum.setValue(value);
            int state = _iptcData.add(iptcDatum);
            if (state == 6)
            {
                throw Exiv2::Error(NON_REPEATABLE);
            }
        }
    }
    // Erase the remaining values if any
    while (dataIterator != _iptcData.end())
    {
        _iptcData.erase(dataIterator);
        dataIterator = std::find_if(dataIterator, _iptcData.end(),
                Exiv2::FindMetadatumById::FindMetadatumById(iptcKey.tag(),
                                                            iptcKey.record()));
    }
}

void Image::deleteIptcTag(std::string key)
{
    if (!_dataRead)
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }

    Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
    Exiv2::IptcMetadata::iterator dataIterator = _iptcData.findKey(iptcKey);

    if (dataIterator == _iptcData.end())
    {
        throw Exiv2::Error(KEY_NOT_FOUND, key);
    }

    while (dataIterator != _iptcData.end())
    {
        _iptcData.erase(dataIterator);
        dataIterator = std::find_if(++dataIterator, _iptcData.end(),
                Exiv2::FindMetadatumById::FindMetadatumById(iptcKey.tag(),
                                                            iptcKey.record()));
    }
}

boost::python::list Image::xmpKeys()
{
    boost::python::list keys;
    if(_dataRead)
    {
        for(Exiv2::XmpMetadata::iterator i = _xmpData.begin();
            i != _xmpData.end();
            ++i)
        {
            keys.append(i->key());
        }
        return keys;
    }
    else
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }
}

boost::python::tuple Image::getXmpTag(std::string key)
{
    if(!_dataRead)
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }

    Exiv2::XmpKey xmpKey = Exiv2::XmpKey(key);

    if(_xmpData.findKey(xmpKey) == _xmpData.end())
    {
        throw Exiv2::Error(KEY_NOT_FOUND, key);
    }

    Exiv2::Xmpdatum xmpDatum = _xmpData[key];
    std::string sTagName = xmpKey.tagName();
    std::string sTagLabel = xmpKey.tagLabel();
    std::string sTagDesc(Exiv2::XmpProperties::propertyDesc(xmpKey));
    std::string sTagType(Exiv2::XmpProperties::propertyInfo(xmpKey)->xmpValueType_);
    std::string sTagValue = xmpDatum.toString();
    return boost::python::make_tuple(key, sTagName, sTagLabel, sTagDesc, sTagType, sTagValue);
}

/*void Image::setXmpTagValues(std::string key, boost::python::tuple values)
{
    if (!_dataRead)
    {
        throw Exiv2::Error(METADATA_NOT_READ);
    }

    Exiv2::XmpKey xmpKey = Exiv2::XmpKey(key);
    unsigned int index = 0;
    unsigned int max = len(values);
    Exiv2::XmpMetadata::iterator dataIterator = _xmpData.findKey(xmpKey);
    while (index < max)
    {
        std::string value = boost::python::extract<std::string>(values[index++]);
        if (dataIterator != _xmpData.end())
        {
            // Override an existing value
            dataIterator->setValue(value);
            dataIterator = std::find_if(++dataIterator, _xmpData.end(),
                Exiv2::FindMetadatumById::FindMetadatumById(xmpKey.tag(),
                                                            xmpKey.record()));
        }
        else
        {
            // Append a new value
            Exiv2::Iptcdatum iptcDatum(iptcKey);
            iptcDatum.setValue(value);
            int state = _iptcData.add(iptcDatum);
            if (state == 6)
            {
                throw Exiv2::Error(NON_REPEATABLE);
            }
        }
    }
    // Erase the remaining values if any
    while (dataIterator != _iptcData.end())
    {
        _iptcData.erase(dataIterator);
        dataIterator = std::find_if(dataIterator, _iptcData.end(),
                Exiv2::FindMetadatumById::FindMetadatumById(iptcKey.tag(),
                                                            iptcKey.record()));
    }
}*/

/*
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
*/

// TODO: update the errors code to reflect changes from src/error.cpp in libexiv2
void translateExiv2Error(Exiv2::Error const& error)
{
    // Use the Python 'C' API to set up an exception object

    // Building a C++ string first allows this code to compile with all
    // versions of libexiv2 (< 0.13 and >= 0.13), because the way exceptions
    // are handled in libexiv2 was changed in 0.13.
    const std::string sMessage(error.what());
    const char* message = sMessage.c_str();

    // The type of the Python exception depends on the error code
    // Warning: this piece of code should be updated in case the error codes
    // defined by Exiv2 (file 'src/error.cpp') are changed
    switch (error.code())
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

} // End of namespace exiv2wrapper
