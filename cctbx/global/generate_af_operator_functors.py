import sys

from operator_functor_info import *
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

def run():
  f = open("operator_functors.h", "w")
  sys.stdout = f
  write_copyright()
  print """
#ifndef CCTBX_ARRAY_FAMILY_OPERATOR_FUNCTORS_H
#define CCTBX_ARRAY_FAMILY_OPERATOR_FUNCTORS_H

namespace cctbx { namespace af {"""

  for op in unary_functors.keys():
    generate_unary_functor(
      unary_functors[op], op + " x")
  for op in binary_functors.keys():
    generate_binary_functor(
      binary_functors[op], "x " + op + " y")
  for op in in_place_binary_functors.keys():
    generate_in_place_binary_functor(
      in_place_binary_functors[op], "x " + op + " y")

  print """
}} // namespace cctbx::af

#endif // CCTBX_ARRAY_FAMILY_OPERATOR_FUNCTORS_H"""
  sys.stdout = sys.__stdout__
  f.close()

if (__name__ == "__main__"):
  run()
