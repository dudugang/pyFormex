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
"""OpenGL drawing functions and base class for all drawable objects.

"""
from __future__ import print_function

import pyformex as pf

from OpenGL import GL,GLU

from colors import *
from formex import *

import geomtools
import simple
import utils
import olist

from lib import drawgl

def glObjType(nplex):
    if nplex == 1:
        objtype = GL.GL_POINTS
    elif nplex == 2:
        objtype = GL.GL_LINES
    elif nplex == 3:
        objtype = GL.GL_TRIANGLES
    elif nplex == 4:
        objtype = GL.GL_QUADS
    else:
        objtype = GL.GL_POLYGON
    return objtype

# A list of elements that can be drawn quadratically using NURBS
_nurbs_elements = [ 'line3', 'quad4', 'quad8', 'quad9', 'hex20' ]

### Some drawing functions ###############################################

def glColor(color,alpha=None):
    """Set the OpenGL color, possibly with transparency.

    color is a tuple of 3 or 4 real values.
    alpha is a single real value.
    All values are between 0.0 and 1.0
    """
    if color is not None:
        if len(color) == 3:
            if alpha is None:
                GL.glColor3fv(color)
            else:
                GL.glColor4fv(append(color,alpha))
        else:
            GL.glColor4fv(color)


def glTexture(texture,mode='*'):
    """Render-time texture environment setup"""
    texmode = {'*': GL.GL_MODULATE, '1': GL.GL_DECAL}[mode]
    # Configure the texture rendering parameters
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glTexParameterf(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
    GL.glTexParameterf(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
    GL.glTexEnvf(GL.GL_TEXTURE_ENV,GL.GL_TEXTURE_ENV_MODE,texmode)
    # Re-select the texture
    GL.glBindTexture(GL.GL_TEXTURE_2D,texture.tex)

#
# Though all three functions drawPoints, drawLines and drawPolygons
# call the same low level drawgl.draw_polygons function, we keep 3 separate
# functions on the higher level, because of special characteristics
# of nplex < 3:   no computation of normals, marksize (nplex=1)
#


# DRAWPOINTS should also be modified to accept an (x,e) model
# (Yes, it makes sense to create a Point mesh
def drawPoints(x,color=None,alpha=1.0,size=None):
    """Draw a collection of points with default or given size and color.

    x is a (npoints,3) shaped array of coordinates.
    If size (float) is given, it specifies the point size.
    If color is given it is an (npoints,3) array of RGB values.
    """
    x = x.astype(float32).reshape(-1,3)
    if color is not None:
        color = resize(color.astype(float32),x.shape)
    if size:
        GL.glPointSize(size)
    x = x.reshape(-1,1,3)
    drawgl.draw_polygons(x,None,color,None,alpha,-1)


def multi_draw_polygons(x,n,color,t,alpha,objtype,nproc=-1):
    from multi import multitask,cpu_count
    if nproc < 1:
        nproc = cpu_count()

    print("MULTIDRAW %s" % nproc)

    if nproc == 1:
        drawgl.draw_polygons(x,n,color,t,alpha,objtype)

    else:
        xblocks = splitar(x,nproc)
        n = t = color = None
        print([xb.shape for xb in xblocks])
        #[ drawgl.draw_polygons(xb,n,color,t,alpha,objtype) for xb in xblocks]

        tasks = [(drawgl.draw_polygons,(xb,n,color,t,alpha,objtype)) for xb in xblocks]
        multitask(tasks,nproc)


def drawPolygons(x,e,color=None,alpha=1.0,texture=None,t=None,normals=None,lighting=False,avgnormals=False,objtype=-1):
    """Draw a collection of polygons.

    The polygons can either be specified as a Formex model or as a Mesh model.

    Parameters:

    - `x`: coordinates of the points. Shape is (nelems,nplex,3) for Formex
      model, of (nnodes,3) for Mesh model.
    - `e`: None for a Formex model, definition of the elements (nelems,nplex)
      for a Mesh model.
    - `color`: either None or an RGB color array with shape (3,), (nelems,3)
      or (nelems,nplex,3).
    - `objtype`: OpenGL drawing mode. The default (-1) will select the
      appropriate value depending on the plexitude of the elements:
      1: point, 2: line, 3: triangle, 4: quad, >4: polygon.
      This value can be set to GL.GL_LINE_LOOP to draw the element's
      circumference independent from the drawing mode.
    """
    pf.debug("drawPolygons",pf.DEBUG.DRAW)
    if e is None:
        nelems = x.shape[0]
    else:
        nelems = e.shape[0]
    n = None
    #print("LIGHTING %s, AVGNORMALS %s" % (lighting,avgnormals))
    if lighting and objtype==-1:
        if normals is None:
            pf.debug("Computing normals",pf.DEBUG.DRAW)
            if avgnormals and e is not None:
                n = geomtools.averageNormals(x,e,treshold=pf.cfg['render/avgnormaltreshold'])
            else:
                if e is None:
                    n = geomtools.polygonNormals(x)
                else:
                    n = geomtools.polygonNormals(x[e])
                #pf.debug("NORMALS:%s" % str(n.shape),pf.DEBUG.DRAW)
        else:
            #print("NORMALS=%s"% normals)
            n = checkArray(normals,(nelems,-1,3),'f')

    # Texture
    if texture is not None:
        glTexture(texture)
        if t is None:
            t = array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
    else:
        t = None


    # Sanitize data before calling library function
    x = x.astype(float32)
    if e is not None:
        e = e.astype(int32)
    if n is not None:
        n = n.astype(float32)
    if color is not None:
        color = color.astype(float32)
        pf.debug("COLORS:%s" % str(color.shape),pf.DEBUG.DRAW)
        if color.shape[-1] != 3 or (
            color.ndim > 1 and color.shape[0] != nelems) :
            pf.debug("INCOMPATIBLE COLOR SHAPE: %s, while nelems=%s" % (str(color.shape),nelems),pf.DEBUG.DRAW)
            color = None
    if t is not None:
        t = t.astype(float32)

    # Call library function
    if e is None:
        drawgl.draw_polygons(x,n,color,t,alpha,objtype)
        #multi_draw_polygons(x,n,color,t,alpha,objtype)
    else:
        drawgl.draw_polygon_elems(x,e,n,color,t,alpha,objtype)


def drawPolyLines(x,e,color):
    """Draw the circumference of polygons."""
    pf.debug("drawPolyLines",pf.DEBUG.DRAW)
    drawPolygons(x,e,color=color,alpha=1.0,objtype=GL.GL_LINE_LOOP)


def drawLines(x,e,color):
    """Draw straight line segments."""
    pf.debug("drawLines",pf.DEBUG.DRAW)
    drawPolygons(x,e,color=color,alpha=1.0)


def drawBezier(x,color=None,objtype=GL.GL_LINE_STRIP,granularity=100):
    """Draw a collection of Bezier curves.

    x: (4,3,3) : control points
    color: (4,) or (4,4): colors
    """
    GL.glMap1f(GL.GL_MAP1_VERTEX_3,0.0,1.0,x)
    GL.glEnable(GL.GL_MAP1_VERTEX_3)
    if color is not None and color.shape == (4,4):
        GL.glMap1f(GL.GL_MAP1_COLOR_4,0.0,1.0,color)
        GL.glEnable(GL.GL_MAP1_COLOR_4)

    u = arange(granularity+1) / float(granularity)
    if color is not None and color.shape == (4,):
        GL.glColor4fv(color)
        color = None

    GL.glBegin(objtype)
    for ui in u:
        #  For multicolors, this will generate both a color and a vertex
        GL.glEvalCoord1f(ui)
    GL.glEnd()

    GL.glDisable(GL.GL_MAP1_VERTEX_3)
    if color is not None:
        GL.glDisable(GL.GL_MAP1_COLOR_4)


def drawBezierPoints(x,color=None,granularity=100):
    drawBezier(x,color=None,objtype=GL.GL_POINTS,granularity=granularity)


def drawNurbsCurves(x,knots,color=None,alpha=1.0,samplingTolerance=5.0):
    """Draw a collection of Nurbs curves.

    x: (nctrl,ndim) or (ncurve,nctrl,ndim) float array: control points,
       specifying either a single curve or ncurve curves defined by the
       same number of control points. ndim can be 3 or 4. If 4, the 4-th
       coordinate is interpreted as a weight for that point.
    knots: (nknots) or (ncurve,nknots) float array: knot vector, containing the
       parameter values to be used in the nurbs definition. Remark that
       nknots must be larger than nctrl. The order of the curve is
       nknots-nctrl and the degree of the curve is order-1.
       If a single knot vector is given, the same is used for all curves.
       Otherwise, the number of knot vectors must match the number of nurbs
       curves.

    If color is given it is an (ncurves,3) array of RGB values.
    """
    nctrl,ndim = x.shape[-2:]
    nknots = asarray(knots).shape[-1]
    order = nknots-nctrl
    if  order > 8:
        utils.warn('Nurbs curves of degree > 7 can currently not be drawn! You can create some approximation by evaluating the curve at some points.')
        return

    if x.ndim == 2:
        x = x.reshape(-1,nctrl,ndim)
        if color is not None and color.ndim == 2:
            color = color.reshape(-1,nctrl,color.shape[-1])

    if color is not None:
        pf.debug('Coords shape: %s' % str(x.shape),pf.DEBUG.DRAW)
        pf.debug('Color shape: %s' % str(color.shape),pf.DEBUG.DRAW)
        if color.ndim == 1:
            pf.debug('Single color',pf.DEBUG.DRAW)
        elif color.ndim == 2 and color.shape[0] == x.shape[0]:
            pf.debug('Element color: %s colors' % color.shape[0],pf.DEBUG.DRAW)
        elif color.shape == x.shape[:-1] + (3,):
            pf.debug('Vertex color: %s colors' % str(color.shape[:-1]),pf.DEBUG.DRAW)
        else:
            raise ValueError,"Number of colors (%s) should equal 1 or the number of curves(%s) or the number of curves * number of vertices" % (color.shape[0],x.shape[0])

        pf.debug("Color shape = %s" % str(color.shape),pf.DEBUG.DRAW)
        if color.shape[-1] not in (3,4):
            raise ValueError,"Expected 3 or 4 color components"

    if color is not None:
        pf.debug("Final Color shape = %s" % str(color.shape),pf.DEBUG.DRAW)

    nurb = GLU.gluNewNurbsRenderer()
    if not nurb:
        raise RuntimeError,"Could not create a new NURBS renderer"

    GLU.gluNurbsProperty(nurb,GLU.GLU_SAMPLING_TOLERANCE,samplingTolerance)

    mode = {3:GL.GL_MAP1_VERTEX_3, 4:GL.GL_MAP1_VERTEX_4}[ndim]

    if color is not None and color.ndim == 1:
        # Handle single color
        pf.debug('Set single color: OK',pf.DEBUG.DRAW)
        glColor(color)
        color = None

    ki = knots
    for i,xi in enumerate(x):
        if color is not None and color.ndim == 2:
            # Handle element color
            glColor(color[i])
        if knots.ndim > 1:
            ki = knots[i]
        GLU.gluBeginCurve(nurb)
        if color is not None and color.ndim == 3:
            # Handle vertex color
            ci = color[i]
            if ci.shape[-1] == 3:
                # gluNurbs always wants 4 colors
                ci = growAxis(ci,1,axis=-1,fill=alpha)
            GLU.gluNurbsCurve(nurb,ki,ci,GL.GL_MAP1_COLOR_4)
        GLU.gluNurbsCurve(nurb,ki,xi,mode)
        GLU.gluEndCurve(nurb)

    GLU.gluDeleteNurbsRenderer(nurb)


def drawQuadraticCurves(x,e=None,color=None,alpha=1.0):
    """Draw a collection of quadratic curves.

    The geometry is specified by x or (x,e).
    x or x[e] is a (nlines,3,3) shaped array of coordinates.
    For each element a quadratic curve through its 3 points is drawn.

    This uses the drawNurbsCurves function for the actual drawing.
    The difference between drawQuadraticCurves(x) and drawNurbsCurves(x)
    is that in the former, the middle point is laying on the curve, while
    in the latter case, the middle point defines the tangents in the end
    points.

    If color is given it is an (nlines,3) array of RGB values.
    """
    pf.debug("drawQuadraticCurves",pf.DEBUG.DRAW)
    if e is None:
        #print("X SHAPE %s" % str(x.shape))
        nelems,nfaces,nplex = x.shape[:3]
        x = x.reshape(-1,nplex,3)
    else:
        if e.ndim == 3:
            nelems,nfaces,nplex = e.shape
            e = e.reshape(-1,nplex)
        elif e.ndim == 2:
            nelems,nplex = e.shape
            nfaces = 1
        else:
            raise ValueError,"Can not handle elems with shape: %s" % str(e.shape)

    if color is not None:
        if color.ndim == 2:
            pf.debug("COLOR SHAPE BEFORE MULTIPLEXING %s" % str(color.shape),pf.DEBUG.DRAW)
            color = color_multiplex(color,nfaces)
            pf.debug("COLOR SHAPE AFTER  MULTIPLEXING %s" % str(color.shape),pf.DEBUG.DRAW)
        if color.ndim > 2:
            color = color.reshape((nelems*nfaces,) + color.shape[-2:]).squeeze()
            pf.debug("COLOR SHAPE AFTER RESHAPING %s" % str(color.shape),pf.DEBUG.DRAW)

    if e is None:
        xx = x.copy()
    else:
        xx = x[e]

    #print xx.shape
    #print xx
    xx[...,1,:] = 2*xx[...,1,:] - 0.5*(xx[...,0,:] + xx[...,2,:])
    #print xx.shape
    #print xx
    knots = array([0.,0.,0.,1.,1.,1.])
    drawNurbsCurves(xx,knots,color=color,alpha=alpha)


_nurbs_renderers_ = []
def drawNurbsSurfaces(x,sknots,tknots,color=None,alpha=1.0,normals='auto',samplingTolerance=20.0):
    """Draw a collection of Nurbs surfaces.

    x: (ns,nt,ndim) or (nsurf,ns,nt,ndim) float array:
       (ns,nt) shaped control points array,
       specifying either a single surface or nsurf surfaces defined by the
       same number of control points. ndim can be 3 or 4. If 4, the 4-th
       coordinate is interpreted as a weight for that point.
    sknots: (nsk) or (nsurf,nsk) float array: knot vector, containing
       the parameter values to be used in the s direction of the surface.
       Remark that nsk must be larger than ns. The order of the surface
       in s-direction is nsk-ns and the degree of the s-curves is nsk-ns-1.
       If a single sknot vector is given, the same is used for all surfaces.
       Otherwise, the number of sknot vectors must match the number of nurbs
       surfaces.
    tknots: (ntk) or (nsurf,ntk) float array: knot vector, containing
       the parameter values to be used in the t direction of the surface.
       Remark that ntk must be larger than nt. The order of the surface
       in t-direction is ntk-nt and the degree of the t-curves is ntk-nt-1.
       If a single sknot vector is given, the same is used for all surfaces.
       Otherwise, the number of sknot vectors must match the number of nurbs
       surfaces.

    If color is given it is an (nsurf,3) array of RGB values.
    """
    import timer
    t = timer.Timer()

    ns,nt,ndim = x.shape[-3:]
    nsk = asarray(sknots).shape[-1]
    ntk = asarray(tknots).shape[-1]
    sorder = nsk-ns
    torder = ntk-nt
    if sorder > 8 or torder > 8:
        utils.warn('Nurbs surfaces of degree > 7 can currently not be drawn! You can approximate the surface by a lower order surface.')
        return

    if x.ndim == 3:
        x = x.reshape(-1,ns,nt,ndim)
        if color is not None and color.ndim == 3:
            color = color.reshape(-1,ns,nt,color.shape[-1])

    if color is not None:
        pf.debug('Coords shape: %s' % str(x.shape),pf.DEBUG.DRAW)
        pf.debug('Color shape: %s' % str(color.shape),pf.DEBUG.DRAW)
        if color.ndim == 1:
            pf.debug('Single color',pf.DEBUG.DRAW)
        elif color.ndim == 2 and color.shape[0] == x.shape[0]:
            pf.debug('Element color: %s' % color.shape[0],pf.DEBUG.DRAW)
        elif color.shape == x.shape[:-1] + (3,):
            pf.debug('Vertex color: %s' % str(color.shape[:-1]),pf.DEBUG.DRAW)
        else:
            raise ValueError,"Number of colors (%s) should equal 1 or the number of faces(%s) or the number of faces * number of vertices" % (color.shape[0],x.shape[0])

        pf.debug("Color shape = %s" % str(color.shape),pf.DEBUG.DRAW)
        if color.shape[-1] not in (3,4):
            raise ValueError,"Expected 3 or 4 color components"

    if normals == 'auto':
        GL.glEnable(GL.GL_AUTO_NORMAL)
    else:
        GL.glDisable(GL.GL_AUTO_NORMAL)

    # The following uses:
    # x: (nsurf,ns,nt,4)
    # sknots: (nsknots) or (nsurf,nsknots)
    # tknots: (ntknots) or (nsurf,ntknots)
    # color: None or (4) or (nsurf,4) or (nsurf,ns,nt,4)
    # samplingTolerance

    if pf.options.fastnurbs:
        alpha=0.5
        x = x.astype(float32)
        sknots = sknots.astype(float32)
        tknots = tknots.astype(float32)
        if color is not None:
            color = color.astype(float32)

            if color.shape[-1] == 3:
                # gluNurbs always wants 4 colors
                color = growAxis(color,3,axis=-1,fill=alpha)

        nb = drawgl.draw_nurbs_surfaces(x,sknots,tknots,color,alpha,samplingTolerance)

    else:
        nurb = GLU.gluNewNurbsRenderer()
        if not nurb:
            raise RuntimeError,"Could not create a new NURBS renderer"

        GLU.gluNurbsProperty(nurb,GLU.GLU_SAMPLING_TOLERANCE,samplingTolerance)

        mode = {3:GL.GL_MAP2_VERTEX_3, 4:GL.GL_MAP2_VERTEX_4}[ndim]

        if color is not None and color.ndim == 1:
            # Handle single color
            pf.debug('Set single color: OK',pf.DEBUG.DRAW)
            glColor(color)
            color = None

        si = sknots
        ti = tknots
        for i,xi in enumerate(x):
            if color is not None and color.ndim == 2:
                # Handle element color
                glColor(color[i])
            if sknots.ndim > 1:
                si = sknots[i]
            if tknots.ndim > 1:
                ti = tknots[i]
            GLU.gluBeginSurface(nurb)
            if color is not None and color.ndim == 4:
                # Handle vertex color
                ci = color[i]
                if ci.shape[-1] == 3:
                    # gluNurbs always wants 4 colors
                    ci = growAxis(ci,1,axis=-1,fill=alpha)
                GLU.gluNurbsSurface(nurb,si,ti,ci,GL.GL_MAP2_COLOR_4)
            GLU.gluNurbsSurface(nurb,si,ti,xi,mode)
            GLU.gluEndSurface(nurb)

        GLU.gluDeleteNurbsRenderer(nurb)

    print("drawNurbsSurfaces: %s seconds" % t.seconds())


def quad4_quad8(x):
    """_Convert an array of quad4 surfaces to quad8"""
    y = roll(x,-1,axis=-2)
    x5_8 = (x+y)/2
    return concatenate([x,x5_8],axis=-2)

def quad8_quad9(x):
    """_Convert an array of quad8 surfaces to quad9"""
    x9 = x[...,:4,:].sum(axis=-2)/2 - x[...,4:,:].sum(axis=-2)/4
    return concatenate([x,x9[...,newaxis,:]],axis=-2)


def drawQuadraticSurfaces(x,e,color=None):
    """Draw a collection of quadratic surfaces.

    The geometry is specified by x or (x,e).
    x or x[e] is a (nsurf,nquad,3) shaped array of coordinates, where
    nquad is either 4,6,8 or 9
    For each element a quadratic surface through its nquad points is drawn.

    This uses the drawNurbsSurfaces function for the actual drawing.
    The difference between drawQuadraticSurfaces(x) and drawNurbsSurfaces(x)
    is that in the former, the internal point is laying on the surface, while
    in the latter case, the middle point defines the tangents in the middle
    points of the sides.

    If color is given it is an (nsurf,3) array of RGB values.
    """
    import timer
    t = timer.Timer()
    pf.debug("drawQuadraticSurfaces",pf.DEBUG.DRAW)
    if e is None:
        nelems,nfaces,nplex = x.shape[:3]
        x = x.reshape(-1,nplex,3)
    else:
        nelems,nfaces,nplex = e.shape[:3]
        e = e.reshape(-1,nplex)

    if color is not None:
        pf.debug('Color shape: %s' % str(color.shape),pf.DEBUG.DRAW)
        if color.ndim == 2:
            pf.debug("COLOR SHAPE BEFORE MULTIPLEXING %s" % str(color.shape),pf.DEBUG.DRAW)
            color = color_multiplex(color,nfaces)
            pf.debug("COLOR SHAPE AFTER  MULTIPLEXING %s" % str(color.shape),pf.DEBUG.DRAW)
        if color.ndim > 2:
            # BV REMOVED squeeze: may break some things
            color = color.reshape((nelems*nfaces,) + color.shape[-2:])#.squeeze()
            pf.debug("COLOR SHAPE AFTER RESHAPING %s" % str(color.shape),pf.DEBUG.DRAW)

    if e is None:
        xx = x.copy()
    else:
        xx = x[e]

    # Draw quad4 as quad4
    if xx.shape[-2] == 4:
        # Bilinear surface
        knots = array([0.,0.,1.,1.])
        xx = xx[...,[0,3,1,2],:]
        xx = xx.reshape(-1,2,2,xx.shape[-1])
        if color is not None and color.ndim > 2:
            color = color[...,[0,3,1,2],:]
            color = color.reshape(-1,2,2,color.shape[-1])
        drawNurbsSurfaces(xx,knots,knots,color)
        return

    # Convert quad8 to quad9
    if xx.shape[-2] == 8:
        xx = quad8_quad9(xx)

    # Convert quad9 to nurbs node order
    xx = xx[...,[0,7,3,4,8,6,1,5,2],:]
    xx = xx.reshape(-1,3,3,xx.shape[-1])
    if color is not None and color.ndim > 2:
        pf.debug("INITIAL COLOR %s" % str(color.shape),pf.DEBUG.DRAW)
        if color.shape[-2] == 8:
            color = quad8_quad9(color)
        color = color[...,[0,7,3,4,8,6,1,5,2],:]
        color = color.reshape(-1,3,3,color.shape[-1])
        pf.debug("RESHAPED COLOR %s" % str(color.shape),pf.DEBUG.DRAW)

    xx[...,1,:] = 2*xx[...,1,:] - 0.5*(xx[...,0,:] + xx[...,2,:])
    xx[...,1,:,:] = 2*xx[...,1,:,:] - 0.5*(xx[...,0,:,:] + xx[...,2,:,:])
    knots = array([0.,0.,0.,1.,1.,1.])
    drawNurbsSurfaces(xx,knots,knots,color)
    print("drawQuadraticSurfaces: %s seconds" % t.seconds())


def color_multiplex(color,nparts):
    """Multiplex a color array over nparts of the elements.

    This function will repeat the colors in an array a number of times
    so that all parts of the same element are colored the same.
    """
    s = list(color.shape)
    s[1:1] = [1]
    color = color.reshape(*s).repeat(nparts,axis=1)
    s[1] = nparts # THIS APPEARS NOT TO BE DOING ANYTHING ?
    return color.reshape(-1,3)


def draw_faces(x,e,color=None,alpha=1.0,texture=None,texc=None,normals=None,lighting=False,avgnormals=False,objtype=-1):
    """Draw a collection of faces.

    (x,e) are one of:
    - x is a (nelems,nfaces,nplex,3) shaped coordinates and e is None,
    - x is a (ncoords,3) shaped coordinates and e is a (nelems,nfaces,nplex)
    connectivity array.

    Each of the nfaces sets of nplex points defines a polygon.

    If color is given it is either an (3,), (nelems,3), (nelems,faces,3)
    or (nelems,faces,nplex,3) array of RGB values.
    In the second case, this function will multiplex the colors, so that
    `nfaces` faces are drawn in the same color.
    This is e.g. convenient when drawing faces of a solid element.
    """
    pf.debug("draw_faces",pf.DEBUG.DRAW)
    if e is None:
        nelems,nfaces,nplex = x.shape[:3]
        x = x.reshape(-1,nplex,3)
    else:
        nelems,nfaces,nplex = e.shape[:3]
        e = e.reshape(-1,nplex)

    if color is not None:
        if color.ndim == 2:
            pf.debug("COLOR SHAPE BEFORE MULTIPLEXING %s" % str(color.shape),pf.DEBUG.DRAW)
            color = color_multiplex(color,nfaces)
            pf.debug("COLOR SHAPE AFTER  MULTIPLEXING %s" % str(color.shape),pf.DEBUG.DRAW)
        if color.ndim > 2:
            color = color.reshape((nelems*nfaces,) + color.shape[-2:]).squeeze()
            pf.debug("COLOR SHAPE AFTER RESHAPING %s" % str(color.shape),pf.DEBUG.DRAW)

    drawPolygons(x,e,color,alpha,texture,texc,normals,lighting,avgnormals,objtype=objtype)


def drawEdges(x,e,edges,eltype,color=None):
    """Draw the edges of a geometry.

    This function draws the edges of a geometry collection, usually of a higher
    dimensionality (i.c. a surface or a volume).
    The edges are identified by constant indices into all element vertices.

    The geometry is specified by x or (x,e)
    The edges are specified by a list of lists. Each list defines a single
    edge of the solid, in local vertex numbers (0..nplex-1).

    If eltype is None, the edges are drawn as polygons. Other allowed values
    are: 'line3'
    """
    pf.debug("drawEdges",pf.DEBUG.DRAW)
    if not type(eltype) == str:
        eltype = eltype.name()
    # We may have edges with different plexitudes!
    # We collect them according to plexitude.
    # But first convert to a list, so that we can call this function
    # with an array too (in case of a single plexitude)
    edges = list(edges)
    for edg in olist.collectOnLength(edges).itervalues():
        fa = asarray(edg)
        nplex = fa.shape[1]
        if e is None:
            coords = x[:,fa,:]
            elems = None
        else:
            coords = x
            elems = e[:,fa]
        pf.debug("COORDS SHAPE: %s" % str(coords.shape),pf.DEBUG.DRAW)
        if elems is not None:
            pf.debug("ELEMS SHAPE: %s" % str(elems.shape),pf.DEBUG.DRAW)
        if color is not None and color.ndim==3:
            pf.debug("COLOR SHAPE BEFORE EXTRACTING: %s" % str(color.shape),pf.DEBUG.DRAW)
            # select the colors of the matching points
            color = color[:,fa,:]
            pf.debug("COLOR SHAPE AFTER EXTRACTING: %s" % str(color.shape),pf.DEBUG.DRAW)

        if eltype == 'line3':
            if 'line3' in pf.cfg['draw/quadline']:
                drawQuadraticCurves(coords,elems,color)
            else:
                draw_faces(coords,elems,color,1.0,objtype=GL.GL_LINE_STRIP)
        else:
            draw_faces(coords,elems,color,1.0)


def drawFaces(x,e,faces,eltype,color=None,alpha=1.0,texture=None,texc=None,normals=None,lighting=False,avgnormals=False):
    """Draw the faces of a geometry.

    This function draws the faces of a geometry collection, usually of a higher
    dimensionality (i.c. a volume).
    The faces are identified by a constant indices into all element vertices.

    The geometry is specified by x or (x,e)
    The faces are specified by a list of lists. Each list defines a single
    face of the solid, in local vertex numbers (0..nplex-1). The faces are
    sorted and collected according to their plexitude before drawing them.
    """
    pf.debug("drawFaces",pf.DEBUG.DRAW)
    # We may have faces with different plexitudes!
    # We collect them according to plexitude.
    # But first convert to a list, so that we can call this function
    # with an array too (in case of a single plexitude)
    faces = list(faces)
    for fac in olist.collectOnLength(faces).itervalues():
        fa = asarray(fac)
        nplex = fa.shape[1]
        if e is None:
            coords = x[:,fa,:]
            elems = None
        else:
            coords = x
            elems = e[:,fa]
        pf.debug("COORDS SHAPE: %s" % str(coords.shape),pf.DEBUG.DRAW)
        if elems is not None:
            pf.debug("ELEMS SHAPE: %s" % str(elems.shape),pf.DEBUG.DRAW)
        if color is not None:
            pf.debug("COLOR SHAPE: %s" % str(color.shape),pf.DEBUG.DRAW)
            # select the colors of the matching points
            if color.ndim==3:
                color = color[:,fa,:]
                pf.debug("COLOR SHAPE AFTER EXTRACTING: %s" % str(color.shape),pf.DEBUG.DRAW)
        if eltype in pf.cfg['draw/quadsurf'] and eltype in _nurbs_elements:
            #print "USING QUADSURF"
            drawQuadraticSurfaces(coords,elems,color)
        else:
            #print "USING POLYGON"
            draw_faces(coords,elems,color,alpha,texture,texc,normals,lighting,avgnormals)


def drawAtPoints(x,mark,color=None):
    """Draw a copy of a 3D actor mark at all points in x.

    x is a (npoints,3) shaped array of coordinates.
    mark is any 3D Actor having a display list attribute.
    If color is given it is an (npoints,3) array of RGB values. It only
    makes sense if the mark was created without color!
    """
    for i,xi in enumerate(x):
        if color is not None:
            GL.glColor3fv(color[i])
        GL.glPushMatrix()
        GL.glTranslatef(*xi)
        GL.glCallList(mark)
        GL.glPopMatrix()


def Shape(a):
    """Return the shape of an array or None"""
    try:
        return a.shape
    except:
        return None


# CANDIDATE FOR C LIBRARY
def averageDirection(a,tol=0.5):
    """Averages vectors that have almost the same direction.

    a is a 2-dim array where rows are normalized directions.
    All vectors that have nearly the same direction are replaced by the
    average of these.

    tol is a value specifying how close the directions should be in order
    to be averaged. A vector b is considered to be the same direction as a
    if its projection on a is longer than the tolerance value. The default
    The default is to have a direction that is nearly the same.
    a is a 2-dim array

    This changes a inplace!
    """
    if a.ndim != 2:
        raise ValueError,"array should be 2-dimensional!"
    nrow = a.shape[0]
    cnt = zeros(nrow,dtype=int32)
    while cnt.min() == 0:
        # select unhandled vectors
        w = where(cnt==0)
        nw = a[w]
        # find all those with direction close to the first
        wok = where(dotpr(nw[0],nw) >= tol)
        wi = w[0][wok[0]]
        # replace each with the sum and remember how many we have
        cnt[wi] = len(wi)
        a[wi] = a[wi].sum(axis=0)

    # divide by the sum to get average
    a /= cnt.reshape(-1,1)

    return a


def averageDirectionsOneNode(d,wi,tol):
    k = d[wi]
    misc.averageDirection(k,tol)
    d[wi] = k


# CANDIDATE FOR C LIBRARY
def nodalSum2(val,elems,tol):
    """Compute the nodal sum of values defined on elements.

    val   : (nelems,nplex,nval) values at points of elements.
    elems : (nelems,nplex) nodal ids of points of elements.
    work  : a work space (unused)

    The return value is a tuple of two arrays:
    res:
    cnt
    On return each value is replaced with the sum of values at that node.
    """
    print("!!!!nodalSum2!!!!")
    val[:] = normalize(val)
    import timer
    from pyformex.lib import misc
    t = timer.Timer()
    nodes = unique(elems)
    t.reset()
    [ averageDirectionsOneNode(val,where(elems==i),tol) for i in nodes ]
    ## for i in nodes:
    ##     wi = where(elems==i)
    ##     k = val[wi]
    ##     #averageDirection(k,tol)
    ##     misc.averageDirection(k,tol)
    ##     val[wi] = k
    print("TIME %s \n" % t.seconds())


def drawCube(s,color=[red,cyan,green,magenta,blue,yellow]):
    """Draws a centered cube with side 2*s and colored faces.

    Colors are specified in the order [FRONT,BACK,RIGHT,LEFT,TOP,BOTTOM].
    """
    vertices = [[s,s,s],[-s,s,s],[-s,-s,s],[s,-s,s],[s,s,-s],[-s,s,-s],[-s,-s,-s],[s,-s,-s]]
    planes = [[0,1,2,3],[4,5,6,7],[0,3,7,4],[1,2,6,5],[0,1,5,4],[3,2,6,7]]
    GL.glBegin(GL.GL_QUADS)
    for i in range(6):
        #glNormal3d(0,1,0);
        GL.glColor(*color[i])
        for j in planes[i]:
            GL.glVertex3f(*vertices[j])
    GL.glEnd()


def drawSphere(s,color=cyan,ndiv=8):
    """Draws a centered sphere with radius s in given color."""
    quad = GLU.gluNewQuadric()
    GLU.gluQuadricNormals(quad, GLU.GLU_SMOOTH)
    GL.glColor(*color)
    GLU.gluSphere(quad,s,ndiv,ndiv)


def drawGridLines(x0,x1,nx):
    """Draw a 3D rectangular grid of lines.

    A grid of lines parallel to the axes is drawn in the domain bounded
    by the rectangular box [x0,x1]. The grid has nx divisions in the axis
    directions, thus lines will be drawn at nx[i]+1 positions in direction i.
    If nx[i] == 0, lines are only drawn for the initial coordinate x0.
    Thus nx=(0,2,3) results in a grid of 3x4 lines in the plane // (y,z) at
    coordinate x=x0[0].
    """
    x0 = asarray(x0)
    x1 = asarray(x1)
    nx = asarray(nx)

    for i in range(3):
        if nx[i] > 0:
            axes = (asarray([1,2]) + i) % 3
            base = simple.regularGrid(x0[axes],x1[axes],nx[axes]).reshape((-1,2))
            x = zeros((base.shape[0],2,3))
            x[:,0,axes] = base
            x[:,1,axes] = base
            x[:,0,i] = x0[i]
            x[:,1,i] = x1[i]
            GL.glBegin(GL.GL_LINES)
            for p in x.reshape((-1,3)):
                GL.glVertex3fv(p)
            GL.glEnd()


def drawGridPlanes(x0,x1,nx):
    """Draw a 3D rectangular grid of planes.

    A grid of planes parallel to the axes is drawn in the domain bounded
    by the rectangular box [x0,x1]. The grid has nx divisions in the axis
    directions, thus planes will be drawn at nx[i]+1 positions in direction i.
    If nx[i] == 0, planes are only drawn for the initial coordinate x0.
    Thus nx=(0,2,3) results in a grid of 3x4 planes // x and
    one plane // (y,z) at coordinate x=x0[0].
    """
    x0 = asarray(x0)
    x1 = asarray(x1)
    nx = asarray(nx)

    for i in range(3):
        axes = (asarray([1,2]) + i) % 3
        if all(nx[axes] > 0):
            j,k = axes
            base = simple.regularGrid(x0[i],x1[i],nx[i]).ravel()
            x = zeros((base.shape[0],4,3))
            corners = array([x0[axes],[x1[j],x0[k]],x1[axes],[x0[j],x1[k]]])
            for j in range(4):
                x[:,j,i] = base
            x[:,:,axes] = corners
            GL.glBegin(GL.GL_QUADS)
            for p in x.reshape((-1,3)):
                GL.glVertex3fv(p)
            GL.glEnd()


######################## Picking functions ########################

def pickPolygons(x,e=None,objtype=-1):
    """Mimics drawPolygons for picking purposes."""
    x = x.astype(float32)
    if e is not None:
        e = e.astype(int32)
    if e is None:
        drawgl.pick_polygons(x,objtype)
    else:
        drawgl.pick_polygon_elems(x,e,objtype)


def pickPolygonEdges(x,e,edg):
    utils.warn("pickPolygonEdges IS NOT IMPLEMENTED YET!")


def pickPoints(x):
    x = x.reshape((-1,1,3))
    pickPolygons(x)



### Settings ###############################################
#
# These are not intended for users but to sanitize user input
#

def saneLineWidth(linewidth):
    """Return a sane value for the line width.

    A sane value is one that will be usable by the draw method.
    It can be either of the following:

    - a float value indicating the line width to be set by draw()
    - None: indicating that the default line width is to be used

    The line width is used in wireframe mode if plex > 1
    and in rendering mode if plex==2.
    """
    if linewidth is not None:
        linewidth = float(linewidth)
    return linewidth


def saneLineStipple(stipple):
    """Return a sane line stipple tuple.

    A line stipple tuple is a tuple (factor,pattern) where
    pattern defines which pixels are on or off (maximum 16 bits),
    factor is a multiplier for each bit.
    """
    try:
        stipple = map(int,stipple)
    except:
        stipple = None
    return stipple


def saneColor(color=None):
    """Return a sane color array derived from the input color.

    A sane color is one that will be usable by the draw method.
    The input value of color can be either of the following:

    - None: indicates that the default color will be used,
    - a single color value in a format accepted by colors.GLcolor,
    - a tuple or list of such colors,
    - an (3,) shaped array of RGB values, ranging from 0.0 to 1.0,
    - an (n,3) shaped array of RGB values,
    - an (n,) shaped array of integer color indices.

    The return value is one of the following:
    - None, indicating no color (current color will be used),
    - a float array with shape (3,), indicating a single color,
    - a float array with shape (n,3), holding a collection of colors,
    - an integer array with shape (n,), holding color index values.

    !! Note that a single color can not be specified as integer RGB values.
    A single list of integers will be interpreted as a color index !
    Turning the single color into a list with one item will work though.
    [[ 0, 0, 255 ]] will be the same as [ 'blue' ], while
    [ 0,0,255 ] would be a color index with 3 values.
    """
    if color is None:
        # no color: use canvas color
        return None

    # detect color index
    try:
        c = asarray(color)
        if c.dtype.kind == 'i':
            # We have a color index
            return c
    except:
        pass

    # not a color index: it must be colors
    try:
        color = GLcolor(color)
    except ValueError:

        try:
            color = map(GLcolor,color)
        except ValueError:
            pass

    # Convert to array
    try:
        # REMOVED THE SQUEEZE: MAY BREAK SOME THINGS !!!
        color = asarray(color)#.squeeze()
        if color.dtype.kind == 'f' and color.shape[-1] == 3:
            # Looks like we have a sane color array
            return color.astype(float32)
    except:
        pass

    return None


def saneColorArray(color,shape):
    """Makes sure the shape of the color array is compatible with shape.

    shape is an (nelems,nplex) tuple
    A compatible color.shape is equal to shape or has either or both of its
    dimensions equal to 1.
    Compatibility is enforced in the following way:
    - if color.shape[1] != nplex and color.shape[1] != 1: take out first
      plane in direction 1
    - if color.shape[0] != nelems and color.shape[0] != 1: repeat the plane
      in direction 0 nelems times
    """
    color = asarray(color)
    if color.ndim == 1:
        return color
    if color.ndim == 3:
        if color.shape[1] > 1 and color.shape[1] != shape[1]:
            color = color[:,0]
    if color.shape[0] > 1 and color.shape[0] != shape[0]:
        color = resize(color,(shape[0],color.shape[1]))
    return color


def saneColorSet(color=None,colormap=None,shape=(1,),canvas=None):
    """Return a sane set of colors.

    A sane set of colors is one that guarantees correct use by the
    draw functions. This means either
    - no color (None)
    - a single color
    - at least as many colors as the shape argument specifies
    - a color index and a color map with enough colors to satisfy the index.
    The return value is a tuple color,colormap. colormap will be None,
    unless color is an integer array, meaning a color index.
    """
    if isInt(shape):  # make sure we get a tuple
        shape = (shape,)
    color = saneColor(color)
    if color is not None:
        pf.debug("SANECOLORSET: color %s, shape %s" % (color.shape,shape),pf.DEBUG.DRAW)
        if color.dtype.kind == 'i':
            ncolors = color.max()+1
            if colormap is None:
                if canvas:
                    colormap = canvas.settings.colormap
                else:
                    colormap = pf.canvas.settings.colormap
                    #cfg['canvas/colormap']
            colormap = saneColor(colormap)
            colormap = saneColorArray(colormap,(ncolors,))
        else:
            color = saneColorArray(color,shape)
            colormap = None

        pf.debug("SANECOLORSET RESULT: %s" % str(color.shape),pf.DEBUG.DRAW)
    return color,colormap


### Drawable Objects ###############################################

class Drawable(object):
    """A Drawable is anything that can be drawn on the OpenGL Canvas.

    This defines the interface for all drawbale objects, but does not
    implement any drawable objects.
    Drawable objects should be instantiated from the derived classes.
    Currently, we have the following derived classes:
      Actor: a 3-D object positioned and oriented in the 3D scene. Defined
             in actors.py.
      Mark: an object positioned in 3D scene but not undergoing the camera
             axis rotations and translations. It will always appear the same
             to the viewer, but will move over the screen according to its
             3D position. Defined in marks.py.
      Decor: an object drawn in 2D viewport coordinates. It will unchangeably
             stick on the viewport until removed. Defined in decors.py.

    A Drawable subclass should minimally reimplement the following methods:
      bbox(): return the actors bounding box.
      nelems(): return the number of elements of the actor.
      drawGL(mode): to draw the object. Takes a mode argument so the
        drawing function can act differently depending on the rendering mode.
        There are currently 5 modes:
           wireframe, flat, smooth, flatwire, smoothwire.
        drawGL should only contain OpenGL calls that are allowed inside a
        display list. This may include calling the display list of another
        actor but *not* creating a new display list.
    """

    def __init__(self,nolight=False,ontop=False,**kargs):
        self.list = None
        self.listmode = None # stores mode of self.list: wireframe/smooth/flat
        self.mode = None # subclasses can set a persistent drawing mode
        self.opak = True
        self.nolight = nolight
        self.ontop = ontop
        self.extra = [] # list of dependent Drawables

    def drawGL(self,**kargs):
        """Perform the OpenGL drawing functions to display the actor."""
        pass

    def pickGL(self,**kargs):
        """Mimick the OpenGL drawing functions to pick (from) the actor."""
        pass

    def redraw(self,**kargs):
        self.draw(**kargs)

    def draw(self,**kargs):
        self.prepare_list(**kargs)
        self.use_list()

    def prepare_list(self,**kargs):
        mode = self.mode
        if mode is None:
            if 'mode' in kargs:
                mode = kargs['mode']
            else:
                canvas = kargs.get('canvas',pf.canvas)
                mode = canvas.rendermode

        if mode.endswith('wire'):
            mode = mode[:-4]

        if self.list is None or mode != self.listmode:
            kargs['mode'] = mode
            self.delete_list()
            self.list = self.create_list(**kargs)

    def use_list(self):
        if self.list:
            GL.glCallList(self.list)
        for i in self.extra:
            i.use_list()

    def create_list(self,**kargs):
        displist = GL.glGenLists(1)
        GL.glNewList(displist,GL.GL_COMPILE)
        ok = False
        try:
            if self.nolight:
                GL.glDisable(GL.GL_LIGHTING)
            if self.ontop:
                GL.glDepthFunc(GL.GL_ALWAYS)
            self.drawGL(**kargs)
            ok = True
        finally:
            if not ok:
                pf.debug("Error while creating a display list",pf.DEBUG.DRAW)
                displist = None
            GL.glEndList()
        self.listmode = kargs['mode']
        return displist

    def delete_list(self):
        if self.list:
            GL.glDeleteLists(self.list,1)
        self.list = None


    def setLineWidth(self,linewidth):
        """Set the linewidth of the Drawable."""
        self.linewidth = saneLineWidth(linewidth)

    def setLineStipple(self,linestipple):
        """Set the linewidth of the Drawable."""
        self.linestipple = saneLineStipple(linestipple)

    def setColor(self,color=None,colormap=None,ncolors=1):
        """Set the color of the Drawable."""
        self.color,self.colormap = saneColorSet(color,colormap,shape=(ncolors,))

    def setTexture(self,texture):
        """Set the texture data of the Drawable."""
        if texture is not None:
            if not isinstance(texture,Texture):
                try:
                    texture = Texture(texture)
                except:
                    texture = None
        self.texture = texture


### Textures ###############################################

class Texture(object):
    """An OpenGL 2D Texture.

    image: raw image data (unsigned byte RGBA data)
    """

    def __init__(self,image,flip=False):
        self.tex = None
        image = asarray(image)
        # print "Texture: type %s, size %s" % (image.dtype, image.shape)
        image = require(image,dtype='ubyte',requirements='C')
        # print "Converted to: type %s, size %s" % (image.dtype, image.shape)
        ny,nx = image.shape[:2]

        # Generate a texture id
        tex = GL.glGenTextures(1)
        # Make our new texture the current 2D texture
        GL.glEnable(GL.GL_TEXTURE_2D)
        #GL.glTexEnvf(GL.GL_TEXTURE_ENV,GL.GL_TEXTURE_ENV_MODE,GL.GL_MODULATE)
        GL.glBindTexture(GL.GL_TEXTURE_2D,tex)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT,1)
        # Copy the texture data into the current texture
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,4,nx,ny,0,
                        GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,image)
        self.tex = tex


    def __del__(self):
        if self.tex:
            GL.glDeleteTextures(self.tex)

### End
