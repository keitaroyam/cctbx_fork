def write_copyright():
  print """// This is an automatically generated file. Do not edit.
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     Jan 2002: Created (Ralf W. Grosse-Kunstleve)
 */"""

arithmetic_unary_ops = ("-")
arithmetic_binary_ops = ("+", "-", "*", "/", "%")
arithmetic_in_place_binary_ops = ("+=", "-=", "*=", "/=", "%=")
logical_unary_ops = ("!")
logical_binary_ops = ("&&", "||")
boolean_ops = ("==", "!=", ">", "<", ">=", "<=")

class empty: pass

def decl_params(array_type_name, op_class, type_flags):
  v = empty
  if (array_type_name == "tiny"):
    if (type_flags == (1,1)):
      v.typelist = \
       ["typename ElementTypeLhs, typename ElementTypeRhs, std::size_t N"]
      v.return_type = (
        "tiny<",
        "  typename binary_operator_traits<",
        "    ElementTypeLhs, ElementTypeRhs>::%s, N>" % (op_class,))
      v.param_lhs = "tiny<ElementTypeLhs, N>"
      v.param_rhs = "tiny<ElementTypeRhs, N>"
    elif (type_flags == (1,0)):
      v.typelist = ["typename ElementTypeLhs, std::size_t N"]
      v.return_type = ("tiny<ElementTypeLhs, N>",)
      v.param_lhs = "tiny<ElementTypeLhs, N>"
      v.param_rhs = "ElementTypeLhs"
    elif (type_flags == (0,1)):
      v.typelist = ["typename ElementTypeRhs, std::size_t N"]
      v.return_type = ("tiny<ElementTypeRhs, N>",)
      v.param_lhs = "ElementTypeRhs"
      v.param_rhs = "tiny<ElementTypeRhs, N>"
  elif (array_type_name == "small"):
    if (type_flags == (1,1)):
      v.typelist = [
        "typename ElementTypeLhs, std::size_t NLhs,",
        "          typename ElementTypeRhs, std::size_t NRhs"]
      v.return_type = (
        "small<",
        "  typename binary_operator_traits<",
        "    ElementTypeLhs, ElementTypeRhs>::%s, (NLhs>NRhs?NLhs:NRhs)>" % (
          op_class,))
      v.param_lhs = "small<ElementTypeLhs, NLhs>"
      v.param_rhs = "small<ElementTypeRhs, NRhs>"
    elif (type_flags == (1,0)):
      v.typelist = ["typename ElementTypeLhs, std::size_t NLhs"]
      v.return_type = ("small<ElementTypeLhs, NLhs>",)
      v.param_lhs = "small<ElementTypeLhs, NLhs>"
      v.param_rhs = "ElementTypeLhs"
    elif (type_flags == (0,1)):
      v.typelist = ["typename ElementTypeRhs, std::size_t NRhs"]
      v.return_type = ("small<ElementTypeRhs, NRhs>",)
      v.param_lhs = "ElementTypeRhs"
      v.param_rhs = "small<ElementTypeRhs, NRhs>"
  else:
    if (type_flags == (1,1)):
      v.typelist = ["typename ElementTypeLhs, typename ElementTypeRhs"]
      v.return_type = (
        "%s<" %(array_type_name,),
        "  typename binary_operator_traits<",
        "    ElementTypeLhs, ElementTypeRhs>::%s>" % (op_class,))
      v.param_lhs = "%s<ElementTypeLhs>" % (array_type_name,)
      v.param_rhs = "%s<ElementTypeRhs>" % (array_type_name,)
    elif (type_flags == (1,0)):
      v.typelist = ["typename ElementTypeLhs"]
      v.return_type = ("%s<ElementTypeLhs>" % (array_type_name,),)
      v.param_lhs = "%s<ElementTypeLhs>" % (array_type_name,)
      v.param_rhs = "ElementTypeLhs"
    elif (type_flags == (0,1)):
      v.typelist = ["typename ElementTypeRhs"]
      v.return_type = ("%s<ElementTypeRhs>" % (array_type_name,),)
      v.param_lhs = "ElementTypeRhs"
      v.param_rhs = "%s<ElementTypeRhs>" % (array_type_name,)
  v.typelist[0] = "template <" + v.typelist[0]
  v.typelist[-1] += ">"
  return v

def algo_params(array_type_name, type_flags):
  v = empty()
  v.result_constructor_args = ""
  v.size_assert = ""
  v.loop_n = "N"
  if (array_type_name != "tiny"):
    if (type_flags == (1,1)):
      v.result_constructor_args = "(lhs.size())"
      v.size_assert = """if (lhs.size() != rhs.size()) throw_range_error();
    """
      v.loop_n = "lhs.size()"
    elif (type_flags == (1,0)):
      v.result_constructor_args = "(lhs.size())"
      v.loop_n = "lhs.size()"
    else:
      v.result_constructor_args = "(rhs.size())"
      v.loop_n = "rhs.size()"
  v.index_lhs = ""
  v.index_rhs = ""
  if (type_flags[0]): v.index_lhs = "[i]"
  if (type_flags[1]): v.index_rhs = "[i]"
  return v

def format_list(list, indent):
  r = ""
  for line in list[:-1]:
    r += indent + line + "\n"
  return r + indent + list[-1]

def elementwise_binary_op(
      array_type_name, op_class, op_symbol, type_flags, function_name):
  d = decl_params(array_type_name, op_class, type_flags)
  a = algo_params(array_type_name, type_flags)
  print """%s
  inline
%s
  %s(
    const %s& lhs,
    const %s& rhs) {
%s
    result%s;
    %sfor(std::size_t i=0;i<%s;i++) result[i] = lhs%s %s rhs%s;
    return result;
  }
""" % (format_list(d.typelist, "  "),
       format_list(d.return_type, "  "),
       function_name, d.param_lhs, d.param_rhs,
       format_list(d.return_type, "    "),
       a.result_constructor_args, a.size_assert, a.loop_n,
       a.index_lhs, op_symbol, a.index_rhs)

def elementwise_inplace_binary_op(
      array_type_name, op_class, op_symbol, type_flags):
  d = decl_params(array_type_name, op_class, type_flags)
  a = algo_params(array_type_name, type_flags)
  print """%s
  inline
  %s&
  operator%s(
    %s& lhs,
    const %s& rhs) {
    %sfor(std::size_t i=0;i<%s;i++) lhs[i] %s rhs%s;
    return lhs;
  }
""" % (format_list(d.typelist, "  "),
       d.param_lhs,
       op_symbol, d.param_lhs, d.param_rhs,
       a.size_assert, a.loop_n,
       op_symbol, a.index_rhs)

def generate_elementwise_binary_op(
      array_type_name, op_class, op_symbol, function_name = None):
  if (function_name == None):
    function_name = "operator" + op_symbol
  for type_flags in ((1,1), (1,0), (0,1)):
    elementwise_binary_op(
      array_type_name, op_class, op_symbol, type_flags, function_name)

def generate_elementwise_inplace_binary_op(
      array_type_name, op_class, op_symbol):
  for type_flags in ((1,1), (1,0)):
    elementwise_inplace_binary_op(
      array_type_name, op_class, op_symbol, type_flags)

def reducing_boolean_op(array_type_name, op_symbol, type_flags):
  d = decl_params(array_type_name, "boolean", type_flags)
  a = algo_params(array_type_name, type_flags)
  truth_test_type = "ElementTypeRhs"
  if (type_flags[0]): truth_test_type = "ElementTypeLhs"
  if (op_symbol == "=="):
    if (a.size_assert != ""):
      a.size_assert = """if (lhs.size() != rhs.size()) return %s() != %s();
    """ % (truth_test_type, truth_test_type)
    tests = (
"""      if (lhs%s != rhs%s) return %s() != %s();"""
    % (a.index_lhs, a.index_rhs, truth_test_type, truth_test_type))
    final_op = "=="
  elif (op_symbol == "!="):
    if (a.size_assert != ""):
      a.size_assert = """if (lhs.size() != rhs.size()) return %s() == %s();
    """ % (truth_test_type, truth_test_type)
    tests = (
"""      if (lhs%s != rhs%s) return %s() == %s();"""
    % (a.index_lhs, a.index_rhs, truth_test_type, truth_test_type))
    final_op = "!="
  elif (op_symbol in ("<", ">")):
    tests = (
"""      if (lhs%s %s rhs%s) return %s() == %s();
      if (rhs%s %s lhs%s) return %s() != %s();"""
    % (a.index_lhs, op_symbol, a.index_rhs, truth_test_type, truth_test_type,
       a.index_rhs, op_symbol, a.index_lhs, truth_test_type, truth_test_type))
    final_op = "!="
  elif (op_symbol in ("<=", ">=")):
    tests = (
"""      if (!(lhs%s %s rhs%s)) return %s() != %s();"""
    % (a.index_lhs, op_symbol, a.index_rhs, truth_test_type, truth_test_type))
    final_op = "=="
  if (type_flags == (1,1)):
    return_type = [
      "typename binary_operator_traits<",
      "  ElementTypeLhs, ElementTypeRhs>::boolean"]
  elif (type_flags == (1,0)):
    return_type = [
      "typename binary_operator_traits<",
      "  ElementTypeLhs, ElementTypeLhs>::boolean"]
  else:
    return_type = [
      "typename binary_operator_traits<",
      "  ElementTypeRhs, ElementTypeRhs>::boolean"]
  print """%s
  inline
%s
  operator%s(
    const %s& lhs,
    const %s& rhs) {
    %sfor(std::size_t i=0;i<%s;i++) {
%s
    }
    return %s() %s %s();
  }
""" % (format_list(d.typelist, "  "),
       format_list(return_type, "  "),
       op_symbol, d.param_lhs, d.param_rhs,
       a.size_assert, a.loop_n, tests,
       truth_test_type, final_op, truth_test_type)

def generate_reducing_boolean_op(array_type_name, op_symbol):
  for type_flags in ((1,1), (1,0), (0,1)):
    reducing_boolean_op(array_type_name, op_symbol, type_flags)

def generate_unary_ops(array_type_name):
  Nresult = ""
  Ntemplate_head = ""
  if (array_type_name in ("tiny", "small")):
    Nresult = ", N"
    Ntemplate_head = ", std::size_t N"
  result_constructor_args = ""
  if (array_type_name != "tiny"): result_constructor_args = "(a.size())"
  for op_class, op_symbol in (("arithmetic", "-"),
                              ("logical", "!")):
    print """  template <typename ElementType%s>
  inline
  %s<
    typename unary_operator_traits<
      ElementType>::%s%s>
  operator%s(const %s<ElementType%s>& a) {
    %s<
      typename unary_operator_traits<
        ElementType>::%s%s> result%s;
    for(std::size_t i=0;i<a.size();i++) result[i] = %sa[i];
    return result;
  }
""" % (Ntemplate_head,
       array_type_name, op_class, Nresult,
       op_symbol, array_type_name, Nresult,
       array_type_name, op_class, Nresult,
       result_constructor_args,
       op_symbol)

def one_type(array_type_name):
  import sys
  f = open("%s_operators.h" % (array_type_name,), "w")
  sys.stdout = f
  write_copyright()
  print """
#ifndef CCTBX_ARRAY_FAMILY_%s_OPERATORS_H
#define CCTBX_ARRAY_FAMILY_%s_OPERATORS_H

#include <cctbx/array_family/operator_traits.h>

namespace cctbx { namespace af {
""" % ((array_type_name.upper(),) * 2)

  generate_unary_ops(array_type_name)
  for op_symbol in arithmetic_binary_ops:
    generate_elementwise_binary_op(
      array_type_name, "arithmetic", op_symbol)
    generate_elementwise_inplace_binary_op(
      array_type_name, "arithmetic", op_symbol + "=")
  for op_symbol in logical_binary_ops:
    generate_elementwise_binary_op(
      array_type_name, "logical", op_symbol)
  for op_symbol, function_name in (
    ("==", "equal_to"),
    ("!=", "not_equal_to"),
    (">", "greater"),
    ("<", "less"),
    (">=", "greater_equal"),
    ("<=", "less_equal")):
    generate_elementwise_binary_op(
      array_type_name, "boolean", op_symbol, function_name)
  for op_symbol in boolean_ops:
    generate_reducing_boolean_op(array_type_name, op_symbol)

  print """}} // namespace cctbx::af

#endif // CCTBX_ARRAY_FAMILY_%s_OPERATORS_H""" % (array_type_name.upper(),)
  sys.stdout = sys.__stdout__
  f.close()

def run():
  one_type("tiny")
  one_type("small")
  one_type("shared")

if (__name__ == "__main__"):
  run()
