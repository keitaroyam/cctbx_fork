import sys

def write_copyright():
  print \
"""/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Jan 2002: Created, based on generate_af_operators.py (rwgk)

   *****************************************************
   THIS IS AN AUTOMATICALLY GENERATED FILE. DO NOT EDIT.
   *****************************************************

   Generated by:
     %s
 */""" % (sys.argv[0],)

from generate_af_algebras import *

def binary_operator_algo_params(type_flags):
  r = empty()
  if (type_flags == (1,1)):
    r.have_both_test = "a1.f && a2.f"
  else:
    r.have_both_test = "a%d.f" % ((type_flags[1] + 1),)
  r.dotv = ["", ""]
  for i in xrange(2):
    if (type_flags[i]): r.dotv[i] = ".v"
  return r

def elementwise_binary_op(op_class, op_symbol, type_flags):
  d = operator_decl_params("flagged_value", "binary", op_class, type_flags)
  a = binary_operator_algo_params(type_flags)
  print """%s
  inline
%s
  operator%s(
    const %s& a1,
    const %s& a2) {
%s result;
    if (%s) {
      result.v = a1%s %s a1%s;
      result.f = true;
    }
    return result;
  }
""" % (format_header("  ", d.header),
       format_list("  ", d.return_array_type),
       op_symbol, d.params[0], d.params[1],
       format_list("    ", d.return_array_type),
       a.have_both_test, a.dotv[0], op_symbol, a.dotv[1])

def elementwise_inplace_binary_op(op_symbol, type_flags):
  d = operator_decl_params("flagged_value", "binary", "n/a", type_flags)
  a = binary_operator_algo_params(type_flags)
  if (type_flags == (1,1)):
    action = """    if (a1.f) {
      if (a2.f) a1.v %s a2.v;
      else a1.f = false;
    }""" % (op_symbol,)
  else:
    action = "    if (a1.f) a1.v %s a2;" % (op_symbol,)
  print """%s
  inline
  %s&
  operator%s(
    %s& a1,
    const %s& a2) {
%s
    return a1;
  }
""" % (format_header("  ", d.header),
       d.params[0],
       op_symbol, d.params[0], d.params[1],
       action)

def generate_elementwise_binary_op(op_class, op_symbol):
  for type_flags in ((1,1), (1,0), (0,1)):
    elementwise_binary_op(op_class, op_symbol, type_flags)
  if (op_class == "arithmetic"):
    for type_flags in ((1,1), (1,0)):
      elementwise_inplace_binary_op(op_symbol + "=", type_flags)

def generate_unary_ops():
  for op_class, op_symbol in (("arithmetic", "-"),
                              ("logical", "!")):
    d = operator_decl_params("flagged_value", "unary", op_class, (1,0))
    print """%s
  inline
%s
  operator%s(const %s& a) {
%s result;
    if (a.f) {
      result.v = %sa.v;
      result.f = true;
    }
    return result;
  }
""" % (format_header("  ", d.header),
       format_list("  ", d.return_array_type),
       op_symbol, d.params[0],
       format_list("    ", d.return_array_type),
       op_symbol)

def run():
  f = open("flagged_value_algebra.h", "w")
  sys.stdout = f
  write_copyright()
  print """
#ifndef CCTBX_ARRAY_FAMILY_FLAGGED_VALUE_ALGEBRA_H
#define CCTBX_ARRAY_FAMILY_FLAGGED_VALUE_ALGEBRA_H

#include <cctbx/array_family/operator_traits_builtin.h>

namespace cctbx { namespace af {
"""

  generate_unary_ops()
  for op_symbol in arithmetic_binary_ops:
    generate_elementwise_binary_op("arithmetic", op_symbol)
  for op_symbol in logical_binary_ops:
    generate_elementwise_binary_op("logical", op_symbol)
  for op_symbol in boolean_ops:
    generate_elementwise_binary_op("boolean", op_symbol)

  print """}} // namespace cctbx::af

#endif // CCTBX_ARRAY_FAMILY_FLAGGED_VALUE_ALGEBRA_H"""
  sys.stdout = sys.__stdout__
  f.close()

if (__name__ == "__main__"):
  run()
