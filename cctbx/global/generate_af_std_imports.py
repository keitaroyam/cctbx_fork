import sys
from generate_af_functors import *

def write_copyright():
  print \
"""/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Feb 2002: Created (Ralf W. Grosse-Kunstleve)

   *****************************************************
   THIS IS AN AUTOMATICALLY GENERATED FILE. DO NOT EDIT.
   *****************************************************

   Generated by:
     %s
 */""" % (sys.argv[0],)

cmath_1arg = (
  'acos', 'cos', 'tan',
  'asin', 'cosh', 'tanh',
  'atan', 'exp', 'sin',
  'fabs', 'log', 'sinh',
  'ceil', 'floor', 'log10', 'sqrt',
)

cmath_2arg = (
  'fmod', 'pow', 'atan2',
)

cstdlib_1arg = (
  'abs',
)

complex_1arg = (
# "cos",
# "cosh",
# "exp",
# "log",
# "log10",
# "sin",
# "sinh",
# "sqrt",
# "tan",
# "tanh",
  "conj",
)

complex_special = (
("ElementType", "real", "std::complex<ElementType>"),
("ElementType", "imag", "std::complex<ElementType>"),
("ElementType", "abs", "std::complex<ElementType>"),
("ElementType", "arg", "std::complex<ElementType>"),
("ElementType", "norm", "std::complex<ElementType>"),
("std::complex<ElementType>", "pow", "std::complex<ElementType>",
                                     "int"),
("std::complex<ElementType>", "pow", "std::complex<ElementType>",
                                     "ElementType"),
("std::complex<ElementType>", "pow", "std::complex<ElementType>",
                                     "std::complex<ElementType>"),
("std::complex<ElementType>", "pow", "ElementType",
                                     "std::complex<ElementType>"),
("std::complex<ElementType>", "polar", "ElementType",
                                       "ElementType"),
)

complex_special_addl_1arg = ("real", "imag", "arg", "norm")
complex_special_addl_2arg = ("polar",)

def generate_1arg_functors():
  for function_name in (
    cmath_1arg + cstdlib_1arg + complex_1arg + complex_special_addl_1arg):
    generate_unary_functor(function_name, function_name + "(x)")

def generate_2arg_functors():
  for function_name in cmath_2arg + complex_special_addl_2arg:
    generate_binary_functor(function_name, function_name + "(x, y)")

def run():
  f = open("std_imports.h", "w")
  sys.stdout = f
  write_copyright()
  print """
#ifndef CCTBX_ARRAY_FAMILY_STD_IMPORTS_H
#define CCTBX_ARRAY_FAMILY_STD_IMPORTS_H

#ifndef DOXYGEN_SHOULD_SKIP_THIS

#include <cmath>
#include <cstdlib>
#include <complex>

namespace cctbx { namespace fn {
"""

  all_function_names = []
  for function_name in cmath_1arg + cmath_2arg + cstdlib_1arg + complex_1arg:
    if (not function_name in all_function_names):
      all_function_names.append(function_name)
  for entry in complex_special:
    function_name = entry[1]
    if (not function_name in all_function_names):
      all_function_names.append(function_name)

  for function_name in all_function_names:
    print "  using std::" + function_name + ";"

  generate_1arg_functors()
  generate_2arg_functors()

  print """
}} // namespace cctbx::fn

#endif // DOXYGEN_SHOULD_SKIP_THIS

#endif // CCTBX_ARRAY_FAMILY_STD_IMPORTS_H"""
  sys.stdout = sys.__stdout__
  f.close()

if (__name__ == "__main__"):
  run()
