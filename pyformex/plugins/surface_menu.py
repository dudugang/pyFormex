# $Id$
##
##  This file is part of pyFormex 0.8.1 Release Wed Dec  9 11:27:53 2009
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Homepage: http://pyformex.org   (http://pyformex.berlios.de)
##  Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
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

"""surface_menu.py

Surface operations plugin menu for pyFormex.
"""

import pyformex as GD
from gui import actors,colors,decors,widgets,menu
from gui.colorscale import ColorScale,ColorLegend
from gui.draw import *
from plugins.surface import *
from plugins.objects import *
from plugins import plot2d,formex_menu,mesh_menu,surface_abq
import simple
from plugins.tools import Plane
from pyformex.arraytools import niceLogSize

import os, timer

##################### selection and annotations ##########################


def draw_edge_numbers(n):
    """Draw the edge numbers of the named surface."""
    S = named(n)
    F = Formex(S.coords[S.edges]) 
    return drawNumbers(F,color=colors.red)

def draw_node_numbers(n):
    """Draw the node numbers of the named surface."""
    S = named(n)
    F = Formex(S.coords) 
    return drawNumbers(F,color=colors.blue)

def draw_normals(n):
    S = named(n)
    C = S.centroids()
    A,N = S.areaNormals()
    D = C + sqrt(A).reshape((-1,1))*N
    F = connect([Formex(C),Formex(D)])
    return draw(F,color='red')

def draw_avg_normals(n):
    S = named(n)
    C = S.coords
    N = S.avgVertexNormals()
    try:
        siz = float(GD.cfg['mark/avgnormalsize'])
    except:
        siz = 0.05 * C.dsize()
    D = C + siz * N
    F = connect([Formex(C),Formex(D)])
    return draw(F,color='orange')
    
selection = DrawableObjects(clas=TriSurface)
ntoggles = len(selection.annotations)
def toggleEdgeNumbers():
    selection.toggleAnnotation(0+ntoggles)
def toggleNodeNumbers():
    selection.toggleAnnotation(1+ntoggles)
def toggleNormals():
    selection.toggleAnnotation(2+ntoggles)
def toggleAvgNormals():
    selection.toggleAnnotation(3+ntoggles)


selection.annotations.extend([[draw_edge_numbers,False],
                              [draw_node_numbers,False],
                              [draw_normals,False],
                              [draw_avg_normals,False],
                              ])

##################### select, read and write ##########################

def read_Surface(fn,exportName=True):
    GD.message("Reading file %s" % fn)
    t = timer.Timer()
    S = TriSurface.read(fn)
    GD.message("Read surface with %d vertices, %d edges, %d triangles in %s seconds" % (S.ncoords(),S.nedges(),S.nelems(),t.seconds()))
    if exportName:
        name = utils.projectName(fn)
        export({name:S})
        selection.set([name])
    return S


def readSelection(select=True,draw=True,multi=True):
    """Read a Surface (or list) from asked file name(s).

    If select is True (default), this becomes the current selection.
    If select and draw are True (default), the selection is drawn.
    """
    types = [ 'Surface Files (*.gts *.stl *.off *.neu *.smesh)', 'All Files (*)' ]
    fn = askFilename(GD.cfg['workdir'],types,multi=multi)
    if fn:
        if not multi:
            fn = [ fn ]
        chdir(fn[0])
        names = map(utils.projectName,fn)
        GD.GUI.setBusy()
        surfaces = [ read_Surface(f,False) for f in fn ]
        for i,S in enumerate(surfaces):
            S.setProp(i)
        GD.GUI.setBusy(False)
        export(dict(zip(names,surfaces)))
        if select:
            GD.message("Set selection to %s" % str(names))
            selection.set(names)
            if draw:
                if max([named(s).nfaces() for s in selection]) < 100000 or ack("""
This is a large model and drawing could take quite some time.
You should consider coarsening the model before drawing it.
Shall I proceed with the drawing now?
"""):
                    selection.draw()
    return fn
    

def printSize():
    for s in selection.names:
        S = named(s)
        GD.message("Surface %s has %d vertices, %s edges and %d faces" %
                   (s,S.ncoords(),S.nedges(),S.nelems()))

def printType():
    for s in selection.names:
        S = named(s)
        if S.isClosedManifold():
            GD.message("Surface %s is a closed manifold" % s)
        elif S.isManifold():
            GD.message("Surface %s is an open manifold" % s)
        else:
            GD.message("Surface %s is not a manifold" % s)

def printArea():
    for s in selection.names:
        S = named(s)
        GD.message("Surface %s has area %s" % (s,S.area()))

def printVolume():
    for s in selection.names:
        S = named(s)
        GD.message("Surface %s has volume %s" % (s,S.volume()))


def printStats():
    for s in selection.names:
        S = named(s)
        GD.message("Statistics for surface %s" % s)
        print(S.stats())

def toFormex(suffix=''):
    """Transform the selection to Formices.

    If a suffix is given, the Formices are stored with names equal to the
    surface names plus the suffix, else, the surface names will be used
    (and the surfaces will thus be cleared from memory).
    """
    if not selection.check():
        selection.ask()

    if not selection.names:
        return

    newnames = selection.names
    if suffix:
        newnames = [ n + suffix for n in newnames ]

    newvalues = [ named(n).toFormex() for n in newnames ]
    export2(newnames,newvalues)

    if not suffix:
        selection.clear()
    formex_menu.selection.set(newnames)
    clear()
    formex_menu.selection.draw()
    

def fromFormex(suffix=''):
    """Transform the Formex selection to TriSurfaces.

    If a suffix is given, the TriSurfaces are stored with names equal to the
    Formex names plus the suffix, else, the Formex names will be used
    (and the Formices will thus be cleared from memory).
    """
    if not formex_menu.selection.check():
        formex_menu.selection.ask()

    if not formex_menu.selection.names:
        return

    names = formex_menu.selection.names
    formices = [ named(n) for n in names ]
    if suffix:
        names = [ n + suffix for n in names ]

    t = timer.Timer()
    surfaces =  dict([ (n,TriSurface(F)) for n,F in zip(names,formices) if F.nplex() == 3])
    print("Converted in %s seconds" % t.seconds())
    print(surfaces.keys())
    export(surfaces)

    if not suffix:
        formex_menu.selection.clear()
    selection.set(surfaces.keys())


def toMesh(suffix=''):
    """Transform the selection to Meshes.

    If a suffix is given, the Meshes are stored with names equal to the
    surface names plus the suffix, else, the surface names will be used
    (and the surfaces will thus be cleared from memory).
    """
    if not selection.check():
        selection.ask()

    if not selection.names:
        return

    newnames = selection.names
    if suffix:
        newnames = [ n + suffix for n in newnames ]

    newvalues = [ named(n).toMesh() for n in newnames ]
    export2(newnames,newvalues)

    if not suffix:
        selection.clear()
    mesh_menu.selection.set(newnames)
    clear()
    mesh_menu.selection.draw()
    

def fromMesh(suffix=''):
    """Transform the Mesh selection to TriSurfaces.

    If a suffix is given, the TriSurfaces are stored with names equal to the
    Mesh names plus the suffix, else, the Mesh names will be used
    (and the Meshes will thus be cleared from memory).
    """
    if not mesh_menu.selection.check():
        mesh_menu.selection.ask()

    if not mesh_menu.selection.names:
        return

    names = mesh_menu.selection.names
    meshes = [ named(n) for n in names ]
    if suffix:
        names = [ n + suffix for n in names ]

    t = timer.Timer()
    surfaces =  dict([ (n,TriSurface(M)) for n,M in zip(names,meshes) if M.eltype == 'tri3'])
    print("Converted in %s seconds" % t.seconds())
    print(surfaces.keys())
    export(surfaces)

    if not suffix:
        mesh_menu.selection.clear()
    selection.set(surfaces.keys())


def toggle_shrink():
    """Toggle the shrink mode"""
    if selection.shrink is None:
        selection.shrink = 0.8
    else:
        selection.shrink = None
    selection.draw()


def toggle_auto_draw():
    global autodraw
    autodraw = not autodraw


## def convert_stl_to_off():
##     """Converts an stl to off format without reading it into pyFormex."""
##     fn = askFilename(GD.cfg['workdir'],"STL files (*.stl)")
##     if fn:     
##         return surface.stl_to_off(fn,sanitize=False)


## def sanitize_stl_to_off():
##     """Sanitizes an stl to off format without reading it into pyFormex."""
##     fn = askFilename(GD.cfg['workdir'],"STL files (*.stl)")
##     if fn:     
##         return surface.stl_to_off(fn,sanitize=True)




def write_surface(types=['surface','gts','stl','off','neu','smesh']):
    F = selection.check(single=True)
    if F:
        if type(types) == str:
            types = [ types ]
        types = map(utils.fileDescription,types)
        fn = askNewFilename(GD.cfg['workdir'],types)
        if fn:
            GD.message("Exporting surface model to %s" % fn)
            GD.GUI.setBusy()
            F.write(fn)   
            GD.GUI.setBusy(False)

#
# Operations with surface type, border, ...
#
def showBorder():
    S = selection.check(single=True)
    if S:
        print(S.nEdgeConnected())
        print(S.borderEdges())
        F = S.border()
        if F.nelems() > 0:
            draw(F,color='red',linewidth=3)
            export({'border':F})
        else:
            warning("The surface %s does not have a border" % selection[0])

def checkBorder():
    S = selection.check(single=True)
    if S:
        border = S.checkBorder()
        if border is None:
            print("The surface has no border.")
        else:
            closed,loop = border
            print("The border is of type %s" % closed)
            print("The sorted border edges are: %s" % loop)


def fillBorder():
    S = selection.check(single=True)
    if S:
        options = ["Cancel","Existing points","New points"]
        res = ask("Which method ?",options)
        if res == options[1]: 
            S.fillBorder(0)
        elif res == options[2]: 
            S.fillBorder(1)
        selection.draw()
        

def fillHoles():
    """Fill the holes in the selected surface."""
    S = selection.check(single=True)
    if S:
        border_elems = S.edges[S.borderEdges()]
        if border_elems.size != 0:
            # partition borders
            print(border_elems)
            border_elems = partitionSegmentedCurve(border_elems)
            print(border_elems)
            
            # draw borders in new viewport
            R = GD.canvas.camera.getRot()
            P = GD.canvas.camera.perspective
            layout(2)
            viewport(1)
            GD.canvas.camera.rot = R
            toolbar.setPerspective(P)
            for i,elems in enumerate(border_elems):
                draw(Formex(S.coords[elems]))
            zoomAll()
            # pick borders for which the hole must be filled
            info("PICK HOLES WHICH HAVE TO BE FILLED.")
            picked = pick(mode='actor')
            layout(1)
            # fill the holes
            triangles = empty((0,3,),dtype=int)
            if picked.has_key(-1):
                for i in picked[-1]:
                    triangles = row_stack([triangles,fillHole(S.coords,border_elems[int(i)])])
                T = TriSurface(S.coords,triangles)
                S.append(T)
                draw(T,color='red',bbox=None)
            else:
                warning("No borders were picked.")
        else:
            warning("The surface %s does not have a border." % selection[0])


# Selectable values for display/histogram
# Each key is a description of a result
# Each value consist of a tuple
#  - function to calculate the values
#  - domain to display: True to display on edges, False to display on elements

SelectableStatsValues = {
    'Facet Area': (TriSurface.facetArea,False),
    'Aspect ratio': (TriSurface.aspectRatio,False),
    'Smallest altitude': (TriSurface.smallestAltitude,False),
    'Longest edge': (TriSurface.longestEdge,False),
    'Shortest edge': (TriSurface.shortestEdge,False),
    'Number of node adjacent elements': (TriSurface.nNodeAdjacent,False),
    'Number of edge adjacent elements': (TriSurface.nEdgeAdjacent,False),
    'Edge angle': (TriSurface.edgeAngles,True),
    'Number of connected elements': (TriSurface.nEdgeConnected,True),
    }

def showHistogram(key,val,cumulative):
    y,x = plot2d.createHistogram(val,cumulative=cumulative)
    return plot2d.showHistogram(x,y,key)

    
def showStatistics():
    S = selection.check(single=True)
    if S:
        dispmodes = ['On Domain','Histogram','Cumulative Histogram']
        keys = SelectableStatsValues.keys()
        keys.sort()
        res  = askItems([('Select Value',None,'select',keys),
                         ('Display Mode',None,'select',dispmodes)
                         ])
        GD.app.processEvents()
        if res:
            key = res['Select Value']
            func,onEdges = SelectableStatsValues[key]
            val = func(S)
            mode = res['Display Mode']
            if mode == 'On Domain':
                showSurfaceValue(S,key,val,onEdges)
            else: 
                showHistogram(key,val,cumulative= mode.startswith('Cumul'))


def showSurfaceValue(S,txt,val,onEdges):
    val = nan_to_num(val)
    mi,ma = val.min(),val.max()
    print(mi,ma)
    # Test: replace min with max
    dec = min(abs(mi),abs(ma))
    print(dec)
    if dec > 0.0:
        dec = max(0,3-int(log10(dec)))
    else:
        dec = 2
    # create a colorscale and draw the colorlegend
    CS = ColorScale('RAINBOW',mi,ma,0.5*(mi+ma),1.)
    cval = array(map(CS.color,ravel(val)))
    cval = cval.reshape(append(val.shape,cval.shape[-1]))
    clear()
    if onEdges:
        F = Formex(S.coords[S.edges])
        draw(F,color=cval)#,linewidth=2)
    else:
        draw(S,color=cval)
    CL = ColorLegend(CS,100)
    CLA = decors.ColorLegend(CL,10,10,30,200,dec=dec) 
    GD.canvas.addDecoration(CLA)
    drawtext(txt,10,230,'hv18')


def showCurvature():
    S = selection.check(single=True)
    if S:
        dispmodes = ['On Domain','Histogram','Cumulative Histogram']
        res  = askItems([('Neighbourhood',1),
                         ('Select Value',None,'select',['Gaussian curvature','Mean curvature','Shape index','Curvedness']),
                         ('Display Mode',None,'select',dispmodes)
                         ])        
        if res:
            key = res['Select Value']
            curv = S.curvature(neighbours=res['Neighbourhood'])
            val = {'Gaussian curvature':0,'Mean curvature':1,'Shape index':2,'Curvedness':3}
            val = curv[val[key]]
            mode = res['Display Mode']
            if mode == 'On Domain':
                val = val[S.elems]
                showSurfaceValue(S,key,val,False)
                smoothwire()
                lights(False)
            else: 
                showHistogram(key,val,cumulative= mode.startswith('Cumul'))


def colorByFront():
    S = selection.check(single=True)
    if S:
        res  = askItems([('front type',None,'select',['node','edge']),
                         ('number of colors',-1),
                         ('front width',1),
                         ('start at',0),
                         ('first prop',0),
                         ])
        GD.app.processEvents()
        if res:
            selection.remember()
            t = timer.Timer()
            ftype = res['front type']
            nwidth = res['front width']
            nsteps = nwidth * res['number of colors']
            startat = res['start at']
            firstprop = res['first prop']
            if ftype == 'node':
                p = S.walkNodeFront(nsteps=nsteps,startat=startat)
            else:
                p = S.walkEdgeFront(nsteps=nsteps,startat=startat)
            S.setProp(p/nwidth + firstprop)
            print("Colored in %s parts (%s seconds)" % (S.p.max()+1,t.seconds()))
            selection.draw()


def partitionByConnection():
    S = selection.check(single=True)
    if S:
        selection.remember()
        t = timer.Timer()
        S.p = S.partitionByConnection()
        print("Partitioned in %s parts (%s seconds)" % (S.p.max()+1,t.seconds()))
        selection.draw()


def partitionByAngle():
    S = selection.check(single=True)
    if S:
        res  = askItems([('angle',60.),('firstprop',1),('startat',0)])
        GD.app.processEvents()
        if res:
            selection.remember()
            t = timer.Timer()
            S.p = S.partitionByAngle(**res)
            print("Partitioned in %s parts (%s seconds)" % (S.p.max()+1,t.seconds()))
            selection.draw()
         
 

#############################################################################
# Transformation of the vertex coordinates (based on Coords)

#
# !! These functions could be made identical to those in Formex_menu
# !! (and thus could be unified) if the surface transfromations were not done
# !! inplace but returned a new surface instance instead.
#
            
def scaleSelection():
    """Scale the selection."""
    FL = selection.check()
    if FL:
        res = askItems([['scale',1.0]],
                       caption = 'Scaling Factor')
        if res:
            scale = float(res['scale'])
            selection.remember(True)
            for F in FL:
                F.scale(scale)
            selection.drawChanges()

            
def scale3Selection():
    """Scale the selection with 3 scale values."""
    FL = selection.check()
    if FL:
        res = askItems([['x-scale',1.0],['y-scale',1.0],['z-scale',1.0]],
                       caption = 'Scaling Factors')
        if res:
            scale = map(float,[res['%c-scale'%c] for c in 'xyz'])
            selection.remember(True)
            for F in FL:
                F.scale(scale)
            selection.drawChanges()


def translateSelection():
    """Translate the selection."""
    FL = selection.check()
    if FL:
        res = askItems([['direction',0],['distance','1.0']],
                       caption = 'Translation Parameters')
        if res:
            dir = int(res['direction'])
            dist = float(res['distance'])
            selection.remember(True)
            for F in FL:
                F.translate(dir,dist)
            selection.drawChanges()


def centerSelection():
    """Center the selection."""
    FL = selection.check()
    if FL:
        selection.remember(True)
        for F in FL:
            F.translate(-F.coords.center())
        selection.drawChanges()


def rotate(mode='global'):
    """Rotate the selection.

    mode is one of 'global','parallel','central','general'
    """
    FL = selection.check()
    if FL:
        if mode == 'global':
            res = askItems([['angle','90.0'],['axis',2]])
            if res:
                angle = float(res['angle'])
                axis = int(res['axis'])
                around = None
        elif mode == 'parallel':
            res = askItems([['angle','90.0'],['axis',2],['point','[0.0,0.0,0.0]']])
            if res:
                axis = int(res['axis'])
                angle = float(res['angle'])
                around = eval(res['point'])
        elif mode == 'central':
            res = askItems([['angle','90.0'],['axis','[0.0,0.0,0.0]']])
            if res:
                angle = float(res['angle'])
                axis = eval(res['axis'])
                around = None
        elif mode == 'general':
            res = askItems([['angle','90.0'],['axis','[0.0,0.0,0.0]'],['point','[0.0,0.0,0.0]']])
            if res:
                angle = float(res['angle'])
                axis = eval(res['axis'])
                around = eval(res['point'])
        if res:
            selection.remember(True)
            for F in FL:
                #print("ROTATE %s %s %s " % (angle,axis,around))
                F.rotate(angle,axis,around)
            selection.drawChanges()


def rotateGlobal():
    rotate('global')

def rotateParallel():
    rotate('parallel')

def rotateCentral():
    rotate('central')

def rotateGeneral():
    rotate('general')


def rollAxes():
    """Rotate the selection."""
    FL = selection.check()
    if FL:
        selection.remember(True)
        for F in FL:
            F.coords.rollAxes()
        selection.drawChanges()


def clip_surface():
    """Clip the stl model."""
    if not check_surface():
        return
    itemlist = [['axis',0],['begin',0.0],['end',1.0],['nodes','any']]
    res = askItems(itemlist,caption='Clipping Parameters')
    if res:
        updateGUI()
        nodes,elems = PF['old_surface'] = PF['surface']
        F = Formex(nodes[elems])
        bb = F.bbox()
        GD.message("Original bbox: %s" % bb) 
        xmi = bb[0][0]
        xma = bb[1][0]
        dx = xma-xmi
        axis = int(res[0][1])
        xc1 = xmi + float(res[1][1]) * dx
        xc2 = xmi + float(res[2][1]) * dx
        nodid = res[3][1]
        #print(nodid)
        clear()
        draw(F,color='yellow')
        w = F.test(nodes='any',dir=axis,min=xc1,max=xc2)
        F = F.clip(w)
        draw(F,color='red')


def clipSelection():
    """Clip the selection.
    
    The coords list is not changed.
    """
    FL = selection.check()
    if FL:
        res = askItems([['axis',0],['begin',0.0],['end',1.0],['nodes','all','select',['all','any','none']]],caption='Clipping Parameters')
        if res:
            bb = bbox(FL)
            axis = int(res['axis'])
            xmi = bb[0][axis]
            xma = bb[1][axis]
            dx = xma-xmi
            xc1 = xmi + float(res['begin']) * dx
            xc2 = xmi + float(res['end']) * dx
            selection.changeValues([ F.clip(F.test(nodes=res['nodes'],dir=axis,min=xc1,max=xc2)) for F in FL ])
            selection.drawChanges()


def cutAtPlane():
    """Cut the selection with a plane."""
    FL = selection.check()
    if not FL:
        return
    
    dsize = bbox(FL).dsize()
    esize = 10 ** (niceLogSize(dsize)-5)

    res = askItems([['Point',(0.0,0.0,0.0)],
                    ['Normal',(1.0,0.0,0.0)],
                    ['New props',[1,2,2,3,4,5,6]],
                    ['Side','positive', 'radio', ['positive','negative','both']],
                    ['Tolerance',esize],
                    ],caption = 'Define the cutting plane')
    if res:
        P = res['Point']
        N = res['Normal']
        p = res['New props']
        side = res['Side']
        atol = res['Tolerance']
        selection.remember(True)
        if side == 'both':
            G = [F.toFormex().cutWithPlane(P,N,side=side,atol=atol,newprops=p) for F in FL]
            G_pos = []
            G_neg  =[]
            for F in G:
                G_pos.append(TriSurface(F[0]))
                G_neg.append(TriSurface(F[1]))
            export(dict([('%s/pos' % n,g) for n,g in zip(selection,G_pos)]))
            export(dict([('%s/neg' % n,g) for n,g in zip(selection,G_neg)]))
            selection.set(['%s/pos' % n for n in selection] + ['%s/neg' % n for n in selection])
            selection.draw()
        else:
            [F.cutWithPlane(P,N,newprops=p,side=side,atol=atol) for F in FL]
            selection.drawChanges()


def cutSelectionByPlanes():
    """Cut the selection with one or more planes, which are already created."""
    S = selection.check(single=True)
    if S:
        res1 = widgets.Selection(listAll(clas=Plane),
                                'Known %sobjects' % selection.object_type(),
                                mode='multi',sort=True).getResult()
        if res1:
            res2 = askItems([['Tolerance',0.],
                    ['Color by', 'side', 'radio', ['side', 'element type']], 
                    ['Side','both', 'radio', ['positive','negative','both']]],
                    caption = 'Cutting parameters')
            if res2:
                planes = map(named, res1)
                p = [plane.P for plane in planes]
                n = [plane.n for plane in planes]
                atol = res2['Tolerance']
                color = res2['Color by']
                side = res2['Side']
                if color == 'element type':
                    newprops = [1,2,2,3,4,5,6]
                else:
                    newprops = None
                if side == 'both':
                    Spos, Sneg = S.toFormex().cutAtPlane(p,n,newprops=newprops,side=side,atol=atol)
                elif side == 'positive':
                    Spos = S.toFormex().cutAtPlane(p,n,newprops=newprops,side=side,atol=atol)
                    Sneg = Formex()
                elif side == 'negative':
                    Sneg = S.toFormex().cutAtPlane(p,n,newprops=newprops,side=side,atol=atol)
                    Spos = Formex()
                if Spos.nelems() !=0:
                    Spos = TriSurface(Spos)
                    if color == 'side':
                        Spos.setProp(2)
                else:
                    Spos = None
                if Sneg.nelems() != 0:
                    Sneg = TriSurface(Sneg)
                    if color == 'side':
                        Sneg.setProp(3)
                else:
                    Sneg = None
                name = selection.names[0]
                export({name+"/pos":Spos})
                export({name+"/neg":Sneg})
                selection.set([name+"/pos",name+"/neg"]+res1)
                selection.draw()


def intersectWithPlane():
    """Intersect the selection with a plane."""
    FL = selection.check()
    res = askItems([['Name','__auto__'],
                    ['Point',(0.0,0.0,0.0)],
                    ['Normal',(1.0,0.0,0.0)],
                    ],caption = 'Define the cutting plane')
    if res:
        name = res['Name']
        P = res['Point']
        N = res['Normal']
        G = [F.toFormex().intersectionLinesWithPlane(P,N) for F in FL]
        draw(G,color='red',linewidth=3)
        export(dict([('%s/%s' % (n,name),g) for n,g in zip(selection,G)])) 


def sliceIt():
    """Slice the surface to a sequence of cross sections."""
    S = selection.check(single=True)
    res = askItems([['Direction',0],
                    ['# slices',10],
                   ],caption = 'Define the slicing planes')
    if res:
        axis = res['Direction']
        nslices = res['# slices']
        bb = S.bbox()
        xmin,xmax = bb[:,axis]
        dx =  (xmax-xmin) / nslices
        x = arange(nslices+1) * dx
        N = unitVector(axis)
        #print(N)
        P = [ bb[0]+N*s for s in x ]
        G = [S.toFormex().intersectionLinesWithPlane(Pi,N) for Pi in P]
        #[ G.setProp(i) for i,G in enumerate(G) ]
        G = Formex.concatenate(G)
        draw(G,color='red',linewidth=3)
        export({'%s/slices%s' % (selection[0],axis):G}) 


##################  Smooth the selected surface #############################

def smoothLowPass():
    """Smooth the selected surface using a low-pass filter."""
    S = selection.check(single=True)
    if S:
        res = askItems([('lambda_value',0.5),
                ('n_iterations',2)],'Low-pass filter')
        if res:
            if not 0.0 <= res['lambda_value'] <= 1.0:
                warning("Lambda should be between 0 and 1.")
                return
            if not mod(res['n_iterations'],2) == 0:
                warning("An even number of iterations is required.")
                return
            selection.remember(True)
            S.smoothLowPass(res['n_iterations'],res['lambda_value'])
            selection.drawChanges()


def smoothLaplaceHC():
    """Smooth the selected surface using a Laplace filter and HC algorithm."""
    S = selection.check(single=True)
    if S:
        res = askItems([('lambda_value',0.5),
                ('n_iterations',2),('alpha',0.),('beta',0.2)],'Laplace filter and HC algorithm')
        if res:
            if not 0.0 <= res['lambda_value'] <= 1.0:
                warning("Lambda should be between 0 and 1.")
                return
            if not 0.0 <= res['alpha'] <= 1.0:
                warning("Alpha should be between 0 and 1.")
                return
            if not 0.0 <= res['beta'] <= 1.0:
                warning("Beta should be between 0 and 1.")
                return            
            selection.remember(True)
            S.smoothLaplaceHC(res['n_iterations'],res['lambda_value'],res['alpha'],res['beta'])
            selection.drawChanges()


###################################################################
########### The following functions are in need of a make-over


def create_tetgen_volume():
    """Generate a volume tetraeder mesh inside an stl surface."""
    types = [ 'STL/OFF Files (*.stl *.off)', 'All Files (*)' ]
    fn = askFilename(GD.cfg['workdir'],types)
    if os.path.exists(fn):
        sta,out = utils.runCommand('tetgen -z %s' % fn)
        GD.message(out)


def flytru_stl():
    """Fly through the stl model."""
    global ctr
    Fc = Formex(array(ctr).reshape((-1,1,3)))
    path = connect([Fc,Fc],bias=[0,1])
    flyAlong(path)
    

def export_surface():
    S = selection.check(single=True)
    if S:
        types = [ "Abaqus INP files (*.inp)" ]
        fn = askNewFilename(GD.cfg['workdir'],types)
        if fn:
            print("Exporting surface model to %s" % fn)
            updateGUI()
            S.refresh()
            nodes,elems = S.coords,S.elems
            surface_abq.abq_export(fn,nodes,elems,'S3',"Abaqus model generated by pyFormex from input file %s" % os.path.basename(fn))



def export_volume():
    if PF['volume'] is None:
        return
    types = [ "Abaqus INP files (*.inp)" ]
    fn = askNewFilename(GD.cfg['workdir'],types)
    if fn:
        print("Exporting volume model to %s" % fn)
        updateGUI()
        nodes,elems = PF['volume']
        stl_abq.abq_export(fn,nodes,elems,'C3D%d' % elems.shape[1],"Abaqus model generated by tetgen from surface in STL file %s.stl" % PF['project'])


def show_nodes():
    n = 0
    data = askItems({'node number':n})
    n = int(data['node number'])
    if n > 0:
        nodes,elems = PF['surface']
        print("Node %s = %s",(n,nodes[n]))


def trim_border(elems,nodes,nb,visual=False):
    """Removes the triangles with nb or more border edges.

    Returns an array with the remaining elements.
    """
    b = border(elems)
    b = b.sum(axis=1)
    trim = where(b>=nb)[0]
    keep = where(b<nb)[0]
    nelems = elems.shape[0]
    ntrim = trim.shape[0]
    nkeep = keep.shape[0]
    print("Selected %s of %s elements, leaving %s" % (ntrim,nelems,nkeep) )

    if visual and ntrim > 0:
        prop = zeros(shape=(F.nelems(),),dtype=int32)
        prop[trim] = 2 # red
        prop[keep] = 1 # yellow
        F = Formex(nodes[elems],prop)
        clear()
        draw(F,view='left')
        
    return elems[keep]


def trim_surface():
    check_surface()
    data = GD.cfg.get('stl/border',{'Number of trim rounds':1, 'Minimum number of border edges':1})
    GD.cfg['stl/border'] = askItems(data)
    GD.GUI.update()
    n = int(data['Number of trim rounds'])
    nb = int(data['Minimum number of border edges'])
    print("Initial number of elements: %s" % elems.shape[0])
    for i in range(n):
        elems = trim_border(elems,nodes,nb)
        print("Number of elements after border removal: %s" % elems.shape[0])


def read_tetgen(surface=True, volume=True):
    """Read a tetgen model from files  fn.node, fn.ele, fn.smesh."""
    ftype = ''
    if surface:
        ftype += ' *.smesh'
    if volume:
        ftype += ' *.ele'
    fn = askFilename(GD.cfg['workdir'],"Tetgen files (%s)" % ftype)
    nodes = elems =surf = None
    if fn:
        chdir(fn)
        project = utils.projectName(fn)
        set_project(project)
        nodes,nodenrs = tetgen.readNodes(project+'.node')
#        print("Read %d nodes" % nodes.shape[0])
        if volume:
            elems,elemnrs,elemattr = tetgen.readElems(project+'.ele')
            print("Read %d tetraeders" % elems.shape[0])
            PF['volume'] = (nodes,elems)
        if surface:
            surf = tetgen.readSurface(project+'.smesh')
            print("Read %d triangles" % surf.shape[0])
            PF['surface'] = (nodes,surf)
    if surface:
        show_surface()
    else:
        show_volume()


def read_tetgen_surface():
    read_tetgen(volume=False)

def read_tetgen_volume():
    read_tetgen(surface=False)


def scale_volume():
    if PF['volume'] is None:
        return
    nodes,elems = PF['volume']
    nodes *= 0.01
    PF['volume'] = (nodes,elems) 
    



def show_volume():
    """Display the volume model."""
    if PF['volume'] is None:
        return
    nodes,elems = PF['volume']
    F = Formex(nodes[elems],eltype='tet4')
    GD.message("BBOX = %s" % F.bbox())
    clear()
    draw(F,color='random')
    PF['vol_model'] = F



def createGrid():
    res = askItems([('name','__auto__'),('nx',3),('ny',3),('b',1),('h',1)])
    if res:
        globals().update(res)
        #name = res['name']
        #nx = res['nx']
        #ny = res['ny']
        #b = 
        S = TriSurface(simple.rectangle(nx,ny,b,h,diag='d'))
        export({name:S})
        selection.set([name])
        selection.draw()


def createCube():
    res = askItems([('name','__auto__')])
    if res:
        name = res['name']
        S = Cube()
        export({name:S})
        selection.set([name])
        selection.draw()

def createSphere():
    res = askItems([('name','__auto__'),('grade',4),])
    if res:
        name = res['name']
        level = max(1,res['grade'])
        S = Sphere(level,verbose=True,filename=name+'.gts')
        export({name:S})
        selection.set([name])
        selection.draw()

_data = {}

def createCone():
    res = askItems([('name','__auto__'),
                    ('radius',1.),
                    ('height',1.),
                    ('angle',360.),
                    ('div_along_radius',6),
                    ('div_along_circ',12),
                    ('diagonals','up','select',['up','down']),
                    ])
    if res:
        name = res['name']
        F = simple.sector(r=res['radius'],t=res['angle'],nr=res['div_along_radius'],nt=res['div_along_circ'],h=res['height'],diag=res['diagonals'])
        export({name:TriSurface(F)})
        selection.set([name])
        selection.draw()


###################  Operations using gts library  ########################


def check():
    S = selection.check(single=True)
    if S:
        GD.message(S.check(verbose=True))


def split():
    S = selection.check(single=True)
    if S:
        GD.message(S.split(base=selection[0],verbose=True))


def coarsen():
    S = selection.check(single=True)
    if S:
        res = askItems([('min_edges',-1),
                        ('max_cost',-1.0),
                        ('mid_vertex',False),
                        ('length_cost',False),
                        ('max_fold',1.0),
                        ('volume_weight',0.5),
                        ('boundary_weight',0.5),
                        ('shape_weight',0.0),
                        ('progressive',False),
                        ('log',False),
                        ('verbose',False),
                        ])
        if res:
            selection.remember()
            if res['min_edges'] <= 0:
                res['min_edges'] = None
            if res['max_cost'] <= 0:
                res['max_cost'] = None
            S.coarsen(**res)
            selection.draw()


def refine():
    S = selection.check(single=True)
    if S:
        res = askItems([('max_edges',-1),
                        ('min_cost',-1.0),
                        ('log',False),
                        ('verbose',False),
                        ])
        if res:
            selection.remember()
            if res['max_edges'] <= 0:
                res['max_edges'] = None
            if res['min_cost'] <= 0:
                res['min_cost'] = None
            S.refine(**res)
            selection.draw()


def smooth():
    S = selection.check(single=True)
    if S:
        res = askItems([('lambda_value',0.5),
                        ('n_iterations',2),
                        ('fold_smoothing',None),
                        ('verbose',False),
                        ],'Laplacian Smoothing')
        if res:
            if not 0.0 <= res['lambda_value'] <= 1.0:
                warning("Lambda should be between 0 and 1.")
                return
            selection.remember()
            if res['fold_smoothing'] is not None:
                res['fold_smoothing'] = float(res['fold_smoothing'])
            S.smooth(**res)
            selection.draw()


def boolean():
    """Boolean operation on two surfaces.

    op is one of
    '+' : union,
    '-' : difference,
    '*' : interesection
    """
    ops = ['+ (Union)','- (Difference)','* (Intersection)']
    S = selection.check(single=False)
    if len(selection.names) != 2:
        warning("You must select exactly two triangulated surfaces!")
        return
    if S:
        res = askItems([('operation',None,'select',ops),
                        ('output intersection curve',False),
                        ('check self interesection',False),
                        ('verbose',False),
                        ],'Boolean Operation')
        if res:
            #selection.remember()
            newS = S[0].boolean(S[1],op=res['operation'].strip()[0],
                        inter=res['output intersection curve'],
                        check=res['check self interesection'],
                        verbose=res['verbose'])
            export({'__auto__':newS})
            #selection.draw()


    
################### menu #################

def create_menu():
    """Create the Surface menu."""
    MenuData = [
        ("&Read Surface Files",readSelection),
        ("&Select Surface(s)",selection.ask),
        ("&Draw Selection",selection.draw),
        ("&Forget Selection",selection.forget),
        ("&Convert to Formex",toFormex),
        ("&Convert to Mesh",toMesh),
        ("&Convert from Formex",fromFormex),
        ("&Convert from Mesh",fromMesh),
        ("&Write Surface Model",write_surface),
        ("---",None),
        ("&Create surface",
         [('&Plane Grid',createGrid),
          ('&Cube',createCube),
          ('&Sphere',createSphere),
          ('&Circle, Sector, Cone',createCone),
          ]),
        ("---",None),
        ("Print &Information",
         [('&Data Size',printSize),
          ('&Bounding Box',selection.printbbox),
          ('&Surface Type',printType),
          ('&Total Area',printArea),
          ('&Enclosed Volume',printVolume),
          ('&All Statistics',printStats),
          ]),
        ("&Set Property",selection.setProperty),
        ("&Shrink",toggle_shrink),
        ("Toggle &Annotations",
         [("&Names",selection.toggleNames,dict(checkable=True)),
          ("&Face Numbers",selection.toggleNumbers,dict(checkable=True)),
          ("&Edge Numbers",toggleEdgeNumbers,dict(checkable=True)),
          ("&Node Numbers",toggleNodeNumbers,dict(checkable=True)),
          ("&Normals",toggleNormals,dict(checkable=True)),
          ("&AvgNormals",toggleAvgNormals,dict(checkable=True)),
          ('&Toggle Bbox',selection.toggleBbox,dict(checkable=True)),
          ]),
        ("&Statistics",showStatistics),
        ("&Show Curvature",showCurvature),
        ("---",None),
        ("&Frontal Methods",
         [("&Color By Front",colorByFront),
          ("&Partition By Connection",partitionByConnection),
          ("&Partition By Angle",partitionByAngle),
          ]),
        ("&Border Line",showBorder),
        ("&Border Type",checkBorder),
        ("&Fill Border",fillBorder),
        ("&Fill Holes",fillHoles),
        ("---",None),
        ("&Transform",
         [("&Scale",scaleSelection),
          ("&Scale non-uniformly",scale3Selection),
          ("&Translate",translateSelection),
          ("&Center",centerSelection),
          ("&Rotate",
           [("&Around Global Axis",rotateGlobal),
            ("&Around Parallel Axis",rotateParallel),
            ("&Around Central Axis",rotateCentral),
            ("&Around General Axis",rotateGeneral),
            ]),
          ("&Roll Axes",rollAxes),
          ]),
        ("&Clip/Cut",
         [("&Clip",clipSelection),
          ("&Cut At Plane",cutAtPlane),
          ("&Multiple Cut",cutSelectionByPlanes),
          ("&Slicer",sliceIt),
          ("&Intersection With Plane",intersectWithPlane),
           ]),
        ("&Smoothing",
         [("&Low-pass filter",smoothLowPass),
         ("&Laplace and HC algorithm",smoothLaplaceHC),
           ]),
        ("&Undo Last Changes",selection.undoChanges),
        ('&GTS functions',
         [('&Check surface',check),
          ('&Split surface',split),
          ("&Coarsen surface",coarsen),
          ("&Refine surface",refine),
          ("&Smooth surface",smooth),
          ("&Boolean operation on two surfaces",boolean),
          ]),
        ("---",None),
#        ("&Show volume model",show_volume),
        # ("&Print Nodal Coordinates",show_nodes),
        # ("&Convert STL file to OFF file",convert_stl_to_off),
        # ("&Sanitize STL file to OFF file",sanitize_stl_to_off),
#        ("&Trim border",trim_surface),
        ("&Create volume mesh",create_tetgen_volume),
#        ("&Read Tetgen Volume",read_tetgen_volume),
        ("&Export surface to Abaqus",export_surface),
#        ("&Export volume to Abaqus",export_volume),
        ("&Close Menu",close_menu),
        ]
    return menu.Menu('Surface',items=MenuData,parent=GD.GUI.menu,before='Help')

    
def show_menu():
    """Show the Tools menu."""
    global _the_menu
    if not GD.GUI.menu.item('Surface'):
        create_menu()


def close_menu():
    """Close the Tools menu."""
    m = GD.GUI.menu.item('Surface')
    if m :
        m.remove()
    

if __name__ == "draw":
    # If executed as a pyformex script
    close_menu()
    show_menu()

# End
