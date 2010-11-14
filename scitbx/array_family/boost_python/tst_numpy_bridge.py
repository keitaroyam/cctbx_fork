from scitbx.array_family import flex

def exercise_basic(flex_type, verbose):
  if (flex_type is flex.bool):
    z = False
  else:
    z = 0
  for n in xrange(10):
    fa = flex_type([z]*n)
    na = fa.as_numpy_array()
    assert na is not None
    if (n == 0 and verbose):
      print "flex.%s -> numpy %s" % (flex_type.__name__, na.dtype)
    assert na.shape == (n,)

def exercise_int():
  fa = flex.int_range(1,7)
  na = fa.as_numpy_array()
  assert na.tolist() == list(fa)
  fa.reshape(flex.grid(2,3))
  na = fa.as_numpy_array()
  assert na.tolist() == [[1, 2, 3], [4, 5, 6]]
  fa = flex.int_range(4*2*3) + 1
  fa.reshape(flex.grid(4,2,3))
  na = fa.as_numpy_array()
  assert na.tolist() == [
    [[1, 2, 3], [4, 5, 6]],
    [[7, 8, 9], [10, 11, 12]],
    [[13, 14, 15], [16, 17, 18]],
    [[19, 20, 21], [22, 23, 24]]]

def run(args):
  assert args in [[], ["--forever"]]
  verbose = True
  while True:
    if (flex.int(0).as_numpy_array() is not None):
      for flex_type in [
            flex.bool,
            flex.int,
            flex.long,
            flex.float,
            flex.double,
            flex.complex_double,
            flex.size_t]:
        exercise_basic(flex_type, verbose)
      exercise_int()
    if (len(args) == 0):
      break
    verbose = False
  print "OK"

if (__name__ == "__main__"):
  import sys
  run(args=sys.argv[1:])
