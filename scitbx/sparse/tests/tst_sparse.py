from scitbx.array_family import flex
from scitbx import sparse
from libtbx.test_utils import approx_equal, Exception_expected
import random

def exercise_vector():
  v = sparse.vector(5)
  assert v.size == 5
  assert v.is_structurally_zero()
  v[1] = 2
  v[2] = 0
  v[3] = 6
  assert [ v[i] for i in xrange(5) ] == [0, 2, 0, 6, 0]
  assert list(v) == [(1,2.), (2,0.), (3,6.)]
  assert list(v.sort_indices()) == [(1,2.), (2,0.), (3,6.)]
  p = flex.size_t([1,2,3,4,0])
  assert list(v.permute(p)) == [(2,2.), (3,0.), (4,6.)]

  v = sparse.vector(10)
  v[7] = -5
  v[1] = -1
  v[4] = 0
  v[1] = 2
  v[9] = 9.
  v[7] = 6
  v[4] = 1
  v[1] = 3
  v[4] = 0
  assert list(v.sort_indices()) == [(1,3.), (4,0.), (7,6.), (9,9.)]

  v = sparse.vector(None)
  v[3] = 1
  v[2] = 1
  v[5] = 1
  try: v.size
  except RuntimeError, e:
    assert str(e).find("SCITBX_ASSERT(size_) failure") != -1
  else:
    raise Exception_expected
  v.sort_indices()
  assert v.size == 6
  v[7] = 1
  assert v.size == 6
  assert v[7] == 1
  v.sort_indices()
  assert v[7] == 0

def exercise_matrix():
  a = sparse.matrix(10,7)
  assert a.n_rows == 10 and a.n_cols == 7
  for c in a.cols():
    assert c.is_structurally_zero()
  a[0,1] = 1.
  a[9,5] = 2.
  for i in xrange(10):
    for j in xrange(7):
      if (i,j) == (0,1): assert a[i,j] == 1.
      elif (i,j) == (9,5): assert a[i,j] == 2.
      else: assert a[i,j] == 0

  a = sparse.matrix(None, 3)
  a[1,1] = 1.
  a[3,2] = 2.
  a[5,1] = 2.
  a[4,0] = 1.
  try: a.n_rows
  except RuntimeError, e:
    assert str(e).find("SCITBX_ASSERT(n_rows_) failure") != -1
  else:
    raise Exception_expected
  a.sort_indices()
  assert a.n_rows == 6
  a[7,0] = 1.
  assert a.n_rows == 6
  assert a[7,0] == 1
  a.sort_indices()
  assert a[7,0] == 0

def random_sparse_vector(n):
  x = sparse.vector(n)
  seen = {}
  for k in xrange(random.randint(1,2*n//3)):
    while True:
      i = random.randint(0,n-1)
      if i not in seen: break
    seen[i] = True
    val = random.uniform(-2., 2.)
    x[i] = val
  return x

def random_sparse_matrix(m,n):
  a = sparse.matrix(m,n)
  seen = {}
  for k in xrange(random.randint(3,2*m*n//3)):
    while True:
      i = random.randint(0,m-1)
      j = random.randint(0,n-1)
      if (i,j) not in seen: break
    seen[(i,j)] = True
    val = random.uniform(-3., 3.)
    a[i,j] = val
  return a

def exercise_matrix_x_vector():
  for m,n in [(5,5), (3,5), (5,3)]:
    for n_test in xrange(50):
      a = random_sparse_matrix(m,n)
      x = random_sparse_vector(n)
      y = a*x
      aa = a.as_dense_matrix()
      xx = x.as_dense_vector()
      yy1 = y.as_dense_vector()
      yy2 = aa.matrix_multiply(xx)
      assert approx_equal(yy1,yy2)

def exercise_matrix_x_matrix():
  a,b = random_sparse_matrix(3,4), random_sparse_matrix(4,2)
  c = a*b
  aa, bb, cc = [ m.as_dense_matrix() for m in (a,b,c) ]
  cc1 = aa.matrix_multiply(bb)
  assert approx_equal(cc, cc1)

def run():
  exercise_vector()
  exercise_matrix()
  exercise_matrix_x_vector()
  exercise_matrix_x_matrix()
  print 'OK'

if __name__ == '__main__':
  run()
