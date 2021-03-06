# $Id$
##
##  This file is part of pyFormex 0.8.9  (Fri Nov  9 10:49:51 CET 2012)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##

"""Write geometry to file in a whole number of formats.

This module defines bothe the basic routines to write geometrical data
to a file and the specialized exporters to write files in a number of
well known standardized formats.

The basic routines are very versatile as well as optimized (using the version
in the pyFormex C-library) and allow to easily create new exporters for
other formats.
"""
from __future__ import print_function

import pyformex as pf
import numpy as np
from lib import misc
from arraytools import checkArray
import utils
import os


#
# DEVS: Do not use Int and Float here, but np.int32 and np.float32
#


def writeData(fil,data,sep='',fmt=None,end='\n'):
    """Write an array of numerical data to an open file.

    Parameters:

    - `fil`: an open file object
    - `data`: a numerical array of int or float type
    - `sep`: a string to be used as separator in case no `fmt` is specified.
      If an empty string, the data are written in binary mode. This is the
      default. For any other string, the data are written in ascii mode with
      the specified string inserted as separator between any two items, and a
      newline appended at the end.
      In both cases, the data are written using the `numpy.tofile`
      function.
    - `fmt`: a format string compatible with the array data type.
      If specified, the `sep` argument is ignored and the data are written
      according to the specified format. This uses the pyFormex functions
      `misc.tofile_int32` or `misc.tofile_float32`, which have accelerated
      versions in the pyFormex C library. This also means that the data arrays
      will be force to type `float32` or `int32` before writing.

      The format string should contain a valid format converter for a
      a single data item in both Python and C. They should also contain
      the necessary spacing or separator. Examples are '%5i ' for int data
      and '%f,' or '%10.3e' for float data. The array will be converted
      to a 2D array, keeping the length of the last axis. Then all elements
      will be written row by row using the specified format string, and the
      `end` string will be added after each row.
    - `end`: a string to be written at the end of the data block (if no `fmt`)
      or at the end of each row (with `fmt`). The default
      value is a newline character.
    """
    kind = data.dtype.kind
    if fmt is None:
        data.tofile(fil,sep)
    else:
        val = data.reshape(-1,data.shape[-1])
        if kind == 'i':
            misc.tofile_int32(val.astype(np.int32),fil,fmt)
        elif kind == 'f':
            misc.tofile_float32(val.astype(np.float32),fil,fmt)
        else:
            raise ValueError,"Can not write data fo type %s" % data.dtype
    if end:
        fil.write(end)


def writeIData(data,fil,fmt,ind=1):
    """Write an indexed array of numerical data to an open file.

    ind = i: autoindex from i
          array: use these indices
    """
    kind = data.dtype.kind
    val = data.reshape(-1,data.shape[-1])
    nrows = val.shape[0]
    if type(ind) is int:
        ind = ind + np.arange(nrows)
    else:
        ind = ind.reshape(-1)
        if ind.shape[0] != nrows:
            raise ValueError,"Index should have same length as data"

    if kind == 'i':
        raise ImplementationError
        misc.tofile_int32(val.astype(np.int32),fil,fmt)
    elif kind == 'f':
        misc.tofile_ifloat32(ind.astype(np.int32),val.astype(np.float32),fil,fmt)
    else:
        raise ValueError,"Can not write data fo type %s" % data.dtype


# Output of mesh file formats

def writeOFF(fn,coords,elems):
    """Write a mesh of polygons to a file in OFF format.

    Parameters:

    - `fn`: file name, by preference ending on '.off'
    - `coords`: float array with shape (ncoords,3), with the coordinates of
      `ncoords` vertices.
    - `elems`: int array with shape (nelems,nplex), with the definition of
      `nelems` polygon elements.
    """
    if coords.dtype.kind != 'f' or coords.ndim != 2 or coords.shape[1] != 3 or elems.dtype.kind != 'i' or elems.ndim != 2:
        raise runtimeError, "Invalid type or shape of argument(s)"

    fil = open(fn,'w')
    fil.write("OFF\n")
    fil.write("%d %d 0\n" % (coords.shape[0],elems.shape[0]))
    writeData(fil,coords,fmt='%f ')
    nelems = np.zeros_like(elems[:,:1])
    nelems.fill(elems.shape[1])
    elemdata = np.column_stack([nelems,elems])
    writeData(fil,elemdata,fmt='%i ')
    fil.close()


# Output of surface file formats

def writeGTS(fn,coords,edges,faces):
    """Write a mesh of triangles to a file in GTS format.

    Parameters:

    - `fn`: file name, by preference ending on '.gts'
    - `coords`: float array with shape (ncoords,3), with the coordinates of
      `ncoords` vertices
    - `edges`: int array with shape (nedges,2), with the definition of
      `nedges` edges in function of the vertex indices
    - `faces`: int array with shape (nfaces,3), with the definition of
      `nfaces` triangles in function of the edge indices
    """
    if coords.dtype.kind != 'f' or coords.ndim != 2 or coords.shape[1] != 3 or edges.dtype.kind != 'i' or edges.ndim != 2 or edges.shape[1] != 2 or faces.dtype.kind != 'i' or faces.ndim != 2 or faces.shape[1] != 3:
        raise runtimeError, "Invalid type or shape of argument(s)"

    fil = open(fn,'w')
    fil.write("%d %d %d\n" % (coords.shape[0],edges.shape[0],faces.shape[0]))
    writeData(fil,coords,fmt='%f ')
    writeData(fil,edges+1,fmt='%i ')
    writeData(fil,faces+1,fmt='%i ')
    fil.write("#GTS file written by %s\n" % pf.Version)
    fil.close()


# Output of surface file formats

def writeSTL(f,x,n=None,binary=False,color=None):
    """Write a collection of triangles to an STL file.

    Parameters:

    - `fn`: file name, by preference ending with '.stl' or '.stla'
    - `x`: (ntriangles,3,3) shaped array with the vertices of the
      triangles
    - `n`: (ntriangles,3) shaped array with the normals of the
      triangles. If not specified, they will be calculated.
    - `binary`: if True, the output file format  will be a binary STL.
      The default is an ascii STL. Note that creation of a binary STL
      requires the extermal program 'admesh'.
    - `color`: a single color can be passed to a binary STL and will be
      stpored in the header.
    """
    if not x.shape[1:] == (3,3):
        raise ValueError,"Expected an (ntri,3,3) array, got %s" % x.shape

    if n is None:
        import geomtools
        a,n = geomtools.areaNormals(x)
        degen = geomtools.degenerate(a,n)
        print("The model contains %d degenerate triangles" % degen.shape[0])
        x = np.column_stack([n.reshape(-1,1,3),x])

    if binary:
        write_stl_bin(f,x,color)
    else:
        write_stl_asc(f,x)


def write_stl_bin(fn,x,color=None):
    """Write a binary stl.

    Parameters:

    - `x`: (ntri,4,3) float array describin ntri triangles.
      The first item of each triangle is the normal, the other
      three are the vertices.
    - `color`: (4,) int array with values in the range 0..255. These are
      the red, green, blue and alpha components of the color. This is a
      single color for all the triangles, and will be stored in the header
      of the STL file.
    """
    x = checkArray(x,shape=(-1,4,3),kind='f')
    if color is not None:
        color = checkArray(color,shape=(4,),kind='i').astype(np.uint8)

    def addTriangle(i):
        x[i].tofile(fil)
        fil.write('\x00\x00')

    pf.message("Writing binary STL %s" % fn)
    ver = pf.fullVersion()
    if len(ver) > 50:
        ver = ver[:50]
    if color is None:
        color = ''
    else:
        color = "COLOR=%4s" % color.tostring()
        pf.message("Adding %s to the header" % color)

    with open(fn,'wb') as fil:
        head = "%-50s%-30s" % (ver,color)
        fil.write(head)
        ntri = x.shape[0]
        pf.message("Number of triangles: %s" % ntri)
        np.array(ntri).astype(np.int32).tofile(fil)
        x = x.astype(np.float32)
        [ addTriangle(i) for i in range(ntri) ]
    pf.message("Finished writing binary STL, %s bytes" % utils.fileSize(fn))


def write_stl_asc(fn,x):
    """Write a collection of triangles to an ascii .stl file.

    Parameters:

    - `fn`: file name, by preference ending with '.stl' or '.stla'
    - `x`: (ntriangles,3,3) shaped array with the vertices of the
      triangles
    """
    if not x.shape[1:] == (4,3):
        raise ValueError,"Expected an (ntri,4,3) array, got %s" % x.shape

    pf.message("Writing ascii STL %s" % fn)
    with open(fn,'wb') as fil:

        fil.write("solid  Created by %s\n" % pf.fullVersion())
        for e in x:
            fil.write("  facet normal %s %s %s\n" % tuple(e[0]))
            fil.write("    outer loop\n")
            for p in e[1:]:
                fil.write("      vertex %s %s %s\n" % tuple(p))
            fil.write("    endloop\n")
            fil.write("  endfacet\n")
        fil.write("endsolid\n")
    pf.message("Finished writing ascii STL, %s bytes" % utils.fileSize(fn))


# End
