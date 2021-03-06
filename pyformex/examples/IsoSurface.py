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

"""IsoSurface

This example illustrates the use of the isosurface plugin to construct
isosurface through a set of data
"""
from __future__ import print_function
_status = 'checked'
_level = 'beginner'
_topics = ['surface']
_techniques = ['isosurface']

from gui.draw import *
from plugins import isosurface as sf
import elements
import plugins.imagearray as ia


def loadImage(file,grey=True):
    """Load a grey image into a numpy array"""
    im = ia.image2numpy(file,order='RGB',indexed=False)
    if grey:
        # Do type conversion because auto conversion produces float64
        im = im.sum(axis=-1).astype(Float) / 3.
    return im


def loadImages(files,glmode=True):
    images = [ loadImage(f) for f in files ]
    images = dstack(images)
    if glmode:
        images /= 255.
    return images


def run():
    clear()
    smooth()

    options = ["Cancel","Image files","DICOM files","Generated from function"]
    ans = ask("This IsoSurface example can either reconstruct a surface from a series of 2D images, or it can use data generated from a function. Use which data?",options)
    ans = options.index(ans)

    if ans == 0:
        return

    elif ans in [1,2]:
        ## fp = askDirname(byfile=True)
        ## if not fp:
        ##     return

        ## files = utils.listTree(fp,listdirs=False)

        fn = askFilename(multi=True)
        if not fn:
            return

        if len(fn) == 1:
            files = utils.NameSequence(fn[0]).files()

        print(files)

        if ans == 1:
            data = loadImages(files)
            scale = ones(3)
        else:
            data,scale = ia.dicom2numpy(files)
            print("Spacing: %s" % scale)
            # normalize
            dmin,dmax = data.min(),data.max()
            data = (data-dmin).astype(float32)/(dmax-dmin)

        # level at which the isosurface is computed
        res = askItems([('isolevel',0.5)])
        if not res:
            return
        level = res['isolevel']
        if level <= 0.0 or level >= 1.0:
            level = data.mean()

    else:
        # data space: create a grid to visualize
        if ack("Large model (takes some time)?"):
            nx,ny,nz = 100,150,200 # for time testing
        else:
            nx,ny,nz = 6,8,10
        F = elements.Hex8.toFormex().rep([nz,ny,nx]).setProp(1)
        #draw(F,mode='wireframe')

        # function to generate data: the distance from the origin
        dist = lambda x,y,z: sqrt(x*x+y*y+z*z)
        data = fromfunction(dist,(nz+1,ny+1,nx+1))
        scale = ones(3)

        # level at which the isosurface is computed
        level = 0.5*data.max()

    print("IMAGE DATA: %s, %s" % (data.shape,data.dtype))
    print("Pixel Spacing: %s" % str(scale))
    print("levels: min = %s, max = %s" % (data.min(),data.max()))
    print("isolevel: %s" % level)

    fast = True

    # Compute the isosurface
    from timer import Timer
    pf.GUI.setBusy()
    timer = Timer()
    tri = sf.isosurface(data,level,nproc=4)
    sec = timer.seconds()
    print("Got %s triangles in %s seconds" % (len(tri),sec))
    if len(tri) > 0:
        S = TriSurface(tri).scale(scale[::-1])
        draw(S)
        export({'isosurf':S})
    pf.GUI.setBusy(False)


# The following is to make it work as a script
if __name__ == 'draw':
    run()


# End
