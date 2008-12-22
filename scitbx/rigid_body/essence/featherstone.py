"""\
Python version of a subset of Roy Featherstone's spatial_v1 matlab code:

  http://axiom.anu.edu.au/~roy/spatial/

  Version 1: January 2008 (latest bug fix: 7 October 2008)

The subset of converted files covers all dependencies of:
  ID.m
  FDab.m

The original matlab comments are preserved as Python docstrings.

See also:
  Rigid Body Dynamics Algorithms.
  Roy Featherstone,
  Springer, New York, 2007.
  ISBN-10: 0387743146
"""

try:
  import scitbx
except ImportError:
  scitbx = None

if (scitbx is not None):
  import scitbx.math
  from scitbx import matrix

  def generalized_inverse(m):
    # assumption to achieve stability: order of magnitude of masses is around 1
    return matrix.sqr(
      scitbx.math.eigensystem.real_symmetric(
        m=m.as_flex_double_matrix(),
        relative_epsilon=1e-12,
        absolute_epsilon=1e-12)
          .generalized_inverse_as_packed_u()
          .matrix_packed_u_as_symmetric())

else:
  import scitbx_matrix as matrix

  def generalized_inverse(m):
    return m.inverse()

import math

class InfType(object): pass
Inf = InfType()

def Xrot(E):
  """
  Featherstone (2007) Tab. 2.2
  Added in Python version.
  """
  a,b,c,d,e,f,g,h,i = E
  return matrix.sqr((
     a,  b,  c,  0,  0,  0,
     d,  e,  f,  0,  0,  0,
     g,  h,  i,  0,  0,  0,
     0,  0,  0,  a,  b,  c,
     0,  0,  0,  d,  e,  f,
     0,  0,  0,  g,  h,  i))

def Xtrans(r):
  """
% Xtrans  spatial coordinate transform (translation of origin).
% Xtrans(r) calculates the coordinate transform matrix from A to B
% coordinates for spatial motion vectors, in which frame B is translated by
% an amount r (3D vector) relative to frame A.
  """
  r1,r2,r3 = r
  return matrix.sqr((
      1,   0,   0, 0, 0, 0,
      0,   1,   0, 0, 0, 0,
      0,   0,   1, 0, 0, 0,
      0,  r3, -r2, 1, 0, 0,
    -r3,   0,  r1, 0, 1, 0,
     r2, -r1,   0, 0, 0, 1))

def crm(v):
  """
% crm  spatial cross-product operator (motion).
% crm(v) calculates the 6x6 matrix such that the expression crm(v)*m is the
% cross product of the spatial motion vectors v and m.
  """
  v1,v2,v3,v4,v5,v6 = v
  return matrix.sqr((
      0, -v3,  v2,   0,   0,   0,
     v3,   0, -v1,   0,   0,   0,
    -v2,  v1,   0,   0,   0,   0,
      0, -v6,  v5,   0, -v3,  v2,
     v6,   0, -v4,  v3,   0, -v1,
    -v5,  v4,   0, -v2,  v1,   0))

def crf(v):
  """
% crf  spatial cross-product operator (force).
% crf(v) calculates the 6x6 matrix such that the expression crf(v)*f is the
% cross product of the spatial motion vector v with the spatial force
% vector f.
  """
  return -crm(v).transpose()

def mcI(m, c, I):
  """
% mcI  spatial rigid-body inertia from mass, CoM and rotational inertia.
% mcI(m,c,I) calculates the spatial inertia matrix of a rigid body from its
% mass, centre of mass (3D vector) and rotational inertia (3x3 matrix)
% about its centre of mass.
  """
  c1,c2,c3 = c
  C = matrix.sqr((
      0, -c3,  c2,
     c3,   0, -c1,
    -c2,  c1,  0))
  return matrix.sqr((
    I + m*C*C.transpose(), m*C,
    m*C.transpose(), m*matrix.identity(3))).resolve_partitions()

def ID(model, qd, qdd, f_ext=None, grav_accn=None):
  """
% ID  Inverse Dynamics via Recursive Newton-Euler Algorithm
% ID(model,qd,qdd,f_ext,grav_accn) calculates the inverse dynamics of a
% kinematic tree via the recursive Newton-Euler algorithm.  qd and qdd
% are vectors of joint velocity and acceleration variables; and
% the return value is a vector of joint force variables.  f_ext is a cell
% array specifying external forces acting on the bodies.  If f_ext == {}
% then there are no external forces; otherwise, f_ext{i} is a spatial force
% vector giving the force acting on body i, expressed in body i
% coordinates.  Empty cells in f_ext are interpreted as zero forces.
% grav_accn is a 3D vector expressing the linear acceleration due to
% gravity.  The arguments f_ext and grav_accn are optional, and default to
% the values {} and [0,0,0], respectively, if omitted.
  """

  Xup = model.Xup()
  v = model.spatial_velocities(Xup=Xup, qd=qd)
  a = [None] * len(Xup)
  f = [None] * len(Xup)
  for i,B in enumerate(model.bodies):
    if (B.J.S is None):
      vJ = qd[i]
      aJ = qdd[i]
    else:
      vJ = B.J.S * qd[i]
      aJ = B.J.S * qdd[i]
    if B.parent == -1:
      a[i] = aJ
      if (grav_accn is not None):
        a[i] += Xup[i] * -grav_accn
    else:
      a[i] = Xup[i] * a[B.parent] + aJ + crm(v[i]) * vJ
    f[i] = B.I * a[i] + crf(v[i]) * B.I * v[i]
    if (f_ext is not None and f_ext[i] is not None):
      f[i] = f[i] - f_ext[i]

  tau = [None] * len(Xup)
  for i in xrange(len(Xup)-1,-1,-1):
    B = model.bodies[i]
    if (B.J.S is None):
      tau[i] = f[i]
    else:
      tau[i] = B.J.S.transpose() * f[i]
    if B.parent != -1:
      f[B.parent] = f[B.parent] + Xup[i].transpose() * f[i]

  return tau

def ID0(model, f_ext):
  """
Simplified Inverse Dynamics via Recursive Newton-Euler Algorithm,
with all qd, qdd zero, but non-zero external forces.
  """
  Xup = model.Xup()
  f = [-e for e in f_ext]
  tau = [None] * len(f)
  for i in xrange(len(f)-1,-1,-1):
    B = model.bodies[i]
    if (B.J.S is None):
      tau[i] = f[i]
    else:
      tau[i] = B.J.S.transpose() * f[i]
    if B.parent != -1:
      f[B.parent] += Xup[i].transpose() * f[i]
  return tau

def FDab(model, qd, tau=None, f_ext=None, grav_accn=None):
  """
% FDab  Forward Dynamics via Articulated-Body Algorithm
% FDab(model,qd,tau,f_ext,grav_accn) calculates the forward dynamics of a
% kinematic tree via the articulated-body algorithm.  qd and tau are
% vectors of joint velocity and force variables; and the return
% value is a vector of joint acceleration variables.  f_ext is a cell array
% specifying external forces acting on the bodies.  If f_ext == {} then
% there are no external forces; otherwise, f_ext{i} is a spatial force
% vector giving the force acting on body i, expressed in body i
% coordinates.  Empty cells in f_ext are interpreted as zero forces.
% grav_accn is a 3D vector expressing the linear acceleration due to
% gravity.  The arguments f_ext and grav_accn are optional, and default to
% the values {} and [0,0,0], respectively, if omitted.
  """

  Xup = model.Xup()
  v = model.spatial_velocities(Xup=Xup, qd=qd)
  c = [None] * len(Xup)
  IA = [None] * len(Xup)
  pA = [None] * len(Xup)
  for i,B in enumerate(model.bodies):
    if (B.J.S is None):
      vJ = qd[i]
    else:
      vJ = B.J.S * qd[i]
    if B.parent == -1:
      c[i] = matrix.col([0,0,0,0,0,0])
    else:
      c[i] = crm(v[i]) * vJ
    IA[i] = B.I
    pA[i] = crf(v[i]) * B.I * v[i]
    if (f_ext is not None and f_ext[i] is not None):
      pA[i] = pA[i] - f_ext[i]

  U = [None] * len(Xup)
  d_inv = [None] * len(Xup)
  u = [None] * len(Xup)
  for i in xrange(len(Xup)-1,-1,-1):
    B = model.bodies[i]
    if (B.J.S is None):
      U[i] = IA[i]
      d = U[i]
      if (tau is None or tau[i] is None):
        u[i] =        - pA[i]
      else:
        u[i] = tau[i] - pA[i]
    else:
      U[i] = IA[i] * B.J.S
      d = B.J.S.transpose() * U[i]
      if (tau is None or tau[i] is None):
        u[i] =        - B.J.S.transpose() * pA[i]
      else:
        u[i] = tau[i] - B.J.S.transpose() * pA[i]
    d_inv[i] = generalized_inverse(d)
    if B.parent != -1:
      Ia = IA[i] - U[i] * d_inv[i] * U[i].transpose()
      pa = pA[i] + Ia*c[i] + U[i] * d_inv[i] * u[i]
      IA[B.parent] = IA[B.parent] + Xup[i].transpose() * Ia * Xup[i]
      pA[B.parent] = pA[B.parent] + Xup[i].transpose() * pa

  a = [None] * len(Xup)
  qdd = [None] * len(Xup)
  for i,B in enumerate(model.bodies):
    if B.parent == -1:
      a[i] = c[i]
      if (grav_accn is not None):
        a[i] += Xup[i] * -grav_accn
    else:
      a[i] = Xup[i] * a[B.parent] + c[i]
    qdd[i] = d_inv[i] * (u[i] - U[i].transpose()*a[i])
    if (B.J.S is None):
      a[i] = a[i] + qdd[i]
    else:
      a[i] = a[i] + B.J.S * qdd[i]

  return qdd
