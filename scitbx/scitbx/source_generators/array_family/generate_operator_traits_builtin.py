import path_to_include

def write_copyright():
  try: name = __file__
  except: name = sys.argv[0]
  print \
"""/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Aug: Copied from cctbx/global (Ralf W. Grosse-Kunstleve)
     2002 Jan: Created, based on generate_vector_algebra_traits.py (rwgk)

   *****************************************************
   THIS IS AN AUTOMATICALLY GENERATED FILE. DO NOT EDIT.
   *****************************************************

   Generated by:
     %s
 */""" % (name,)

# Signed types only, to avoid the pitfalls of signed/unsigned conversions.
types_ordered = (
  "signed char",
  "short",
  "int",
  "long",
  "float",
  "double",
  "std::complex<float>",
  "std::complex<double>",
)

class pair:

  def __init__(self, lhs, rhs):
    self.lhs = lhs
    self.rhs = rhs
  def __cmp__(self, other):
    if (self.lhs == other.lhs and self.rhs == other.rhs): return 0
    return 1

special_pairs = (
  (pair("double", "std::complex<float>"), "std::complex<double>"),
  (pair("std::complex<float>", "double"), "std::complex<double>"),
)

import sys

def build_pairs():
  op_types = []
  result_type = []
  for i in xrange(len(types_ordered)):
    for j in xrange(len(types_ordered)):
      op_types.append(pair(types_ordered[i], types_ordered[j]))
      if (i >= j):
        result_type.append(0)
      else:
        result_type.append(types_ordered[j])
  for op_t, result_t in special_pairs:
    result_type[op_types.index(op_t)] = result_t
  return op_types, result_type

def run():
  op_types, result_type = build_pairs()
  assert len(op_types) == len(result_type)
  if ("--Raw" in sys.argv):
    for i in xrange(len(op_types)):
      print "%s + %s = %s" % (op_types[i].lhs, op_types[i].rhs, result_type[i])
  else:
    output_file_name = path_to_include.expand("operator_traits_builtin.h")
    print "Generating:", output_file_name
    f = open(output_file_name, "w")
    sys.stdout = f
    write_copyright()
    print """
#ifndef SCITBX_ARRAY_FAMILY_OPERATOR_TRAITS_BUILTIN_H
#define SCITBX_ARRAY_FAMILY_OPERATOR_TRAITS_BUILTIN_H

#ifndef DOXYGEN_SHOULD_SKIP_THIS

#include <complex>

namespace scitbx { namespace af {

  // The default traits: the result type is the type of the lhs argument.
  template<typename TypeLHS, typename TypeRHS>
  struct binary_operator_traits {
    typedef TypeLHS arithmetic;
  };

  // The remainder of this file defines the traits where the
  // result type is the type of the rhs argument.
"""

    for i in xrange(len(op_types)):
      if (result_type[i]):
        print """  template<>
  struct binary_operator_traits<%s, %s > {
    typedef %s arithmetic;
  };
""" % (op_types[i].lhs, op_types[i].rhs, result_type[i])

    print "}} // namespace scitbx::af"
    print ""
    print "#endif // DOXYGEN_SHOULD_SKIP_THIS"
    print ""
    print "#endif // SCITBX_ARRAY_FAMILY_OPERATOR_TRAITS_BUILTIN_H"
    sys.stdout = sys.__stdout__
    f.close()

if (__name__ == "__main__"):
  run()
