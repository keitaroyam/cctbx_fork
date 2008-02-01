from libtbx import utils
from libtbx.test_utils import Exception_expected, approx_equal, show_diff
from cStringIO import StringIO

def exercise_indented_display():
  out = StringIO()
  level0 = utils.buffered_indentor(file_object=out)
  print >> level0, "level0"
  level0.flush()
  level1 = level0.shift_right()
  print >> level1, "level1"
  level1.flush()
  assert out.getvalue() == ""
  level1.write_buffer()
  assert not show_diff(out.getvalue(), """\
level0
  level1
""")
  print >> level1, "abc",
  level1.write_buffer()
  assert not show_diff(out.getvalue(), """\
level0
  level1
  abc""")
  print >> level1
  level1.write_buffer()
  assert not show_diff(out.getvalue(), """\
level0
  level1
  abc
""")
  print >> level1, "def",
  level1.write_buffer()
  assert not show_diff(out.getvalue(), """\
level0
  level1
  abc
  def""")
  level1.write("")
  print >> level1, "hij"
  level1.write_buffer()
  assert not show_diff(out.getvalue(), """\
level0
  level1
  abc
  def hij
""")

def exercise_approx_equal():
  assert approx_equal(1., 1. + 1e-11)
  assert approx_equal(1+1j, 0.997+1.004j, eps=1e-2)
  assert approx_equal(1, 0.997+0.004j, eps=1e-2)
  assert approx_equal(1+0.003j, 0.997, eps=1e-2)
  assert approx_equal([ 2.5, 3.4+5.8j, 7.89],
                      [ 2.4+0.1j, 3.5+5.9j, 7.90], eps=0.2)

def exercise_group_args():
  g = utils.group_args(a=1, b=2, c=3)
  assert g.a == 1 and g.b == 2 and g.c == 3
  def f1(a,b,c):
    assert a == 1 and b == 2 and c == 3
  f1(**g.__dict__)
  g = utils.group_args(self="foo", a=1, b=2)
  assert not hasattr(g, 'self') and g.a == 1 and g.b == 2
  def f2(a,b):
    assert a == 1 and b == 2
  f2(**g.__dict__)

def exercise():
  assert utils.flat_list(0) == [0]
  assert utils.flat_list([1,2,3]) == [1,2,3]
  assert utils.flat_list([1,[2,3,4],3]) == [1,2,3,4,3]
  assert utils.flat_list([1,[2,3,4],[[3,4],[5,6]]]) == [1,2,3,4,3,4,5,6]
  try:
    raise RuntimeError("Trial")
  except KeyboardInterrupt: raise
  except:
    assert utils.format_exception() == "RuntimeError: Trial"
  else: raise Exception_expected
  try:
    assert 1 == 2
  except KeyboardInterrupt: raise
  except:
    s = utils.format_exception()
    assert s.startswith("AssertionError: ")
    assert s.find("tst_utils.py line ") >= 0
  else: raise Exception_expected
  exercise_indented_display()
  exercise_approx_equal()
  exercise_group_args()
  print "OK"

if (__name__ == "__main__"):
  exercise()
