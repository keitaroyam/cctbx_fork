from __future__ import generators

import os
if not hasattr(os.path, "devnull"):
  if os.name == "nt":
    os.path.devnull = "nul"
  else:
    os.path.devnull = "/dev/null"

__builtins__.setdefault("False", 0)
__builtins__.setdefault("True", 1)

if ("bool" not in __builtins__):
  def bool(value):
    if (value): return True
    return False
  __builtins__["bool"] = bool

if ("enumerate" not in __builtins__):
  def enumerate(iterable):
    """enumerate(iterable) -> iterator for index, value of iterable

  Return an enumerate object.  iterable must be an other object that supports
  iteration.  The enumerate object yields pairs containing a count (from
  zero) and a value yielded by the iterable argument.  enumerate is useful
  for obtaining an indexed list: (0, seq[0]), (1, seq[1]), (2, seq[2]), ..."""
    i = 0
    it = iter(iterable)
    while 1:
      yield (i, it.next())
      i += 1
  __builtins__["enumerate"] = enumerate

if ("sum" not in __builtins__):
  def sum(sequence, start=0):
    """sum(sequence, start=0) -> value

Returns the sum of a sequence of numbers (NOT strings) plus the value
of parameter 'start'.  When the sequence is empty, returns start."""
    if (len(sequence) == 0): return start
    sequence = iter(sequence)
    if (start is None):
      result = sequence.next()
    else:
      result = start
    for item in sequence:
      result += item
    return result
  __builtins__["sum"] = sum

if ("sorted" not in __builtins__):
  def sorted(iterable, cmp=None, key=None, reverse=False):
    """\
sorted(iterable, cmp=None, key=None, reverse=False) --> new sorted list"""
    assert key is None, "Not implemented."
    result = list(iterable)
    if (cmp is None): result.sort()
    else:             result.sort(cmp)
    if (reverse): result.reverse()
    return result
  __builtins__["sorted"] = sorted

if ("reversed" not in __builtins__):
  def reversed(seq):
    """ Return a reverse iterator. seq must be an object which supports
    the sequence protocol (the __len__() method and the __getitem__() method
    with integer arguments starting at 0). New in version 2.4. """
    i = len(seq)
    while i > 0:
      i -= 1
      yield seq[i]
  __builtins__["reversed"] = reversed

class _advertise_subprocess(object):

  def __init__(self, function_id, target):
    self.function_id = function_id
    self.target = target

  def __call__(self, *args, **kwargs):
    import libtbx.load_env
    if (   libtbx.env.full_testing
        or libtbx.env.is_development_environment()):
      def is_exception():
        from sys import _getframe
        frames_back = 1
        while True:
          try: f = _getframe(frames_back)
          except ValueError: break
          else:
            p = f.f_code.co_filename
            while True:
              d,b = os.path.split(p)
              if (len(d) == 0 or len(b) == 0): break
              b = b.lower()
              if (   b.startswith("python")
                  or b == "lib"):
                for n in ["os","StringIO","UserDict","UserList","UserString"]:
                  if (not os.path.isfile(os.path.join(p, n+".py"))):
                    break
                else:
                  return True
              elif (b == "scons"):
                if (os.path.isfile(os.path.join(p, "SConsign.py"))):
                  return True
              p = d
            frames_back += 1
        return False
      if (not is_exception()):
        from warnings import warn
        warn(
          message="%s is not safe: please use the subprocess module"
                  " or libtbx.easy_run instead." % self.function_id,
          stacklevel=2)
    return self.target(*args, **kwargs)

def _install_advertise_subprocess():
  for fn in ["system",
             "popen", "popen2", "popen3", "popen4",
             "spawnl", "spawnle", "spawnlp", "spawnlpe",
             "spawnv", "spawnve", "spawnvp", "spawnvpe"]:
    f = getattr(os, fn, None)
    if (f is not None):
      w = _advertise_subprocess(function_id="os."+fn+"()", target=f)
      setattr(os, fn, w)

_install_advertise_subprocess()
