from __future__ import division
from libtbx import adopt_init_args
from cctbx import geometry_restraints
from cctbx.array_family import flex
import scitbx.restraints
from stdlib import math
import sys

class energies(scitbx.restraints.energies):

  def __init__(self, sites_cart,
               unit_cell=None,
               bond_proxies=None,
               nonbonded_proxies=None,
               nonbonded_function=None,
               angle_proxies=None,
               dihedral_proxies=None,
               reference_coordinate_proxies=None,
               reference_dihedral_manager=None,
               ncs_dihedral_manager=None,
               den_manager=None,
               chirality_proxies=None,
               planarity_proxies=None,
               parallelity_proxies=None,
               bond_similarity_proxies=None,
               ramachandran_manager=None,
               external_energy_function=None,
               compute_gradients=True,
               gradients=None,
               disable_asu_cache=False,
               normalization=False,
               extension_objects=[]):
    adopt_init_args(self, locals())
    scitbx.restraints.energies.__init__(self,
                                        compute_gradients=compute_gradients,
                                        gradients=gradients,
                                        gradients_size=sites_cart.size(),
                                        gradients_factory=flex.vec3_double,
                                        normalization=normalization)
    self.n_dihedral_restraints = None
    self.dihedral_restraints_residual_sum = 0
    if (nonbonded_proxies is not None): assert nonbonded_function is not None
    if (compute_gradients):
      if (self.gradients is None):
        self.gradients = flex.vec3_double(sites_cart.size(), [0,0,0])
      else:
        assert self.gradients.size() == sites_cart.size()

    if (bond_proxies is None):
      self.n_bond_proxies = None
      self.bond_residual_sum = 0
    else:
      self.n_bond_proxies = bond_proxies.n_total()
      self.bond_residual_sum = geometry_restraints.bond_residual_sum(
        sites_cart=sites_cart,
        sorted_asu_proxies=bond_proxies,
        gradient_array=self.gradients,
        disable_cache=disable_asu_cache)
      self.number_of_restraints += self.n_bond_proxies
      self.residual_sum += self.bond_residual_sum
    if (nonbonded_proxies is None):
      self.n_nonbonded_proxies = None
      self.nonbonded_residual_sum = 0
    else:
      self.n_nonbonded_proxies = nonbonded_proxies.n_total()
      self.nonbonded_residual_sum = geometry_restraints.nonbonded_residual_sum(
        sites_cart=sites_cart,
        sorted_asu_proxies=nonbonded_proxies,
        gradient_array=self.gradients,
        function=nonbonded_function,
        disable_cache=False)
      self.number_of_restraints += self.n_nonbonded_proxies
      self.residual_sum += self.nonbonded_residual_sum

    # ====================================================================
    # Unit cell dependent
    # ====================================================================
    # name, parameter, function to call
    for name, proxies, residual_sum_function in [
        ("angle", angle_proxies, geometry_restraints.angle_residual_sum),
        ("dihedral",dihedral_proxies, geometry_restraints.dihedral_residual_sum),
        ("planarity", planarity_proxies, geometry_restraints.planarity_residual_sum),
        ("parallelity", parallelity_proxies, geometry_restraints.parallelity_residual_sum),
        ("bond_similarity", bond_similarity_proxies, geometry_restraints.bond_similarity_residual_sum)]:
      setattr(self, "n_%s_proxies" % name, None)
      setattr(self, "%s_residual_sum" % name, 0)
      if proxies is not None:
        n_proxies = proxies.size()
        # setattr(self, "n_%s_proxies" % name, proxies.size())
        if unit_cell is None:
          res_sum = residual_sum_function(
              sites_cart=sites_cart,
              proxies=proxies,
              gradient_array=self.gradients)
        else:
          res_sum = residual_sum_function(
              unit_cell=unit_cell,
              sites_cart=sites_cart,
              proxies=proxies,
              gradient_array=self.gradients)
        self.number_of_restraints += n_proxies
        self.residual_sum += res_sum
        setattr(self, "n_%s_proxies" % name, n_proxies)
        setattr(self, "%s_residual_sum" % name, res_sum)

    # ====================================================================
    # Managers
    # ====================================================================
    for name, manager in [
        ("reference_dihedral", reference_dihedral_manager),
        ("ncs_dihedral", ncs_dihedral_manager),
        ("den", den_manager),
        ("ramachandran", ramachandran_manager)]:
      setattr(self, "n_%s_proxies" % name, None)
      setattr(self, "%s_residual_sum" % name, 0)
      if manager is not None:
        n_proxies = manager.get_n_proxies()
        res_sum = manager.target_and_gradients(
            unit_cell=unit_cell,
            sites_cart=sites_cart,
            gradient_array=self.gradients)
        self.number_of_restraints += n_proxies
        self.residual_sum += res_sum
        setattr(self, "n_%s_proxies" % name, n_proxies)
        setattr(self, "%s_residual_sum" % name, res_sum)

    # ====================================================================
    # The rest (not yet unified)
    # ====================================================================
    if reference_coordinate_proxies is None:
      self.n_reference_coordinate_proxies = None
      self.reference_coordinate_residual_sum = 0
    else:
      import boost.python
      ext = boost.python.import_ext("mmtbx_reference_coordinate_ext")
      self.n_reference_coordinate_proxies = reference_coordinate_proxies.size()
      self.reference_coordinate_residual_sum = \
          ext.reference_coordinate_residual_sum(
              sites_cart=sites_cart,
              proxies=reference_coordinate_proxies,
              gradient_array=self.gradients)
      self.number_of_restraints += self.n_reference_coordinate_proxies
      self.residual_sum += self.reference_coordinate_residual_sum

    if (chirality_proxies is None):
      self.n_chirality_proxies = None
      self.chirality_residual_sum = 0
    else:
      self.n_chirality_proxies = len(chirality_proxies)
      self.chirality_residual_sum = geometry_restraints.chirality_residual_sum(
        sites_cart=sites_cart,
        proxies=chirality_proxies,
        gradient_array=self.gradients)
      self.number_of_restraints += self.n_chirality_proxies
      self.residual_sum += self.chirality_residual_sum

    if (external_energy_function is not None) :
      self.external_energy = external_energy_function(
        sites_cart=sites_cart,
        gradient_array=self.gradients)
      self.residual_sum += self.external_energy
    else :
      self.external_energy = 0
    for extension_obj in self.extension_objects:
      extension_obj.energies_add(energies_obj=self)
    self.finalize_target_and_gradients()

  # Not used anymore? -- used in model_statistics.py
  def get_filtered_n_bond_proxies(self):
    correct_id_proxies = [i.origin_id for i in self.bond_proxies.simple].count(0)
    return correct_id_proxies

  def get_filtered_n_angle_proxies(self):
    correct_id_proxies = [i.origin_id for i in self.angle_proxies].count(0)
    return correct_id_proxies

  def bond_deviations_z(self):
    '''
    Calculate rmsz of bond deviations

    Compute rmsz, the Root-Mean-Square of the z-scors for a set of data
    using z_i = {x_i - mu / sigma}  and rmsz = sqrt(mean(z*z))
    x_i: atcual bond length
    mu: geometry restraints mean
    sigma:  geometry restraints standard deviation
    z_i: z-score for bond i
    z: array of z_i

    The sigma and the (x_i - mu) are model constrains, geometry restraints. They function extracts
    from self, not calculated from data.

    :returns:
    b_rmsz: rmsz, root mean square of the z-scors of all bonds
    b_z_min/max: min/max abolute values of z-scors
    '''
    if(self.n_bond_proxies is not None):
      bond_deltas = self.bond_proxies.deltas(
          sites_cart=self.sites_cart, origin_id=0)
      if len(bond_deltas) >0:
        sigmas = [geometry_restraints.weight_as_sigma(x.weight) for x in self.bond_proxies.simple]
        z_scores = flex.double([(bond_delta/sigma) for bond_delta,sigma in zip(bond_deltas,sigmas)])
        b_rmsz = math.sqrt(flex.mean_default(z_scores*z_scores,0))
        b_z_max = flex.max_default(flex.abs(z_scores), 0)
        b_z_min = flex.min_default(flex.abs(z_scores), 0)
        return b_z_min, b_z_max, b_rmsz
      else:
        return 0,0,0

  def bond_deviations(self):
    if(self.n_bond_proxies is not None):
      bond_deltas = self.bond_proxies.deltas(
          sites_cart=self.sites_cart, origin_id=0)
      if len(bond_deltas) >0:
        b_sq  = bond_deltas * bond_deltas
        b_ave = math.sqrt(flex.mean_default(b_sq, 0))
        b_max = math.sqrt(flex.max_default(b_sq, 0))
        b_min = math.sqrt(flex.min_default(b_sq, 0))
        return b_min, b_max, b_ave
      else:
        return 0,0,0

  def angle_deviations_z(self):
    '''
    Calculate rmsz of angles deviations

    Compute rmsz, the Root-Mean-Square of the z-scors for a set of data
    using z_i = {x_i - mu / sigma}  and rmsz = sqrt(mean(z*z))

    Compute rmsz, the Root-Mean-Square of the z-scors for a set of data
    using z_i = {x_i - mu / sigma}  and rmsz = sqrt(mean(z*z))
    x_i: atcual bond angle
    mu: geometry restraints mean
    sigma:  geometry restraints standard deviation
    z_i: z-score for bond i
    z: array of z_i

    The sigma and the (x_i - mu) are model constrains, geometry restraints. They function extracts
    from self, not calculated from data.

    :returns:
    a_rmsz: rmsz, root mean square of the z-scors of all angles
    a_z_min/max: min/max values of z-scors
    '''
    if(self.n_angle_proxies is not None):
      angle_deltas = self.angle_proxies.proxy_select(origin_id=0).deltas(
          sites_cart=self.sites_cart)
      if len(angle_deltas) > 0:
        sigmas = [geometry_restraints.weight_as_sigma(x.weight) for x in self.angle_proxies]
        z_scores = flex.double([(angle_delta/sigma) for angle_delta,sigma in zip(angle_deltas,sigmas)])
        a_rmsz = math.sqrt(flex.mean_default(z_scores*z_scores,0))
        a_z_max = flex.max_default(flex.abs(z_scores), 0)
        a_z_min = flex.min_default(flex.abs(z_scores), 0)
        return a_z_min, a_z_max, a_rmsz
      else:
        return 0,0,0

  def angle_deviations(self):
    if(self.n_angle_proxies is not None):
      angle_deltas = self.angle_proxies.proxy_select(origin_id=0).deltas(
          sites_cart=self.sites_cart)
      if len(angle_deltas) > 0:
        a_sq  = angle_deltas * angle_deltas
        a_ave = math.sqrt(flex.mean_default(a_sq, 0))
        a_max = math.sqrt(flex.max_default(a_sq, 0))
        a_min = math.sqrt(flex.min_default(a_sq, 0))
        return a_min, a_max, a_ave
      else:
        return 0,0,0

  def nonbonded_distances(self):
    return geometry_restraints.nonbonded_deltas(
      sites_cart         = self.sites_cart,
      sorted_asu_proxies = self.nonbonded_proxies)

  def nonbonded_deviations(self):
    if(self.n_nonbonded_proxies is not None):
      nonbonded_deltas = self.nonbonded_distances()
      r_sq  = nonbonded_deltas * nonbonded_deltas
      r_ave = math.sqrt(flex.mean_default(r_sq, 0))
      r_max = math.sqrt(flex.max_default(r_sq, 0))
      r_min = math.sqrt(flex.min_default(r_sq, 0))
      return r_min, r_max, r_ave

  def dihedral_deviations(self):
    # !!!XXX!!! Warnign! this works wrong because it is not aware of origin_id!
    if(self.n_dihedral_proxies is not None):
      dihedral_deltas = geometry_restraints.dihedral_deltas(
        sites_cart = self.sites_cart,
        proxies    = self.dihedral_proxies)
      d_sq  = dihedral_deltas * dihedral_deltas
      d_ave = math.sqrt(flex.mean_default(d_sq, 0))
      d_max = math.sqrt(flex.max_default(d_sq, 0))
      d_min = math.sqrt(flex.min_default(d_sq, 0))
      return d_min, d_max, d_ave

  def reference_dihedral_deviations(self):
    assert 0, "Not working"
    if(self.n_reference_dihedral_proxies is not None):
      reference_dihedral_deltas = geometry_restraints.reference_dihedral_deltas(
        sites_cart = self.sites_cart,
        proxies    = self.reference_dihedral_proxies)
      d_sq  = reference_dihedral_deltas * reference_dihedral_deltas
      d_ave = math.sqrt(flex.mean_default(d_sq, 0))
      d_max = math.sqrt(flex.max_default(d_sq, 0))
      d_min = math.sqrt(flex.min_default(d_sq, 0))
      return d_min, d_max, d_ave

  # def ncs_dihedral_deviations(self):
      # It is probably wrong anyway - origin_id!
  #   if(self.n_ncs_dihedral_proxies is not None):
  #     ncs_dihedral_deltas = geometry_restraints.ncs_dihedral_deltas(
  #       sites_cart = self.sites_cart,
  #       proxies    = self.ncs_dihedral_manager.ncs_dihedral_proxies)
  #     d_sq  = ncs_dihedral_deltas * ncs_dihedral_deltas
  #     d_ave = math.sqrt(flex.mean_default(d_sq, 0))
  #     d_max = math.sqrt(flex.max_default(d_sq, 0))
  #     d_min = math.sqrt(flex.min_default(d_sq, 0))
  #     return d_min, d_max, d_ave

  def chirality_deviations(self):
    if(self.n_chirality_proxies is not None):
      chirality_deltas = geometry_restraints.chirality_deltas(
        sites_cart = self.sites_cart,
        proxies    = self.chirality_proxies)
      c_sq  = chirality_deltas * chirality_deltas
      c_ave = math.sqrt(flex.mean_default(c_sq, 0))
      c_max = math.sqrt(flex.max_default(c_sq, 0))
      c_min = math.sqrt(flex.min_default(c_sq, 0))
      return c_min, c_max, c_ave

  def planarity_deviations(self):
    # XXX Need update, does not respect origin_id
    # assert 0, "Not counting for origin_id"
    if(self.n_planarity_proxies is not None):
      planarity_deltas = geometry_restraints.planarity_deltas_rms(
        sites_cart = self.sites_cart,
        proxies    = self.planarity_proxies)
      p_sq  = planarity_deltas * planarity_deltas
      p_ave = math.sqrt(flex.mean_default(p_sq, 0))
      p_max = math.sqrt(flex.max_default(p_sq, 0))
      p_min = math.sqrt(flex.min_default(p_sq, 0))
      return p_min, p_max, p_ave

  def parallelity_deviations(self):
    if self.n_parallelity_proxies is not None:
      parallelity_deltas = geometry_restraints.parallelity_deltas(
        sites_cart = self.sites_cart,
        proxies    = self.parallelity_proxies)
      p_sq  = parallelity_deltas * parallelity_deltas
      p_ave = math.sqrt(flex.mean_default(p_sq, 0))
      p_max = math.sqrt(flex.max_default(p_sq, 0))
      p_min = math.sqrt(flex.min_default(p_sq, 0))
      return p_min, p_max, p_ave

  def show(self, f=None, prefix=""):
    if (f is None): f = sys.stdout
    print >> f, prefix+"target: %.6g" % self.target

    for p_name in ["bond", "nonbonded", "angle", "dihedral",
        "reference_dihedral", "reference_coordinate", "ncs_dihedral",
        "den", "chirality", "planarity", "parallelity", "ramachandran",
        "bond_similarity"]:
      if getattr(self, "n_%s_proxies" % p_name) is not None:
        print >> f, "%s  %s_residual_sum (n=%d): %.6g" % (
            prefix,
            p_name,
            getattr(self, "n_%s_proxies" % p_name),
            getattr(self, "%s_residual_sum" % p_name))
    for extension_obj in self.extension_objects:
      extension_obj.energies_show(energies_obj=self, f=f, prefix=prefix)
    if (self.gradients is not None):
      print >> f, prefix+"  norm of gradients: %.6g" % self.gradients.norm()
