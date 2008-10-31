from __future__ import division

flex = None
numpy = None
Numeric = None
LinearAlgebra = None
try: from scitbx.array_family import flex
except ImportError:
  try: import numpy.linalg
  except ImportError:
    try: import Numeric
    except ImportError:
      pass
    else:
      try: import LinearAlgebra
      except ImportError:
        pass

try:
  from stdlib import math
except ImportError:
  import math

class rec(object):

  def __init__(self, elems, n):
    assert len(n) == 2
    if (not isinstance(elems, tuple)):
      elems = tuple(elems)
    assert len(elems) == n[0] * n[1]
    self.elems = elems
    self.n = tuple(n)

  def n_rows(self):
    return self.n[0]

  def n_columns(self):
    return self.n[1]

  def __repr__(self):
    if self.n[0] == 1:
      return "matrix.row(%s)" % (self.elems,)
    elif self.n[1] == 1:
      return "matrix.col(%s)" % (self.elems,)
    else:
      return "matrix.rec(%s)" % (
        tuple([ self.elems[i:i+self.n[1]]
                for i in xrange(0, len(self.elems), self.n[1]) ]),
      )

  def __neg__(self):
    return rec([-e for e in self.elems], self.n)

  def __add__(self, other):
    assert self.n == other.n
    a = self.elems
    b = other.elems
    return rec([a[i] + b[i] for i in xrange(len(a))], self.n)

  def __sub__(self, other):
    assert self.n == other.n
    a = self.elems
    b = other.elems
    return rec([a[i] - b[i] for i in xrange(len(a))], self.n)

  def __mul__(self, other):
    if (not hasattr(other, "elems")):
      return rec([x * other for x in self.elems], self.n)
    a = self.elems
    ar = self.n_rows()
    ac = self.n_columns()
    b = other.elems
    if (other.n_rows() != ac):
      raise RuntimeError(
        "Incompatible matrices:\n"
        "  self.n:  %s\n"
        "  other.n: %s" % (str(self.n), str(other.n)))
    bc = other.n_columns()
    result = []
    for i in xrange(ar):
      for k in xrange(bc):
        s = 0
        for j in xrange(ac):
          s += a[i * ac + j] * b[j * bc + k]
        result.append(s)
    if (ar == bc):
      return sqr(result)
    return rec(result, (ar, bc))

  def __rmul__(self, other):
    "scalar * matrix"
    if (isinstance(other, rec)): # work around odd Python 2.2 feature
      return other.__mul__(self)
    return self * other

  def transpose_multiply(self, other=None):
    a = self.elems
    ar = self.n_rows()
    ac = self.n_columns()
    if (other is None):
      result = [0] * (ac * ac)
      jac = 0
      for j in xrange(ar):
        ik = 0
        for i in xrange(ac):
          for k in xrange(ac):
            result[ik] += a[jac + i] * a[jac + k]
            ik += 1
        jac += ac
      return sqr(result)
    b = other.elems
    assert other.n_rows() == ar, "Incompatible matrices."
    bc = other.n_columns()
    result = [0] * (ac * bc)
    jac = 0
    jbc = 0
    for j in xrange(ar):
      ik = 0
      for i in xrange(ac):
        for k in xrange(bc):
          result[ik] += a[jac + i] * b[jbc + k]
          ik += 1
      jac += ac
      jbc += bc
    if (ac == bc):
      return sqr(result)
    return rec(result, (ac, bc))

  def __div__(self, other):
    return rec([e/other for e in self.elems], self.n)

  def __truediv__(self, other):
    return rec([e/other for e in self.elems], self.n)

  def __floordiv__(self, other):
    return rec([e//other for e in self.elems], self.n)

  def __call__(self, ir, ic):
    return self.elems[ir * self.n_columns() + ic]

  def __len__(self):
    return len(self.elems)

  def __getitem__(self, i):
    return self.elems[i]

  def as_float(self):
    return rec([float(e) for e in self.elems], self.n)

  def as_int(self, rounding=True):
    if rounding:
      return rec([int(round(e)) for e in self.elems], self.n)
    else:
      return rec([int(e) for e in self.elems], self.n)

  def each_abs(self):
    return rec([abs(e) for e in self.elems], self.n)

  def min(self):
    result = None
    for e in self.elems:
      if (result is None or result > e):
        result = e
    return result

  def max(self):
    result = None
    for e in self.elems:
      if (result is None or result < e):
        result = e
    return result

  def min_index(self):
    result = None
    for i in xrange(len(self.elems)):
      if (result is None or self.elems[result] > self.elems[i]):
        result = i
    return result

  def max_index(self):
    result = None
    for i in xrange(len(self.elems)):
      if (result is None or self.elems[result] < self.elems[i]):
        result = i
    return result

  def sum(self):
    result = 0
    for e in self.elems:
      result += e
    return result

  def product(self):
    result = 1
    for e in self.elems:
      result *= e
    return result

  def trace(self):
    assert self.n_rows() == self.n_columns()
    n = self.n_rows()
    result = 0
    for i in xrange(n):
      result += self.elems[i*n+i]
    return result

  def norm_sq(self):
    assert self.n_rows() == 1 or self.n_columns() == 1
    result = 0
    for e in self.elems:
      result += e*e
    return result

  def __abs__(self):
    return math.sqrt(self.norm_sq())

  def normalize(self):
    return self / abs(self)

  def dot(self, other=None):
    result = 0
    a = self.elems
    if (other is None):
      for i in xrange(len(a)):
        v = a[i]
        result += v * v
    else:
      assert len(self.elems) == len(other.elems)
      b = other.elems
      for i in xrange(len(a)):
        result += a[i] * b[i]
    return result

  def cross(self, other):
    assert self.n in ((3,1), (1,3))
    assert self.n == other.n
    a = self.elems
    b = other.elems
    return col((
      a[1] * b[2] - b[1] * a[2],
      a[2] * b[0] - b[2] * a[0],
      a[0] * b[1] - b[0] * a[1]))

  def ortho(self):
    assert self.n in ((3,1), (1,3))
    x, y, z = self.elems
    a, b, c = abs(x), abs(y), abs(z)
    if c <= a and c <= b:
      return col((-y, x, 0))
    if b <= a and b <= c:
      return col((-z, 0, x))
    return col((0, -z, y))

  def rotate(self, axis, angle, deg=False):
    assert self.n in ((3,1), (1,3))
    assert axis.n == self.n
    if deg: angle *= math.pi/180
    n = axis.normalize()
    x = self
    c, s = math.cos(angle), math.sin(angle)
    return x*c + n*n.dot(x)*(1-c) + x.cross(n)*s

  def outer_product(self, other=None):
    if (other is None): other = self
    assert self.n[0] == 1 or self.n[1] == 1
    assert other.n[0] == 1 or other.n[1] == 1
    result = []
    for a in self.elems:
      for b in other.elems:
        result.append(a*b)
    return rec(result, (len(self.elems), len(other.elems)))

  def cos_angle(self, other, value_if_undefined=None):
    self_norm_sq = self.norm_sq()
    if (self_norm_sq == 0): return value_if_undefined
    other_norm_sq = other.norm_sq()
    if (other_norm_sq == 0): return value_if_undefined
    d = self_norm_sq * other_norm_sq
    if (d == 0): return value_if_undefined
    return self.dot(other) / math.sqrt(d)

  def angle(self, other, value_if_undefined=None, deg=False):
    cos_angle = self.cos_angle(other=other)
    if (cos_angle is None): return value_if_undefined
    result = math.acos(max(-1,min(1,cos_angle)))
    if (deg): result *= 180/math.pi
    return result

  def accute_angle(self, other, value_if_undefined=None, deg=False):
    cos_angle = self.cos_angle(other=other)
    if (cos_angle is None): return value_if_undefined
    if (cos_angle < 0): cos_angle *= -1
    result = math.acos(min(1,cos_angle))
    if (deg): result *= 180/math.pi
    return result

  def is_square(self):
    return self.n[0] == self.n[1]

  def determinant(self):
    assert self.is_square()
    m = self.elems
    n = self.n[0]
    if (n == 1):
      return m[0]
    if (n == 2):
      return m[0]*m[3] - m[1]*m[2]
    if (n == 3):
      return   m[0] * (m[4] * m[8] - m[5] * m[7]) \
             - m[1] * (m[3] * m[8] - m[5] * m[6]) \
             + m[2] * (m[3] * m[7] - m[4] * m[6])
    if (flex is None):
      raise RuntimeError(
        "cannot compute determinant of %d x %d matrix:"
        " scitbx.array_family.flex module not available." % self.n)
    m = flex.double(m)
    m.resize(flex.grid(self.n))
    return m.matrix_determinant_via_lu();

  def co_factor_matrix_transposed(self):
    n = self.n
    if (n == (1,1)):
      return rec(elems=(1,), n=n)
    m = self.elems
    if (n == (2,2)):
      return rec(elems=(m[3], -m[1], -m[2], m[0]), n=n)
    if (n == (3,3)):
      return rec(elems=(
         m[4] * m[8] - m[5] * m[7],
        -m[1] * m[8] + m[2] * m[7],
         m[1] * m[5] - m[2] * m[4],
        -m[3] * m[8] + m[5] * m[6],
         m[0] * m[8] - m[2] * m[6],
        -m[0] * m[5] + m[2] * m[3],
         m[3] * m[7] - m[4] * m[6],
        -m[0] * m[7] + m[1] * m[6],
         m[0] * m[4] - m[1] * m[3]), n=n)
    assert self.is_square()
    raise RuntimeError("Not implemented.")

  def inverse(self):
    assert self.is_square()
    n = self.n
    if (n[0] < 4):
      determinant = self.determinant()
      assert determinant != 0
      return self.co_factor_matrix_transposed() / determinant
    m = None
    if (flex is not None):
      m = flex.double(self.elems)
      m.resize(flex.grid(n))
      m.matrix_inversion_in_place()
    elif (numpy is not None):
      m = numpy.asarray(self.elems)
      m.shape = n
      m = numpy.ravel(numpy.linalg.inv(m))
    elif (Numeric is not None and LinearAlgebra is not None):
      m = Numeric.asarray(self.elems)
      m.shape = n
      m = Numeric.ravel(LinearAlgebra.inverse(m))
    if (m is None):
      raise RuntimeError(
        "cannot compute inverse of %d x %d matrix:"
        " all known numeric packages are unavailable." % self.n)
    return rec(elems=m, n=n)

  def transpose(self):
    elems = []
    for j in xrange(self.n_columns()):
      for i in xrange(self.n_rows()):
        elems.append(self(i,j))
    return rec(elems, (self.n_columns(), self.n_rows()))

  def mathematica_form(self,
        label="",
        one_row_per_line=False,
        format=None,
        prefix=""):
    nr = self.n_rows()
    nc = self.n_columns()
    s = prefix
    indent = prefix
    if (label):
      s += label + "="
      indent += " " * (len(label) + 1)
    s += "{"
    if (nc != 0):
      for ir in xrange(nr):
        s += "{"
        for ic in xrange(nc):
          if (format is None):
            s += str(self(ir, ic))
          else:
            s += format % self(ir, ic)
          if (ic+1 != nc): s += ", "
          else: s += "}"
        if (ir+1 != nr):
          s += ","
          if (one_row_per_line):
            s += "\n"
            s += indent
          s += " "
    return s + "}"

  def as_list_of_lists(self):
    result = []
    nr,nc = self.n
    for ir in xrange(nr):
      result.append(list(self.elems[ir*nc:(ir+1)*nc]))
    return result

  def as_sym_mat3(self):
    assert self.n == (3,3)
    m = self.elems
    return (m[0],m[4],m[8],
            (m[1]+m[3])/2.,
            (m[2]+m[6])/2.,
            (m[5]+m[7])/2.)

  def as_mat3(self):
    assert self.n == (3,3)
    return self.elems

  def extract_block(self, stop, start=(0,0), step=(1,1)):
    assert 0 <= stop[0] <= self.n[0]
    assert 0 <= stop[1] <= self.n[1]
    i_rows = range(start[0], stop[0], step[0])
    i_colums = range(start[1], stop[1], step[1])
    result = []
    for ir in i_rows:
      for ic in i_colums:
        result.append(self(ir,ic))
    return rec(result, (len(i_rows),len(i_colums)))

  def __eq__(self, other):
    if self is other: return True
    if other is None: return False
    if issubclass(type(other), rec):
      return self.elems == other.elems
    for ir in xrange(self.n_rows()):
      for ic in xrange(self.n_columns()):
        if self(ir,ic) != other[ir,ic]: return False
    return True

  def resolve_partitions(self):
    nr,nc = self.n
    result_nr = 0
    for ir in xrange(nr):
      part_nr = 0
      for ic in xrange(nc):
        part = self(ir,ic)
        assert isinstance(part, rec)
        if (ic == 0): part_nr = part.n[0]
        else: assert part.n[0] == part_nr
      result_nr += part_nr
    result_nc = 0
    for ic in xrange(nc):
      part_nc = 0
      for ir in xrange(nr):
        part = self(ir,ic)
        if (ir == 0): part_nc = part.n[1]
        else: assert part.n[1] == part_nc
      result_nc += part_nc
    result_elems = [0] * (result_nr * result_nc)
    result_ir = 0
    for ir in xrange(nr):
      result_ic = 0
      for ic in xrange(nc):
        part = self(ir,ic)
        part_nr,part_nc = part.n
        i_part = 0
        for part_ir in xrange(part_nr):
          i_result = (result_ir + part_ir) * result_nc + result_ic
          for part_ic in xrange(part_nc):
            result_elems[i_result + part_ic] = part[i_part]
            i_part += 1
        result_ic += part_nc
      assert result_ic == result_nc
      result_ir += part_nr
    assert result_ir == result_nr
    return rec(elems=result_elems, n=(result_nr, result_nc))

class row(rec):

  def __init__(self, elems):
    rec.__init__(self, elems, (1, len(elems)))

class col(rec):

  def __init__(self, elems):
    rec.__init__(self, elems, (len(elems), 1))

  def random(cls, n, a, b):
    from random import uniform
    return cls([ uniform(a,b) for i in xrange(n) ])
  random = classmethod(random)

class sqr(rec):

  def __init__(self, elems):
    l = len(elems)
    n = int(l**(.5) + 0.5)
    assert l == n * n
    rec.__init__(self, elems, (n,n))

class diag(rec):

  def __init__(self, diag_elems):
    n = len(diag_elems)
    elems = [0 for i in xrange(n*n)]
    for i in xrange(n):
      elems[i*(n+1)] = diag_elems[i]
    rec.__init__(self, elems, (n,n))

class identity(diag):

  def __init__(self, n):
    super(identity, self).__init__((1.,)*n)

class inversion(diag):

  def __init__(self, n):
    super(inversion, self).__init__((-1.,)*n)

class sym(rec):

  def __init__(self, elems=None, sym_mat3=None):
    assert elems is None, "Not implemented."
    assert len(sym_mat3) == 6
    m = sym_mat3
    rec.__init__(self, (m[0], m[3], m[4],
                        m[3], m[1], m[5],
                        m[4], m[5], m[2]), (3,3))

def cross_product_matrix((v0, v1, v2)):
  """\
Matrix associated with vector cross product:
  a.cross(b) is equivalent to cross_product_matrix(a) * b
Useful for simplification of equations. Used frequently in
robotics and classical mechanics literature.
"""
  return sqr((
      0, -v2,  v1,
     v2,   0, -v0,
    -v1,  v0,   0))

class rt(object):

  def __init__(self, tuple_r_t):
    if (hasattr(tuple_r_t[0], "elems")):
      self.r = sqr(tuple_r_t[0].elems)
    else:
      self.r = sqr(tuple_r_t[0])
    if (hasattr(tuple_r_t[1], "elems")):
      self.t = col(tuple_r_t[1].elems)
    else:
      self.t = col(tuple_r_t[1])
    assert self.r.n_rows() == self.t.n_rows()

  def __add__(self, other):
    if (isinstance(other, rt)):
      return rt((self.r + other.r, self.t + other.t))
    else:
      return rt((self.r, self.t + other))

  def __sub__(self, other):
    if (isinstance(other, rt)):
      return rt((self.r - other.r, self.t - other.t))
    else:
      return rt((self.r, self.t - other))

  def __mul__(self, other):
    if (isinstance(other, rt)):
      return rt((self.r * other.r, self.r * other.t + self.t))
    if (isinstance(other, rec)):
      if (other.n == self.r.n):
        return rt((self.r * other, self.t))
      if (other.n == self.t.n):
        return self.r * other + self.t
      raise ValueError(
        "cannot multiply %s by %s: incompatible number of rows or columns"
          % (repr(self), repr(other)))
    n = len(self.t.elems)
    if (isinstance(other, (list, tuple))):
      if (len(other) == n):
        return self.r * col(other) + self.t
      if (len(other) == n*n):
        return rt((self.r * sqr(other), self.t))
      raise ValueError(
        "cannot multiply %s by %s: incompatible number of elements"
          % (repr(self), repr(other)))
    if (n == 3 and flex is not None and isinstance(other, flex.vec3_double)):
      return self.r.elems * other + self.t.elems
    raise TypeError("cannot multiply %s by %s" % (repr(self), repr(other)))

  def inverse(self):
    r_inv = self.r.inverse()
    return rt((r_inv, -(r_inv*self.t)))

  def inverse_assuming_orthogonal_r(self):
    r_inv = self.r.transpose()
    return rt((r_inv, -(r_inv*self.t)))

  def as_float(self):
    return rt((self.r.as_float(), self.t.as_float()))

  def as_augmented_matrix(self):
    assert self.r.n_rows() == self.r.n_columns()
    n = self.r.n_rows()
    result = []
    for i_row in xrange(n):
      result.extend(self.r.elems[i_row*n:(i_row+1)*n])
      result.append(self.t[i_row])
    result.extend([0]*n)
    result.append(1)
    return rec(result, (n+1,n+1))

def col_list(seq): return [col(elem) for elem in seq]
def row_list(seq): return [row(elem) for elem in seq]

def exercise():
  try:
    from libtbx import test_utils
  except ImportError:
    print "Warning: libtbx not available: some tests disabled."
    def approx_equal(a, b): return True
    Exception_expected = RuntimeError
  else:
    approx_equal = test_utils.approx_equal
    Exception_expected = test_utils.Exception_expected
  for n in [(0,0), (1,0), (0,1)]:
    a = rec((),n)
    assert a.mathematica_form() == "{}"
  a = rec(range(1,7), (3,2))
  assert len(a) == 6
  assert a[1] == 2
  assert (a*3).mathematica_form() == "{{3, 6}, {9, 12}, {15, 18}}"
  assert (-2*a).mathematica_form() == "{{-2, -4}, {-6, -8}, {-10, -12}}"
  b = rec(range(1,7), (2,3))
  assert a.dot(b) == 91
  assert col((3,4)).dot() == 25
  c = a * b
  d = rt((c, (1,2,3)))
  assert (-a).mathematica_form() == "{{-1, -2}, {-3, -4}, {-5, -6}}"
  assert d.r.mathematica_form() == "{{9, 12, 15}, {19, 26, 33}, {29, 40, 51}}"
  assert d.t.mathematica_form() == "{{1}, {2}, {3}}"
  e = d + col((3,5,6))
  assert e.r.mathematica_form() == "{{9, 12, 15}, {19, 26, 33}, {29, 40, 51}}"
  assert e.t.mathematica_form() == "{{4}, {7}, {9}}"
  f = e - col((1,2,3))
  assert f.r.mathematica_form() == "{{9, 12, 15}, {19, 26, 33}, {29, 40, 51}}"
  assert f.t.mathematica_form() == "{{3}, {5}, {6}}"
  e = e + f
  assert e.r.mathematica_form() \
      == "{{18, 24, 30}, {38, 52, 66}, {58, 80, 102}}"
  assert e.t.mathematica_form() == "{{7}, {12}, {15}}"
  f = f - e
  assert f.r.mathematica_form() \
      == "{{-9, -12, -15}, {-19, -26, -33}, {-29, -40, -51}}"
  assert f.t.mathematica_form() == "{{-4}, {-7}, {-9}}"
  e = f.as_float()
  assert e.r.mathematica_form() \
      == "{{-9.0, -12.0, -15.0}, {-19.0, -26.0, -33.0}, {-29.0, -40.0, -51.0}}"
  assert e.t.mathematica_form() == "{{-4.0}, {-7.0}, {-9.0}}"
  a = f.as_augmented_matrix()
  assert a.mathematica_form() == "{{-9, -12, -15, -4}, {-19, -26, -33, -7}," \
                               + " {-29, -40, -51, -9}, {0, 0, 0, 1}}"
  assert a.extract_block(stop=(1,1)).mathematica_form() \
      == "{{-9}}"
  assert a.extract_block(stop=(2,2)).mathematica_form() \
      == "{{-9, -12}, {-19, -26}}"
  assert a.extract_block(stop=(3,3)).mathematica_form() \
      == "{{-9, -12, -15}, {-19, -26, -33}, {-29, -40, -51}}"
  assert a.extract_block(stop=(4,4)).mathematica_form() \
      == a.mathematica_form()
  assert a.extract_block(stop=(4,4),step=(2,2)).mathematica_form() \
      == "{{-9, -15}, {-29, -51}}"
  assert a.extract_block(start=(1,1),stop=(4,4),step=(2,2)).mathematica_form()\
      == "{{-26, -7}, {0, 1}}"
  assert a.extract_block(start=(1,0),stop=(4,3),step=(2,1)).mathematica_form()\
      == "{{-19, -26, -33}, {0, 0, 0}}"
  #
  ar = range(1,10)
  at = range(1,4)
  br = range(11,20)
  bt = range(4,7)
  g = rt((ar,at)) * rt((br,bt))
  assert g.r.mathematica_form() == \
    "{{90, 96, 102}, {216, 231, 246}, {342, 366, 390}}"
  assert g.t.mathematica_form() == "{{33}, {79}, {125}}"
  grt = g.r.transpose()
  assert grt.mathematica_form() == \
    "{{90, 216, 342}, {96, 231, 366}, {102, 246, 390}}"
  grtt = grt.transpose()
  assert grtt.mathematica_form() == \
    "{{90, 96, 102}, {216, 231, 246}, {342, 366, 390}}"
  gtt = g.t.transpose()
  assert gtt.mathematica_form() == "{{33, 79, 125}}"
  gttt = gtt.transpose()
  assert gttt.mathematica_form() == "{{33}, {79}, {125}}"
  assert sqr([4]).determinant() == 4
  assert sqr([3,2,-7,15]).determinant() == 59
  m = sqr([4])
  mi = m.inverse()
  assert mi.mathematica_form() == "{{0.25}}"
  m = sqr((1,5,-3,9))
  mi = m.inverse()
  assert mi.n == (2,2)
  assert approx_equal(mi, (3/8, -5/24, 1/8, 1/24))
  m = sqr((7, 7, -4, 3, 1, -1, 15, 16, -9))
  assert m.determinant() == 1
  mi = m.inverse()
  assert mi.mathematica_form() \
      == "{{7.0, -1.0, -3.0}, {12.0, -3.0, -5.0}, {33.0, -7.0, -14.0}}"
  assert (m*mi).mathematica_form() \
      == "{{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}}"
  assert (mi*m).mathematica_form() \
      == "{{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}}"
  s = rt((m, (1,-2,3)))
  si = s.inverse()
  assert si.r.mathematica_form() == mi.mathematica_form()
  assert (s*si).r.mathematica_form() \
      == "{{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}}"
  assert (si*s).r.mathematica_form() \
      == "{{1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, 0.0, 1.0}}"
  assert si.t.mathematica_form().replace("-0.0", "0.0") \
      == "{{0.0}, {-3.0}, {-5.0}}"
  assert (s*si).t.mathematica_form() == "{{0.0}, {0.0}, {0.0}}"
  assert (si*s).t.mathematica_form() == "{{0.0}, {0.0}, {0.0}}"
  #
  m = rt((sqr([
    0.1226004505424059, 0.69470636260753704, -0.70876808568064376,
    0.20921402107901119, -0.71619825067837384, -0.66579993925291725,
    -0.97015391712385002, -0.066656848694206489, -0.23314853980114805]),
    col((0.34, -0.78, 0.43))))
  assert approx_equal(m.r*m.r.transpose(), (1,0,0,0,1,0,0,0,1))
  mi = m.inverse()
  mio = m.inverse_assuming_orthogonal_r()
  assert approx_equal(mio.r, mi.r)
  assert approx_equal(mio.t, mi.t)
  #
  r = rec(elems=(8,-4,3,-2,7,9,-3,2,1), n=(3,3))
  t = rec(elems=(7,-6,3), n=(3,1))
  gr = g * r
  assert gr.r == g.r * r
  assert gr.t == g.t
  gt = g * t
  assert gt == g.r * t + g.t
  gr = g * r.elems
  assert gr.r == g.r * r
  assert gr.t == g.t
  gt = g * t.elems
  assert gt == g.r * t + g.t
  try: g * col([1])
  except ValueError, e:
    assert str(e).startswith("cannot multiply ")
    assert str(e).endswith(": incompatible number of rows or columns")
  else: raise Exception_expected
  try: g * [1]
  except ValueError, e:
    assert str(e).startswith("cannot multiply ")
    assert str(e).endswith(": incompatible number of elements")
  else: raise Exception_expected
  if (flex is not None):
    gv = g * flex.vec3_double([(-1,2,3),(2,-3,4)])
    assert isinstance(gv, flex.vec3_double)
    assert approx_equal(gv, [(441, 1063, 1685), (333, 802, 1271)])
  #
  try: from boost import rational
  except ImportError: pass
  else:
    assert approx_equal(col((rational.int(3,4),2,1.5)).as_float(),(0.75,2,1.5))
  #
  assert approx_equal(col((-2,3,-6)).normalize().elems, (-2/7.,3/7.,-6/7.))
  assert col((-1,2,-3)).each_abs().elems == (1,2,3)
  assert col((5,3,4)).min() == 3
  assert col((4,5,3)).max() == 5
  assert col((5,3,4)).min_index() == 1
  assert col((4,5,3)).max_index() == 1
  assert col((4,5,3)).sum() == 12
  assert col((2,3,4)).product() == 2*3*4
  assert sqr((1,2,3,4,5,6,7,8,9)).trace() == 15
  assert diag((1,2,3)).mathematica_form() == \
    "{{1, 0, 0}, {0, 2, 0}, {0, 0, 3}}"
  assert approx_equal(col((1,0,0)).cos_angle(col((1,1,0)))**2, 0.5)
  assert approx_equal(col((1,0,0)).angle(col((1,1,0))), 0.785398163397)
  assert approx_equal(col((1,0,0)).angle(col((1,1,0)), deg=True), 45)
  assert approx_equal(col((-1,0,0)).angle(col((1,1,0)), deg=True), 45+90)
  assert approx_equal(col((1,0,0)).accute_angle(col((1,1,0)), deg=True), 45)
  assert approx_equal(col((-1,0,0)).accute_angle(col((1,1,0)), deg=True), 45)
  m = sqr([4, 4, -1, 0, -3, -3, -3, -2, -3, 2, -1, 1, -4, 1, 3, 2])
  if (flex is not None):
    md = m.determinant()
    assert approx_equal(md, -75)
  else:
    try: m.determinant()
    except RuntimeError, e:
      assert str(e) == "cannot compute determinant of 4 x 4 matrix:" \
        " scitbx.array_family.flex module not available."
    else: raise Exception_expected
  if (   flex is not None
      or numpy is not None
      or (Numeric is not None and LinearAlgebra is not None)):
    mi = m.inverse()
    assert mi.n == (4,4)
    assert approx_equal(mi, (
      -2/15,-17/75,4/75,-19/75,
      7/15,22/75,-14/75,29/75,
      1/3,4/15,-8/15,8/15,
      -1,-1,1,-1))
  else:
    try: m.inverse()
    except RuntimeError, e:
      assert str(e) == "cannot compute inverse of 4 x 4 matrix:" \
        " all known numeric packages are unavailable."
    else: raise Exception_expected
  #
  r = sqr([-0.9533, 0.2413, -0.1815,
           0.2702, 0.414, -0.8692,
           -0.1346, -0.8777, -0.4599])
  assert r.mathematica_form(
    label="rotation",
    format="%.6g",
    one_row_per_line=True,
    prefix="  ") == """\
  rotation={{-0.9533, 0.2413, -0.1815},
            {0.2702, 0.414, -0.8692},
            {-0.1346, -0.8777, -0.4599}}"""
  r = sqr([])
  assert r.mathematica_form() == "{}"
  assert r.mathematica_form(one_row_per_line=True) == "{}"
  r = sqr([1])
  assert r.mathematica_form() == "{{1}}"
  assert r.mathematica_form(one_row_per_line=True, prefix="&$") == """\
&${{1}}"""
  #
  a = rec(range(1,6+1), (3,2))
  b = rec(range(1,15+1), (3,5))
  assert approx_equal(a.transpose_multiply(b), a.transpose() * b)
  assert approx_equal(a.transpose_multiply(a), a.transpose() * a)
  assert approx_equal(a.transpose_multiply(), a.transpose() * a)
  assert approx_equal(b.transpose_multiply(b), b.transpose() * b)
  assert approx_equal(b.transpose_multiply(), b.transpose() * b)
  #
  a = col([1,2,3])
  b = row([10,20])
  assert a.outer_product(b).as_list_of_lists() == [[10,20],[20,40],[30,60]]
  assert a.outer_product().as_list_of_lists() == [[1,2,3],[2,4,6],[3,6,9]]
  #
  a = sym(sym_mat3=range(6))
  assert a.as_list_of_lists() == [[0, 3, 4], [3, 1, 5], [4, 5, 2]]
  assert approx_equal(a.as_sym_mat3(), range(6))
  #
  x = col((1,2,3))
  assert repr(x) == "matrix.col((1, 2, 3))"
  y = row((3,2,1))
  assert repr(y) =="matrix.row((3, 2, 1))"
  m = rec((1,2,3,
           4,5,6,
           7,8,9,
           4,2,9), (4,3))
  assert repr(m) == "matrix.rec(((1, 2, 3), (4, 5, 6), (7, 8, 9), (4, 2, 9)))"
  #
  t = (1,2,3,4,5,6)
  g = (3,2)
  a = rec(t, g)
  b = rec(t, g)
  assert a == b
  if (flex is not None):
    c = flex.double(t)
    c.reshape(flex.grid(g))
    assert a == c
  #
  a = identity(4)
  for ir in xrange(4):
    for ic in xrange(4):
      assert (ir == ic and a(ir,ic) == 1) or (ir != ic and a(ir,ic) == 0)
  a = inversion(4)
  for ir in xrange(4):
    for ic in xrange(4):
      assert (ir == ic and a(ir,ic) == -1) or (ir != ic and a(ir,ic) == 0)
  #
  x = col((3/2+0.01, 5/4-0.02, 11/8+0.001))
  assert (x*8).as_int()/8 == col((3/2, 5/4, 11/8))
  #
  for x in [(0, 0, 0), (1, -2, 5), (-2, 5, 1), (5, 1, -2) ]:
    x = col(x)
    assert approx_equal(x.dot(x.ortho()), 0)
  #
  x = col((1, -2, 3))
  n = col((-2, 4, 5))
  alpha = 2*math.pi/3
  y = x.rotate(n, alpha)
  n = n.normalize()
  x_perp = x - n.dot(x)*n
  y_perp = y - n.dot(y)*n
  assert approx_equal(x_perp.angle(y_perp), alpha)
  #
  a = col((1.43416642866471794, -2.47841960952275497, -0.7632916804502845))
  b = col((0.34428681113080323, -1.85983494542314587, 0.37702845822372399))
  assert approx_equal(a.cross(b), cross_product_matrix(a) * b)
  #
  a = col_list(seq=[(1,2), (2,3)])
  for e in a: assert isinstance(e, col)
  assert approx_equal(a, [(1,2), (2,3)])
  a = row_list(seq=[(1,2), (2,3)])
  for e in a: assert isinstance(e, row)
  assert approx_equal(a, [(1,2), (2,3)])
  #
  def f(a): return a.resolve_partitions().mathematica_form()
  a = rec(elems=[], n=[0,0])
  assert f(a) == "{}"
  a = rec(elems=[], n=[0,1])
  assert f(a) == "{}"
  a = rec(elems=[], n=[1,0])
  assert f(a) == "{}"
  for e in [col([]), row([])]:
    a = rec(elems=[e], n=[1,1])
    assert f(a) == "{}"
    a = rec(elems=[e, e], n=[1,2])
    assert f(a) == "{}"
    a = rec(elems=[e, e], n=[2,1])
    assert f(a) == "{}"
  for e in [col([1]), row([1])]:
    a = rec(elems=[e], n=[1,1])
    assert f(a) == "{{1}}"
  a = rec(elems=[col([1,2]), col([3,4])], n=[1,2])
  assert f(a) == "{{1, 3}, {2, 4}}"
  a = rec(elems=[col([1,2]), col([3,4])], n=[2,1])
  assert f(a) == "{{1}, {2}, {3}, {4}}"
  a = rec(elems=[sqr([1,2,3,4]), sqr([5,6,7,8])], n=[1,2])
  assert f(a) == "{{1, 2, 5, 6}, {3, 4, 7, 8}}"
  a = rec(elems=[sqr([1,2,3,4]), sqr([5,6,7,8])], n=[2,1])
  assert f(a) == "{{1, 2}, {3, 4}, {5, 6}, {7, 8}}"
  a = rec(elems=[rec([1,2,3,4,5,6], n=(2,3)), rec([7,8], n=(2,1))], n=[1,2])
  assert f(a) == "{{1, 2, 3, 7}, {4, 5, 6, 8}}"
  a = rec(elems=[rec([1,2,3,4,5,6], n=(2,3)), rec([7,8,9], n=(1,3))], n=[2,1])
  assert f(a) == "{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}"
  a = rec(
    elems=[
      sqr([11,12,13,14,15,16,17,18,19]),
      sqr([21,22,23,24,25,26,27,28,29]),
      sqr([31,32,33,34,35,36,37,38,39]),
      sqr([41,42,43,44,45,46,47,48,49])],
    n=[2,2])
  assert a.resolve_partitions().mathematica_form(one_row_per_line=True) == """\
{{11, 12, 13, 21, 22, 23},
 {14, 15, 16, 24, 25, 26},
 {17, 18, 19, 27, 28, 29},
 {31, 32, 33, 41, 42, 43},
 {34, 35, 36, 44, 45, 46},
 {37, 38, 39, 47, 48, 49}}"""
  a = rec(
    elems=[
      rec([1,2,3,4,5,6], n=(2,3)),
      rec([7,8,9,10,11,12,13,14], n=(2,4)),
      rec([15,16,17,18,19,20,21,22,23], n=(3,3)),
      rec([24,25,26,27,28,29,30,31,32,33,34,35], n=(3,4)),
      rec([36,37,38], n=(1,3)),
      rec([39,40,41,42], n=(1,4))],
    n=[3,2])
  assert a.resolve_partitions().mathematica_form(one_row_per_line=True) == """\
{{1, 2, 3, 7, 8, 9, 10},
 {4, 5, 6, 11, 12, 13, 14},
 {15, 16, 17, 24, 25, 26, 27},
 {18, 19, 20, 28, 29, 30, 31},
 {21, 22, 23, 32, 33, 34, 35},
 {36, 37, 38, 39, 40, 41, 42}}"""
  #
  print "OK"

if (__name__ == "__main__"):
  exercise()
