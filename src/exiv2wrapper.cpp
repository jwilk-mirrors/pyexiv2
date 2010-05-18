// *****************************************************************************
/*
 * Copyright (C) 2006-2010 Olivier Tilloy <olivier@tilloy.net>
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

#include "boost/python/stl_iterator.hpp"

#include <fstream>

// Custom error codes for Exiv2 exceptions
#define METADATA_NOT_READ 101
#define NON_REPEATABLE 102
#define KEY_NOT_FOUND 103

// Custom macros
#define CHECK_METADATA_READ \
    if (!_dataRead) throw Exiv2::Error(METADATA_NOT_READ);

namespace exiv2wrapper
{

void Image::_instantiate_image()
{
    // If an exception is thrown, it has to be done outside of the
    // Py_{BEGIN,END}_ALLOW_THREADS block.
    Exiv2::Error error(0);

    // Release the GIL to allow other python threads to run
    // while opening the file.
    Py_BEGIN_ALLOW_THREADS

    try
    {
        if (_data != 0)
        {
            _image = Exiv2::ImageFactory::open(_data, _size);
        }
        else
        {
            _image = Exiv2::ImageFactory::open(_filename);
        }
    }
    catch (Exiv2::Error& err)
    {
        error = err;
    }

    // Re-acquire the GIL
    Py_END_ALLOW_THREADS

    if (error.code() == 0)
    {
        assert(_image.get() != 0);
        _dataRead = false;
    }
    else
    {
        throw error;
    }
}

// Base constructor
Image::Image(const std::string& filename)
{
    _filename = filename;
    _data = 0;
    _instantiate_image();
}

// From buffer constructor
Image::Image(const std::string& buffer, long size)
{
    // Deep copy of the data buffer
    _data = new Exiv2::byte[size];
    for (unsigned long i = 0; i < size; ++i)
    {
        _data[i] = buffer[i];
    }

    _size = size;
    _instantiate_image();
}

// Copy constructor
Image::Image(const Image& image)
{
    _filename = image._filename;
    _instantiate_image();
}

Image::~Image()
{
    if (_data != 0)
    {
        delete[] _data;
    }
}

void Image::readMetadata()
{
    // If an exception is thrown, it has to be done outside of the
    // Py_{BEGIN,END}_ALLOW_THREADS block.
    Exiv2::Error error(0);

    // Release the GIL to allow other python threads to run
    // while reading metadata.
    Py_BEGIN_ALLOW_THREADS

    try
    {
        _image->readMetadata();
        _exifData = _image->exifData();
        _iptcData = _image->iptcData();
        _xmpData = _image->xmpData();
        _dataRead = true;
    }
    catch (Exiv2::Error& err)
    {
        error = err;
    }

    // Re-acquire the GIL
    Py_END_ALLOW_THREADS

    if (error.code() != 0)
    {
        throw error;
    }
}

void Image::writeMetadata()
{
    CHECK_METADATA_READ

    // If an exception is thrown, it has to be done outside of the
    // Py_{BEGIN,END}_ALLOW_THREADS block.
    Exiv2::Error error(0);

    // Release the GIL to allow other python threads to run
    // while writing metadata.
    Py_BEGIN_ALLOW_THREADS

    try
    {
        _image->setExifData(_exifData);
        _image->setIptcData(_iptcData);
        _image->setXmpData(_xmpData);
        _image->writeMetadata();
    }
    catch (Exiv2::Error& err)
    {
        error = err;
    }

    // Re-acquire the GIL
    Py_END_ALLOW_THREADS

    if (error.code() != 0)
    {
        throw error;
    }
}

unsigned int Image::pixelWidth() const
{
    CHECK_METADATA_READ
    return _image->pixelWidth();
}

unsigned int Image::pixelHeight() const
{
    CHECK_METADATA_READ
    return _image->pixelHeight();
}

std::string Image::mimeType() const
{
    CHECK_METADATA_READ
    return _image->mimeType();
}

boost::python::list Image::exifKeys()
{
    CHECK_METADATA_READ

    boost::python::list keys;
    for(Exiv2::ExifMetadata::iterator i = _exifData.begin();
        i != _exifData.end();
        ++i)
    {
        keys.append(i->key());
    }
    return keys;
}

const ExifTag Image::getExifTag(std::string key)
{
    CHECK_METADATA_READ

    Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);

    if(_exifData.findKey(exifKey) == _exifData.end())
    {
        throw Exiv2::Error(KEY_NOT_FOUND, key);
    }

    return ExifTag(key, &_exifData[key], &_exifData);
}

void Image::setExifTagValue(std::string key, std::string value)
{
    CHECK_METADATA_READ

    _exifData[key] = value;
}

void Image::deleteExifTag(std::string key)
{
    CHECK_METADATA_READ

    Exiv2::ExifKey exifKey = Exiv2::ExifKey(key);
    Exiv2::ExifMetadata::iterator datum = _exifData.findKey(exifKey);
    if(datum == _exifData.end())
    {
        throw Exiv2::Error(KEY_NOT_FOUND, key);
    }

    _exifData.erase(datum);
}

boost::python::list Image::iptcKeys()
{
    CHECK_METADATA_READ

    boost::python::list keys;
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

const IptcTag Image::getIptcTag(std::string key)
{
    CHECK_METADATA_READ

    Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);

    if(_iptcData.findKey(iptcKey) == _iptcData.end())
    {
        throw Exiv2::Error(KEY_NOT_FOUND, key);
    }

    Exiv2::IptcMetadata* data = new Exiv2::IptcMetadata();
    for (Exiv2::IptcMetadata::iterator iterator = _iptcData.begin();
         iterator != _iptcData.end(); ++iterator)
    {
        if (iterator->key() == key)
        {
            data->push_back(*iterator);
        }
    }

    return IptcTag(key, data);
}


// Copied from libexiv2's src/iptc.cpp.
// Was previously called Exiv2::FindMetadatumById::FindMetadatumById but it was
// renamed and moved in revision 1727. See http://dev.exiv2.org/issues/show/581.
//! Unary predicate that matches an Iptcdatum with given record and dataset
class FindIptcdatum {
public:
    //! Constructor, initializes the object with the record and dataset id
    FindIptcdatum(uint16_t dataset, uint16_t record)
        : dataset_(dataset), record_(record) {}
    /*!
      @brief Returns true if the record and dataset id of the argument
            Iptcdatum is equal to that of the object.
    */
    bool operator()(const Exiv2::Iptcdatum& iptcdatum) const
    {
        return dataset_ == iptcdatum.tag() && record_ == iptcdatum.record();
    }

private:
    // DATA
    uint16_t dataset_;
    uint16_t record_;

}; // class FindIptcdatum


void Image::setIptcTagValues(std::string key, boost::python::list values)
{
    CHECK_METADATA_READ

    Exiv2::IptcKey iptcKey = Exiv2::IptcKey(key);
    unsigned int index = 0;
    unsigned int max = boost::python::len(values);
    Exiv2::IptcMetadata::iterator dataIterator = _iptcData.findKey(iptcKey);
    while (index < max)
    {
        std::string value = boost::python::extract<std::string>(values[index++]);
        if (dataIterator != _iptcData.end())
        {
            // Override an existing value
            dataIterator->setValue(value);
            dataIterator = std::find_if(++dataIterator, _iptcData.end(),
                FindIptcdatum(iptcKey.tag(), iptcKey.record()));
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
            // Reset dataIterator that has been invalidated by appending a datum
            dataIterator = _iptcData.end();
        }
    }
    // Erase the remaining values if any
    while (dataIterator != _iptcData.end())
    {
        _iptcData.erase(dataIterator);
        dataIterator = std::find_if(dataIterator, _iptcData.end(),
                FindIptcdatum(iptcKey.tag(), iptcKey.record()));
    }
}

void Image::deleteIptcTag(std::string key)
{
    CHECK_METADATA_READ

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
                FindIptcdatum(iptcKey.tag(), iptcKey.record()));
    }
}

boost::python::list Image::xmpKeys()
{
    CHECK_METADATA_READ

    boost::python::list keys;
    for(Exiv2::XmpMetadata::iterator i = _xmpData.begin();
        i != _xmpData.end();
        ++i)
    {
        keys.append(i->key());
    }
    return keys;
}

const XmpTag Image::getXmpTag(std::string key)
{
    CHECK_METADATA_READ

    Exiv2::XmpKey xmpKey = Exiv2::XmpKey(key);

    if(_xmpData.findKey(xmpKey) == _xmpData.end())
    {
        throw Exiv2::Error(KEY_NOT_FOUND, key);
    }

    return XmpTag(key, &_xmpData[key]);
}

void Image::setXmpTagTextValue(const std::string& key, const std::string& value)
{
    CHECK_METADATA_READ

    _xmpData[key].setValue(value);
}

void Image::setXmpTagArrayValue(const std::string& key, const boost::python::list& values)
{
    CHECK_METADATA_READ

    Exiv2::Xmpdatum& datum = _xmpData[key];
    // Reset the value
    datum.setValue(0);

    for(boost::python::stl_input_iterator<std::string> iterator(values);
        iterator != boost::python::stl_input_iterator<std::string>();
        ++iterator)
    {
        datum.setValue(*iterator);
    }
}

void Image::setXmpTagLangAltValue(const std::string& key, const boost::python::dict& values)
{
    CHECK_METADATA_READ

    Exiv2::Xmpdatum& datum = _xmpData[key];
    // Reset the value
    datum.setValue(0);

    for(boost::python::stl_input_iterator<std::string> iterator(values);
        iterator != boost::python::stl_input_iterator<std::string>();
        ++iterator)
    {
        std::string key = *iterator;
        std::string value = boost::python::extract<std::string>(values.get(key));
        datum.setValue("lang=\"" + key + "\" " + value);
    }
}

void Image::deleteXmpTag(std::string key)
{
    CHECK_METADATA_READ

    Exiv2::XmpKey xmpKey = Exiv2::XmpKey(key);
    Exiv2::XmpMetadata::iterator i = _xmpData.findKey(xmpKey);
    if(i != _xmpData.end())
    {
        _xmpData.erase(i);
    }
    else
        throw Exiv2::Error(KEY_NOT_FOUND, key);
}

boost::python::list Image::previews()
{
    CHECK_METADATA_READ

    boost::python::list previews;
    Exiv2::PreviewManager pm(*_image);
    Exiv2::PreviewPropertiesList props = pm.getPreviewProperties();
    for (Exiv2::PreviewPropertiesList::const_iterator i = props.begin();
         i != props.end();
         ++i)
    {
        previews.append(Preview(pm.getPreviewImage(*i)));
    }

    return previews;
}

void Image::copyMetadata(Image& other, bool exif, bool iptc, bool xmp) const
{
    CHECK_METADATA_READ
    if (!other._dataRead) throw Exiv2::Error(METADATA_NOT_READ);

    if (exif)
        other._exifData = _exifData;
    if (iptc)
        other._iptcData = _iptcData;
    if (xmp)
        other._xmpData = _xmpData;
}

std::string Image::getDataBuffer() const
{
    std::string buffer;

    // Release the GIL to allow other python threads to run
    // while reading the image data.
    Py_BEGIN_ALLOW_THREADS

    Exiv2::BasicIo& io = _image->io();
    long size = io.size();
    long pos = -1;

    if (io.isopen())
    {
        // Remember the current position in the stream
        pos = io.tell();
        // Go to the beginning of the stream
        io.seek(0, Exiv2::BasicIo::beg);
    }
    else
    {
        io.open();
    }

    // Copy the data buffer in a string. Since the data buffer can contain null
    // characters ('\x00'), the string cannot be simply constructed like that:
    //     _data = std::string((char*) previewImage.pData());
    // because it would be truncated after the first occurence of a null
    // character. Therefore, it has to be copied character by character.
    // First allocate the memory for the whole string...
    buffer.resize(size, ' ');
    // ... then fill it with the raw data.
    for (unsigned long i = 0; i < size; ++i)
    {
        io.read((Exiv2::byte*) &buffer[i], 1);
    }

    if (pos == -1)
    {
        // The stream was initially closed
        io.close();
    }
    else
    {
        // Reset to the initial position in the stream
        io.seek(pos, Exiv2::BasicIo::beg);
    }

    // Re-acquire the GIL
    Py_END_ALLOW_THREADS

    return buffer;
}


ExifTag::ExifTag(const std::string& key, Exiv2::Exifdatum* datum, Exiv2::ExifData* data): _key(key)
{
    if (datum != 0 && data != 0)
    {
        _datum = datum;
        _data = data;
    }
    else
    {
        _datum = new Exiv2::Exifdatum(_key);
        _data = 0;
    }

    const uint16_t tag = _datum->tag();
    const Exiv2::IfdId ifd = _datum->ifdId();
    _type = Exiv2::TypeInfo::typeName(Exiv2::ExifTags::tagType(tag, ifd));
    _name = Exiv2::ExifTags::tagName(tag, ifd);
    _label = Exiv2::ExifTags::tagLabel(tag, ifd);
    _description = Exiv2::ExifTags::tagDesc(tag, ifd);
    _sectionName = Exiv2::ExifTags::sectionName(tag, ifd);
    _sectionDescription = Exiv2::ExifTags::sectionDesc(tag, ifd);
}

ExifTag::~ExifTag()
{
    if (_data == 0)
    {
        delete _datum;
    }
}

void ExifTag::setRawValue(const std::string& value)
{
    _datum->setValue(value);
}

const std::string ExifTag::getKey()
{
    return _key.key();
}

const std::string ExifTag::getType()
{
    return _type;
}

const std::string ExifTag::getName()
{
    return _name;
}

const std::string ExifTag::getLabel()
{
    return _label;
}

const std::string ExifTag::getDescription()
{
    return _description;
}

const std::string ExifTag::getSectionName()
{
    return _sectionName;
}

const std::string ExifTag::getSectionDescription()
{
    return _sectionDescription;
}

const std::string ExifTag::getRawValue()
{
    return _datum->toString();
}

const std::string ExifTag::getHumanValue()
{
    return _datum->print(_data);
}


IptcTag::IptcTag(const std::string& key, Exiv2::IptcMetadata* data): _key(key)
{
    _from_data = (data != 0);

    if (_from_data)
    {
        _data = data;
    }
    else
    {
        _data = new Exiv2::IptcMetadata();
        _data->push_back(Exiv2::Iptcdatum(_key));
    }

    Exiv2::IptcMetadata::iterator iterator = _data->begin();
    const uint16_t tag = iterator->tag();
    const uint16_t record = iterator->record();
    _type = Exiv2::TypeInfo::typeName(Exiv2::IptcDataSets::dataSetType(tag, record));
    _name = Exiv2::IptcDataSets::dataSetName(tag, record);
    _title = Exiv2::IptcDataSets::dataSetTitle(tag, record);
    _description = Exiv2::IptcDataSets::dataSetDesc(tag, record);
    // What is the photoshop name anyway? Where is it used?
    _photoshopName = Exiv2::IptcDataSets::dataSetPsName(tag, record);
    _repeatable = Exiv2::IptcDataSets::dataSetRepeatable(tag, record);
    _recordName = Exiv2::IptcDataSets::recordName(record);
    _recordDescription = Exiv2::IptcDataSets::recordDesc(record);

    if (!_repeatable && (_data->size() > 1))
    {
        // The tag is not repeatable but we are trying to assign it more than
        // one value.
        throw Exiv2::Error(NON_REPEATABLE);
    }
}

IptcTag::~IptcTag()
{
    if (!_from_data)
    {
        delete _data;
    }
}

void IptcTag::setRawValues(const boost::python::list& values)
{
    if (!_repeatable && (boost::python::len(values) > 1))
    {
        // The tag is not repeatable but we are trying to assign it more than
        // one value.
        throw Exiv2::Error(NON_REPEATABLE);
    }

    _data->clear();
    for(boost::python::stl_input_iterator<std::string> iterator(values);
        iterator != boost::python::stl_input_iterator<std::string>();
        ++iterator)
    {
        Exiv2::Iptcdatum datum(_key);
        datum.setValue(*iterator);
        _data->push_back(datum);
    }
}

const std::string IptcTag::getKey()
{
    return _key.key();
}

const std::string IptcTag::getType()
{
    return _type;
}

const std::string IptcTag::getName()
{
    return _name;
}

const std::string IptcTag::getTitle()
{
    return _title;
}

const std::string IptcTag::getDescription()
{
    return _description;
}

const std::string IptcTag::getPhotoshopName()
{
    return _photoshopName;
}

const bool IptcTag::isRepeatable()
{
    return _repeatable;
}

const std::string IptcTag::getRecordName()
{
    return _recordName;
}

const std::string IptcTag::getRecordDescription()
{
    return _recordDescription;
}

const boost::python::list IptcTag::getRawValues()
{
    boost::python::list values;
    for(Exiv2::IptcMetadata::iterator iterator = _data->begin();
        iterator != _data->end(); ++iterator)
    {
        values.append(iterator->toString());
    }
    return values;
}


XmpTag::XmpTag(const std::string& key, Exiv2::Xmpdatum* datum): _key(key)
{
    _from_datum = (datum != 0);

    if (_from_datum)
    {
        _datum = datum;
    }
    else
    {
        _datum = new Exiv2::Xmpdatum(_key);
    }

    _exiv2_type = Exiv2::TypeInfo::typeName(Exiv2::XmpProperties::propertyType(_key));

    const char* title = Exiv2::XmpProperties::propertyTitle(_key);
    if (title != 0)
    {
        _title = title;
    }

    const char* description = Exiv2::XmpProperties::propertyDesc(_key);
    if (description != 0)
    {
        _description = description;
    }

    const Exiv2::XmpPropertyInfo* info = Exiv2::XmpProperties::propertyInfo(_key);
    if (info != 0)
    {
        _name = info->name_;
        _type = info->xmpValueType_;
    }
}

XmpTag::~XmpTag()
{
    if (!_from_datum)
    {
        delete _datum;
    }
}

void XmpTag::setTextValue(const std::string& value)
{
    _datum->setValue(value);
}

void XmpTag::setArrayValue(const boost::python::list& values)
{
    // Reset the value
    _datum->setValue(0);

    for(boost::python::stl_input_iterator<std::string> iterator(values);
        iterator != boost::python::stl_input_iterator<std::string>();
        ++iterator)
    {
        _datum->setValue(*iterator);
    }
}

void XmpTag::setLangAltValue(const boost::python::dict& values)
{
    // Reset the value
    _datum->setValue(0);

    for(boost::python::stl_input_iterator<std::string> iterator(values);
        iterator != boost::python::stl_input_iterator<std::string>();
        ++iterator)
    {
        std::string key = *iterator;
        std::string value = boost::python::extract<std::string>(values.get(key));
        _datum->setValue("lang=\"" + key + "\" " + value);
    }
}

const std::string XmpTag::getKey()
{
    return _key.key();
}

const std::string XmpTag::getExiv2Type()
{
    return _exiv2_type;
}

const std::string XmpTag::getType()
{
    return _type;
}

const std::string XmpTag::getName()
{
    return _name;
}

const std::string XmpTag::getTitle()
{
    return _title;
}

const std::string XmpTag::getDescription()
{
    return _description;
}

const std::string XmpTag::getTextValue()
{
    return dynamic_cast<const Exiv2::XmpTextValue*>(&_datum->value())->value_;
}

const boost::python::list XmpTag::getArrayValue()
{
    std::vector<std::string> value =
        dynamic_cast<const Exiv2::XmpArrayValue*>(&_datum->value())->value_;
    boost::python::list rvalue;
    for(std::vector<std::string>::const_iterator i = value.begin();
        i != value.end(); ++i)
    {
        rvalue.append(*i);
    }
    return rvalue;
}

const boost::python::dict XmpTag::getLangAltValue()
{
    Exiv2::LangAltValue::ValueType value =
        dynamic_cast<const Exiv2::LangAltValue*>(&_datum->value())->value_;
    boost::python::dict rvalue;
    for (Exiv2::LangAltValue::ValueType::const_iterator i = value.begin();
         i != value.end(); ++i)
    {
        rvalue[i->first] = i->second;
    }
    return rvalue;
}


Preview::Preview(const Exiv2::PreviewImage& previewImage)
{
    _mimeType = previewImage.mimeType();
    _extension = previewImage.extension();
    _size = previewImage.size();
    _dimensions = boost::python::make_tuple(previewImage.width(),
                                            previewImage.height());
    // Copy the data buffer in a string. Since the data buffer can contain null
    // characters ('\x00'), the string cannot be simply constructed like that:
    //     _data = std::string((char*) previewImage.pData());
    // because it would be truncated after the first occurence of a null
    // character. Therefore, it has to be copied character by character.
    const Exiv2::byte* pData = previewImage.pData();
    // First allocate the memory for the whole string...
    _data = std::string(_size, ' ');
    // ... then fill it with the raw data.
    for(unsigned int i = 0; i < _size; ++i)
    {
        _data[i] = pData[i];
    }
}

void Preview::writeToFile(const std::string& path) const
{
    std::string filename = path + _extension;
    std::ofstream fd(filename.c_str(), std::ios::out);
    fd << _data;
    fd.close();
}


void translateExiv2Error(Exiv2::Error const& error)
{
    // Use the Python 'C' API to set up an exception object
    const char* message = error.what();

    // The type of the Python exception depends on the error code
    // Warning: this piece of code should be updated in case the error codes
    // defined by Exiv2 (file 'src/error.cpp') are changed
    switch (error.code())
    {
        // Exiv2 error codes
        case 2:
            // {path}: Call to `{function}' failed: {strerror}
            // May be raised when reading a file
            PyErr_SetString(PyExc_RuntimeError, message);
            break;
        case 3:
            // This does not look like a {image type} image
            // May be raised by readMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 4:
            // Invalid dataset name `{dataset name}'
            // May be raised when instantiating an IptcKey from a string
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 5:
            // Invalid record name `{record name}'
            // May be raised when instantiating an IptcKey from a string
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 6:
            // Invalid key `{key}'
            // May be raised when instantiating an ExifKey, an IptcKey or an
            // XmpKey from a string
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 7:
            // Invalid tag name or ifdId `{tag name}', ifdId {ifdId}
            // May be raised when instantiating an ExifKey from a string
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 8:
            // Value not set
            // May be raised when calling value() on a datum
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 9:
            // {path}: Failed to open the data source: {strerror}
            // May be raised by readMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 10:
            // {path}: Failed to open file ({mode}): {strerror}
            // May be raised by writeMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 11:
            // {path}: The file contains data of an unknown image type
            // May be raised when opening an image
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 12:
            // The memory contains data of an unknown image type
            // May be raised when instantiating an image from a data buffer
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 13:
            // Image type {image type} is not supported
            // May be raised when creating a new image
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 14:
            // Failed to read image data
            // May be raised by readMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 15:
            // This does not look like a JPEG image
            // May be raised by readMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 17:
            // {old path}: Failed to rename file to {new path}: {strerror}
            // May be raised by writeMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 18:
            // {path}: Transfer failed: {strerror}
            // May be raised by writeMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 19:
            // Memory transfer failed: {strerror}
            // May be raised by writeMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 20:
            // Failed to read input data
            // May be raised by writeMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 21:
            // Failed to write image
            // May be raised by writeMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 22:
            // Input data does not contain a valid image
            // May be raised by writeMetadata()
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 23:
            // Invalid ifdId {ifdId}
            // May be raised when instantiating an ExifKey from a tag and
            // IFD item string
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 26:
            // Offset out of range
            // May be raised by writeMetadata() (TIFF)
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 27:
            // Unsupported data area offset type
            // May be raised by writeMetadata() (TIFF)
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 28:
            // Invalid charset: `{charset name}'
            // May be raised when instantiating a CommentValue from a string
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 29:
            // Unsupported date format
            // May be raised when instantiating a DateValue from a string
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 30:
            // Unsupported time format
            // May be raised when instantiating a TimeValue from a string
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 31:
            // Writing to {image format} images is not supported
            // May be raised by writeMetadata() for certain image types
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 32:
            // Setting {metadata type} in {image format} images is not supported
            // May be raised when setting certain types of metadata for certain
            // image types that don't support them
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 33:
            // This does not look like a CRW image
            // May be raised by readMetadata() (CRW)
            PyErr_SetString(PyExc_IOError, message);
            break;
        case 35:
            // No namespace info available for XMP prefix `{prefix}'
            // May be raised when retrieving property info for an XmpKey
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 36:
            // No prefix registered for namespace `{namespace}', needed for
            // property path `{property path}'
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 37:
            // Size of {type of metadata} JPEG segment is larger than
            // 65535 bytes
            // May be raised by writeMetadata() (JPEG)
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 38:
            // Unhandled Xmpdatum {key} of type {value type}
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_TypeError, message);
            break;
        case 39:
            // Unhandled XMP node {key} with opt={XMP Toolkit option flags}
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_TypeError, message);
            break;
        case 40:
            // XMP Toolkit error {error id}: {error message}
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_RuntimeError, message);
            break;
        case 41:
            // Failed to decode Lang Alt property {property path}
            // with opt={XMP Toolkit option flags}
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 42:
            // Failed to decode Lang Alt qualifier {qualifier path}
            // with opt={XMP Toolkit option flags}
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 43:
            // Failed to encode Lang Alt property {key}
            // May be raised by writeMetadata()
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 44:
            // Failed to determine property name from path {property path},
            // namespace {namespace}
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 45:
            // Schema namespace {namespace} is not registered with
            // the XMP Toolkit
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 46:
            // No namespace registered for prefix `{prefix}'
            // May be raised when instantiating an XmpKey from a string
            PyErr_SetString(PyExc_KeyError, message);
            break;
        case 47:
            // Aliases are not supported. Please send this XMP packet
            // to ahuggel@gmx.net `{namespace}', `{property path}', `{value}'
            // May be raised by readMetadata() when reading the XMP data
            PyErr_SetString(PyExc_ValueError, message);
            break;
        case 48:
            // Invalid XmpText type `{type}'
            // May be raised when instantiating an XmpTextValue from a string
            PyErr_SetString(PyExc_TypeError, message);
            break;
        case 49:
            // TIFF directory {TIFF directory name} has too many entries
            // May be raised by writeMetadata() (TIFF)
            PyErr_SetString(PyExc_IOError, message);
            break;

        // Custom error codes
        case METADATA_NOT_READ:
            PyErr_SetString(PyExc_IOError, "Image metadata has not been read yet");
            break;
        case NON_REPEATABLE:
            PyErr_SetString(PyExc_KeyError, "Tag is not repeatable");
            break;
        case KEY_NOT_FOUND:
            PyErr_SetString(PyExc_KeyError, "Tag not set");
            break;

        // Default handler
        default:
            PyErr_SetString(PyExc_RuntimeError, message);
    }
}

} // End of namespace exiv2wrapper

