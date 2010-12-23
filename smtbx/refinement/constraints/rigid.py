import smtbx.refinement.constraints as _
from smtbx.refinement.constraints import InvalidConstraint

class rigid_pivoted_rotable_group(object):
  """ a set of atoms (rigid body) rides on a pivot atom and rotates around
  the pivot-pivot_neighbour bond, the original geometry is not altered
  """

  def __init__(self, pivot, pivot_neighbour, ind_sequence):
    if len(ind_sequence) == 0:
      raise InvalidConstraint("at least one atom is expected")
    self.pivot = pivot
    self.pivot_neighbour = pivot_neighbour
    self.indices = ind_sequence

  def __eq__(self, other):
    if (pivot != other.pivot or pivot_neighbour != other.pivot_neghbour\
    or self.indices != other.indices):
      return False
    return True

  def add_to(self, reparametrisation):
    scatterers = reparametrisation.structure.scatterers()
    pivot_sp = reparametrisation.add_new_site_parameter(self.pivot)
    pivot_n_sp = reparametrisation.add_new_site_parameter(self.pivot_neighbour)
    azimuth = reparametrisation.add(_.independent_scalar_parameter,
                                    value=0, variable=True)
    scatterers = tuple([scatterers[i] for i in self.indices])
    param = reparametrisation.add(
      _.rigid_pivoted_rotable_group,
      pivot = pivot_sp,
      pivot_neighbour = pivot_n_sp,
      azimuth = azimuth,
      atoms = scatterers)
    for i, j in enumerate(self.indices):
      reparametrisation.add_new_site_proxy_parameter(param, i, j)
      reparametrisation.asu_scatterer_parameters[j].site = param

