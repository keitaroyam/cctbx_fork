from __future__ import division
from iotbx.shelx.errors import *
from iotbx.shelx.lexer import *
from iotbx.shelx.parsers import *
import iotbx.shelx.writer # implicit import

import boost.python
ext = boost.python.import_ext("iotbx_shelx_ext")

def cctbx_xray_structure_from(cls, file=None, filename=None,
                              set_grad_flags=True,
                              min_distance_sym_equiv=0.5,
                              strictly_shelxl=True):
  from iotbx import builders
  builder = builders.crystal_structure_builder(
    set_grad_flags=set_grad_flags,
    min_distance_sym_equiv=min_distance_sym_equiv)
  stream = command_stream(file=file, filename=filename)
  stream = crystal_symmetry_parser(stream, builder)
  stream = atom_parser(stream.filtered_commands(), builder, strictly_shelxl)
  stream.parse()
  return builder.structure

def smtbx_refinement_model_from(cls, ins_or_res=None, hkl=None,
                                fo_sq=None):
  import os
  from iotbx.reflection_file_reader import any_reflection_file
  import iotbx.builders

  if ins_or_res is None:
    assert hkl is not None
    root, _ = os.path.splitext(hkl)
    ins = "%s.ins" % root
    res = "%s.res" % root
    ins_exists = os.path.isfile(ins)
    res_exists = os.path.isfile(res)
    assert ins_exists or res_exists
    if res_exists: ins_or_res = res
    elif ins_exists: ins_or_res = ins

  builder = iotbx.builders.mixin_builder_class(
    "smtbx_builder",
    iotbx.builders.weighted_constrained_restrained_crystal_structure_builder,
    iotbx.builders.reflection_data_source_builder,
    iotbx.builders.twinning_builder)()

  stream = command_stream(filename=ins_or_res)
  stream = crystal_symmetry_parser(stream, builder)
  stream = afix_parser(stream.filtered_commands(), builder)
  stream = atom_parser(stream.filtered_commands(), builder)
  stream = restraint_parser(stream.filtered_commands(), builder)
  stream = instruction_parser(stream.filtered_commands(), builder)
  stream.parse()

  if fo_sq is None:
    if hkl is None:
      assert ins_or_res is not None
      root, _ = os.path.splitext(ins_or_res)
      hkl = "%s.hkl" % root
    assert os.path.isfile(hkl)
    fo_sq = any_reflection_file("%s=hklf4" % hkl)\
           .as_miller_arrays(crystal_symmetry=builder.structure)[0]\
           .merge_equivalents().array()
  else:
    assert hkl is None


  return cls(fo_sq.as_xray_observations(),
             builder.structure,
             builder.constraints,
             builder.restraints_manager,
             builder.weighting_scheme)
