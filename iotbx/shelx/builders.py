from cctbx import crystal
from cctbx import xray
from cctbx import geometry_restraints
from cctbx import adp_restraints
from smtbx.refinement.restraints\
     import adp_restraints as smtbx_adp_restraints

from iotbx.shelx import util

class crystal_symmetry_builder(object):

  def make_crystal_symmetry(self, unit_cell, space_group):
    self.crystal_symmetry = crystal.symmetry(unit_cell=unit_cell,
                                             space_group=space_group)


class crystal_structure_builder(crystal_symmetry_builder,
                                util.behaviour_of_variable):

  def __init__(self,
               set_grad_flags=True,
               min_distance_sym_equiv=0.5):
    super(crystal_structure_builder, self).__init__()
    self.set_grad_flags = set_grad_flags
    self.min_distance_sym_equiv = min_distance_sym_equiv

  def make_structure(self):
    self.structure = xray.structure(
      special_position_settings=crystal.special_position_settings(
        crystal_symmetry=self.crystal_symmetry,
        min_distance_sym_equiv=self.min_distance_sym_equiv))

  def add_scatterer(self, scatterer, behaviour_of_variable):
    """ If the parameter set_grad_flags passed to the constructor was True,
        the scatterer.flags.grad_xxx() will be set to True
        if the corresponding variables have been found to be refined
        by the parser using this builder.
    """
    if self.set_grad_flags:
      f = scatterer.flags
      if behaviour_of_variable[0:3].count(self.fixed) != 3:
        f.set_grad_site(True)
      if behaviour_of_variable[3] != self.fixed:
        f.set_grad_occupancy(True)
      if f.use_u_iso():
        if behaviour_of_variable[4] != self.fixed:
          f.set_grad_u_iso(True)
      else:
        if behaviour_of_variable[-6:].count(self.fixed) != 3:
          f.set_grad_u_aniso(True)
    self.structure.add_scatterer(scatterer)


class afixed_crystal_structure_builder(crystal_structure_builder):

  def __init__(self, *args, **kwds):
    super(afixed_crystal_structure_builder, self).__init__(*args, **kwds)
    self.afixed = []
    self.afix = None

  def start_afix(self, constraint_type, kwds):
    self.afix = (constraint_type, kwds,
                 len(self.structure.scatterers()))

  def end_afix(self):
    last = len(self.structure.scatterers())
    constraint_type, kwds, first = self.afix
    kwds['constrained_scatterer_indices'] = tuple(xrange(first, last))
    self.afixed.append((constraint_type, kwds))

  def finish(self):
    pass


class restrained_crystal_structure_builder(afixed_crystal_structure_builder):

  def __init__(self, *args, **kwds):
    super(restrained_crystal_structure_builder, self).__init__(*args, **kwds)
    geom = geometry_restraints
    adp = adp_restraints
    self.proxies = {
      geom.bond_sym_proxy: [],
      geom.angle_proxy: geom.shared_angle_proxy(),
      geom.dihedral_proxy: geom.shared_dihedral_proxy(),
      geom.chirality_proxy: geom.shared_chirality_proxy(),
      geom.planarity_proxy: geom.shared_planarity_proxy(),
      geom.bond_similarity_proxy: geom.shared_bond_similarity_proxy(),
      adp.adp_similarity_proxy: adp.shared_adp_similarity_proxy(),
      adp.isotropic_adp_proxy: adp.shared_isotropic_adp_proxy(),
      adp.rigid_bond_proxy: adp.shared_rigid_bond_proxy(),
    }
    self.adp_proxy_builders = {
      adp.adp_similarity_proxy: smtbx_adp_restraints.adp_similarity_restraints,
      adp.rigid_bond_proxy: smtbx_adp_restraints.rigid_bond_restraints,
      adp.isotropic_adp_proxy: smtbx_adp_restraints.isotropic_adp_restraints
    }

  def add_restraint(self, proxy_type, kwds):
    if proxy_type in self.adp_proxy_builders:
      kwds['proxies'] = self.proxies[proxy_type]
      kwds['xray_structure'] = self.structure
      self.adp_proxy_builders[proxy_type](**kwds)
    else:
      proxy=proxy_type(**kwds)
      self.proxies[proxy_type].append(proxy)
