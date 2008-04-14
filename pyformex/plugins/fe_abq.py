#!/usr/bin/env pyformex
# $Id$
##
## This file is part of pyFormex 0.7 Release Fri Apr  4 18:41:11 2008
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
"""A number of functions to write an Abaqus input file.

There are low level functions that just generate a part of an Abaqus
input file, conforming to the Keywords manual.

Then there are higher level functions that read data from the property module
and write them to the Abaqus input file.
"""

from plugins.properties import *
from mydict import *
import globaldata as GD
#from numpy import *
import datetime
import os


##################################################
## Some Abaqus .inp format output routines
##################################################

# Create automatic names for node and element sets

def autoName(base,*args):
    return (base + '_%s' * len(args)) % args 

def Nset(*args):
    return autoName('Nset',*args)

def Eset(*args):
    return autoName('Eset',*args)


def writeHeading(fil, text=''):
    """Write the heading of the Abaqus input file."""
    head = """**  Abaqus input file created by pyFormex (c) B.Verhegghe
**  (see http://pyformex.berlios.de)
**
*HEADING
%s
""" % text
    fil.write(head)


def writeNodes(fil, nodes, name='Nall', nofs=1):
    """Write nodal coordinates.

    The nodes are added to the named node set. 
    If a name different from 'Nall' is specified, the nodes will also
    be added to a set named 'Nall'.
    The nofs specifies an offset for the node numbers.
    The default is 1, because Abaqus numbering starts at 1.  
    """
    fil.write('*NODE, NSET=%s\n' % name)
    for i,n in enumerate(nodes):
        fil.write("%d, %14.6e, %14.6e, %14.6e\n" % ((i+nofs,)+tuple(n)))
    if name != 'Nall':
        fil.write('*NSET, NSET=Nall\n%s\n' % name)


def writeElems(fil, elems, type, name='Eall', eofs=1, nofs=1):
    """Write element group of given type.

    elems is the list with the element node numbers.
    The elements are added to the named element set. 
    If a name different from 'Eall' is specified, the elements will also
    be added to a set named 'Eall'.
    The eofs and nofs specify offsets for element and node numbers.
    The default is 1, because Abaqus numbering starts at 1.  
    """
    fil.write('*ELEMENT, TYPE=%s, ELSET=%s\n' % (type.upper(),name))
    nn = elems.shape[1]
    fmt = '%d' + nn*', %d' + '\n'
    for i,e in enumerate(elems+nofs):
        fil.write(fmt % ((i+eofs,)+tuple(e)))
    writeSubset(fil, 'ELSET', 'Eall', name)


def writeSet(fil, type, name, set, ofs=1):
    """Write a named set of nodes or elements (type=NSET|ELSET)"""
    fil.write("*%s,%s=%s\n" % (type,type,name))
    for i in asarray(set)+ofs:
        fil.write("%d,\n" % i)


def writeSubset(fil, type, name, subname):
    """Make a named set a subset of another one (type=NSET|ELSET)"""
    fil.write('*%s, %s=%s\n%s\n' % (type,type,name,subname))


def writeFrameSection(fil,elset,A,I11,I12,I22,J,E,G,
                      rho=None,orient=None):
    """Write a general frame section for the named element set.

    The specified values are:
      A: cross section
      I11: moment of inertia around the 1 axis
      I22: moment of inertia around the 2 axis
      I12: inertia product around the 1-2 axes
      J: Torsional constant
      E: Young's modulus of the material
      G: Shear modulus of the material
    Optional data:
      rho: density of the material
      orient: a vector specifying the direction cosines of the 1 axis
    """
    extra = orientation = ''
    if rho:
        extra = ',DENSITY=%s' % rho
    if orient:
        orientation = '%s %s %s' % (orient[0], orient[1], orient[2])
    fil.write("""*FRAME SECTION,ELSET=%s,SECTION=general%s
%s, %s, %s, %s, %s
%s
%s, %s
""" %(elset,extra,
      A,I11,I12,I22,J,
      orientation,
      E,G))


materialswritten=[]
def writeMaterial(fil, mat):
    """Write a material section.
    
    mat is the property dict of the material.
    If the matrial has a name and has already been written, this function
    does nothing.
    """
    if mat.name is not None and mat.name not in materialswritten:
        if mat.poisson_ratio is None and mat.shear_modulus is not None:
            mat.poisson_ratio = 0.5 * mat.young_modulus / mat.shear_modulus - 1.0
        fil.write("""*MATERIAL, NAME=%s
*ELASTIC
%s,%s
*DENSITY
%s
"""%(mat.name, float(mat.young_modulus), float(mat.poisson_ratio), float(mat.density)))
        materialswritten.append(mat.name)
        if mat.plastic is not None:
            fil.write('*PLASTIC\n')
            plastic=eval(mat['plastic'])
            for i in range(len(plastic)):
	      fil.write( '%s, %s\n' % (plastic[i][0],plastic[i][1]))
	if mat.damping == 'Yes':
		fil.write("*DAMPING")
		if mat.alpha != 'None':
			fil.write(", ALPHA = %s" %mat.alpha)
		if mat.beta != 'None':
			fil.write(", BETA = %s" %mat.beta)
		fil.write("\n")



##################################################
## Some higher level functions, interfacing with the properties module
##################################################

plane_stress_elems = [
    'CPS3','CPS4','CPS4I','CPS4R','CPS6','CPS6M','CPS8','CPS8M']
plane_strain_elems = [
    'CPE3','CPE3H','CPE4','CPE4H','CPE4I','CPE4IH','CPE4R','CPE4RH',
    'CPE6','CPE6H','CPE6M','CPE6MH','CPE8','CPE8H','CPE8R','CPE8RH']
generalized_plane_strain_elems = [
    'CPEG3','CPEG3H','CPEG4','CPEG4H','CPEG4I','CPEG4IH','CPEG4R','CPEG4RH',
    'CPEG6','CPEG6H','CPEG6M','CPEG6MH','CPEG8','CPEG8H','CPEG8R','CPEG8RH']
solid2d_elems = plane_stress_elems + plane_strain_elems + generalized_plane_strain_elems

solid3d_elems = ['C3D4', 'C3D4H','C3D6', 'C3D6H', 'C3D8','C3D8H','C3D8R', 'C3D8RH','C3D10','C3D10H','C3D10M','C3D10MH','C3D15','C3D15H','C3D20','C3D20H','C3D20R','C3D20RH',]


def writeSection(fil, nr):
    """Write an element section for the named element set.
    
    nr is the property number of the element set.
    """
    el = the_elemproperties[nr]

    mat = el.material
    if mat is not None:
        writeMaterial(fil,mat)

    ############
    ##FRAME elements
    ##########################
    if el.elemtype.upper() in ['FRAME3D', 'FRAME2D']:
        if el.sectiontype.upper() == 'GENERAL':
            fil.write("""*FRAME SECTION, ELSET=%s, SECTION=GENERAL, DENSITY=%s
%s, %s, %s, %s, %s \n"""%(Eset(nr),float(el.density),float(el.cross_section),float(el.moment_inertia_11),float(el.moment_inertia_12),float(el.moment_inertia_22),float(el.torsional_rigidity)))
            if el.orientation != None:
                fil.write("""%s,%s,%s"""%(el.orientation[0],el.orientation[1],el.orientation[2]))
            fil.write("""\n %s, %s \n"""%(float(el.young_modulus),float(el.shear_modulus)))
        if el.sectiontype.upper() == 'CIRC':
            fil.write("""*FRAME SECTION, ELSET=%s, SECTION=CIRC, DENSITY=%s
%s \n"""%(Eset(nr),float(el.density),float(el.radius)))
            if el.orientation != None:
                fil.write("""%s,%s,%s"""%(el.orientation[0],el.orientation[1],el.orientation[2]))
            fil.write("""\n %s, %s \n"""%(float(el.young_modulus),float(el.shear_modulus)))

    ##############
    ##connector elements
    ##########################  
    elif el.elemtype.upper() in ['CONN3D2', 'CONN2D2']:
        if el.sectiontype.upper() != 'GENERAL':
            fil.write("""*CONNECTOR SECTION,ELSET=%s
%s
""" %(Eset(nr),el.sectiontype.upper()))

    ############
    ##TRUSS elements
    ##########################  
    elif el.elemtype.upper() in ['T2D2', 'T2D2H' , 'T2D3', 'T2D3H', 'T3D2', 'T3D2H', 'T3D3', 'T3D3H']:
        if el.sectiontype.upper() == 'GENERAL':
            fil.write("""*SOLID SECTION, ELSET=%s, MATERIAL=%s
%s
""" %(Eset(nr),el.material.name, float(el.cross_section)))
        elif el.sectiontype.upper() == 'CIRC':
            fil.write("""*SOLID SECTION, ELSET=%s, MATERIAL=%s
%s
""" %(Eset(nr),el.material.name, float(el.radius)**2*pi))

    ############
    ##BEAM elements
    ##########################
    elif el.elemtype.upper() in ['B21', 'B21H','B22', 'B22H', 'B23','B23H','B31', 'B31H','B32','B32H','B33','B33H']:
        if el.sectiontype.upper() == 'GENERAL':
            fil.write("""*BEAM GENERAL SECTION, ELSET=%s, SECTION=GENERAL, DENSITY=%s
%s, %s, %s, %s, %s \n"""%(Eset(nr),float(el.density), float(el.cross_section),float(el.moment_inertia_11),float(el.moment_inertia_12),float(el.moment_inertia_22),float(el.torsional_rigidity)))
            if el.orientation != None:
                fil.write("%s,%s,%s"%(el.orientation[0],el.orientation[1],el.orientation[2]))
            fil.write("\n %s, %s \n"%(float(el.young_modulus),float(el.shear_modulus)))
        if el.sectiontype.upper() == 'CIRC':
            fil.write("""*BEAM GENERAL SECTION, ELSET=%s, SECTION=CIRC, DENSITY=%s
%s \n"""%(Eset(nr),float(el.density),float(el.radius)))
            if el.orientation != None:
                fil.write("""%s,%s,%s"""%(el.orientation[0],el.orientation[1],el.orientation[2]))
            fil.write("""\n %s, %s \n"""%(float(el.young_modulus),float(el.shear_modulus)))
	if el.sectiontype.upper() == 'RECT':
            fil.write('*BEAM SECTION, ELSET=%s, material=%s,\n** Section: %s  Profile: %s\ntemperature=GRADIENTS, SECTION=RECT\n %s,%s\n' %(Eset(nr),el.material.name,el.name,el.name,float(el.height),float(el.width)))
            if el.orientation != None:
                fil.write("""%s,%s,%s\n"""%(el.orientation[0],el.orientation[1],el.orientation[2]))
		

    ############
    ## SHELL elements
    ##########################
    elif el.elemtype.upper() in ['STRI3', 'S3','S3R', 'S3RS', 'STRI65','S4','S4R', 'S4RS','S4RSW','S4R5','S8R','S8R5', 'S9R5',]:
        if el.sectiontype.upper() == 'SHELL':
            if mat is not None:
                fil.write("""*SHELL SECTION, ELSET=%s, MATERIAL=%s
%s \n""" % (Eset(nr),mat.name,float(el.thickness)))

    ############
    ## MEMBRANE elements
    ##########################
    elif el.elemtype.upper() in ['M3D3', 'M3D4','M3D4R', 'M3D6', 'M3D8','M3D8R','M3D9', 'M3D9R',]:
        if el.sectiontype.upper() == 'MEMBRANE':
            if mat is not None:
                fil.write("""*MEMBRANE SECTION, ELSET=%s, MATERIAL=%s
%s \n""" % (Eset(nr),mat.name,float(el.thickness)))


    ############
    ## 3DSOLID elements
    ##########################
    elif el.elemtype.upper() in solid3d_elems:
        if el.sectiontype.upper() == '3DSOLID':
            if mat is not None:
                fil.write("""*SOLID SECTION, ELSET=%s, MATERIAL=%s
%s \n""" % (Eset(nr),mat.name,1.))

    ############
    ## 2D SOLID elements
    ##########################
    elif el.elemtype.upper() in solid2d_elems:
        if el.sectiontype.upper() == 'SOLID':
            if mat is not None:
                fil.write("""*SOLID SECTION, ELSET=%s, MATERIAL=%s
%s \n""" % (Eset(nr),mat.name,float(el.thickness)))
            
    ############
    ## RIGID elements
    ##########################
    elif el.elemtype.upper() in ['R2D2','RB2D2','RB3D2','RAX2','R3D3','R3D4']:
        if el.sectiontype.upper() == 'RIGID':
            fil.write("""*RIGID BODY,REFNODE=%s,density=%s, ELSET=%s\n""" % (el.nodeset,el.density,Eset(nr)))



    ############
    ## UNSUPPORTED elements
    ##########################
    else:
        warning('Sorry, elementtype %s is not yet supported' % el.elemtype)
    

def transform(fil, propnr):
    """Transform the nodal coordinates of the nodes with a given property number."""
    n = the_nodeproperties[propnr]
    if n.coords.lower()=='cartesian':
        if n.coordset!=[]:
            fil.write("""*TRANSFORM, NSET=%s, TYPE=R
%s,%s,%s,%s,%s,%s
"""%(Nset(propnr),n.coordset[0],n.coordset[1],n.coordset[2],n.coordset[3],n.coordset[4],n.coordset[5]))
    elif n.coords.lower()=='spherical':
        fil.write("""*TRANSFORM, NSET=%s, TYPE=S
%s,%s,%s,%s,%s,%s
"""%(Nset(propnr),n.coordset[0],n.coordset[1],n.coordset[2],n.coordset[3],n.coordset[4],n.coordset[5]))
    elif n.coords.lower()=='cylindrical':
        fil.write("""*TRANSFORM, NSET=%s, TYPE=C
%s,%s,%s,%s,%s,%s
"""%(Nset(propnr),n.coordset[0],n.coordset[1],n.coordset[2],n.coordset[3],n.coordset[4],n.coordset[5]))
    else:
        warning('%s is not a valid coordinate system'%the_nodeproperties[propnr].coords)

    
def writeBoundaries(fil, recset='ALL', op='MOD'):
    """Write nodal boundary conditions.
    
    recset is a list of node record numbers that should be scanned for data.
    By default, all records will be scanned.

    By default, the boundary conditions are applied as a modification of the
    existing boundary conditions, i.e. initial conditions and conditions from
    previous steps remain in effect.
    The user can set op='NEW' to remove the previous conditions.
    This will also remove initial conditions!
    """
    if recset == 'ALL':
        recset = the_nodeproperties.iterkeys()

    for i in recset:
        if the_nodeproperties[i].bound!=None:
            fil.write("*BOUNDARY, OP=%s\n" % op)
            if isinstance(the_nodeproperties[i].bound,list):
                for b in range(6):
                    if the_nodeproperties[i].bound[b]==1:
                        fil.write("%s, %s\n" % (Nset(i),b+1))
            elif isinstance(the_nodeproperties[i].bound,str):
                fil.write("%s, %s\n" % (Nset(i),the_nodeproperties[i].bound))
            else:
                warning("The boundaries have to defined in a list 'boundset'")


def writeDisplacements(fil, recset='ALL', op='MOD'):
    """Write boundary conditions of type BOUNDARY, TYPE=DISPLACEMENT

    recset is a list of node record numbers that should be scanned for data.
    By default, all records will be scanned.
    
    By default, the boundary conditions are applied as a modification of the
    existing boundary conditions, i.e. initial conditions and conditions from
    previous steps remain in effect.
    The user can set op='NEW' to remove the previous conditions.
    This will also remove initial conditions!
    """
    if recset == 'ALL':
        recset = the_nodeproperties.iterkeys()
        
    for i in recset:
        if the_nodeproperties[i].displacement!=None:
            fil.write("*BOUNDARY, TYPE=DISPLACEMENT, OP=%s" % op)
            if the_nodeproperties[i].amplitude!=None:
                fil.write(", AMPLITUDE=%s" % the_nodeproperties[i].amplitude)
            fil.write("\n")
            for d in range(len(the_nodeproperties[i].displacement)):
                fil.write("%s, %s, %s, %s\n" % (Nset(i),the_nodeproperties[i].displacement[d][0],the_nodeproperties[i].displacement[d][0],the_nodeproperties[i].displacement[d][1]))
            
            
def writeCloads(fil, recset='ALL', op='NEW'):
    """Write cloads.
    
    recset is a list of node record numbers that should be scanned for data.
    By default, all records will be scanned.

    By default, the loads are applied as new values in the current step.
    The user can set op='MOD' to add the loads to already existing ones.
    """
    if recset == 'ALL':
        recset = the_nodeproperties.iterkeys()
       
    fil.write("*CLOAD, OP=%s\n" % op)
    for i in recset:
        if the_nodeproperties[i].cload != None:
            for cl in range(6):
                if the_nodeproperties[i].cload[cl] != 0:
                    fil.write("%s, %s, %s\n" % (Nset(i),cl+1,the_nodeproperties[i].cload[cl]))


def writeDloads(fil, recset='ALL', op='NEW'):
    """Write Dloads.
    
    recset is a list of node record numbers that should be scanned for data.
    By default, all records will be scanned.

    By default, the loads are applied as new values in the current step.
    The user can set op='MOD' to add the loads to already existing ones.
    """
    if recset == 'ALL':
        recset = the_elemproperties.iterkeys()
       
    for i in recset:
        if isinstance(the_elemproperties[i].elemload, list):
            for load in range(len(the_elemproperties[i].elemload)):
                fil.write("*DLOAD, OP=%s" % op)
                if the_elemproperties[i].elemload[load].amplitude!=None:
                    fil.write(", AMPLITUDE=%s" % the_elemproperties[i].elemload[load].amplitude)
                fil.write("\n")
                if the_elemproperties[i].elemload[load].loadlabel.upper() == 'GRAV':
                    fil.write("%s, GRAV, 9.81, 0, 0 ,-1\n" % (Eset(i)))
                else:
                    fil.write("%s, %s, %s\n" % (Eset(i),the_elemproperties[i].elemload[load].loadlabel,the_elemproperties[i].elemload[load].magnitude))

#######################################################
# General model data
#
def writeAmplitude(fil, name=None):
    fil.write("*AMPLITUDE, NAME=%s\n" %name)
    n = len(the_modelproperties[name].amplitude)
    for i in range(n-1):
        fil.write("%s, " % the_modelproperties[name].amplitude[i])
    fil.write("%s\n" % the_modelproperties[name].amplitude[n-1])

    
def writeInteraction(fil , name=None, op='NEW'):
    if the_modelproperties[name].interactionname.upper()=='ALLWITHSELF':
        fil.write('** INTERACTIONS, NAME=%s\n*Contact, op=%s\n*contact inclusions,ALL EXTERIOR\n*Contact property assignment\n ,  ,  %s\n'% (the_modelproperties[name].interactionname,op,the_modelproperties[name].interaction.intprop))
    else:
        fil.write('** INTERACTIONS, NAME=%s\n*Contact Pair, interaction=%s\n%s,%s\n'%(the_modelproperties[name].interactionname,the_modelproperties[name].interaction.intprop,the_modelproperties[name].interaction.surface1,the_modelproperties[name].interaction.surface2))

    
def writeIntprop(fil,name=None):
    fil.write("*Surface interaction, name=%s\n" %name)
    fil.write("*%s\n%s,\n" %(the_modelproperties[name].intprop.inttype,the_modelproperties[name].intprop.parameter))
    
    
def writeDamping(fil,name=None):
    fil.write("*global damping")
    if the_modelproperties[name].damping.field is not None:
    	fil.write(", Field = %s"%the_modelproperties[name].damping.field)
    else:
	fil.write(", Field = ALL")
    if the_modelproperties[name].damping.alpha is not None:
	fil.write(", alpha = %s"%the_modelproperties[name].damping.alpha)
    if the_modelproperties[name].damping.beta is not None:
	fil.write(", beta = %s"%the_modelproperties[name].damping.beta)
    fil.write("\n")

    
def writeElemSurface(fil,number=None,abqdata=None):
    if number is not None and abqdata is not None:
        elemsnumbers=where(abqdata.elemprop==number)[0]
        fil.write('*ELset,Elset=%s\n'% elemproperties[number].surfaces.setname)
        for i in elemsnumbers:
            n=i+1
            fil.write('%s,\n'%n)
            fil.write('*Surface, type =Element, name=%s\n%s,%s\n' %(elemproperties[number].surfaces.name,elemproperties[number].surfaces.setname,elemproperties[number].surfaces.arg))

            
def writeNodeSurface(fil,number=None,abqdata=None):
    if number is not None and abqdata is not None:
        nodenumbers=where(abqdata.nodeprop==number)[0]
        fil.write('*ELset,Elset=%s\n'% nodeproperties[number].surfaces.setname)
        for i in nodenumbers:
            n=i+1
            fil.write('%s,\n'%n)
            fil.write('*Surface, type =Node, name=%s\n%s,%s\n' %(nodeproperties[number].surfaces.name,nodeproperties[number].surfaces.setname,nodeproperties[number].surfaces.arg))

    
def writeSurface(fil,name=None,abqdata=None):
    if name is not None and abqdata is not None:
        if elemproperties[name].surfaces=='Element':
            global elemsprops
            elemssetsurfaces=[]
            for i in range(len(elemproperties)):
                if elemproperties[i].surfaces==the_modelproperties[name].setname:
                    elemssetsurfaces.append(i)
		elemssur=[]
		for i in elemssetsurfaces:
                    elemss=where(abqdata.elemprop[:]==i)[0]
                    elemssur.extend(elemss)
                if len(elemssur)>0:
                    fil.write('*ELset,Elset=%s, internal\n'% the_modelproperties[name].setname)
                    for i in range(len(elemssur)):
                        getal=elemssur[i]+1
                        fil.write('%s,\n'%getal)
			fil.write('*Surface, type =Element, name=%s, internal\n%s,%s\n' %(name,the_modelproperties[name].setname,the_modelproperties[name].arg))

	elif the_modelproperties[name].surftype=='Node':
            nodes=[]
            nFormex=len(abqdata.elems)
            length=zeros(nFormex)
            for j in range(nFormex):
                length[j]=len(abqdata.elems[j])
            partnumbers=[]
            for j in range(nFormex):
                partnumbers=append(partnumbers,ones(length[j])*j)
            for j in elemssur:
                partnumber=int(partnumbers[j])
                part=abqdata.elems[partnumber]
                elemcount=0
                for i in range(partnumber):
                    elemcount+=length[i]
                    nodes.extend(part[j-elemcount])
		nodes = unique(nodes)
		fil.write('*Nset,Nset=%s, internal\n'% the_modelproperties[name].setname)
		for i in range(len(nodes)):
                    getal=nodes[i]+1
                    fil.write('%s,\n'%getal)
		fil.write('*Surface, type =Node, name=%s, internal\n%s,%s\n'%(name,the_modelproperties[name].setname,the_modelproperties[name].arg))


### Output requests ###################################
#
# Output: goes to the .odb file (for postprocessing with Abaqus/CAE)
# Result: goes to the .fil file (for postprocessing with other means)
#######################################################

def writeStepOutput(fil,kind,type,variable='PRESELECT'):
    """Write the global step output requests.
    
    type = 'FIELD' or 'HISTORY'
    variable = 'ALL' or 'PRESELECT'
    """
    fil.write("*OUTPUT, %s, VARIABLE=%s\n" %(type.upper(),variable.upper()))


def writeNodeOutput(fil,kind,keys,set='Nall'):
    """ Write a request for nodal result output to the .odb file.

    keys is a list of NODE output identifiers
    set is single item or a list of items, where each item is either:
      - a property number
      - a node set name
      for which the results should be written
    """
    output = 'OUTPUT'
    if type(set) == str or type(set) == int:
        set = [ set ]
    for i in set:
        if type(i) == int:
            setname = Nset(str(i))
        else:
            setname = i
        s = "*NODE %s, NSET=%s" % (output,setname)
        fil.write("%s\n" % s)
        for key in keys:
            fil.write("%s\n" % key)


def writeNodeResult(fil,kind,keys,set='Nall',output='FILE',freq=1,
                    globalaxes=False,
                    summary=False,total=False):
    """ Write a request for nodal result output to the .fil or .dat file.

    keys is a list of NODE output identifiers
    set is single item or a list of items, where each item is either:
      - a property number
      - a node set name
      for which the results should be written
    output is either 'FILE' (.fil) or 'PRINT' (.dat)(Standard only)
    freq is the output frequency in increments (0 = no output)

    Extra arguments:
    globalaxes: If 'YES', the requested output is returned in the global axes.
      Default is to use the local axes wherever defined.

    Extra arguments for output='PRINT':
    summary: if True, a summary with minimum and maximum is written
    total: if True, sums the values for each key

    Remark: the 'kind' argument is not used, but is included so that we can
    easily call it with a Results dict as arguments
    """
    if type(set) == str or type(set) == int:
        set = [ set ]
    for i in set:
        if type(i) == int:
            setname = Nset(str(i))
        else:
            setname = i
        s = "*NODE %s, NSET=%s" % (output,setname)
        if freq != 1:
            s += ", FREQUENCY=%s" % freq
        if globalaxes:
            s += ", GLOBAL=YES"
        if output=='PRINT':
            if summary:
                s += ", SUMMARY=YES"
            if total:
                s += ", TOTAL=YES"
        fil.write("%s\n" % s)
        for key in keys:
            fil.write("%s\n" % key)


def writeElemOutput(fil,kind,keys,set='Eall'):
    """ Write a request for element output to the .odb file.

    keys is a list of ELEMENT output identifiers
    set is single item or a list of items, where each item is either:
      - a property number
      - an element set name
      for which the results should be written
    """
    output = 'OUTPUT'
    if type(set) == str or type(set) == int:
        set = [ set ]
    for i in set:
        if type(i) == int:
            setname = Eset(str(i))
        else:
            setname = i
        s = "*ELEMENT %s, ELSET=%s" % (output,setname)
        fil.write("%s\n" % s)
        for key in keys:
            fil.write("%s\n" % key)


def writeElemResult(fil,kind,keys,set='Eall',output='FILE',freq=1,
                    pos=None,
                    summary=False,total=False):
    """ Write a request for element result output to the .fil or .dat file.

    keys is a list of ELEMENT output identifiers
    set is single item or a list of items, where each item is either:
      - a property number
      - an element set name
      for which the results should be written
    output is either 'FILE' (.fil) or 'PRINT' (.dat)(Standard only)
    freq is the output frequency in increments (0 = no output)

    Extra arguments:
    pos: Position of the points in the elements at which the results are
      written. Should be one of:
      'INTEGRATION POINTS' (default)
      'CENTROIDAL'
      'NODES'
      'AVERAGED AT NODES'
      Non-default values are only available for ABAQUS/Standard.
      
    Extra arguments for output='PRINT':
    summary: if True, a summary with minimum and maximum is written
    total: if True, sums the values for each key

    Remark: the 'kind' argument is not used, but is included so that we can
    easily call it with a Results dict as arguments
    """
    if type(set) == str or type(set) == int:
        set = [ set ]
    for i in set:
        if type(i) == int:
            setname = Eset(str(i))
        else:
            setname = i
        s = "*EL %s, ELSET=%s" % (output,setname)
        if freq != 1:
            s += ", FREQUENCY=%s" % freq
        if pos:
            s += ", POSITION=%s" % pos
        if output=='PRINT':
            if summary:
                s += ", SUMMARY=YES"
            if total:
                s += ", TOTAL=YES"
        fil.write("%s\n" % s)
        for key in keys:
            fil.write("%s\n" % key)


def writeModelProps():
    for i in the_modelproperties:
        if the_modelproperties[i].interaction is not None:
            writeInteraction(fil, i)
    for i in the_modelproperties:
        if the_modelproperties[i].damping is not None:
            writedamping(fil, i)


def writeStep(fil, analysis='STATIC', time=[0,0,0,0], nlgeom='NO', cloadset='ALL', opcl='NEW', dloadset='ALL', opdl='NEW', boundset=None, opb=None, dispset='ALL', op='MOD', out=[], res=[]):
    """Write a load step.
        
    analysis is the analysis type. Currently, only STATIC is supported.
    time is a list which defines the time step.
    If nlgeom='YES', the analysis will be non-linear.
    cloadset is a list of property numbers of which the cloads will be used in this analysis.
    dloadset is a list of property numbers of which the dloads will be used in this analysis.
    boundset is a list of property numbers of which the bounds will be used in this analysis.
    By default, the load is applied as a new load, i.e. loads
    from previous steps are removed. The user can set op='MOD'
    to keep/modify the previous loads.
    out is a list of Output-instances.
    res is a list of Result-instances.
    """ 
    if analysis.upper()=='STATIC':
        fil.write("""*STEP, NLGEOM=%s
*STATIC
%s, %s, %s, %s
""" % (nlgeom, time[0], time[1], time[2], time[3]))
    elif analysis.upper()=='EXPLICIT':
        fil.write("""*STEP, NLGEOM=%s
*DYNAMIC, EXPLICIT
, %s\n*BULK VISCOSITY\n0.06, 1.2
""" % (nlgeom, time[0]))
    else:
        GD.message('Skipping undefined step %s' % analysis)
        return

    if boundset is not None:
        writeBoundaries(fil, boundset, opb)
    writeDisplacements(fil, dispset,op)
    writeCloads(fil, cloadset, opcl)
    writeDloads(fil, dloadset, opdl)
    writeModelProps()
    for i in out:
        if i.kind is None:
            writeStepOutput(fil,**i)
        if i.kind == 'N':
            writeNodeOutput(fil,**i)
        elif i.kind == 'E':
            writeElemOutput(fil,**i)
    for i in res:
        if i.kind == 'N':
            writeNodeResult(fil,**i)
        elif i.kind == 'E':
            writeElemResult(fil,**i)
    fil.write("*END STEP\n")


##################################################
## Some classes to store all the required information
################################################## 


class Model(Dict):
    """Contains all model data."""
    
    def __init__(self,nodes,elems,nodeprop,elemprop,initialboundaries='ALL'):
        """Create new model data.

        nodes is an array with nodal coordinates
        elems is either a single element connectivity array, or a list of such.
        In a simple case, nodes and elems can be the arrays obtained by 
            nodes, elems = F.feModel()
        This is however limited to a model where all elements have the same
        number of nodes. Then you can use the list of elems arrays. The 'fe'
        plugin has a helper function to create this list. E.g., if FL is a
        list of Formices (possibly with different plexitude), then
          fe.mergeModels([Fi.feModel() for Fi in FL])
        will return the (nodes,elems) tuple to create the Model.

        nodeprop is a list of global node property numbers.
        elemprop is a list of global element property numbers.

        The global node and element property numbers are used to identify
        the nodes/elements in Node/Element property records that do not have
        the nset/eset argument set
        
        initialboundaries is a list of the initial boundaries. The default is
        to apply ALL boundary conditions initially. Specify a (possibly
        empty) list to override the default.
        """
        if not type(elems) == list:
            elems = [ elems ]
        Dict.__init__(self, {'nodes':asarray(nodes),
                             'elems':map(asarray,elems),
                             'nodeprop':asarray(nodeprop),
                             'elemprop':asarray(elemprop),
                             'initialboundaries':initialboundaries}) 


class Step(Dict):
    """Contains all data about a step."""
    
    def __init__(self, analysis='STATIC', time=[0,0,0,0], nlgeom='NO', cloadset='ALL', opcl='NEW', dloadset='ALL', opdl='NEW', boundset=None, opb=None, dispset='ALL', op='MOD'):
        """Create new analysis data.
        
        analysis is the analysis type. Should be one of:
          'STATIC', 'EXPLICIT'
        time is a list which defines the time step.
        If nlgeom='YES', the analysis will be non-linear.
        cloadset is a list of property numbers of which the cloads will be used in this analysis.
        dloadset is a list of property numbers of which the dloads will be used in this analysis.
        boundset is a list of property numbers of which the bounds will be used in this analysis. Initial boundaries are defined in a Model instance.
        By default, the load is applied as a new load, i.e. loads
        from previous steps are removed. The user can set op='MOD'
        to keep/modify the previous loads.
        """
        Dict.__init__(self,{'analysis':analysis, 'time':time, 'nlgeom':nlgeom, 'cloadset':cloadset, 'opcl':opcl, 'dloadset':dloadset, 'opdl':opdl, 'boundset':boundset, 'opb': opb, 'dispset' : dispset , 'op': op})

    
class Output(Dict):
    """A request for output to .odb and history."""
    
    def __init__(self,kind=None,keys=None,set=None,
                 type='FIELD',variable='PRESELECT'):
        """ Create new output request.
        
        kind = None, 'NODE', or 'ELEMENT' (first character suffices)

        For kind=='':

          type =  'FIELD' or 'HISTORY'
          variable = 'ALL' or 'PRESELECT'

        For kind=='NODE' or 'ELEMENT':

          keys is a list of output identifiers (compatible with kind type)
        
          set is single item or a list of items, where each item is either:
            - a property number
            - a node set name
            for which the results should be written
          If no set is specified, the default is 'Nall' for kind=='NODE'
          and 'Eall' for kind='ELEMENT'
        """
        if kind:
            kind = kind[0].upper()
        if set is None:
            set = "%sall" % kind
        Dict.__init__(self,{'kind':kind})
        if kind is not None:
            self.update({'keys':keys,'set':set})
        else:
            self.update({'type':type,'variable':variable})


class Result(Dict):
    """A request for output of results on nodes or elements."""
    
    def __init__(self,kind,keys,set=None,output='FILE',freq=1,
                 **kargs):
        """Create new result request.
        
        kind = 'NODE' or 'ELEMENT' (actually, the first character suffices)

        keys is a list of output identifiers (compatible with kind type)
        
        set is single item or a list of items, where each item is either:
          - a property number
          - a node set name
          for which the results should be written
        If no set is specified, the default is 'Nall' for kind=='NODE'
        and 'Eall' for kind='ELEMENT'
        
        output is either 'FILE' (.fil) or 'PRINT' (.dat)(Standard only)
        freq is the output frequency in increments (0 = no output)

        Extra keyword arguments are available: see the writeNodeResults and
        writeElemResults functions for details.
        """
        kind = kind[0].upper()
        if set is None:
            set = "%sall" % kind
        Dict.__init__(self,{'keys':keys,'kind':kind,'set':set,'output':output,
                            'freq':freq})
        self.update(dict(**kargs))


class AbqData(CascadingDict):
    """Contains all data required to write the abaqus input file."""
    
    def __init__(self, model, steps=[], res=[],out=[]):
        """Create new AbqData. 
        
        model is a Model instance.
        steps is a list of Step instances.
        res is a list of Result instances.
        out is a list of Output instances.
        """
        CascadingDict.__init__(self, {'model':model, 'steps':steps, 'res':res, 'out':out})

    
##################################################
## Combine all previous functions to write the Abaqus input file
##################################################

def abqInputNames(job):
    """Returns corresponding Abq jobname and input filename.

    job can be either a jobname or input file name, with or without
    directory part, with or without extension (.inp)
    
    The Abq jobname is the basename without the extension.
    The abq filename is the abspath of the job with extension '.inp'
    """
    jobname = os.path.basename(job)
    if jobname.endswith('.inp'):
        jobname = jobname[:-4]
    filename = os.path.abspath(job)
    if not filename.endswith('.inp'):
        filename += '.inp'
    return jobname,filename


def writeAbqInput(abqdata, jobname=None):
    """Write an Abaqus input file.
    
    abqdata is an AbqData-instance.
    job is the name of the inputfile.
    """
    global materialswritten
    materialswritten = []
    # Create the Abaqus input file
    if jobname is None:
        jobname = str(GD.scriptName)[:-3]
    jobname,filename = abqInputNames(jobname)
    fil = file(filename,'w')
    GD.message("Writing to file %s" % (filename))
    
    writeHeading(fil, """Model: %s     Date: %s      Created by pyFormex
Script: %s 
""" % (jobname, datetime.date.today(), GD.scriptName))
    
    nnod = abqdata.nodes.shape[0]
    GD.message("Writing %s nodes" % nnod)
    writeNodes(fil, abqdata.nodes)
    
    GD.message("Writing node sets")
    nlist = arange(nnod)
    for i,v in the_nodeproperties.iteritems():
        if v.has_key('nset') and v['nset'] is not None:
            nodeset = v['nset']
        else:
            nodeset = nlist[abqdata.nodeprop == i]
        if len(nodeset) > 0:
            writeSet(fil, 'NSET', Nset(str(i)), nodeset)
            transform(fil,i)

    GD.message("Writing element sets")
    n=0
    # we process the elementgroups one by one
    GD.message("Number of element groups: %s" % len(abqdata.elems))
    for j,elems in enumerate(abqdata.elems):
        ne = len(elems)
        nlist = arange(ne)           # The element numbers for this group
        eprop = abqdata.elemprop[n:n+ne] # The properties in this group
        GD.message("Number of elements in group %s: %s" % (j,ne))
        for i,v in the_elemproperties.iteritems():
            if v.has_key('eset') and v['eset'] is not None:
                elemset = v['eset']
            else:
                elemset = nlist[eprop == i] # The elems with property i
            if len(elemset) > 0:
                print "Elements in group %s with property %s: %s" % (j,i,elemset)
                subsetname = '%s' % Eset(j,i)
                writeElems(fil, elems[elemset],the_elemproperties[i].elemtype,subsetname,eofs=n+1)
                n += len(elemset)
                writeSubset(fil, 'ELSET', Eset(i), subsetname)
    if sum([len(elems) for elems in abqdata.elems]) != n:
        GD.message("!!Not all elements have been written out!!")
    GD.message("Total number of elements: %s" % n)

    GD.message("Writing element sections")
    for i in the_elemproperties:
        writeSection(fil,i)

    GD.message("Writing surfaces")
    for i in the_nodeproperties:
	if the_nodeproperties[i].surfaces is not None:
            writeNodeSurface(fil,i,abqdata)
    for i in the_elemproperties:
	if the_elemproperties[i].surfaces is not None:
            writeElemSurface(fil,i,abqdata)
	
    GD.message("Writing model properties")
    for i in the_modelproperties:
        if the_modelproperties[i].amplitude is not None:
	    GD.message("Writing amplitude: %s" % i)
            writeAmplitude(fil, i)
        if the_modelproperties[i].intprop is not None:
	    GD.message("Writing interaction property: %s" % i)
            writeIntprop(fil, i)

    GD.message("Writing steps")
    writeBoundaries(fil, abqdata.initialboundaries)
    for i in range(len(abqdata.analysis)):
        a = abqdata.analysis[i]
        writeStep(fil,a.analysis,a.time,a.nlgeom,a.cloadset,a.opcl,a.dloadset,a.opdl,a.boundset,a.opb,a.dispset,a.op,abqdata.out,abqdata.res)

    GD.message("Done")


##################################################
## Test
##################################################

if __name__ == "script" or __name__ == "draw":

    from plugins import properties
    reload(properties)
    
    workHere()
    
    #creating the formex (just 4 points)
    F=Formex([[[0,0]],[[1,0]],[[1,1]],[[0,1]]],[12,8,2])
    draw(F)
    
    # Create p[roperties database
    P = properties.PropertiesDB()
    #install example databases
    # either like this
    Mat = MaterialDB('../../examples/materials.db')
    P.setMaterialDB(Mat)
    # or like this
    P.setSectionDB(SectionDB('../../examples/sections.db'))
    
    # creating properties
    S1=ElemSection('IPEA100', 'steel')
    S2=ElemSection({'name':'circle','radius':10,'sectiontype':'circ'},'steel','CIRC')
    S3=ElemSection(sectiontype='join')
    BL1=ElemLoad(0.5,loadlabel='PZ')
    BL2=ElemLoad(loadlabel='Grav')
    #S2.density=7850
    S2.cross_section=572
    np1=NodeProperty(9,cload=[2,6,4,0,0,0], displacement=[[3,5]],coords='cylindrical',coordset=[0,0,0,0,0,1])
    np2=NodeProperty(8,cload=[9,2,5,3,0,4], bound='pinned')
    np3=NodeProperty(7,None,[1,1,1,0,0,1], displacement=[[2,6],[4,8]])
    bottom = ElemProperty(12,S2,[BL1],'T2D3')
    top = ElemProperty(2,S2,[BL2],elemtype='FRAME2D')
    diag = ElemProperty(8,S3,elemtype='conn3d2')
    
    #creating the input file
    old = seterr(all='ignore')
    nodes,elems = F.feModel()
    seterr(**old)
    step1 = Step(nlgeom='yes', cloadset=[], boundset=[8])
    step2 = Step(cloadset=[9], dloadset=[], dispset=[9])
    outhist = Output(type='history')
    outfield = Output(type='field', kind='node', set= [9,8], keys='SF')
    elemres = Result(kind='ELEMENT',keys=['S','SP','SINV'])
    noderes = Result(kind='NODE',set=[7,9], keys=['U','COORD'])
    model = Model(nodes, elems, [9,8,0,7], F.p, initialboundaries=[7])
    total = AbqData(model, analysis=[step1, step2], res=[elemres, noderes], out=[outhist, outfield])
    print model
    writeAbqInput(total, jobname='testing')
    
    
# End