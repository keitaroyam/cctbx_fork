import cctbx.array_family.flex

from scitbx.python_utils import misc
ext = misc.import_ext("cctbx_boost.uctbx_ext")
misc.import_regular_symbols(globals(), ext.__dict__)
del misc

from scitbx.boost_python_utils import injector
import sys

class unit_cell(ext.unit_cell):

  def __init__(self, parameters, is_metrical_matrix=00000):
    if (isinstance(parameters, str)):
      parameters = [float(p) for p in parameters.replace(",", " ").split()]
    ext.unit_cell.__init__(self, parameters, is_metrical_matrix)

class _unit_cell(injector, ext.unit_cell):

  def __str__(self):
    return "(%.6g, %.6g, %.6g, %.6g, %.6g, %.6g)" % self.parameters()

  def show_parameters(self, f=None):
    if (f is None): f = sys.stdout
    print >> f, "Unit cell:", str(self)

  def minimum_reduction(self, expected_cycle_limit=None, iteration_limit=None):
    if (expected_cycle_limit is None): expected_cycle_limit = 2
    if (iteration_limit is None): iteration_limit = 100
    return fast_minimum_reduction(self, expected_cycle_limit, iteration_limit)

  def minimum_cell(self, expected_cycle_limit=None, iteration_limit=None):
    return self.minimum_reduction(
      expected_cycle_limit, iteration_limit).as_unit_cell()

  def is_buerger_cell(self, relative_epsilon=None):
    from cctbx.uctbx.reduction_base import gruber_parameterization
    return gruber_parameterization(self, relative_epsilon).is_buerger_cell()

  def is_niggli_cell(self, relative_epsilon=None):
    from cctbx.uctbx.reduction_base import gruber_parameterization
    return gruber_parameterization(self, relative_epsilon).is_niggli_cell()

  def niggli_reduction(self, relative_epsilon=None, iteration_limit=None):
    from cctbx.uctbx import krivy_gruber_1976
    return krivy_gruber_1976.reduction(self, relative_epsilon, iteration_limit)

  def niggli_cell(self, relative_epsilon=None, iteration_limit=None):
    return self.niggli_reduction(
      relative_epsilon, iteration_limit).as_unit_cell()
