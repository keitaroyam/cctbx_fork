import cctbx.array_family.flex

from scitbx.python_utils import misc
ext = misc.import_ext("cctbx_boost.dmtbx_ext")
misc.import_regular_symbols(globals(), ext.__dict__)
del misc

from cctbx.array_family import flex
from scitbx.boost_python_utils import injector
import sys

class _weighted_triplet_phase_relation(
  injector, weighted_triplet_phase_relation):

  def format(self, miller_indices, ih=None):
    l = [miller_indices[self.ik()],
         self.friedel_flag_k(),
         miller_indices[self.ihmk()],
         self.friedel_flag_hmk(),
         self.ht_sum(),
         self.weight()]
    if (ih is not None):
      l.insert(0, miller_indices[ih])
    return " ".join([str(item).replace(" ", "") for item in l])

class _triplet_generator(injector, triplet_generator):

  def apply_tangent_formula(self, amplitudes, phases,
                                  selection_fixed=None,
                                  use_fixed_only=00000,
                                  reuse_results=00000,
                                  sum_epsilon=1.e-10):
    if (selection_fixed is None): selection_fixed = flex.bool()
    return triplet_generator.raw_apply_tangent_formula(
      self, amplitudes, phases,
      selection_fixed, use_fixed_only, reuse_results, sum_epsilon)
