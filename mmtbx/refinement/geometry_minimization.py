from __future__ import division
import iotbx.phil
from cctbx import geometry_restraints
import cctbx.geometry_restraints.lbfgs
import scitbx.lbfgs
import sys


master_params_str = """\
  alternate_nonbonded_off_on=False
    .type = bool
  restrain_c_alpha_positions=False
    .type = bool
  max_iterations=500
    .type = int
  macro_cycles=1
    .type = int
  show_geometry_restraints=False
    .type = bool
"""

def master_params():
  return iotbx.phil.parse(master_params_str)

class lbfgs(geometry_restraints.lbfgs.lbfgs):

  def __init__(self,
        sites_cart,
        geometry_restraints_manager,
        geometry_restraints_flags,
        lbfgs_termination_params,
        sites_cart_selection=None,
        lbfgs_exception_handling_params=None,
        rmsd_bonds_termination_cutoff=0,
        rmsd_angles_termination_cutoff=0,
        site_labels=None):
    self.rmsd_bonds_termination_cutoff = rmsd_bonds_termination_cutoff
    self.rmsd_angles_termination_cutoff = rmsd_angles_termination_cutoff
    geometry_restraints.lbfgs.lbfgs.__init__(self,
      sites_cart=sites_cart,
      geometry_restraints_manager=geometry_restraints_manager,
      geometry_restraints_flags=geometry_restraints_flags,
      lbfgs_termination_params=lbfgs_termination_params,
      sites_cart_selection=sites_cart_selection,
      lbfgs_exception_handling_params=lbfgs_exception_handling_params,
      site_labels=site_labels)

  def callback_after_step(self, minimizer):
    self.apply_shifts()
    if([self.rmsd_angles, self.rmsd_bonds].count(None) == 0):
      if(self.rmsd_angles < self.rmsd_angles_termination_cutoff and
         self.rmsd_bonds < self.rmsd_bonds_termination_cutoff):
        return True

def run(processed_pdb_file, params=master_params().extract(), log=sys.stdout):
  co = params
  geometry_restraints_flags = geometry_restraints.flags.flags(default=True)
  all_chain_proxies = processed_pdb_file.all_chain_proxies
  reference_manager = None
  if (co.restrain_c_alpha_positions):
    from mmtbx.geometry_restraints import reference
    ca_selection=all_chain_proxies.pdb_hierarchy.get_peptide_c_alpha_selection()
    ca_sites_cart = \
      all_chain_proxies.sites_cart.deep_copy().select(ca_selection)
    reference_manager = reference.manager()
    reference_manager.add_coordinate_restraints(
      sites_cart=ca_sites_cart,
      selection=ca_selection)
  geometry_restraints_manager = processed_pdb_file.\
    geometry_restraints_manager(show_energies = False,
                                reference_manager=\
                                  reference_manager)
  special_position_settings = all_chain_proxies.special_position_settings
  sites_cart = all_chain_proxies.sites_cart_exact().deep_copy()
  atom_labels = [atom.id_str() for atom in all_chain_proxies.pdb_atoms]
  geometry_restraints_manager.site_symmetry_table \
    .show_special_position_shifts(
      special_position_settings=special_position_settings,
      site_labels=atom_labels,
      sites_cart_original=all_chain_proxies.sites_cart,
      sites_cart_exact=sites_cart,
      out=log,
      prefix="  ")
  if (co.show_geometry_restraints):
    geometry_restraints_manager.show_sorted(
      flags=geometry_restraints_flags,
      sites_cart=sites_cart,
      site_labels=atom_labels)
  pair_proxies =  geometry_restraints_manager.pair_proxies(
    sites_cart=all_chain_proxies.sites_cart,
    flags=geometry_restraints_flags)
  pair_proxies.bond_proxies.show_sorted(
    by_value="residual",
    sites_cart=sites_cart,
    site_labels=atom_labels,
    f=log,
    max_items=10)
  if (pair_proxies.nonbonded_proxies is not None):
    pair_proxies.nonbonded_proxies.show_sorted(
      by_value="delta",
      sites_cart=sites_cart,
      site_labels=atom_labels,
      f=log,
      max_items=10)
  del pair_proxies
  print >> log
  log.flush()
  if (co.alternate_nonbonded_off_on and co.macro_cycles % 2 != 0):
    co.macro_cycles += 1
    print >> log, "INFO: Number of macro cycles increased by one to ensure use of"
    print >> log, "      nonbonded interactions in last macro cycle."
    print >> log
  for i_macro_cycle in xrange(co.macro_cycles):
    if (co.alternate_nonbonded_off_on):
      geometry_restraints_flags.nonbonded = bool(i_macro_cycle % 2)
      print >> log, "Use nonbonded interactions this macro cycle:", \
        geometry_restraints_flags.nonbonded
    minimized = lbfgs(
      sites_cart=sites_cart,
      geometry_restraints_manager=geometry_restraints_manager,
      geometry_restraints_flags=geometry_restraints_flags,
      lbfgs_termination_params=scitbx.lbfgs.termination_parameters(
        max_iterations=co.max_iterations),
      lbfgs_exception_handling_params=
        scitbx.lbfgs.exception_handling_parameters(
          ignore_line_search_failed_step_at_lower_bound=True))
    print >> log, "Energies at start of minimization:"
    minimized.first_target_result.show(f=log)
    print >> log
    print >> log, "Number of minimization iterations:", minimized.minimizer.iter()
    print >> log, "Root-mean-square coordinate difference: %.3f" % (
      all_chain_proxies.sites_cart.rms_difference(sites_cart))
    print >> log
    print >> log, "Energies at end of minimization:"
    minimized.final_target_result.show(f=log)
    print >> log
    geometry_restraints_manager.pair_proxies(
      sites_cart=sites_cart,
      flags=geometry_restraints_flags) \
        .bond_proxies.show_sorted(
          by_value="residual",
          sites_cart=sites_cart,
          site_labels=atom_labels,
          f=log,
          max_items=10)
    print >> log
  assert geometry_restraints_flags.nonbonded
  return sites_cart

class run2(object):
  def __init__(self,
               sites_cart,
               restraints_manager,
               pdb_hierarchy,
               max_number_of_iterations       = 500,
               number_of_macro_cycles         = 5,
               selection                      = None,
               bond                           = False,
               nonbonded                      = False,
               angle                          = False,
               dihedral                       = False,
               chirality                      = False,
               planarity                      = False,
               generic_restraints             = False,
               rmsd_bonds_termination_cutoff  = 0,
               rmsd_angles_termination_cutoff = 0,
               alternate_nonbonded_off_on     = False,
               cdl                            = False,
               log                            = None):
    self.log = log
    if self.log is None:
      self.log = sys.stdout
    self.pdb_hierarchy = pdb_hierarchy
    self.minimized = None
    self.sites_cart = sites_cart
    self.restraints_manager = restraints_manager
    assert max_number_of_iterations+number_of_macro_cycles > 0
    assert [bond,nonbonded,angle,dihedral,chirality,planarity].count(False) < 6
    self.cdl_proxies = None
    if(cdl):
      from mmtbx.conformation_dependent_library import setup_restraints
      self.cdl_proxies = setup_restraints(restraints_manager)
    if(alternate_nonbonded_off_on and number_of_macro_cycles % 2 != 0):
      number_of_macro_cycles += 1
    import scitbx.lbfgs
    lbfgs_termination_params = scitbx.lbfgs.termination_parameters(
      max_iterations = max_number_of_iterations)
    exception_handling_params = scitbx.lbfgs.exception_handling_parameters(
      ignore_line_search_failed_step_at_lower_bound = True)
    geometry_restraints_flags = geometry_restraints.flags.flags(
      bond               = bond,
      nonbonded          = nonbonded,
      angle              = angle,
      dihedral           = dihedral,
      chirality          = chirality,
      planarity          = planarity,
      reference_dihedral = True,
      bond_similarity    = True,
      generic_restraints = True)
    self.update_cdl_restraints()
    self.show()
    for i_macro_cycle in xrange(number_of_macro_cycles):
      print >> self.log, "  macro-cycle:", i_macro_cycle
      if(alternate_nonbonded_off_on and i_macro_cycle<=number_of_macro_cycles/2):
        geometry_restraints_flags.nonbonded = bool(i_macro_cycle % 2)
      self.update_cdl_restraints(macro_cycle=i_macro_cycle)
      self.minimized = lbfgs(
        sites_cart                      = self.sites_cart,
        geometry_restraints_manager     = restraints_manager.geometry,
        geometry_restraints_flags       = geometry_restraints_flags,
        lbfgs_termination_params        = lbfgs_termination_params,
        lbfgs_exception_handling_params = exception_handling_params,
        sites_cart_selection            = selection,
        rmsd_bonds_termination_cutoff   = rmsd_bonds_termination_cutoff,
        rmsd_angles_termination_cutoff  = rmsd_angles_termination_cutoff,
        site_labels                     = None)
      self.show()
      geometry_restraints_flags.nonbonded = nonbonded
      lbfgs_termination_params = scitbx.lbfgs.termination_parameters(
          max_iterations = max_number_of_iterations)

  def update_cdl_restraints(self, macro_cycle=None):
    if(self.cdl_proxies is not None):
      from mmtbx.conformation_dependent_library import update_restraints
      if(macro_cycle is None):
        rc = update_restraints(
          self.pdb_hierarchy,
          self.restraints_manager,
          cdl_proxies=self.cdl_proxies,
          log=self.log,
          verbose=False)
      elif(macro_cycle>0):
        rc = update_restraints(
          self.pdb_hierarchy,
          self.restraints_manager,
          sites_cart=self.sites_cart,
          cdl_proxies=self.cdl_proxies,
          log=self.log,
          verbose=False)

  def show(self):
    es = self.restraints_manager.geometry.energies_sites(
      sites_cart = self.sites_cart, compute_gradients = False)
    es.show(prefix="    ", f=self.log)
