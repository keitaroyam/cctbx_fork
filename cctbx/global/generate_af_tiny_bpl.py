# $Id$

# Visual C++ 6.0 does not support partial ordering. Therefore the
# Boost.Python converters for af::tiny need to be enumerated
# explicitly.

def write_copyright():
  print """// This is an automatically generated file. Do not edit.
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Mar 2002: modified copy of generate_carray_bpl.py (rwgk)
     Apr 2001: SourceForge release (R.W. Grosse-Kunstleve)
 */"""

def one_definition(T, N, declaration):
  prototype = """
  cctbx::af::tiny<%s, %d> from_python(PyObject* p,
    boost::python::type<const cctbx::af::tiny<%s, %d>&>)""" % (T, N, T, N)
  if (declaration):
    print prototype + ";"
  else:
    print prototype
    print """
  {
    boost::python::tuple
    tup = cctbx::bpl_utils::tuple_from_python_list_or_tuple(p);
    cctbx::af::tiny<%s, %d> result;
    if (tup.size() != result.size()) {
      PyErr_SetString(PyExc_ValueError,
        "incorrect number of values in tuple.");
      throw boost::python::error_already_set();
    }
    for(int i=0;i<result.size();i++) {
      result[i] = from_python(tup[i].get(), boost::python::type<%s>());
    }
    return result;
  }""" % (T, N, T)

  prototype = """
  PyObject* to_python(const cctbx::af::tiny<%s, %d>& tobj)""" % (T, N)
  if (declaration):
    print prototype + ";"
  else:
    print prototype
    print """
  {
    boost::python::tuple result(tobj.size());
    for(int i=0;i<tobj.size();i++) {
      result.set_item(i, boost::python::ref(to_python(tobj[i])));
    }
    return result.reference().release();
  }
"""

def write_declarations(T_N_List):
  write_copyright()
  print """
#ifndef CCTBX_ARRAY_FAMILY_TINY_BPL_H
#define CCTBX_ARRAY_FAMILY_TINY_BPL_H

#include <cctbx/array_family/tiny.h>

BOOST_PYTHON_BEGIN_CONVERSION_NAMESPACE
"""

  for array_type in T_N_List:
    one_definition(array_type.T, array_type.N, 1)

  print """
BOOST_PYTHON_END_CONVERSION_NAMESPACE

#endif // CCTBX_ARRAY_FAMILY_TINY_BPL_H
"""

def write_definitions(T_N_List):
  write_copyright()
  print """
#include <cctbx/bpl_utils.h>
#include <cctbx/array_family/tiny_bpl.h>

BOOST_PYTHON_BEGIN_CONVERSION_NAMESPACE
"""

  for array_type in T_N_List:
    one_definition(array_type.T, array_type.N, 0)

  print """
BOOST_PYTHON_END_CONVERSION_NAMESPACE
"""

class T_N:
  def __init__(self, T, N):
    self.T = T
    self.N = N

def run():
  T_N_List = (
    T_N("int", 2),
    T_N("int", 3),
    T_N("int", 9),
    T_N("long", 3),
    T_N("double", 3),
    T_N("double", 6),
    T_N("double", 9),
    T_N("std::size_t", 2),
  )
  import sys
  f = open("tiny_bpl.h", "w")
  sys.stdout = f
  write_declarations(T_N_List)
  sys.stdout = sys.__stdout__
  f.close()
  f = open("tiny_bpl.cpp", "w")
  sys.stdout = f
  write_definitions(T_N_List)
  sys.stdout = sys.__stdout__
  f.close()

if (__name__ == "__main__"):
  run()
