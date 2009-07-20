from featherstone import matrix, cb_as_spatial_transform
import math

class zero_dof_alignment(object):

  def __init__(O):
    O.cb_0b = matrix.rt(((1,0,0,0,1,0,0,0,1), (0,0,0)))
    O.cb_b0 = O.cb_0b

class zero_dof(object):

  degrees_of_freedom = 0
  qd_zero = matrix.zeros(n=degrees_of_freedom)
  qdd_zero = qd_zero

  def __init__(O):
    O.q_size = 0
    O.cb_ps = matrix.rt(((1,0,0,0,1,0,0,0,1), (0,0,0)))
    O.cb_sp = O.cb_ps
    O.Xj = cb_as_spatial_transform(O.cb_ps)
    O.S = matrix.rec(elems=(), n=(6,0))

  def get_linear_velocity(O, qd):
    return None

  def new_linear_velocity(O, qd, value):
    return None

  def time_step_position(O, qd, delta_t):
    return zero_dof()

  def time_step_velocity(O, qd, qdd, delta_t):
    return zero_dof.qd_zero

  def tau_as_d_pot_d_q(O, tau):
    return zero_dof.qd_zero

  def get_q(O):
    return ()

  def new_q(O, q):
    return zero_dof()

class six_dof_alignment(object):

  def __init__(O, center_of_mass):
    O.cb_0b = matrix.rt(((1,0,0,0,1,0,0,0,1), -center_of_mass))
    O.cb_b0 = matrix.rt(((1,0,0,0,1,0,0,0,1), center_of_mass))

class six_dof(object):

  degrees_of_freedom = 6
  qd_zero = matrix.zeros(n=degrees_of_freedom)
  qdd_zero = qd_zero

  def __init__(O, qE, qr):
    O.qE = qE
    O.qr = qr
    O.q_size = 7
    O.unit_quaternion = qE.normalize() # RBDA, bottom of p. 86
    O.E = RBDA_Eq_4_12(q=O.unit_quaternion)
    O.r = qr
    O.cb_ps = matrix.rt((O.E, -O.E * O.r)) # RBDA Eq. 2.28
    O.cb_sp = matrix.rt((O.E.transpose(), O.r))
    O.Xj = cb_as_spatial_transform(O.cb_ps)
    O.S = None

  def get_linear_velocity(O, qd):
    return matrix.col(qd.elems[3:])

  def new_linear_velocity(O, qd, value):
    return matrix.col((matrix.col(qd.elems[:3]), value)).resolve_partitions()

  def time_step_position(O, qd, delta_t):
    w_body_frame, v_body_frame = matrix.col_list([qd.elems[:3], qd.elems[3:]])
    qEd = RBDA_Eq_4_13(q=O.unit_quaternion) * w_body_frame
    new_qE = (O.qE + qEd * delta_t).normalize()
    qrd = O.E.transpose() * v_body_frame
    new_qr = O.qr + qrd * delta_t
    return six_dof(qE=new_qE, qr=new_qr)

  def time_step_velocity(O, qd, qdd, delta_t):
    return qd + qdd * delta_t

  def tau_as_d_pot_d_q(O, tau):
    d = d_unit_quaternion_d_qE_matrix(q=O.qE)
    c = d * 4 * RBDA_Eq_4_13(q=O.unit_quaternion)
    n, f = matrix.col_list([tau.elems[:3], tau.elems[3:]])
    return matrix.col((c * n, O.E.transpose() * f)).resolve_partitions()

  def get_q(O):
    return O.qE.elems + O.qr.elems

  def new_q(O, q):
    new_qE, new_qr = matrix.col_list((q[:4], q[4:]))
    return six_dof(qE=new_qE, qr=new_qr)

class spherical_alignment(object):

  def __init__(O, pivot):
    O.cb_0b = matrix.rt(((1,0,0,0,1,0,0,0,1), -pivot))
    O.cb_b0 = matrix.rt(((1,0,0,0,1,0,0,0,1), pivot))

class spherical(object):

  degrees_of_freedom = 3
  qd_zero = matrix.zeros(n=degrees_of_freedom)
  qdd_zero = qd_zero

  def __init__(O, qE):
    O.qE = qE
    O.q_size = 4
    O.unit_quaternion = qE.normalize() # RBDA, bottom of p. 86
    O.E = RBDA_Eq_4_12(q=O.unit_quaternion)
    O.cb_ps = matrix.rt((O.E, (0,0,0)))
    O.cb_sp = matrix.rt((O.E.transpose(), (0,0,0)))
    O.Xj = cb_as_spatial_transform(O.cb_ps)
    O.S = matrix.rec((
      1,0,0,
      0,1,0,
      0,0,1,
      0,0,0,
      0,0,0,
      0,0,0), n=(6,3))

  def get_linear_velocity(O, qd):
    return None

  def new_linear_velocity(O, qd, value):
    return None

  def time_step_position(O, qd, delta_t):
    w_body_frame = qd
    d = d_unit_quaternion_d_qE_matrix(q=O.qE)
    qEd = d * RBDA_Eq_4_13(q=O.unit_quaternion) * w_body_frame
    new_qE = O.qE + qEd * delta_t
    return spherical(qE=new_qE)

  def time_step_velocity(O, qd, qdd, delta_t):
    return qd + qdd * delta_t

  def tau_as_d_pot_d_q(O, tau):
    d = d_unit_quaternion_d_qE_matrix(q=O.qE)
    c = d * 4 * RBDA_Eq_4_13(q=O.unit_quaternion)
    n = tau
    return c * n

  def get_q(O):
    return O.qE.elems

  def new_q(O, q):
    return spherical(qE=matrix.col(q))

class revolute_alignment(object):

  def __init__(O, pivot, normal):
    r = normal.vector_to_001_rotation()
    O.cb_0b = matrix.rt((r, -r * pivot))
    O.cb_b0 = matrix.rt((r.transpose(), pivot))

class revolute(object):

  degrees_of_freedom = 1
  qd_zero = matrix.zeros(n=degrees_of_freedom)
  qdd_zero = qd_zero

  def __init__(O, qE):
    O.qE = qE
    O.q_size = len(qE)
    #
    c, s = math.cos(qE[0]), math.sin(qE[0])
    O.E = matrix.sqr((c, s, 0, -s, c, 0, 0, 0, 1)) # RBDA Tab. 2.2
    O.r = matrix.col((0,0,0))
    #
    O.cb_ps = matrix.rt((O.E, (0,0,0)))
    O.cb_sp = matrix.rt((O.E.transpose(), (0,0,0)))
    O.Xj = cb_as_spatial_transform(O.cb_ps)
    O.S = matrix.col((0,0,1,0,0,0))

  def get_linear_velocity(O, qd):
    return None

  def new_linear_velocity(O, qd, value):
    return None

  def time_step_position(O, qd, delta_t):
    new_qE = O.qE + qd * delta_t
    return revolute(qE=new_qE)

  def time_step_velocity(O, qd, qdd, delta_t):
    return qd + qdd * delta_t

  def tau_as_d_pot_d_q(O, tau):
    return tau

  def get_q(O):
    return O.qE.elems

  def new_q(O, q):
    return revolute(qE=matrix.col(q))

class translational_alignment(six_dof_alignment): pass

class translational(object):

  degrees_of_freedom = 3
  qd_zero = matrix.zeros(n=degrees_of_freedom)
  qdd_zero = qd_zero

  def __init__(O, qr):
    O.qr = qr
    O.q_size = 3
    O.r = qr
    O.cb_ps = matrix.rt(((1,0,0,0,1,0,0,0,1), -O.r))
    O.cb_sp = matrix.rt(((1,0,0,0,1,0,0,0,1), O.r))
    O.Xj = cb_as_spatial_transform(O.cb_ps)
    O.S = matrix.rec((
      0,0,0,
      0,0,0,
      0,0,0,
      1,0,0,
      0,1,0,
      0,0,1), n=(6,3))

  def get_linear_velocity(O, qd):
    return qd

  def new_linear_velocity(O, qd, value):
    return value

  def time_step_position(O, qd, delta_t):
    new_qr = O.qr + qd * delta_t
    return translational(qr=new_qr)

  def time_step_velocity(O, qd, qdd, delta_t):
    return qd + qdd * delta_t

  def tau_as_d_pot_d_q(O, tau):
    return tau

  def get_q(O):
    return O.qr.elems

  def new_q(O, q):
    return translational(qr=matrix.col(q))

def RBDA_Eq_4_12(q):
  p0, p1, p2, p3 = q
  return matrix.sqr((
    p0**2+p1**2-0.5,   p1*p2+p0*p3,     p1*p3-p0*p2,
      p1*p2-p0*p3,   p0**2+p2**2-0.5,   p2*p3+p0*p1,
      p1*p3+p0*p2,     p2*p3-p0*p1,   p0**2+p3**2-0.5)) * 2

def RBDA_Eq_4_13(q):
  p0, p1, p2, p3 = q
  return matrix.rec((
    -p1, -p2, -p3,
    p0, -p3, p2,
    p3, p0, -p1,
    -p2, p1, p0), n=(4,3)) * 0.5

def d_unit_quaternion_d_qE_matrix(q):
  """
  Coefficent matrix for converting gradients w.r.t. normalized Euler
  parameters to gradients w.r.t. non-normalized parameters, as produced
  e.g. by a minimizer in the line search.
  Mathematica code:
    nsq = p0^2+p1^2+p2^2+p3^2
    p0p = p0 / Sqrt[nsq]
    p1p = p1 / Sqrt[nsq]
    p2p = p2 / Sqrt[nsq]
    p3p = p3 / Sqrt[nsq]
    n3 = (p0^2+p1^2+p2^2+p3^2)^(3/2)
    FortranForm[FullSimplify[D[p0p,p0]*n3]]
    FortranForm[FullSimplify[D[p1p,p0]*n3]]
    FortranForm[FullSimplify[D[p2p,p0]*n3]]
    FortranForm[FullSimplify[D[p3p,p0]*n3]]
    FortranForm[FullSimplify[D[p0p,p1]*n3]]
    FortranForm[FullSimplify[D[p1p,p1]*n3]]
    FortranForm[FullSimplify[D[p2p,p1]*n3]]
    FortranForm[FullSimplify[D[p3p,p1]*n3]]
    FortranForm[FullSimplify[D[p0p,p2]*n3]]
    FortranForm[FullSimplify[D[p1p,p2]*n3]]
    FortranForm[FullSimplify[D[p2p,p2]*n3]]
    FortranForm[FullSimplify[D[p3p,p2]*n3]]
    FortranForm[FullSimplify[D[p0p,p3]*n3]]
    FortranForm[FullSimplify[D[p1p,p3]*n3]]
    FortranForm[FullSimplify[D[p2p,p3]*n3]]
    FortranForm[FullSimplify[D[p3p,p3]*n3]]
  """
  p0,p1,p2,p3 = q
  p0s,p1s,p2s,p3s = p0**2, p1**2, p2**2, p3**2
  n3 = (p0s+p1s+p2s+p3s)**(3/2.)
  c00 = p1s+p2s+p3s
  c11 = p0s+p2s+p3s
  c22 = p0s+p1s+p3s
  c33 = p0s+p1s+p2s
  c01 = -p0*p1
  c02 = -p0*p2
  c03 = -p0*p3
  c12 = -p1*p2
  c13 = -p1*p3
  c23 = -p2*p3
  return matrix.sqr((
    c00, c01, c02, c03,
    c01, c11, c12, c13,
    c02, c12, c22, c23,
    c03, c13, c23, c33)) / n3
