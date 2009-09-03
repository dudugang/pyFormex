#!/usr/bin/env pyformex
# $Id$
##
##  This file is part of pyFormex 0.8 Release Sat Jun 13 10:22:42 2009
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Website: http://pyformex.berlios.de/
##  Copyright (C) Benedict Verhegghe (bverheg@users.berlios.de) 
##  Distributed under the GNU General Public License version 3 or later.
##
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
"""image_numpy

This module contains functions to convert bitmap images into numpy
arrays and vice versa.

Most of this code was borrowed from the PyQwt mailing list
"""

from PyQt4.QtGui import QImage, QColor
import numpy

_bgra_rec = numpy.dtype({'b': (numpy.uint8, 0),
                         'g': (numpy.uint8, 1),
                         'r': (numpy.uint8, 2),
                         'a': (numpy.uint8, 3)})

def qimage2numpy(qimage):
    if qimage.format() in (QImage.Format_ARGB32_Premultiplied,
                           QImage.Format_ARGB32,
                           QImage.Format_RGB32):
        dtype = _bgra_rec
    elif qimage.format() == QImage.Format_Indexed8:
        dtype = numpy.uint8
    else:
        raise ValueError("qimage2numpy only supports 32bit and 8bit images")
    # FIXME: raise error if alignment does not match
    buf = qimage.bits().asstring(qimage.numBytes())
    return numpy.frombuffer(buf, dtype).reshape(
        (qimage.height(), qimage.width()))

def numpy2qimage(array):
	if numpy.ndim(array) == 2:
		return gray2qimage(array)
	elif numpy.ndim(array) == 3:
		return rgb2qimage(array)
	raise ValueError("can only convert 2D or 3D arrays")

def gray2qimage(gray):
	"""Convert the 2D numpy array `gray` into a 8-bit QImage with a gray
	colormap.  The first dimension represents the vertical image axis."""
	if len(gray.shape) != 2:
		raise ValueError("gray2QImage can only convert 2D arrays")

	gray = numpy.require(gray, numpy.uint8, 'C')

	h, w = gray.shape

	result = QImage(gray.data, w, h, QImage.Format_Indexed8)
	result.ndarray = gray
	for i in range(256):
		result.setColor(i, QColor(i, i, i).rgb())
	return result

def rgb2qimage(rgb):
	"""Convert the 3D numpy array `rgb` into a 32-bit QImage.  `rgb` must
	have three dimensions with the vertical, horizontal and RGB image axes."""
	if len(rgb.shape) != 3:
		raise ValueError("rgb2QImage can expects the first (or last) dimension to contain exactly three (R,G,B) channels")
	if rgb.shape[2] != 3:
		raise ValueError("rgb2QImage can only convert 3D arrays")

	h, w, channels = rgb.shape

	# Qt expects 32bit BGRA data for color images:
	bgra = numpy.empty((h, w, 4), numpy.uint8, 'C')
	bgra[...,0] = rgb[...,2]
	bgra[...,1] = rgb[...,1]
	bgra[...,2] = rgb[...,0]
	bgra[...,3].fill(255)

	result = QImage(bgra.data, w, h, QImage.Format_RGB32)
	result.ndarray = bgra
	return result

## if __name__ == '__main__':
##     import pylab
##     i = QImage()
##     i.load("../../Testimages/house.png")
##     v = qimage2numpy(i)
## #     v2 = qimage_view(i)
## #     v2["b"] = 0
##     rgb = numpy.empty(v.shape + (3, ), dtype = numpy.uint8)
##     rgb[...,0] = v["r"]
##     rgb[...,1] = v["g"]
##     rgb[...,2] = v["b"]
##     pylab.imshow(rgb)
##     pylab.show()

# End