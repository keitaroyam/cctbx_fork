import boost.python
boost.python.import_ext("smtbx_refinement_constraints_ext")
import smtbx_refinement_constraints_ext as ext
from smtbx_refinement_constraints_ext import *

import libtbx
import scitbx.sparse
from scitbx.array_family import flex
from cctbx import crystal
from cctbx.eltbx import covalent_radii

class _parameter(boost.python.injector, ext.parameter):

  def arguments(self):
    """ An iterator over its arguments """
    for i in xrange(self.n_arguments):
      yield self.argument(i)

  def __str__(self):
    """ String representation using the graphviz DOT language """
    try:
      scatt = ', '.join([ sc.label for sc in self.scatterers ])
      scatt = "(%s)" % scatt
    except AttributeError:
      scatt = ""
    lbl = '%i [label="%s%s%s #%s"]' % (
      self.index, ('', '*')[self.is_root], self.__class__.__name__,
      scatt, self.index)
    return lbl


class reparametrisation(ext.reparametrisation):
  """ Enhance the C++ level reparametrisation class for ease of use """

  temperature = 20 # Celsius
  covalent_bond_tolerance = 0.5 # Angstrom

  def __init__(self,
               structure,
               geometrical_constraints,
               **kwds):
    """ Construct for the given instance of xray.structure subject to the
    given sequence of constraints. Each constraint instance shall understand:
    constraint.add_to(self). That method shall perform 2 tasks:

      - add to self the parameters relevant to the reparametrisation
        associated with that constraint;

      - update self.asu_scatterer_parameters.

    The latter is an array containing one instance of scatterer_parameters
    for each scatterer in the a.s.u.
    C.f. module geometrical_hydrogens in this package for a typical example
    """
    super(reparametrisation, self).__init__(structure.unit_cell())
    self.structure = xs = structure
    scatterers = xs.scatterers()
    self.site_symmetry_table_ = self.structure.site_symmetry_table()
    libtbx.adopt_optional_init_args(self, kwds)
    self.asu_scatterer_parameters = shared_scatterer_parameters(xs.scatterers())

    radii = [
      covalent_radii.table(elt).radius()
      for elt in xs.scattering_type_registry().type_index_pairs_as_dict() ]
    self.buffer_thickness = 2*max(radii) + self.covalent_bond_tolerance

    asu_mappings = xs.asu_mappings(buffer_thickness=self.buffer_thickness)
    bond_table = crystal.pair_asu_table(asu_mappings)
    bond_table.add_covalent_pairs(xs.scattering_types(),
                                  tolerance=self.covalent_bond_tolerance)
    self.pair_sym_table = bond_table.extract_pair_sym_table(
      skip_j_seq_less_than_i_seq=False)

    for constraint in geometrical_constraints:
      constraint.add_to(self)

    for i_sc in xrange(len(self.asu_scatterer_parameters)):
      self.add_new_site_parameter(i_sc)
      self.add_new_thermal_displacement_parameter(i_sc)
      self.add_new_occupancy_parameter(i_sc)
    self.finalise()

  def finalise(self):
    super(reparametrisation, self).finalise()
    self.mapping_to_grad_fc = \
        self.asu_scatterer_parameters.mapping_to_grad_fc()

  def _(self):
    return self.jacobian_transpose.n_rows
  n_independent_params = property(_)

  def jacobian_transpose_matching_grad_fc(self):
    """ The columns of self.jacobian_transpose corresponding to crystallographic
    parameters, in the same order as the derivatives in grad Fc. In this class,
    the latter is assumed to follow the convention of smtbx.structure_factors
    """
    return self.jacobian_transpose.select_columns(self.mapping_to_grad_fc)

  def add_new_occupancy_parameter(self, i_sc):
    occ = self.asu_scatterer_parameters[i_sc].occupancy
    if occ is None:
      sc = self.structure.scatterers()[i_sc]
      occ = self.add(independent_occupancy_parameter, sc)
      self.asu_scatterer_parameters[i_sc].occupancy = occ
    return occ

  def add_new_site_parameter(self, i_scatterer, symm_op=None):
    s = self.asu_scatterer_parameters[i_scatterer].site
    if s is None:
      site_symm = self.site_symmetry_table_.get(i_scatterer)
      sc = self.structure.scatterers()[i_scatterer]
      if site_symm.is_point_group_1():
        s = self.add(independent_site_parameter, sc)
      else:
        s = self.add(special_position_site, site_symm, sc)
      if symm_op is not None and not symm_op.is_unit_mx():
        s = self.add(symmetry_equivalent_site_parameter, s)
      self.asu_scatterer_parameters[i_scatterer].site = s
    return s

  def add_new_thermal_displacement_parameter(self, i_scatterer):
    u = self.asu_scatterer_parameters[i_scatterer].u
    if u is None:
      sc = self.structure.scatterers()[i_scatterer]
      assert not (sc.flags.use_u_iso() and sc.flags.use_u_aniso())
      if sc.flags.use_u_iso():
        u = self.add(independent_u_iso_parameter, sc)
      else:
        site_symm = self.site_symmetry_table_.get(i_scatterer)
        if site_symm.is_point_group_1():
          u = self.add(independent_u_star_parameter, sc)
        else:
          u = self.add(special_position_u_star_parameter,
                       site_symm,
                       sc)
      self.asu_scatterer_parameters[i_scatterer].u = u
    return u

  def __str__(self):
    """ String representation using the graphviz DOT language """
    self.finalise()
    bits = []
    for p in self.parameters():
      for q in p.arguments():
        bits.append("%i -> %i" % (p.index, q.index))
    dsu_bits = []
    for p in self.parameters():
      dsu_bits.append((p.index, str(p)))
    dsu_bits.sort()
    bits.extend([ p for i,p in dsu_bits ])
    return "digraph dependencies {\n%s\n}" % ';\n'.join(bits)
