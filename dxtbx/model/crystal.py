from __future__ import division
from scitbx import matrix
from cctbx.uctbx import unit_cell
from cctbx.sgtbx import space_group as SG
from cctbx.sgtbx import space_group_symbols
from cctbx.crystal_orientation import crystal_orientation

class crystal_model(object):
  '''Simple model for the crystal lattice geometry and symmetry

  A crystal is initialised from the elements of its real space axes
  a, b, and c. Space group information must also be provided, either
  in the form of a symbol, or an existing
  cctbx.sgtbx.space_group object. If space_group_symbol is provided,
  it is passed to the cctbx.sgtbx.space_group_symbols constructor.
  This accepts either extended Hermann Mauguin format, or Hall format
  with the prefix 'Hall:'. E.g.

  space_group_symbol = "P b a n:1"
      or
  space_group_symbol = "Hall:P 2 2 -1ab"

  Optionally the crystal mosaicity value may be set, with the deg
  parameter controlling whether this value is treated as being an
  angle in degrees or radians.'''

  def __init__(self, real_space_a, real_space_b, real_space_c,
               space_group_symbol=None, space_group=None,
               mosaicity=None, deg=True):

    # Set the space group
    assert [space_group_symbol, space_group].count(None) == 1
    if space_group_symbol:
      self._sg = SG(space_group_symbols(space_group_symbol))
    else: self._sg = space_group

    # Set the mosaicity
    if mosaicity is not None:
      self.set_mosaicity(mosaicity, deg=deg)
    else:
      self._mosaicity = 0.0

    # setting matrix at initialisation
    real_space_a = matrix.col(real_space_a)
    real_space_b = matrix.col(real_space_b)
    real_space_c = matrix.col(real_space_c)
    A = matrix.sqr(real_space_a.elems +  real_space_b.elems + \
                   real_space_c.elems).inverse()

    # unit cell
    self.set_unit_cell(real_space_a, real_space_b, real_space_c)

    # reciprocal space orthogonalisation matrix (is the transpose of the
    # real space fractionalisation matrix, see http://goo.gl/H3p1s)
    self._update_B()

    # initial orientation matrix
    self._U = A * self._B.inverse()

    # set up attributes for scan-varying model
    self.reset_scan_points()

    return

  @property
  def num_scan_points(self):
    return self._num_scan_points

  def show(self, show_scan_varying=False, out=None):
    if out is None:
      import sys
      out = sys.stdout
    uc = self.get_unit_cell().parameters()
    sg = str(self.get_space_group().info())
    umat = self.get_U().mathematica_form(format="% 5.4f",
                                         one_row_per_line=True).splitlines()
    bmat = self.get_B().mathematica_form(format="% 5.4f",
                                         one_row_per_line=True).splitlines()
    amat = (self.get_U() * self.get_B()).mathematica_form(format="% 5.4f",
                                         one_row_per_line=True).splitlines()

    msg =  ["Crystal:"]
    msg.append("    Unit cell: " + "(%5.3f, %5.3f, %5.3f, %5.3f, %5.3f, %5.3f)" % uc)
    msg.append("    Space group: " + sg)
    msg.append("    U matrix:  " + umat[0])
    msg.append("               " + umat[1])
    msg.append("               " + umat[2])
    msg.append("    B matrix:  " + bmat[0])
    msg.append("               " + bmat[1])
    msg.append("               " + bmat[2])
    msg.append("    A = UB:    " + amat[0])
    msg.append("               " + amat[1])
    msg.append("               " + amat[2])
    if self.num_scan_points > 0:
      msg.append("    A sampled at " + str(self.num_scan_points) \
                 + " scan points")
      if show_scan_varying:
        for i in range(self.num_scan_points):
          A = self.get_A_at_scan_point(i)
          B = self.get_B_at_scan_point(i)
          U = self.get_U_at_scan_point(i)
          uc = self.get_unit_cell_at_scan_point(i).parameters()
          umat = U.mathematica_form(format="% 5.4f",
                                    one_row_per_line=True).splitlines()
          bmat = B.mathematica_form(format="% 5.4f",
                                    one_row_per_line=True).splitlines()
          amat = A.mathematica_form(format="% 5.4f",
                                    one_row_per_line=True).splitlines()
          msg.append("  Scan point #%i:" %(i+1))
          msg.append("    Unit cell: " + "(%5.3f, %5.3f, %5.3f, %5.3f, %5.3f, %5.3f)" % uc)
          msg.append("    U matrix:  " + umat[0])
          msg.append("               " + umat[1])
          msg.append("               " + umat[2])
          msg.append("    B matrix:  " + bmat[0])
          msg.append("               " + bmat[1])
          msg.append("               " + bmat[2])
          msg.append("    A = UB:    " + amat[0])
          msg.append("               " + amat[1])
          msg.append("               " + amat[2])
    print >> out, "\n".join(msg)

  def __str__(self):
    from cStringIO import StringIO
    s = StringIO()
    msg = self.show(out=s)
    s.seek(0)
    return s.read()

  def set_unit_cell(self, real_space_a, real_space_b, real_space_c):
    cell = (real_space_a.length(),
            real_space_b.length(),
            real_space_c.length(),
            real_space_b.angle(real_space_c, deg = True),
            real_space_c.angle(real_space_a, deg = True),
            real_space_a.angle(real_space_b, deg = True))
    self._uc = unit_cell(cell)
    self._update_B()

  def get_unit_cell_at_scan_point(self, t):
    B = self.get_B_at_scan_point(t)
    co = crystal_orientation(B)
    return co.unit_cell()

  def _update_B(self):
    self._B = matrix.sqr(self._uc.fractionalization_matrix()).transpose()

  def set_U(self, U):

    # check U is a rotation matrix.
    assert(U.is_r3_rotation_matrix())
    self._U = U

    # reset scan-varying data, if the static U has changed
    self.reset_scan_points()

  def get_U(self):
    return self._U

  def get_B(self):
    return self._B

  def set_B(self, B):

    # also set the unit cell
    co = crystal_orientation(B,True)
    self._uc = co.unit_cell()
    self._B = matrix.sqr(self._uc.fractionalization_matrix()).transpose()

    # reset scan-varying data, if the static B has changed
    self.reset_scan_points()

  def set_A_at_scan_points(self, A_list):
    '''Set the setting matrix A at a series of checkpoints within a rotation
    scan. There would typically be n+1 points, where n is the number of images
    in the scan. The first point is the state at the beginning of the rotation
    scan. The final point is the state at the end of the rotation scan.
    Intervening points give the state at the start of the rotation at the 2nd
    to the nth image.

    This data is held separately from the 'static' U and B because per-image
    setting matrices may be refined whilst restraining to a previously
    determined best-fit static UB. The values will be reset if any changes are
    made to the static U and B matrices.
    '''

    self._A_at_scan_points = [matrix.sqr(e) for e in A_list]
    self._num_scan_points = len(A_list)

  def get_A_at_scan_point(self, t):
    '''Return the setting matrix with index t. This will typically have been
    set with reference to a particular scan, such that it equals the UB matrix
    appropriate at the start of the rotation for the image with array index t
    '''

    return self._A_at_scan_points[t]

  def get_U_at_scan_point(self, t):
    '''Return orientation matrix with index t.'''

    Bt = self.get_B_at_scan_point(t)
    At = self._A_at_scan_points[t]

    return At * Bt.inverse()

  def get_B_at_scan_point(self, t):
    '''Return orthogonalisation matrix with index t.'''

    At = self._A_at_scan_points[t]
    uc = unit_cell(orthogonalization_matrix=At.transpose().inverse())

    return matrix.sqr(uc.fractionalization_matrix()).transpose()

  def get_unit_cell_at_scan_point(self, t):
    '''Return unit cell with index t.'''

    At = self._A_at_scan_points[t]
    uc = unit_cell(orthogonalization_matrix=At.transpose().inverse())

    return uc

  def reset_scan_points(self):
    self._num_scan_points = 0
    self._A_at_scan_points = None

  def get_unit_cell(self):
    return self._uc

  def set_space_group(self, space_group):
    self._sg = space_group

  def get_space_group(self):
    return self._sg

  def get_mosaicity(self, deg=True):
    from math import pi
    if deg == True:
      return self._mosaicity * 180.0 / pi

    return self._mosaicity

  def set_mosaicity(self, mosaicity, deg=True):
    from math import pi
    if deg == True:
      self._mosaicity = mosaicity * pi / 180.0
    else:
      self._mosaicity = mosaicity

  def get_A(self):
    return self._U * self._B

  def __eq__(self, other, eps=1e-7):
    if isinstance(other, crystal_model):
      d_mosaicity = abs(self._mosaicity - other._mosaicity)
      d_U = sum([abs(u1 - u2) for u1, u2 in zip(self._U, other._U)])
      d_B = sum([abs(b1 - b2) for b1, b2 in zip(self._B, other._B)])
      if self.num_scan_points > 0:
        if other.num_scan_points != self.num_scan_points: return False
        for i in range(self.num_scan_points):
          A1, A2 = self.get_A_at_scan_point(i), other.get_A_at_scan_point(i)
          d_A = sum([abs(a1 - a2) for a1, a2 in zip(A1, A2)])
          if d_A > eps: return False
      return (d_mosaicity <= eps and
              d_U <= eps and
              d_B <= eps and
              self._sg == other._sg)
    return NotImplemented

  def get_real_space_vectors(self):
    A_inv = self.get_A().inverse()
    return (matrix.col(A_inv[:3]),
            matrix.col(A_inv[3:6]),
            matrix.col(A_inv[6:9]))

  def change_basis(self, change_of_basis_op):
    # cctbx change of basis matrices and those Giacovazzo are related by
    # inverse and transpose, i.e. Giacovazzo's "M" is related to the cctbx
    # cb_op as follows:
    #   M = cb_op.c_inv().r().transpose()
    #   M_inverse = cb_op_to_minimum.c().r().transpose()

    # (Giacovazzo calls the direct matrix "A",
    #  we call the reciprocal matrix "A")
    # Therefore, from equation 2.19 in Giacovazzo:
    #   A' = M A

    # and:
    #   (A')^-1 = (M A)^-1
    #   (A')^-1 = A^-1 M^-1

    #reciprocal_matrix = self.get_A()
    #rm_cb = reciprocal_matrix * M.inverse()
    #dm_cb = rm_cb.inverse()
    #from libtbx.test_utils import approx_equal
    #assert approx_equal(dm_cb.elems, new_direct_matrix.elems)

    direct_matrix = self.get_A().inverse()
    M = matrix.sqr(change_of_basis_op.c_inv().r().transpose().as_double())
    # equation 2.19 of Giacovazzo
    new_direct_matrix = M * direct_matrix
    real_space_a = new_direct_matrix[:3]
    real_space_b = new_direct_matrix[3:6]
    real_space_c = new_direct_matrix[6:9]
    other = crystal_model(real_space_a,
                          real_space_b,
                          real_space_c,
                          space_group=self.get_space_group().change_basis(
                            change_of_basis_op),
                          mosaicity=self.get_mosaicity())
    if self.num_scan_points > 0:
      M_inv = M.inverse()
      other.set_A_at_scan_points(
        [At * M_inv for At in self._A_at_scan_points])
      assert other.num_scan_points == self.num_scan_points
    return other

def crystal_model_from_mosflm_matrix(mosflm_A_matrix,
                                     unit_cell=None,
                                     wavelength=None,
                                     space_group=None):
  '''Create a crystal_model from a Mosflm A matrix (a*, b*, c*); N.B. assumes
  the mosflm coordinate frame:

                                                   /!
                      Y-axis                      / !
                        ^                        /  !
                        !                       /   !
                        !                      /    !
                        !   /                 /  Xd !
                        !  /                 / * ^  !
                        ! /                  ! 3 !  !
                        !/      X-ray beam   !   !  !
                        /------------------------/--!---->X-axis
                       /                     !  / *1!
                    <-/-                     ! /    !
                     /  \+ve phi             ! Yd  /
                    /   /                    ! 2  /
                   /                         ! * /
                  Z-axis                  Ys ^ _/
                Rotation                     ! /| Xs
                 axis                        !/
                                             O

  Also assume that the mosaic spread is 0. If space_group is None spacegroup
  will be assigned as P1.
  '''

  if not space_group:
    space_group = SG('P1')

  A_star = matrix.sqr(mosflm_A_matrix)
  A = A_star.inverse()

  if unit_cell:
    unit_cell_constants = unit_cell.parameters()
    a = matrix.col(A.elems[0:3])
    wavelength = unit_cell_constants[0] / a.length()
    A *= wavelength
  elif wavelength:
    A *= wavelength
  else:
    # assume user has pre-scaled
    pass

  a = A.elems[0:3]
  b = A.elems[3:6]
  c = A.elems[6:9]
  rotate_mosflm_to_imgCIF = matrix.sqr((0, 0, 1, 0, 1, 0, -1, 0, 0))
  _a = rotate_mosflm_to_imgCIF * a
  _b = rotate_mosflm_to_imgCIF * b
  _c = rotate_mosflm_to_imgCIF * c

  return crystal_model(_a, _b, _c, space_group=space_group)
