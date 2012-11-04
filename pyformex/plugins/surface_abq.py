# $Id$
##
##  This file is part of pyFormex 0.8.8  (Sun Nov  4 17:22:49 CET 2012)
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
"""Create tetraeder mesh inside .STL surface and export in Abaqus format.

Usage: pyformex --nogui surface_abq SURFACE_FILES
Generates input-surface.inp and input-volume.inp with the
surface and volume modules in Abaqus(R) input format. 
"""
from __future__ import print_function
from mesh import Mesh
from plugins import fe_abq,tetgen
import os


def stl_to_abaqus(fn):
    print("Converting %s to Abaqus .INP format" % fn)
    tetgen.runTetgen(fn)
    fb = os.path.splitext(fn)[0]
    nodes = tetgen.readNodes(fb+'.1.node')
    elems = tetgen.readElems(fb+'.1.ele')
    faces = tetgen.readSurface(fb+'.1.smesh')
    print("Exporting surface model")
    smesh = Mesh(nodes,faces,eltype='S3')
    fe_abq.exportMesh(fb+'-surface.inp',smesh,"Abaqus model generated by tetgen from surface in STL file %s" % fn)
    print("Exporting volume model")
    vmesh = Mesh(nodes,elems,eltype='C3D%d' % elems.shape[1])
    abq_export(fb+'-volume.inp',vmesh,"Abaqus model generated by tetgen from surface in STL file %s" % fn)
     

# Processing starts here

if __name__ == "script":
    import sys

    for f in sys.argv[2:]:
        if f.endswith('.stl') and os.path.exists(f):
            print("Processing %s" % f)
            stl_to_abaqus(f)
        else:
            print("Ignore argument %s" % f)

           

# End
