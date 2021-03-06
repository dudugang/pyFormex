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

"""A collection of numerical array utilities.

These are general utility functions that depend only on the :mod:`numpy`
array model. All pyformex modules needing :mod:`numpy` should import
everything from this module::

  from arraytools import *
"""
from __future__ import print_function

from numpy import *

import sys
if sys.hexversion >= 0x02060000:
    # We have combinations and permutations built in
    from itertools import combinations,permutations
else:
    # Provide our own implementation of combinations,permutations
    def combinations(iterable, r):
        # combinations('ABCD', 2) --> AB AC AD BC BD CD
        # combinations(range(4), 3) --> 012 013 023 123
        pool = tuple(iterable)
        n = len(pool)
        if r > n:
            return
        indices = range(r)
        yield tuple(pool[i] for i in indices)
        while True:
            for i in reversed(range(r)):
                if indices[i] != i + n - r:
                    break
            else:
                return
            indices[i] += 1
            for j in range(i+1, r):
                indices[j] = indices[j-1] + 1
            yield tuple(pool[i] for i in indices)

    def permutations(iterable, r=None):
        # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
        # permutations(range(3)) --> 012 021 102 120 201 210
        pool = tuple(iterable)
        n = len(pool)
        if r is None:
            r = n
        if r > n:
            return
        indices = range(n)
        cycles = range(n, n-r, -1)
        yield tuple(pool[i] for i in indices[:r])
        while n:
            for i in reversed(range(r)):
                cycles[i] -= 1
                if cycles[i] == 0:
                    indices[i:] = indices[i+1:] + indices[i:i+1]
                    cycles[i] = n - i
                else:
                    j = cycles[i]
                    indices[i], indices[-j] = indices[-j], indices[i]
                    yield tuple(pool[i] for i in indices[:r])
                    break
            else:
                return

# Define a wrapper function for old versions of numpy

try:
    unique([1],True)
except TypeError:
    from numpy import unique1d as unique

if unique([1],True)[0][0] == 0:
    # We have the old numy version
    import warnings
    warnings.warn("BEWARE: OLD VERSION OF NUMPY!!!! We advise you to upgrade NumPy!")
    def unique(a,return_indices=False):
        """Replacement for numpy's unique1d"""
        import numpy
        if return_indices:
            indices,uniq = numpy.unique1d(a,True)
            return uniq,indices
        else:
            return numpy.unique1d(a)


# default float and int types
Float = float32
Int = int32


def isInt(obj):
    """Test if an object is an integer number

    Returns True if the object is a single integer number, else False.
    The type of the object can be either a Python integer (int) or a
    numpy integer.
    """
    return isinstance(obj,(int,integer))


###########################################################################
##
##   some math functions
##
#########################

# pi is defined in numpy
# DEG is a multiplier to transform degrees to radians
# RAD is a multiplier to transform radians to radians
DEG = pi/180.
RAD = 1.
golden_ratio = 0.5 * (1.0 + sqrt(5.))


# Convenience functions: trigonometric functions with argument in degrees

def sind(arg,angle_spec=DEG):
    """Return the sine of an angle in degrees.

    For convenience, this can also be used with an angle in radians,
    by specifying `angle_spec=RAD`.

    >>> print(sind(30), sind(pi/6,RAD))
    0.5 0.5
    """
    return sin(arg*angle_spec)


def cosd(arg,angle_spec=DEG):
    """Return the cosine of an angle in degrees.

    For convenience, this can also be used with an angle in radians,
    by specifying ``angle_spec=RAD``.

    >>> print(cosd(60), cosd(pi/3,RAD))
    0.5 0.5
    """
    return cos(arg*angle_spec)


def tand(arg,angle_spec=DEG):
    """Return the tangens of an angle in degrees.

    For convenience, this can also be used with an angle in radians,
    by specifying ``angle_spec=RAD``.
    """
    return tan(arg*angle_spec)


def arcsind(arg,angle_spec=DEG):
    """Return the angle whose sine is equal to the argument.

    By default, the angle is returned in Degrees.
    Specifying `angle_spec=RAD` will return the angle in radians.

    >>> print(arcsind(0.5), arcsind(1.0,RAD))
    30.0 1.57079632679
    """
    return arcsin(arg)/angle_spec


def arccosd(arg,angle_spec=DEG):
    """Return the angle whose cosine is equal to the argument.

    By default, the angle is returned in Degrees.
    Specifying `angle_spec=RAD` will return the angle in radians.

    >>> print(arccosd(0.5), arccosd(-1.0,RAD))
    60.0 3.14159265359
    """
    return arccos(arg)/angle_spec


def arctand(arg,angle_spec=DEG):
    """Return the angle whose tangens is equal to the argument.

    By default, the angle is returned in Degrees.
    Specifying `angle_spec=RAD` will return the angle in radians.

    >>> print(arctand(1.0), arctand(-1.0,RAD))
    45.0 -0.785398163397
    """
    return arctan(arg)/angle_spec


def arctand2(sin,cos,angle_spec=DEG):
    """Return the angle whose sine and cosine values are given.

    By default, the angle is returned in Degrees.
    Specifying `angle_spec=RAD` will return the angle in radians.
    This returns an angle in the range ]-180,180].

    >>> print(arctand2(0.0,-1.0), arctand2(-sqrt(0.5),-sqrt(0.5),RAD))
    180.0 -2.35619449019
    """
    return arctan2(sin,cos)/angle_spec


def niceLogSize(f):
    """Return the smallest integer e such that 10**e > abs(f).

    This returns the number of digits before the decimal point.

    >>> print([ niceLogSize(a) for a in [1.3, 35679.23, 0.4, 0.00045676] ])
    [1, 5, 0, -3]

    """
    return int(ceil(log10(abs(f))))


def niceNumber(f,below=False):
    """Return a nice number close to f.

    f is a float number, whose sign is disregarded.

    A number close to abs(f) but having only 1 significant digit is returned.
    By default, the value is above abs(f). Setting below=True returns a
    value above.

    Example:

      >>> numbers = [ 0.0837, 0.837, 8.37, 83.7, 93.7]
      >>> [ str(niceNumber(f)) for f in numbers ]
      ['0.09', '0.9', '9.0', '90.0', '100.0']
      >>> [ str(niceNumber(f,below=True)) for f in numbers ]
      ['0.08', '0.8', '8.0', '80.0', '90.0']
    """
    fa = abs(f)
    s = "%.0e" % fa
    m,n = map(int,s.split('e'))
    if not below:
        m = m+1
    return m*10.**n


def dotpr (A,B,axis=-1):
    """Return the dot product of vectors of A and B in the direction of axis.

    This multiplies the elements of the arrays A and B, and the sums the
    result in the direction of the specified axis. Default is the last axis.
    Thus, if A and B are sets of vectors in their last array direction, the
    result is the dot product of vectors of A with vectors of B.
    A and B should be broadcast compatible.

    >>> A = array( [[1.0, 1.0], [1.0,-1.0], [0.0, 5.0]] )
    >>> B = array( [[5.0, 3.0], [2.0, 3.0], [1.33,2.0]] )
    >>> print(dotpr(A,B))
    [  8.  -1.  10.]

    """
    A = asarray(A)
    B = asarray(B)
    return (A*B).sum(axis)


def length(A,axis=-1):
    """Returns the length of the vectors of A in the direction of axis.

    The components of the vectors are stored along the specified array axis
    (default axis is the last).
    """
    A = asarray(A)
    return sqrt((A*A).sum(axis))


def normalize(A,axis=-1):
    """Normalize the vectors of A in the direction of axis.

    The components of the vectors are stored along the specified array axis
    (default axis is the last).
    """
    A = asarray(A)
    shape = list(A.shape)
    shape[axis] = 1
    Al = length(A,axis).reshape(shape)
#    if (Al == 0.).any():
#        raise ValueError,"Normalization of zero vector."
    return A/Al


def projection(A,B,axis=-1):
    """Return the (signed) length of the projection of vector of A on B.

    The components of the vectors are stored along the specified array axis
    (default axis is the last).
    """
    d = dotpr(A,B,axis)
    Bl = length(B,axis)
    if (Bl == 0.).any():
        raise ValueError,"Projection on zero vector."
    return d/Bl


def orthog(A,B,axis=-1):
    """Return the component of vector of A that is orthogonal to B.

    The components of the vectors are stored along the specified array axis
    (default axis is the last).
    """
    p = projection(A,B,axis=-1)
    return A - p * normalize(B)


def norm(v,n=2):
    """Return thr `n`-norm of the vector `v`.

    Default is the quadratic norm (vector length).
    ``n == 1`` returns the sum.
    ``n<=0`` returns the max absolute value.
    """
    a = asarray(v).flat
    if n == 2:
        return sqrt((a*a).sum())
    if n > 2:
        return (a**n).sum()**(1./n)
    if n == 1:
        return a.sum()
    if n <= 0:
        return abs(a).max()
    return


def horner(a,u):
    """Compute the value of a polynom using Horner's rule.

    Parameters:

    - `a`: float(n+1,nd), `nd`-dimensional coefficients of the polynom of
      degree `n`, starting from lowest degree.
    - `u`: float(nu), parametric values where the polynom is evaluated

    Returns float(nu,nd), nd-dimensional values of the polynom.

    >>> print(horner([[1.,1.,1.],[1.,2.,3.]],[0.5,1.0]))
    [[ 1.5  2.   2.5]
     [ 2.   3.   4. ]]

    """
    a = asarray(a)
    u = asarray(u).reshape(-1,1)
    c = a[-1]
    for i in range(-2,-1-len(a),-1):
        c = c * u + a[i]
    return c


def solveMany(A,b,direct=True):
    """Solve many systems of linear equations.

    Parameters:

    - `A`: (ndof,ndof,nsys) shaped float array.
    - `b`: (ndof,nrhs,nsys) shaped float array.

    Returns: a float array `x` with same shape as `b`, where ``x[:,i,j]``
    solves the system of linear equations A[:,:,j].x[:,i,j] = b[:,i,j].

    For ndof in [1,2,3], all solutions are by default computed directly and
    simultaneously. If ``direct=False`` is specified, a general linear
    equation solver is called for each system of equations. This is also the
    method used if ``ndof>4``.
    """
    ndof,nrhs,nsys = b.shape
    if A.shape[:2] != (ndof,ndof):
        raise ValueError,"A(%s) and b(%s) have incompatible shape" % (A.shape,b.shape)

    if ndof < 4 and direct:
        A = addAxis(A,2)
        b = addAxis(b,1)

        if ndof == 1:
            x = b[0]/A[0,0]

        elif ndof == 2:
            denom = cross(A[:,0],A[:,1],axis=0)
            As = roll(A,-1,axis=1)
            As[:,1] *= -1.
            x = cross(b,As,axis=0) / denom

        elif ndof == 3:
            C = cross(roll(A,-1,axis=1),roll(A,-2,axis=1),axis=0)
            denom = dotpr(A[:,0],C[:,0],axis=0)
            x = dotpr(b,C,axis=0) / denom

    else:
        x = dstack([linalg.solve(A[:,:,i],b[:,:,i]) for i in range(nsys)])

    return x


def inside(p,mi,ma):
    """Return true if point p is inside bbox defined by points mi and ma"""
    return p[0] >= mi[0] and p[1] >= mi[1] and p[2] >= mi[2] and \
           p[0] <= ma[0] and p[1] <= ma[1] and p[2] <= ma[2]


def isClose(values,target,rtol=1.e-5,atol=1.e-8):
    """Returns an array flagging the elements close to target.

    `values` is a float array, `target` is a float value.
    `values` and `target` should be broadcastable to the same shape.

    The return value is a boolean array with shape of `values` flagging
    where the values are close to target.
    Two values `a` and `b` are considered close if
    :math:`| a - b | < atol + rtol * | b |`
    """
    values = asarray(values)
    target = asarray(target)
    return abs(values - target) < atol + rtol * abs(target)


def anyVector(v):
    """Create a 3D vector.

    v is some data compatible with a (3)-shaped float array.
    Returns v as such an array.
    """
    return asarray(v,dtype=Float).reshape((3))


def unitVector(v):
    """Return a unit vector in the direction of v.

    - `v` is either an integer specifying one of the global axes (0,1,2),
      or a 3-element array or compatible.
    """
    if array(v).size == 1:
        u = zeros((3),dtype=Float)
        u[v] = 1.0
    else:
        u = asarray(v,dtype=Float).reshape((3))
        ul = length(u)
        if ul <= 0.0:
            raise ValueError,"Zero length vector %s" % v
        u = u/ul
    return u


def rotationMatrix(angle,axis=None,angle_spec=DEG):
    """Return a rotation matrix over angle, optionally around axis.

    The angle is specified in degrees, unless angle_spec=RAD is specified.
    If axis==None (default), a 2x2 rotation matrix is returned.
    Else, axis should specifyi the rotation axis in a 3D world. It is either
    one of 0,1,2, specifying a global axis, or a vector with 3 components
    specifying an axis through the origin.
    In either case a 3x3 rotation matrix is returned.
    Note that:

    - rotationMatrix(angle,[1,0,0]) == rotationMatrix(angle,0)
    - rotationMatrix(angle,[0,1,0]) == rotationMatrix(angle,1)
    - rotationMatrix(angle,[0,0,1]) == rotationMatrix(angle,2)

    but the latter functions calls are more efficient.
    The result is returned as an array.
    """
    a = angle*angle_spec
    c = cos(a)
    s = sin(a)
    if axis==None:
        f = [[c,s],[-s,c]]
    elif array(axis).size == 1:
        f = [[0.0 for i in range(3)] for j in range(3)]
        axes = range(3)
        i,j,k = axes[axis:]+axes[:axis]
        f[i][i] = 1.0
        f[j][j] = c
        f[j][k] = s
        f[k][j] = -s
        f[k][k] = c
    else:
        X,Y,Z = unitVector(axis)
        t = 1.-c
        f = [ [ t*X*X + c  , t*X*Y + s*Z, t*X*Z - s*Y ],
              [ t*Y*X - s*Z, t*Y*Y + c  , t*Y*Z + s*X ],
              [ t*Z*X + s*Y, t*Z*Y - s*X, t*Z*Z + c   ] ]

    return array(f)


def rotmat(x):
    """Create a rotation matrix defined by 3 points in space.

    x is an array of 3 points.
    After applying the resulting rotation matrix to the global axes,
    the 0 axis becomes // to the vectors x0-x1,
    the 1 axis lies in the plane x0,x1,x2 and is orthogonal to x0-x1,
    and the 3 axis is orthogonal to the plane x0,x1,x2.
    """
    x = asanyarray(x)
    u = normalize(x[1]-x[0])
    v = normalize(x[2]-x[0])
    v = normalize(orthog(v,u))
    w = cross(u,v) # is orthog and normalized
    m = row_stack([u,v,w])
    return m


def trfMatrix(x,y):
    """Find the transformation matrix from points x0 to x1.

    x and y are each arrays of 3 non-colinear points.
    The return value is a tuple of a translation vector and a rotation
    matrix.
    The returned translation trl and rotationmatrix rot transform the
    points x thus that:

    - point x0 coincides with point y0,
    - line x0,x1 coincides with line y0,y1
    - plane x0,x1,x2 coincides with plane y0,y1,y2

    The rotation is to be applied first and should be around the first
    point x0. The full transformation of a Coords object is thus obtained
    by::

      (coords-x0)*rot+trl+x0 = coords*rot+(trl+x0-x0*rot)
    """
    # rotation matrices for both systems
    r1 = rotmat(x)
    r2 = rotmat(y)
    # combined rotation matrix
    r = dot(r1.transpose(),r2)
    # translation vector (in a rotate first operation
    t = y[0] - dot(x[0],r)
    return r,t


def rotMatrix(u,w=[0.,0.,1.],n=3):
    """Create a rotation matrix that rotates axis 0 to the given vector.

    u is a vector representing the
    Return either a 3x3(default) or 4x4(if n==4) rotation matrix.
    """
    u = unitVector(u)

    try:
        v = unitVector(cross(w,u))
    except:
        if w == [0.,0.,1.]:
            w = [0.,1.,0.]
            v = unitVector(cross(w,u))
        else:
            raise

    w = unitVector(cross(u,v))

    m = row_stack([u,v,w])

    if n != 4:
        return m
    else:
        a = identity(4)
        a[0:3,0:3] = m
        return a

# HOW DOES THIS DEAL WITH GIMBALL LOCK?
def rotationAnglesFromMatrix(mat,angle_spec=DEG):
    """Return rotation angles from rotation matrix mat.

    This returns the three angles around the global axes 0, 1 and 2.
    The angles are returned in degrees, unless angle_spec=RAD.
    """
    rx = arctan(mat[1,2]/mat[2,2])
    ry = -arcsin(mat[0,2])
    rz = arctan(mat[0,1]/mat[0,0])
    for rxi in [rx,pi+rx]:
        for ryi in [ry,pi-ry]:
            for rzi in [rz,pi+rz]:
                R = dot(dot(rotationMatrix(rxi,0,RAD),rotationMatrix(ryi,1,RAD)),rotationMatrix(rzi,2,RAD))
                T = isClose(mat,R,rtol=1.e-3,atol=1.e-3)
                if T.all():
                    return rxi / angle_spec, ryi / angle_spec, rzi / angle_spec


# WHAT IF EITHER vec1 or vec2 is // to upvec?
def vectorRotation(vec1,vec2,upvec=None):
    """Return a rotation matrix for rotating vector vec1 to vec2.

    If upvec is specified, the rotation matrix will be such that the plane of
    vec2 and the rotated upvec will be parallel to the original upvec.

    This function is like :func:`arraytools.rotMatrix`, but allows the
    specification of vec1.
    The returned matrix should be used in postmultiplication to the Coords.
    """
    u = normalize(vec1)
    u1 = normalize(vec2)
    if upvec is None:
        w = cross(u,u1)
        if length(w) == 0.: # vec1 and vec2 are parallel
            x,y,z = u
            w = array([1.,0.,0.]) if x==0. and y==0. else array([-y,x,0.])
        w = normalize(w)
        v = normalize(cross(w,u))
        v1 = normalize(cross(w,u1))
        w1 = w
    else:
        w = normalize(upvec)
        v = normalize(cross(w,u))
        w = normalize(cross(u,v))
        v1 = normalize(cross(w,u1))
        w1 = normalize(cross(u1,v1))
    mat1 = column_stack([u,v,w])
    mat2 = row_stack([u1,v1,w1])
    mat = dot(mat1,mat2)
    return mat


def growAxis(a,add,axis=-1,fill=0):
    """Increase the length of a single array axis.

    The specified axis of the array `a` is increased with a value `add` and
    the new elements all get the value `fill`.

    Parameters:

    - `a`: array.

    - `add`: int
      The value to add to the axis length. If<=0, the unchanged array
      is returned.

    - `axis`: int
      The axis to change, default -1 (last).

    - `fill`: int or float
      The value to set the new elements to.

    Returns an array with same dimension and type as `a`, but with a length along
    `axis` equal to ``a.shape[axis]+add``. The new elements all have the
    value `fill`.

    Example:

      >>> growAxis([[1,2,3],[4,5,6]],2)
      array([[1, 2, 3, 0, 0],
             [4, 5, 6, 0, 0]])

    """
    a = asarray(a)
    if axis >= len(a.shape):
        raise ValueError,"No such axis number!"
    if add <= 0:
        return a
    else:
        missing = list(a.shape)
        missing[axis] = add
        return concatenate([a,fill * ones(missing,dtype=a.dtype)],axis=axis)


def reorderAxis(a,order,axis=-1):
    """Reorder the planes of an array along the specified axis.

    The elements of the array are reordered along the specified axis
    according to the specified order.

    Parameters:

    - `a`: array_like
    - `order`: specifies how to reorder the elements. It is either one
      of the special string values defined below, or else it is an index
      holding a permutation of `arange(self.nelems()`. Each value specifies the
      index of the old element that should be placed at its position.
      Thus, the order values are the old index numbers at the position of the
      new index number.

      `order` can also take one of the following predefined values,
      resulting in the corresponding renumbering scheme being generated:

      - 'reverse': the elements along axis are placed in reverse order
      - 'random': the elements along axis are placed in random order

    Returns an array with the same elements of self, where only the order
    along the specified axis has been changed.

    Example::

      >>> reorderAxis([[1,2,3],[4,5,6]],[2,0,1])
      array([[3, 1, 2],
             [6, 4, 5]])

    """
    a = asarray(a)
    n = a.shape[axis]
    if order == 'reverse':
        order = arange(n-1,-1,-1)
    elif order == 'random':
        order = random.permutation(n)
    else:
        order = asarray(order)
    return a.take(order,axis)


def reverseAxis(a,axis=-1):
    """Reverse the elements along a computed axis.

    Example::

      >>> reverseAxis([[1,2,3],[4,5,6]],0)
      array([[4, 5, 6],
             [1, 2, 3]])

    Note that if the axis is known in advance, it may be more efficient to use
    an indexing operation::

      >>> A = array([[1,2,3],[4,5,6]])
      >>> print(A[:,::-1])
      [[3 2 1]
       [6 5 4]]

    """
    return reorderAxis(a,'reverse',axis)


def addAxis(a,axis=0):
    """Add an additional axis with length 1 to an array.

    The new axis is inserted before the specified one. Default is to
    add it at the front.
    """
    s = list(a.shape)
    s[axis:axis] = [1]
    return a.reshape(s)


def stack(al,axis=0):
    """Stack a list of arrays along a new axis.

    al is a list of arrays all of the same shape.
    The return value is a new array with one extra axis, along which the
    input arrays are stacked. The position of the new axis can be specified,
    and is the first axis by default.
    """
    return concatenate([addAxis(ai,axis) for ai in al],axis=axis)


def concat(al,axis=0):
    """Smart array concatenation ignoring empty arrays"""
    if len(al) > 0:
        return concatenate([a for a in al if a.size > 0],axis=axis)
    else:
        return []


def splitrange(n,nblk):
    """Split the range of integers 0..n in nblk almost equal sized slices.

    This divides the range of integer numbers 0..n in nblk slices of (almost)
    equal size. If n > nblk, returns nblk+1 integers in the range 0..n.
    If n <= nblk, returns range(n+1).

    Example:

      >>> splitrange(7,3)
      array([0, 2, 5, 7])
    """
    if n > nblk:
        ndata = (arange(nblk+1) * n * 1.0 / nblk).round().astype(int)
    else:
        ndata = range(n+1)
    return ndata


def splitar(ar,nblk,close=False):
    """Split an array in nblk subarrays along axis 0.

    Splits the array ar along its first axis in nblk blocks of (almost)
    equal size.

    Returns a list of nblk arrays, unless the size of the array is smaller
    than nblk, in which case a list with the original array is returned.

    If close==True, the elements where the array is split occur in both
    blocks delimited by the element.

    Example:

      >>> splitar(arange(7),3)
      [array([0, 1]), array([2, 3, 4]), array([5, 6])]
      >>> splitar(arange(7),3,close=True)
      [array([0, 1, 2]), array([2, 3, 4]), array([4, 5, 6])]
    """
    ar = asanyarray(ar)
    na = ar.shape[0]
    if close:
        na -= 1
    if nblk > na:
        return [ar]

    ndata = splitrange(na,nblk)
    if close:
        return [ ar[i:j+1] for i,j in zip(ndata[:-1],ndata[1:]) ]
    else:
        return [ ar[i:j] for i,j in zip(ndata[:-1],ndata[1:]) ]


def checkInt(value,min=None,max=None):
    """Check that a value is an int in the range min..max

    Range borders that are None are not checked upon.
    Returns an int in the specified range.
    Raises an exception if the value is invalid.
    """
    try:
        a = int(value)
        if min is not None and a < min:
            raise
        if max is not None and a > max:
            raise
        return a
    except:
        raise ValueError,"Expected an int in the range(%s, %s), got: %s" % (value)


def checkFloat(value,min=None,max=None):
    """Check that a value is a float in the range min..max

    Range borders that are None are not checked upon.
    Returns a float in the specified range.
    Raises an exception if the value is invalid.
    """
    try:
        a = float(value)
        if min is not None and a < min:
            raise
        if max is not None and a > max:
            raise
        return a
    except:
        raise ValueError,"Expected a float in the range(%s, %s), got: %s" % (min,max,value)


def checkArray(a,shape=None,kind=None,allow=None):
    """Check that an array a has the correct shape and type.

    The input `a` is anything that can be converted into a numpy array.
    Either `shape` and/or `kind` can be specified. and will then be checked.
    The dimensions where `shape` contains a -1 value are not checked. The
    number of dimensions should match.
    If `kind` does not match, but the value is included in `allow`,
    conversion to the requested type is attempted.

    Returns the array if valid; else, an error is raised.
    """
    try:
        a = asarray(a)
        shape = asarray(shape)
        w = where(shape >= 0)[0]
        if (asarray(a.shape)[w] != shape[w]).any():
            raise
        if kind is not None:
            if allow is None and a.dtype.kind != kind:
                raise
            if kind == 'f':
                a = a.astype(Float)
        return a
    except:
        raise ValueError,"Expected shape %s, kind %s, got: %s, %s" % (shape,kind,a.shape,a.dtype.kind)



def checkArray1D(a,size=None,kind=None,allow=None):
    """Check that an array a has the correct size and type.

    Either size and or kind can be specified.
    If kind does not match, but is included in allow, conversion to the
    requested type is attempted.
    Returns the array if valid.
    Else, an error is raised.
    """
    try:
        a = asarray(a)#.ravel() # seems sensible not to ravel!
        if (size is not None and a.size != size):
            raise
        if kind is not None:
            if allow is None and a.dtype.kind != kind:
                raise
            if kind == 'f':
                a = a.astype(Float)
        return a
    except:
        raise ValueError,"Expected size %s, kind %s, got: %s" % (size,kind,a)


def checkArrayDim(a,ndim=-1):
    """Check that an array has the correct dimensionality.

    Returns asarray(a) if ndim < 0 or a.ndim == ndim
    Else, an error is raised.
    """
    try:
        aa = asarray(a)
        if (ndim >= 0 and aa.ndim != ndim):
            raise
        return aa
    except:
        raise ValueError,"Expected an array with %s dimensions" % ndim


def checkUniqueNumbers(nrs,nmin=0,nmax=None):
    """Check that an array contains a set of unique integers in a given range.

    This functions tests that all integer numbers in the array are within the
    range math:`nmin <= i < nmax`

    Parameters:

    - `nrs`: an integer array of any shape.
    - `nmin`: minimum allowed value. If set to None, the test is skipped.
    - `nmax`: maximum allowed value + 1! If set to None, the test is skipped.

    Default range is [0,unlimited].

    If the numbers are no unique or one of the limits is passed, an error
    is raised. Else, the sorted list of unique values is returned.
    """
    nrs = asarray(nrs)
    uniq = unique(nrs)
    if uniq.size != nrs.size or \
           (nmin is not None and uniq.min() < nmin) or \
           (nmax is not None and uniq.max() > nmax):
        raise ValueError,"Values not unique or not in range"
    return uniq


def readArray(file,dtype,shape,sep=' '):
    """Read an array from an open file.

    This uses :func:`numpy.fromfile` to read an array with known shape and
    data type from an open file.
    The sep parameter can be specified as in `numpy.fromfile`.
    If an empty string is given as separator, the data is read in
    binary mode. In that case (only) an extra '\\n' after the data
    will be stripped off.
    """
    shape = asarray(shape)
    size = shape.prod()
    data = fromfile(file=file,dtype=dtype,count=size,sep=sep).reshape(shape)
    if sep == '':
        pos = file.tell()
        byte = file.read(1)
        if not ord(byte) == 10:
            # not a newline: push back
            file.seek(pos)
    return data


def writeArray(file,array,sep=' '):
    """Write an array to an open file.

    This uses :func:`numpy.tofile` to write an array to an open file.
    The sep parameter can be specified as in tofile.
    """
    array.tofile(file,sep=sep)


def cubicEquation(a,b,c,d):
    """Solve a cubiq equation using a direct method.

    a,b,c,d are the (floating point) coefficients of a third degree
    polynomial equation::

      a*x**3+b*x**2+c*x+d=0

    This function computes the three roots (real and complex) of this equation
    and returns full information about their kind, sorting order, occurrence
    of double roots. It uses scaling of the variables to enhance the accuracy.

    The return value is a tuple (r1,r2,r3,kind), where r1,r2 and r3 are three
    float values and kind is an integer specifying the kind of roots.

    Depending on the value of `kind`, the roots are defined as follows:

    ======     ============================================================
     kind        roots
    ======     ============================================================
      0         three real roots r1 < r2 < r3
      1         three real roots r1 < r2 = r3
      2         three real roots r1 = r2 < r3
      3         three real roots r1 = r2 = r3
      4         one real root r1 and two complex conjugate roots with real
                part r2 and imaginary part r3; the complex roots are thus:
                r2+i*r3 en r2-i*r3, where i=sqrt(-1).
    ======     ============================================================

    If the coefficient a==0, a ValueError is raised.

    Example:

      >>> cubicEquation(1.,-3.,3.,-1.)
      ([1.0, 1.0, 1.0], 3)

    """
    #
    # BV: We should return the solution of a second degree equation if a==0
    #
    if a == 0.0:
        raise ValueError,"Coeeficient a of cubiq equation should not be 0"

    e3 = 1./3.
    pie = pi*2.*e3
    r = b/a
    s = c/a
    t = d/a

    # scale variable
    sc = max(abs(r),sqrt(abs(s)),abs(t)**e3)
    sc = 10**(int(log10(sc)))
    r = r/sc
    s = s/sc/sc
    t = t/sc/sc/sc

    rx = r*e3
    p3 = (s-r*rx)*e3
    q2 = rx**3-rx*s/2.+t/2.

    q2s = q2*q2
    p3c = p3**3
    som = q2s+p3c

    if som <= 0.0:

        # 3 different real roots
        ic = 0
        roots = [ -rx ] * 3
        rt = sqrt(-p3c)
        if abs(rt) > 0.0:
            phi = cos(-q2/rt)*e3
            rt = 2.*sqrt(-p3)
            roots += rt * cos(phi + [0.,+pie, -pie])

        # sort the 3 roots

        roots.sort()
        if roots[1] == roots[2]:
            ic += 1
        if roots[1] == roots[0]:
            ic += 2

    else: # som < 0.0
        #  1 real and 2 complex conjugate roots
        ic = 4
        som = sqrt(som)
        u = -q2+som
        u = sign(abs(u)**e3) * u
        v = -q2-som
        v = sign(abs(v)**e3) * v
        r1 = u+v
        r2 = -r1/2-rx
        r3 = (u-v)*sqrt(3.)/2.
        r1 = r1-rx
        roots = array([r1,r2,r3])

    # scale and return values
    roots *= sc
    return roots,ic


# THIS MAY BE FASTER THAN olist.collectOnLength, BUT IT IS DEPENDENT ON NUMPY

## def collectOnLength(items):
##     """Collect items with same length.

##     a is a list of items of any type for which the function len()
##     returns an integer value.
##     The items are sorted in a number of bins, each containing the
##     items with the same length.
##     The return value is a tuple of:
##     - a list of bins with the sorted items,
##     - a list of indices of these items in the input list,
##     - a list of lengths of the bins,
##     - a list of the item length in each bin.
##     """
##     np = array([ len(e) for e in items ])
##     itemlen = unique(np)
##     itemnrs = [ where(np==p)[0] for p in itemlen ]
##     itemgrps = [ olist.select(items,i) for i in itemnrs ]
##     itemcnt = [ len(i) for i in itemnrs ]
##     return itemgrps,itemnrs,itemcnt,itemlen


def uniqueOrdered(ar1, return_index=False, return_inverse=False):
    """
    Find the unique elements of an array.

    This works like numpy's unique, but uses a stable sorting algorithm.
    The returned index may therefore hold other entries for multiply
    occurring values. In such case, uniqueOrdered returns the first
    occurrence in the flattened array.
    The unique elements and the inverse index are always the same as those
    returned by numpy's unique.

    Parameters:

    - `ar1`: array_like
      This array will be flattened if it is not already 1-D.
    - `return_index`: bool, optional
      If True, also return the indices against `ar1` that result in the
      unique array.
    - `return_inverse`: bool, optional
      If True, also return the indices against the unique array that
      result in `ar1`.

    Returns:

    - `unique`: ndarray
      The unique values.
    - `unique_indices`: ndarray, optional
      The indices of the unique values. Only provided if `return_index` is
      True.
    - `unique_inverse`: ndarray, optional
      The indices to reconstruct the original array. Only provided if
      `return_inverse` is True.

    Example::

      >>> a = array([2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,7,8])
      >>> uniq,ind,inv = unique(a,True,True)
      >>> print(uniq)
      [1 2 3 4 5 6 7 8]
      >>> print(ind)
      [7 0 1 2 3 4 5 6]
      >>> print(inv)
      [1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 6 7]
      >>> uniq,ind,inv = uniqueOrdered(a,True,True)
      >>> print(uniq)
      [1 2 3 4 5 6 7 8]
      >>> print(ind)
      [7 0 1 2 3 4 5 6]
      >>> print(inv)
      [1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 6 7]

    Notice the difference in the fourth element of the `ind` array.

    """
    import numpy as np
    ar = np.asanyarray(ar1).flatten()
    if ar.size == 0:
        if return_inverse and return_index:
            return ar, np.empty(0, np.bool), np.empty(0, np.bool)
        elif return_inverse or return_index:
            return ar, np.empty(0, np.bool)
        else:
            return ar

    if return_inverse or return_index:
        perm = ar.argsort(kind='mergesort')
        aux = ar[perm]
        flag = np.concatenate(([True], aux[1:] != aux[:-1]))
        if return_inverse:
            iflag = np.cumsum(flag) - 1
            iperm = perm.argsort()
            if return_index:
                return aux[flag], perm[flag], iflag[iperm]
            else:
                return aux[flag], iflag[iperm]
        else:
            return aux[flag], perm[flag]

    else:
        ar.sort()
        flag = np.concatenate(([True], ar[1:] != ar[:-1]))
        return ar[flag]


def renumberIndex(index):
    """Renumber an index sequentially.

    Given a one-dimensional integer array with only non-negative values,
    and `nval` being the number of different values in it, and you want to
    replace its elements with values in the range `0..nval`, such that
    identical numbers are always replaced with the same number and the
    new values at their first occurrence form an increasing sequence `0..nval`.
    This function will give you the old numbers corresponding with each
    position `0..nval`.

    Parameters:

    - `index`: array_like, 1-D, integer
      An array with non-negative integer values

    Returns:

      A 1-D integer array with length equal to `nval`, where `nval`
      is the number of different values in `index`, and holding the original
      values corresponding to the new value `0..nval`.

    Remark:

      Use :func:`inverseUniqueIndex` to find the inverse mapping
      needed to replace the values in the index by the new ones.

    Example::

      >>> renumberIndex([0,5,2,2,6,0])
      array([0, 5, 2, 6])
      >>> inverseUniqueIndex(renumberIndex([0,5,2,2,6,0]))[[0,5,2,2,6,0]]
      array([0, 1, 2, 2, 3, 0])

    """
    un,pos = uniqueOrdered(index,True)
    srt = pos.argsort()
    old = un[srt]
    return old


def complement(index,n=-1):
    """Return the complement of an index in a range(0,n).

    The complement is the list of numbers from the range(0,n) that are
    not included in the index.

    Parameters:

    - `index`: array_like, 1-D, int or bool. If integer, it is a list with
      the non-negative numbers to be excluded from the range(0,n).
      If boolean, it normally has the length of the range and flags the
      elements to be returned with a False value.

    - `n`: int: the upper limit for the range of numbers. If `index` is of
      type integer and `n` is not specified or is negative, it will be set
      equal to the largest number in `index` plus 1. If `index` is of type
      boolean and `n` is larger than the length of `index`, `index` will be
      padded with `False` values until length `n`.

    Returns:

      If `index` is integer: a 1-D integer array with the numbers from
      range(0,n) that are not included in `index`. If `index` is boolean,
      the negated `index` padded to or cut at length `n`.

    Example:

      >>> print(complement([0,5,2,6]))
      [1 3 4]
      >>> print(complement([0,5,2,6],10))
      [1 3 4 7 8 9]
      >>> print(complement([False,True,True,True],6))
      [ True False False False  True  True]
    """
    index = asarray(index)
    if index.dtype == bool:
        m = index.shape[0]
        if n > m:
            comp = ones(n,dtype=bool)
            comp[:m] = ~index
        else:
            comp = ~index[:n]
    else:
        if n < 0:
            n = max(n,1+index.max())
        comp = delete(arange(n),index)
    return comp


def inverseUniqueIndex(index):
    """Inverse an index.

    Given a 1-D integer array with *unique* non-negative values, and
    `max` being the highest value in it, this function returns the position
    in the array of the values `0..max`. Values not occurring in input index
    get a value -1 in the inverse index.

    Parameters:

    - `index`: array_like, 1-D, integer
      An array with non-negative values, which all have to be unique.

    Returns:

      A 1-D integer array with length `max+1`, with the positions in
      `index` of the values `0..max`, or -1 if the value does not occur in
      `index`.

    Remark:

      The inverse index translates the unique index numbers in a
      sequential index, so that
      ``inverseUniqueIndex(index)[index] == arange(1+index.max())``.


    Example::

      >>> inverseUniqueIndex([0,5,2,6])
      array([ 0, -1,  2, -1, -1,  1,  3])
      >>> inverseUniqueIndex([0,5,2,6])[[0,5,2,6]]
      array([0, 1, 2, 3])

    """
    ind = asarray(index)
    inv = -ones(ind.max()+1,dtype=ind.dtype)
    inv[ind] = arange(ind.size,dtype=inv.dtype)
    return inv


def sortSubsets(a,w=None):
    """Sort subsets of an integer array a.

    a is a 1-D integer array. Subsets of the array are the collections
    of equal values.
    w is a float array with same size of a, specifying a weight for each
    of the array elements in a.
    If no weight is specified, all elements have the same weight.

    The subsets of a are sorted in order of decreasing total weight of the
    subsets (or number of elements if weight is None).

    The return value is an integer array of the same size of a, specifying
    for each element the index of its subset in the sorted list of subsets.

    Example:

      >>> sortSubsets([0,1,2,3,1,2,3,2,3,3])
      array([3, 2, 1, 0, 2, 1, 0, 1, 0, 0])

      >>> sortSubsets([0,1,2,3,1,2,3,2,3,3],w=[9,8,7,6,5,4,3,2,1,0])
      array([3, 1, 0, 2, 1, 0, 2, 0, 2, 2])
    """
    a = asarray(a).ravel()
    if w is None:
        h = histogram(a,list(unique(a))+[a.max()+1])[0]
    else:
        w = asarray(w).ravel()
        h = [w[a==j].sum() for j in unique(a)]
    srt = argsort(h)[::-1]
    inv = inverseUniqueIndex(srt)
    return inv[a]


def sortByColumns(a):
    """Sort an array on all its columns, from left to right.

    The rows of a 2-dimensional array are sorted, first on the first
    column, then on the second to resolve ties, etc..

    Parameters:

    - `a`: array_like, 2-D

    Returns a 1-D integer array specifying the order in which the rows have to
      be taken to obtain an array sorted by columns.

    Example::

      >>> sortByColumns([[1,2],[2,3],[3,2],[1,3],[2,3]])
      array([0, 3, 1, 4, 2])

    """
    A = checkArrayDim(a,2)
    keys = [A[:,i] for i in range(A.shape[1]-1,-1,-1)]
    return lexsort(keys)


def uniqueRows(a,permutations=False):
    """Find the unique rows of a 2-D array.

    Parameters:

    - `a`: array_like, 2-D
    - `permutations`: bool
      If True, rows which are permutations of the same data are considered
      equal. The default is to consider permutations as different.

    Returns:

    - `uniq`: a 1-D integer array with the numbers of the unique rows from `a`.
      The order of the elements in `uniq` is determined by the sorting
      procedure: in the current implementation this is :func:`sortByColumns`.
      If `permutations==True`, `a` is sorted along its axis -1 before calling
      this sorting function.
    - `uniqid`: a 1-D integer array with length equal to `a.shape[0]` with the
      numbers of `uniq` corresponding to each of the rows of `a`.

    Example::

      >>> uniqueRows([[1,2],[2,3],[3,2],[1,3],[2,3]])
      (array([0, 3, 1, 2]), array([0, 2, 3, 1, 2]))
      >>> uniqueRows([[1,2],[2,3],[3,2],[1,3],[2,3]],permutations=True)
      (array([0, 3, 1]), array([0, 2, 2, 1, 2]))

    """
    A = array(a,copy=permutations)
    if A.ndim != 2:
        raise ValueError
    if permutations:
        A.sort(axis=-1)
    srt = sortByColumns(A)
    A = A.take(srt,axis=0)
    ok = (A != roll(A,1,axis=0)).any(axis=1)
    if not ok[0]: # all doubles -> should result in one unique element
        ok[0] = True
    w = where(ok)[0]
    inv = inverseUniqueIndex(srt)
    uniqid = w.searchsorted(inv,side='right')-1
    uniq = srt[ok]
    return uniq,uniqid


def argNearestValue(values,target):
    """Return the index of the item nearest to target.

    Parameters:

    - `values`: a list of float values
    - `target`: a float value

    Returns the position of the item in `values` that is
    nearest to `target`.

    Example:

      >>> argNearestValue([0.1,0.5,0.9],0.7)
      1
    """
    v = array(values).ravel()
    c = v - target
    return argmin(c*c)


def nearestValue(values,target):
    """Return the item nearest to target.

    ``values``: a list of float values

    ``target``: a single value

    Returns the item in ``values`` values that is
    nearest to ``target``.
    """
    return values[argNearestValue(values,target)]

#
# BV: This is a candidate for the C-library
#

def inverseIndex(index,maxcon=4):
    """Return an inverse index.

    An index is an array pointing at other items by their position.
    The inverse index is a collection of the reverse pointers.
    Negative values in the input index are disregarded.

    Parameters:

    - `index`: an array of integers, where only non-negative values are
      meaningful, and negative values are silently ignored. A Connectivity
      is a suitable argument.
    - `maxcon`: int: an initial estimate for the maximum number of rows a
      single element of index occurs at. The default will usually do well,
      because the procedure will automatically enlarge it when needed.

    Returns:

      An (mr,mc) shaped integer array where:

      - `mr` will be equal to the highest positive value in index, +1.
      - `mc` will be equal to the highest row-multiplicity of any number
        in `index`.

      Row `i` of the inverse index contains all the row numbers of `index`
      that contain the number `i`. Because the number of rows containing
      the number `i` is usually not a constant, the resulting array will have
      a number of columns `mc` corresponding to the highest row-occurrence of
      any single number. Shorter rows are padded with -1 values to flag
      non-existing entries.

    Example::

      >>> inverseIndex([[0,1],[0,2],[1,2],[0,3]])
      array([[ 0,  1,  3],
             [-1,  0,  2],
             [-1,  1,  2],
             [-1, -1,  3]])

    """
    ind = asarray(index)
    if len(ind.shape) != 2 or ind.dtype.kind != 'i':
        raise ValueError,"nndex should be an integer array with dimension 2"
    nr,nc = ind.shape
    mr = ind.max() + 1
    mc = maxcon*nc
    # start with all -1 flags, maxcon*nc columns (because in each column
    # of index, some number might appear with multiplicity maxcon)
    inverse = zeros((mr,mc),dtype=ind.dtype) - 1
    i = 0 # column in inverse where we will store next result
    for c in range(nc):
        col = ind[:,c].copy()  # make a copy, because we will change it
        while(col.max() >= 0):
            # we still have values to process in this column
            uniq,pos = unique(col,True)
            #put the unique values at a unique position in inverse index
            ok = uniq >= 0
            if i >= inverse.shape[1]:
                # no more columns available, expand it
                inverse = concatenate([inverse,zeros_like(inverse)-1],axis=-1)
            inverse[uniq[ok],i] = pos[ok]
            i += 1
            # remove the stored values from index
            col[pos[ok]] = -1

    inverse.sort(axis=-1)
    maxc = inverse.max(axis=0)
    inverse = inverse[:,maxc>=0]
    return inverse


def matchIndex(target,values):
    """Find position of values in target.

    This function finds the position in the array `target` of the elements
    from the array `values`.

    Parameters:

    - `target`: an index array with all non-negative values. If not 1-D, it
      will be flattened.
    - `values`: an index array with all non-negative values. If not 1-D, it
      will be flattened.

    Returns:

      An index array with the same size as `values`.
      For each number in `values`, the index contains the position of that value
      in the flattened `target`, or -1 if that number does not occur in `target`.
      If an element from `values` occurs more than once in `target`, it is
      currently undefined which of those positions is returned.

    Remark that after ``m = matchIndex(target,values)`` the equality
    ``target[m] == values`` holds in all the non-negative positions of `m`.

    Example:

      >>> A = array([1,3,4,5,7,8,9])
      >>> B = array([0,6,7,1,2])
      >>> matchIndex(A,B)
      array([-1, -1,  4,  0, -1])
    """
    target = target.reshape(-1,1)
    values = values.reshape(-1)
    inv = inverseIndex(target)[:,0]
    diff = values.max()-len(inv)+1
    if diff > 0:
        inv = concatenate([inv,-ones((diff,),dtype=Int)])
    return inv[values]


## THIS IS A CANDIDATE FOR THE LIBRARY !!!
def groupArgmin(val,gid):
    """Compute the group minimum

    Computes the minimum value per group of a set of values tagged with
    a group number.

    Parameters:

    - `val`: (nval,) shaped array of values
    - `gid`: (nval,) shaped int array of group identifiers

    Returns:

    - `ugid`: (ngrp,) shaped int array with unique group identifiers
    - `minpos`: (ngrp,p) shape int array giving the position in `val` of
      the minimum of all values with the corresponding group identifier
      in `ugid`.

    After return, the minimum values corresponding to the groups in `ugid`
    are given by ``val[minpos]``.

    >>> val = array([ 0.0, 1.0, 2.0, 3.0, 4.0, -5.0 ])
    >>> gid = array([ 2, 1, 1, 6, 6, 1 ])
    >>> print(groupArgmin(val,gid))
    (array([1, 2, 6]), array([5, 0, 3]))
    """
    ugid = unique(gid)
    minid = hstack([ val[gid == i].argmin() for i in ugid ])
    rng = arange(val.size)
    minpos = hstack([ rng[gid == i][j] for i,j in zip(ugid,minid) ])
    return ugid,minpos


###########################################################
# Working with sets of vectors

def vectorLength(vec):
    """Return the lengths of a set of vectors.

    vec is an (n,3) shaped array holding a collection of vectors.
    The result is an (n,) shaped array with the length of each vector.
    """
    return length(vec)


def vectorNormalize(vec):
    """Normalize a set of vectors.

    vec is a (n,3) shaped arrays holding a collection of vectors.
    The result is a tuple of two arrays:

    - length (n): the length of the vectors vec
    - normal (n,3): unit-length vectors along vec.
    """
    length = vectorLength(vec)
    normal = vec / length.reshape((-1,1))
    return length,normal


def vectorPairAreaNormals(vec1,vec2):
    """Compute area of and normals on parallellograms formed by vec1 and vec2.

    vec1 and vec2 are (n,3) shaped arrays holding collections of vectors.
    As a convenience, single vectors may also be specified with shape (3,),
    and will be converted to (1,3).

    The result is a tuple of two arrays:

    - area (n) : the area of the parallellogram formed by vec1 and vec2.
    - normal (n,3) : (normalized) vectors normal to each couple (vec1,2).

    These are calculated from the cross product of vec1 and vec2, which indeed
    gives area * normal.

    Note that where two vectors are parallel, an area zero results and
    an axis with components NaN.
    """
    normal = cross(vec1.reshape(-1,3),vec2.reshape(-1,3))
    area = vectorLength(normal)
    errh = seterr(divide='ignore',invalid='ignore')
    normal /= area.reshape((-1,1))
    seterr(**errh)
    return area,normal


def vectorPairArea(vec1,vec2):
    """Compute area of the parallellogram formed by a vector pair vec1,vec2.

    vec1 and vec2 are (n,3) shaped arrays holding collections of vectors.
    The result is an (n) shaped array with the area of the parallellograms
    formed by each pair of vectors (vec1,vec2).
    """
    normal = cross(vec1.reshape(-1,3),vec2.reshape(-1,3))
    return length(normal)


def vectorPairNormals(vec1,vec2):
    """Compute vectors normal to vec1 and vec2.

    vec1 and vec2 are (n,3) shaped arrays holding collections of vectors.
    The result is an (n,3) shaped array of unit length vectors normal to
    each couple (edg1,edg2).
    """
    return vectorPairAreaNormals(vec1,vec2)[1]


def vectorTripleProduct(vec1,vec2,vec3):
    """Compute triple product vec1 . (vec2 x vec3).

    vec1, vec2, vec3 are (n,3) shaped arrays holding collections of vectors.
    The result is a (n,) shaped array with the triple product of each set
    of corresponding vectors from vec1,vec2,vec3.
    This is also the square of the volume of the parallellepid formex by
    the 3 vectors.
    If vec1 is a unit normal, the result is also the area of the parallellogram
    (vec2,vec3) projected in the direction vec1.
    """
    return dotpr(vec1,cross(vec2,vec3))


def vectorPairCosAngle(v1,v2):
    """Return the cosinus of the angle between the vectors v1 and v2.

    vec1 and vec2 are (n,3) shaped arrays holding collections of vectors.
    The result is an (n) shaped array with the cosinus of the angle between
    each pair of vectors (vec1,vec2).
    """
    v1 = asarray(v1)
    v2 = asarray(v2)
    cos = dotpr(v1,v2) / sqrt(dotpr(v1,v1)*dotpr(v2,v2))
    # clip to [-1.,1.] in case of rounding errors
    return cos.clip(min=-1.,max=1.)


def vectorPairAngle(v1,v2):
    """Return the angle (in radians) between the vectors v1 and v2.

    vec1 and vec2 are (n,3) shaped arrays holding collections of vectors.
    The result is an (n) shaped array with the angle between
    each pair of vectors (vec1,vec2).
    """
    return arccos(vectorPairCosAngle(v1,v2))


def multiplicity(a):
    """Return the multiplicity of the numbers in a

    a is a 1-D integer array.

    Returns a tuple of:

    - 'mult': the multiplicity of the unique values in a
    - 'uniq': the sorted list of unique values in a

    Example:

      >>> multiplicity([0,3,5,1,4,1,0,7,1])
      (array([2, 3, 1, 1, 1, 1]), array([0, 1, 3, 4, 5, 7]))
    """
    bins = unique(a)
    mult,b = histogram(a,bins=concatenate([bins,[max(a)+1]]))
    return mult,bins


def histogram2(a,bins,range=None):
    """Compute the histogram of a set of data.

    This function is like numpy's histogram function, but also returns
    the bin index for each individual entry in the data set.

    Parameters:

    - `a`: array_like.
      Input data. The histogram is computed over the flattened array.

    - `bins`: int or sequence of scalars.
      If bins is an int, it defines the number of equal-width bins
      in the given range. If bins is a sequence, it defines the bin edges,
      allowing for non-uniform bin widths. Both the leftmost and rightmost
      edges are included, thus the number of bins is len(bins)-1.

    - `range`: (float, float), optional. The lower and upper range of the bins.
      If not provided, range is simply (a.min(), a.max()). Values outside the
      range are ignored. This parameter is ignored if bins is a sequence.

    Returns:

    - `hist`: integer array with length nbins, holding the number of elements
      in each bin,
    - `ind`: a sequence of nbins integer arrays, each holding the indices of
      the elements fitting in the respective bins,
    - `xbins`: array of same type as data and with length nbins+1:
      returns the bin edges.

    Example:

      >>> hist,ind,xbins = histogram2([1,2,3,4,2,3,1],[1,2,3,4,5])
      >>> print(hist)
      [2 2 2 1]
      >>> for i in ind: print(i)
      [0 6]
      [1 4]
      [2 5]
      [3]
      >>> print(xbins)
      [1 2 3 4 5]
    """
    ar = asarray(a)
    if array(bins).size == 1:
        nbins = bins
        xbins = linspace(a.min(),a.max(),nbins+1)
    else:
        xbins = asarray(bins)
        nbins = len(xbins)-1
    d = digitize(ar,xbins)
    ind = [ where(d==i)[0] for i in arange(1,nbins+1) ]
    hist = asarray([ i.size for i in ind ])
    return hist,ind,xbins


def movingView(a, size):
    """Create a moving view along the first axis of an array

    Parameters:

    - `a` : array_like: array for wihch to create a moving view
    - `size` : int: size of the moving view

    Returns an array that is a view of the original array with an extra first
      axis of length w.

      Using swapaxes(0,axis) moving views over any axis can be created.

    Example:

      >>> x=arange(10).reshape((5,2))
      >>> print(x)
      [[0 1]
       [2 3]
       [4 5]
       [6 7]
       [8 9]]
      >>> print(movingView(x, 3))
      [[[0 1]
        [2 3]
        [4 5]]
      <BLANKLINE>
       [[2 3]
        [4 5]
        [6 7]]
      <BLANKLINE>
       [[4 5]
        [6 7]
        [8 9]]]

    Calculate rolling sum of first axis:

      >>> print(movingView(x, 3).sum(axis=0))
      [[ 6  9]
       [12 15]
       [18 21]]
    """
    from numpy.lib import stride_tricks
    if size < 1:
        raise ValueError, "`size` must be at least 1."
    if size > a.shape[0]:
        raise ValueError, "`size` is too long."
    shape = (size, a.shape[0] - size + 1) + a.shape[1:]
    strides = (a.strides[0],) + a.strides
    return stride_tricks.as_strided(a, shape=shape, strides=strides)


def movingAverage(a,n,m0=None,m1=None):
    """Compute the moving average along the first axis of an array.

    Parameters:

    - `a` : array_like: array to be averaged
    - `n` : int: moving sample size
    - `m0` : optional, int: if specified, the first data set of a will
      be prepended this number of times
    - `m1` : optional, int: if specified, the last data set of a will
      be appended this number of times

    Returns:

      An array with the moving average over n data sets along the first axis of a.
      The array has the same shape as a, except possibly for the length of the
      first axis.
      If neither m0 nor m1 are set, the first axis will have a length of
      a.shape[0] - (n-1).
      If both m0 and m1 are give, the first axis will have a length of
      a.shape[0] - (n-1) + m0 + m1.
      If either m0 or m1 are set and the other not, the missing value m0 or m1
      will be computed thus that the return array has a first axis with length
      a.shape[0].

    Example:

      >>> x=arange(10).reshape((5,2))
      >>> print(movingAverage(x,3))
      [[ 2.  3.]
       [ 4.  5.]
       [ 6.  7.]]
      >>> print(movingAverage(x,3,2))
      [[ 0.          1.        ]
       [ 0.66666667  1.66666667]
       [ 2.          3.        ]
       [ 4.          5.        ]
       [ 6.          7.        ]]
    """
    if m0 is None and m1 is None:
        ae = a
    else:
        if m0 is None:
            m0 = n-1 - m1
        elif m1 is None:
            m1 = n-1 - m0
        ae = [a[:1]] * m0 + [ a ] + [a[-1:]] * m1
        ae = concatenate(ae,axis=0)
    return movingView(ae,n).mean(axis=0)


def randomNoise(shape,min=0.0,max=1.0):
    """Create an array with random values between min and max"""
    return random.random(shape) * (max-min) + min


def unitDivisor(div,start=0):
    """Divide a unit interval in equal parts.

    This function is intended to be used by interpolation functions
    that accept an input as either an int or a list of floats.

    Parameters:

    - `div`: an integer, or a list of floating point values.
      If it is an integer, returns a list of floating point values
      dividing the interval 0.0 toi 1.0 in div equal parts.
    - `start`: Set to 1 to skip the start value (0.0) of the interval.

    Returns: If `div` is a an integer, returns the floating point values
    dividing the unit interval in div equal parts. If `div` is a list,
    just returns `div` as a 1D array.
    """
    div = asarray(div).ravel()
    if div.size == 1 and div.dtype.kind=='i':
        n = div[0]
        div = arange(start,n+1) / float(n)
    return div


def uniformParamValues(n,umin=0.0,umax=1.0):
    """Create a set of uniformly distributed parameter values in a range.

    Parameters:

    - `n`: int: number of intervals in which the range should be divided.
      The number of values returned is ``n+1``.
    - `umin`, `umax`: float: start and end value of the interval. Default
      interval is [0.0..1.0].

    Returns:

      A float array with n+1 equidistant values in the range umin..umax.
      For n > 0, both of the endpoints are included. For n=0, a single
      value at the center of the interval will be returned. For n<0, an
      empty array is returned.

    Example:

      >>> uniformParamValues(4).tolist()
      [0.0, 0.25, 0.5, 0.75, 1.0]
      >>> uniformParamValues(0).tolist()
      [0.5]
      >>> uniformParamValues(-1).tolist()
      []
      >>> uniformParamValues(2,1.5,2.5).tolist()
      [1.5, 2.0, 2.5]
    """
    if n == 0:
        return array([0.5*(umax+umin)])
    else:
        return umin + arange(n+1) * (umax-umin) / n


def nodalSum(val,elems,avg=False,return_all=True,direction_treshold=None):
    """Compute the nodal sum of values defined on elements.

    val is a (nelems,nplex,nval) array of values defined at points of elements.
    elems is a (nelems,nplex) array with nodal ids of all points of elements.

    The return value is a (nelems,nplex,nval) array where each value is
    replaced with the sum of its value at that node.
    If avg=True, the values are replaced with the average instead.
    If return_all==True(default), returns an array with shape (nelems,nplex,3),
    else, returns an array with shape (maxnodenr+1,3). In the latter case,
    nodes not occurring in elems will have all zero values.

    If a direction_tolerance is specified and nval > 1, values will only be
    summed if their direction is close (projection of one onto the other is
    higher than the specified tolerance).
    """
    from pyformex.lib import misc
    if val.ndim != 3:
        val.reshape(val.shape+(1,))
    if elems.shape != val.shape[:2]:
        raise RuntimeError,"shape of val and elems does not match"
    val = val.astype(float32)
    elems = elems.astype(int32)
    if val.shape[2] > 1 and direction_treshold is not None:
        #nodalSum2(val,elems,direction_treshold)
        val = misc.nodalSum(val,elems,elems.max(),avg,return_all)
    else:
        val = misc.nodalSum(val,elems,elems.max(),avg,return_all)
    return val


def pprint(a,label=''):
    """Pretty print an array with a label in front.

    When printing a numpy array with a lable in font, the first row of
    the array is not aligned with the remainder. This function will solve
    that issue and prints the full array nicely aligned.

    - `a`: a numpy array
    - `label`: a sting to be printed in front of the array

    Example:

      >>> a = arange(12).reshape(-1,3)
      >>> pprint(a,'Reshaped range = ')
      Reshaped range = [[ 0  1  2]
                        [ 3  4  5]
                        [ 6  7  8]
                        [ 9 10 11]]

    """
    import pprint
    s = str(a).split('\n')
    print(label+s[0])
    dummy = ' '*len(label)
    for l in s[1:]:
        print(dummy+l)


# End
