""" All X-H bond lengths are in Angstrom and their values are taken from
ShelXL documentation (p. 4-3) """

import iotbx.constraints.geometrical as _input
import smtbx.refinement.constraints as _
from scitbx.matrix import col

class geometrical_hydrogens_mixin(object):

  need_pivot_neighbour_substituent = False

  def add_to(self, reparametrisation):
    i_pivot = self.pivot
    scatterers = reparametrisation.structure.scatterers()
    pivot_site = scatterers[i_pivot].site
    pivot_site_param = reparametrisation.add_new_site_parameter(i_pivot)
    pivot_neighbour_sites = ()
    pivot_neighbour_site_params = ()
    pivot_neighbour_substituent_site_param = None
    for j, ops in reparametrisation.pair_sym_table[i_pivot].items():
      if j in self.constrained_site_indices: continue
      for op in ops:
        s = reparametrisation.add_new_site_parameter(j, op)
        pivot_neighbour_site_params += (s,)
        pivot_neighbour_sites += (op*scatterers[j].site,)
        if (self.need_pivot_neighbour_substituent
            and pivot_neighbour_substituent_site_param is None):
          for k, ops_k in reparametrisation.pair_sym_table[j].items():
            if k != i_pivot:
              pivot_neighbour_substituent_site_param = \
                reparametrisation.add_new_site_parameter(k, ops_k[0])
              break

    bond_length = reparametrisation.add(
      _.independent_scalar_parameter,
      value=self.ideal_bond_length(scatterers[i_pivot].scattering_type,
                                   reparametrisation.temperature),
      variable=self.stretching)

    hydrogens = tuple(
      [ scatterers[i_sc] for i_sc in self.constrained_site_indices ])

    param = self.add_hydrogen_to(
      reparametrisation=reparametrisation,
      bond_length=bond_length,
      pivot_site=pivot_site,
      pivot_neighbour_sites=pivot_neighbour_sites,
      pivot_site_param=pivot_site_param,
      pivot_neighbour_site_params=pivot_neighbour_site_params,
      pivot_neighbour_substituent_site_param=
        pivot_neighbour_substituent_site_param,
      hydrogens=hydrogens)
    for i_sc in self.constrained_site_indices:
      reparametrisation.asu_scatterer_parameters[i_sc].site = param

  def ideal_bond_length(self, pivot_element, temperature):
    d = self.room_temperature_bond_length[pivot_element]
    if temperature is not None:
      if   temperature < -20: d += 0.1
      elif temperature < -70: d += 0.2
    return d


class terminal_tetrahedral_xhn_site_mixin(geometrical_hydrogens_mixin):

  def add_hydrogen_to(self, reparametrisation, bond_length,
                      pivot_site      , pivot_neighbour_sites,
                      pivot_site_param, pivot_neighbour_site_params,
                      hydrogens, **kwds):
    assert len(pivot_neighbour_site_params) == 1
    azimuth = reparametrisation.add(_.independent_scalar_parameter,
                                    value=0, variable=self.rotating)
    uc = reparametrisation.structure.unit_cell()
    return reparametrisation.add(
      getattr(_, self.__class__.__name__),
      pivot=pivot_site_param,
      pivot_neighbour=pivot_neighbour_site_params[0],
      length=bond_length,
      azimuth=azimuth,
      e_zero_azimuth=uc.orthogonalize(
        col(hydrogens[0].site) - col(pivot_site)),
      hydrogen=hydrogens)


class terminal_tetrahedral_xh_site(_input.terminal_tetrahedral_xh_site,
                                   terminal_tetrahedral_xhn_site_mixin):

  room_temperature_bond_length = { 'O' : 0.82,
                                   }

class terminal_tetrahedral_xh3_sites(_input.terminal_tetrahedral_xh3_sites,
                                     terminal_tetrahedral_xhn_site_mixin):

  room_temperature_bond_length = { 'C' : 0.96,
                                   'N' : 0.89,
                                   }


class tertiary_ch_site(_input.tertiary_ch_site,
                       geometrical_hydrogens_mixin):

  room_temperature_bond_length = { 'C' : 0.98,
                                   }

  def add_hydrogen_to(self, reparametrisation, bond_length,
                      pivot_site      , pivot_neighbour_sites,
                      pivot_site_param, pivot_neighbour_site_params,
                      hydrogens, **kwds):
    assert len(pivot_neighbour_site_params) == 3
    return reparametrisation.add(
      _.tertiary_ch_site,
      pivot=pivot_site_param,
      pivot_neighbour_0=pivot_neighbour_site_params[0],
      pivot_neighbour_1=pivot_neighbour_site_params[1],
      pivot_neighbour_2=pivot_neighbour_site_params[2],
      length=bond_length,
      hydrogen=hydrogens[0])


class secondary_ch2_sites(_input.secondary_ch2_sites,
                          geometrical_hydrogens_mixin):

  room_temperature_bond_length = { 'C' : 0.97,
                                   }

  def add_hydrogen_to(self, reparametrisation, bond_length,
                      pivot_site      , pivot_neighbour_sites,
                      pivot_site_param, pivot_neighbour_site_params,
                      hydrogens, **kwds):
    assert len(pivot_neighbour_site_params) == 2
    flapping = reparametrisation.add(_.angle_starting_tetrahedral,
                                     variable=True)
    return reparametrisation.add(
      _.secondary_ch2_sites,
      pivot=pivot_site_param,
      pivot_neighbour_0=pivot_neighbour_site_params[0],
      pivot_neighbour_1=pivot_neighbour_site_params[1],
      length=bond_length,
      h_c_h_angle=flapping,
      hydrogen_0=hydrogens[0],
      hydrogen_1=hydrogens[1])


class secondary_planar_xh_site(_input.secondary_planar_xh_site,
                               geometrical_hydrogens_mixin):

  room_temperature_bond_length = { 'C' : 0.93,
                                   'N' : 0.86,
                                   }

  def add_hydrogen_to(self, reparametrisation, bond_length,
                      pivot_site      , pivot_neighbour_sites,
                      pivot_site_param, pivot_neighbour_site_params,
                      hydrogens, **kwds):
    assert len(pivot_neighbour_site_params) == 2
    return reparametrisation.add(
      _.secondary_planar_xh_site,
      pivot=pivot_site_param,
      pivot_neighbour_0=pivot_neighbour_site_params[0],
      pivot_neighbour_1=pivot_neighbour_site_params[1],
      length=bond_length,
      hydrogen=hydrogens[0])


class terminal_planar_xh2_sites(_input.terminal_planar_xh2_sites,
                                geometrical_hydrogens_mixin):

  need_pivot_neighbour_substituent = True

  room_temperature_bond_length = \
    secondary_planar_xh_site.room_temperature_bond_length

  def add_hydrogen_to(self, reparametrisation, bond_length,
                      pivot_site      , pivot_neighbour_sites,
                      pivot_site_param, pivot_neighbour_site_params,
                      pivot_neighbour_substituent_site_param,
                      hydrogens, **kwds):
    assert len(pivot_neighbour_site_params) == 1
    return reparametrisation.add(
      _.terminal_planar_xh2_sites,
      pivot=pivot_site_param,
      pivot_neighbour=pivot_neighbour_site_params[0],
      pivot_neighbour_substituent=pivot_neighbour_substituent_site_param,
      length=bond_length,
      hydrogen_0=hydrogens[0],
      hydrogen_1=hydrogens[1])


class terminal_linear_ch_site(_input.terminal_linear_ch_site,
                              geometrical_hydrogens_mixin):

  room_temperature_bond_length = { 'C' : 0.93,
                                   }

  def add_hydrogen_to(self, reparametrisation, bond_length,
                      pivot_site      , pivot_neighbour_sites,
                      pivot_site_param, pivot_neighbour_site_params,
                      hydrogens, **kwds):
    assert len(pivot_neighbour_site_params) == 1
    return reparametrisation.add(
      _.terminal_linear_ch_site,
      pivot=pivot_site_param,
      pivot_neighbour=pivot_neighbour_site_params[0],
      length=bond_length,
      hydrogen=hydrogens[0])
