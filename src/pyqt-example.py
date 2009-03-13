#!/usr/bin/python
# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2007 Olivier Tilloy <olivier@tilloy.net>
#
# This file is part of the pyexiv2 distribution.
#
# pyexiv2 is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# pyexiv2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyexiv2; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, 5th Floor, Boston, MA 02110-1301 USA.
#
#
# File:      pyqt-example.py
# Author(s): Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import sys
from PyQt4 import QtGui
import pyexiv2

if __name__ == '__main__':
	"""
	Example of how to combine pyqt and pyexiv2 to display thumbnail data.

	Minimalistic example of how to load and display with pyqt the thumbnail data
	extracted from an image using the method Image.getThumbnailData().
	The path to the image file from which the thumbnail data should be extracted
	should be passed as the only argument of the script.

	It is of course assumed that you have pyqt installed.
	"""
	if (len(sys.argv) != 2):
		print 'Usage: ' + sys.argv[0] + ' path/to/picture/file/containing/jpeg/thumbnail'
		sys.exit(1)

	app = QtGui.QApplication([])

	# Load the image, read the metadata and extract the thumbnail data
	filename = sys.argv[1]
	image = pyexiv2.Image(filename)
	image.readMetadata()

	try:
		ttype, tdata = image.getThumbnailData()
	except IOError:
		print 'Error: %s does not contain an EXIF thumbnail.' % filename
		sys.exit(1)

	# Create a QT pixmap from the thumbnail data
	pixmap = QtGui.QPixmap()
	pixmap.loadFromData(tdata, ttype.split('/')[1].upper())

	# Create a QT label to display the pixmap
	label = QtGui.QLabel(None)
	label.setPixmap(pixmap)

	# Show the application's main window
	label.show()
	app.exec_()
