from iotbx import reflection_file_reader
from iotbx.option_parser import iotbx_option_parser
from cctbx import crystal
from cctbx import sgtbx
from cctbx.array_family import flex
from libtbx.itertbx import count
import sys

class array_cache:

  def __init__(self, input):
    self.input = input
    self.change_of_basis_op_to_minimum_cell \
      = self.input.change_of_basis_op_to_minimum_cell()
    self.observations = self.input.change_basis(
      cb_op=self.change_of_basis_op_to_minimum_cell) \
        .expand_to_p1() \
        .map_to_asu()
    if (self.input.anomalous_flag()):
      self.anom_diffs = abs(self.input.anomalous_differences()).change_basis(
        cb_op=self.change_of_basis_op_to_minimum_cell) \
          .expand_to_p1() \
          .map_to_asu()
    else:
      self.anom_diffs = None
    self.minimum_cell_symmetry = crystal.symmetry.change_basis(
      self.input,
      cb_op=self.change_of_basis_op_to_minimum_cell)
    self.patterson_group = self.minimum_cell_symmetry.space_group() \
      .build_derived_patterson_group()
    self.patterson_group.make_tidy()
    self.resolution_range = self.input.resolution_range()

  def similarity_transformations(self,
        other,
        relative_length_tolerance=0.02,
        absolute_angle_tolerance=2):
    c_inv_rs = self.minimum_cell_symmetry.unit_cell() \
      .similarity_transformations(
        other=other.minimum_cell_symmetry.unit_cell(),
        relative_length_tolerance=relative_length_tolerance,
        absolute_angle_tolerance=absolute_angle_tolerance)
    expanded_groups = [self.patterson_group]
    if (other.patterson_group != self.patterson_group):
      expanded_groups.append(other.patterson_group)
    patterson_groups = tuple(expanded_groups)
    result = []
    for c_inv_r in c_inv_rs:
      c_inv = sgtbx.rt_mx(sgtbx.rot_mx(c_inv_r))
      if (c_inv.is_unit_mx()):
        result.append(sgtbx.change_of_basis_op(c_inv))
      else:
        for patterson_group in patterson_groups:
          expanded_group = sgtbx.space_group(patterson_group)
          try:
            expanded_group.expand_smx(c_inv)
          except:
            result.append(sgtbx.change_of_basis_op(c_inv).inverse())
          else:
            expanded_group.make_tidy()
            def is_in_expanded_groups():
              for g in expanded_groups:
                if (g == expanded_group): return True
              return False
            if (not is_in_expanded_groups()):
              expanded_groups.append(expanded_group)
              result.append(sgtbx.change_of_basis_op(c_inv).inverse())
    return result

  def combined_cb_op(self, other, cb_op):
    s = self.change_of_basis_op_to_minimum_cell
    o = other.change_of_basis_op_to_minimum_cell
    return s.inverse() * cb_op.new_denominators(s) * o

  def setup_common_binner(self,
        other,
        auto_binning=False,
        reflections_per_bin=0,
        n_bins=0):
    d_max = min(self.resolution_range[0], other.resolution_range[0])
    d_min = max(self.resolution_range[1], other.resolution_range[1])
    if (d_max == d_min):
      d_max += d_max*0.5
      d_min -= d_min*0.5
    self.observations.setup_binner(
      d_max=d_max,
      d_min=d_min,
      auto_binning=auto_binning,
      reflections_per_bin=reflections_per_bin,
      n_bins=n_bins)
    if (self.anom_diffs is not None and other.anom_diffs is not None):
      self.anom_diffs.setup_binner(
        d_max=d_max,
        d_min=d_min,
        auto_binning=auto_binning,
        reflections_per_bin=reflections_per_bin,
        n_bins=n_bins)

def binned_correlation_fmt(correlation):
  return "%6.3f" % correlation.coefficient()

def run(args):
  print "Command line arguments:",
  for arg in args: print arg,
  print
  print
  command_line = (iotbx_option_parser(
    usage="iotbx.reflection_statistics [options] reflection_file [...]",
    description="Example: iotbx.reflection_statistics data1.mtz data2.sca")
    .enable_symmetry_comprehensive()
    .option(None, "--quick",
      action="store_true",
      dest="quick",
      help="Do not compute statistics between pairs of data arrays")
    .enable_resolutions()
    .option(None, "--bins",
      action="store",
      type="int",
      dest="n_bins",
      default=10,
      help="Number of bins",
      metavar="INT")
  ).process(args=args)
  if (len(command_line.args) == 0):
    command_line.parser.show_help()
    return
  array_caches = []
  for file_name in command_line.args:
    reflection_file = reflection_file_reader.any_reflection_file(
      file_name=file_name)
    miller_arrays = None
    if (reflection_file.file_type() is not None):
      try:
        miller_arrays = reflection_file.as_miller_arrays(
          crystal_symmetry=command_line.symmetry)
      except:
        pass
    if (miller_arrays is None):
      print >> sys.stderr, "Warning: unknown file format:", file_name
      print >> sys.stderr
      sys.stderr.flush()
    else:
      for miller_array in miller_arrays:
        info = miller_array.info()
        miller_array = miller_array.select(
          miller_array.indices() != (0,0,0))
        if (miller_array.indices().size() == 0): continue
        if (miller_array.is_xray_intensity_array()):
          miller_array = miller_array.f_sq_as_f()
        elif (miller_array.is_complex_array()):
          miller_array = abs(miller_array)
        if (miller_array.is_real_array()):
          if (miller_array.unit_cell() is None):
            print
            print "*" * 79
            print "Unknown unit cell parameters:", miller_array.info()
            print "Use --symmetry or --unit_cell to define unit cell:"
            print "*" * 79
            print
            command_line.parser.show_help()
            return
          if (miller_array.space_group_info() is None):
            print
            print "*" * 79
            print "Unknown space group:", miller_array.info()
            print "Use --symmetry or --space_group to define space group:"
            print "*" * 79
            print
            command_line.parser.show_help()
            return
          if (   command_line.options.resolution is not None
              or command_line.options.low_resolution is not None):
            miller_array = miller_array.resolution_filter(
              d_max=command_line.options.low_resolution,
              d_min=command_line.options.resolution)
          miller_array = miller_array.map_to_asu()
          miller_array.set_info(info=info)
          array_caches.append(array_cache(input=miller_array))
  if (len(array_caches) > 2):
    print "Array indices (for quick searching):"
    for i_0,cache_0 in enumerate(array_caches):
      print "  %2d:" % (i_0+1), cache_0.input.info()
    print
    print "Useful search patterns are:"
    print "    Summary i"
    print "    CC Obs i j"
    print "    CC Ano i j"
    print "  i and j are the indices shown above."
    print
  n_bins = command_line.options.n_bins
  for i_0,cache_0 in enumerate(array_caches):
    print "Summary", i_0+1
    cache_0.input.show_comprehensive_summary()
    print
    reindexing_info = cache_0.input.reindexing_info(max_delta=0.1)
    if (len(reindexing_info.matrices) == 0):
      print "Possible twin laws: None"
      print
    else:
      print "Space group of the metric:", \
        reindexing_info.lattice_symmetry() \
          .as_reference_setting() \
          .space_group_info()
      s = str(reindexing_info.idealized_unit_cell())
      if (s != str(cache_0.input.unit_cell())):
        print "Idealized unit cell:", s
      print "Possible twin laws:"
      for c in reindexing_info.matrices:
        print " ", c.r().as_hkl()
      print
    print "Completeness of %s:" % str(cache_0.input.info())
    cache_0.input.setup_binner(n_bins=n_bins)
    cache_0.input.show_completeness_in_bins()
    print
    if (cache_0.input.anomalous_flag()):
      print "Anomalous signal of %s:" % str(cache_0.input.info())
      print cache_0.input.anomalous_signal.__doc__
      anom_signal = cache_0.input.anomalous_signal(use_binning=True)
      anom_signal.show(data_fmt="%.4f")
      print
    if (not command_line.options.quick):
      for j_1,cache_1 in enumerate(array_caches[i_0+1:]):
        i_1 = j_1+i_0+1
        similarity_transformations = cache_0.similarity_transformations(
          other=cache_1,
          relative_length_tolerance=0.05,
          absolute_angle_tolerance=5)
        if (len(similarity_transformations) == 0):
          print "Incompatible unit cells:"
          print " ", cache_0.input.info()
          print " ", cache_1.input.info()
          print "No comparison."
          print
        else:
          ccs = flex.double()
          for cb_op in similarity_transformations:
            similar_array_1 = cache_1.observations \
              .change_basis(cb_op) \
              .map_to_asu()
            ccs.append(cache_0.observations.correlation(
              other=similar_array_1,
              assert_is_similar_symmetry=False).coefficient())
          permutation = flex.sort_permutation(ccs, reverse=True)
          ccs = ccs.select(permutation)
          similarity_transformations = flex.select(
            similarity_transformations, permutation=permutation)
          for i_cb_op,cb_op,cc in zip(count(),
                                      similarity_transformations,
                                      ccs):
            combined_cb_op = cache_0.combined_cb_op(other=cache_1, cb_op=cb_op)
            if (not combined_cb_op.c().is_unit_mx()):
              reindexing_note = " with reindexing"
              hkl_str = " "+combined_cb_op.as_hkl()
            else:
              reindexing_note = ""
              hkl_str = ""
            print "CC Obs", i_0+1, i_1+1, "%6.3f"%cc, combined_cb_op.as_hkl()
            print "Correlation of:"
            print " ", cache_0.input.info()
            print " ", cache_1.input.info()
            print "Overall correlation%s: %6.3f%s" % (
              reindexing_note, cc, hkl_str)
            show_in_bins = False
            if (i_cb_op == 0 or (cc >= 0.3 and cc >= ccs[0]-0.2)):
              show_in_bins = True
              similar_array_1 = cache_1.observations \
                .change_basis(cb_op) \
                .map_to_asu()
              cache_0.setup_common_binner(cache_1, n_bins=n_bins)
              correlation = cache_0.observations.correlation(
                other=similar_array_1,
                use_binning=True,
                assert_is_similar_symmetry=False)
              correlation.show(data_fmt=binned_correlation_fmt)
            print
            if (    cache_0.anom_diffs is not None
                and cache_1.anom_diffs is not None):
              similar_anom_diffs_1 = cache_1.anom_diffs \
                .change_basis(cb_op) \
                .map_to_asu()
              correlation = cache_0.anom_diffs.correlation(
                other=similar_anom_diffs_1,
                assert_is_similar_symmetry=False)
              print "CC Ano", i_0+1, i_1+1, \
                "%6.3f"%correlation.coefficient(), combined_cb_op.as_hkl()
              print "Anomalous difference correlation of:"
              print " ", cache_0.input.info()
              print " ", cache_1.input.info()
              print "Overall correlation%s: %6.3f%s" % (
                reindexing_note, correlation.coefficient(), hkl_str)
              if (show_in_bins):
                correlation = cache_0.anom_diffs.correlation(
                  other=similar_anom_diffs_1,
                  use_binning=True,
                  assert_is_similar_symmetry=False)
                correlation.show(data_fmt=binned_correlation_fmt)
              print
    print "=" * 79
    print

if (__name__ == "__main__"):
  run(sys.argv[1:])
