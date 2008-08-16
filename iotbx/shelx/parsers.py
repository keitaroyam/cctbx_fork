""" Lexing of ins/res files """

from __future__ import generators

from cctbx import uctbx
from cctbx import sgtbx
from cctbx import xray
from cctbx import eltbx
from cctbx import adptbx

import scitbx.math

from libtbx import forward_compatibility
from libtbx import adopt_init_args

from iotbx.shelx import errors, util


class parser(object):

  def __init__(self, command_stream, builder=None):
    self.command_stream = command_stream
    self.builder = builder

  def parse(self):
    for command in self.filtered_commands(): pass


class crystal_symmetry_parser(parser):
  """ A parser pulling out the crystal symmetry info from a command stream """

  def filtered_commands(self):
    """ Yields those command in self.command_stream
        that this parser is not concerned with. On the contrary,
        CELL, LATT, SYMM are swallowed.
        The resulting info is available in self.crystal_symmetry
    """
    unit_cell = None
    space_group = sgtbx.space_group()
    for command in self.command_stream:
      cmd, args = command[0], command[-1]
      if cmd == 'CELL':
        assert unit_cell is None
        unit_cell = uctbx.unit_cell(args[1:])
      elif cmd == 'LATT':
        assert len(args) == 1
        n = int(args[0])
        if n > 0:
          space_group.expand_inv(sgtbx.tr_vec((0,0,0)))
        z = "*PIRFABC"[abs(n)]
        space_group.expand_conventional_centring_type(z)
      elif cmd == 'SYMM':
        assert len(args) == 1
        s = sgtbx.rt_mx(args[0])
        space_group.expand_smx(s)
      else:
        if cmd == 'SFAC':
          assert unit_cell is not None
          self.builder.make_crystal_symmetry(unit_cell=unit_cell,
                                             space_group=space_group)
        yield command

  def parse(self):
    for command in self.filtered_commands():
      if command[0] == 'SFAC': break


class atom_parser(parser, util.behaviour_of_variable):
  """ A parser pulling out the scatterer info from a command stream """

  shelx_commands = dict([ (cmd, 1) for cmd in [
    'ACTA', 'AFIX', 'ANIS', 'BASF', 'BIND', 'BLOC', 'BOND', 'BUMP', 'CELL',
    'CGLS', 'CHIV', 'CONF', 'CONN', 'DAMP', 'DANG', 'DEFS', 'DELU', 'DFIX',
    'DISP', 'EADP', 'END ', 'EQIV', 'EXTI', 'EXYZ', 'FEND', 'FLAT', 'FMAP',
    'FRAG', 'FREE', 'FVAR', 'GRID', 'HFIX', 'HKLF', 'HOPE', 'HTAB', 'ISOR',
    'L.S.', 'LATT', 'LAUE', 'LIST', 'MERG', 'MOLE', 'MORE', 'MOVE', 'MPLA',
    'MUST', 'NCSY', 'OMIT', 'PART', 'PLAN', 'REM ', 'RESI', 'RTAB', 'SADI',
    'SAME', 'SFAC', 'SHEL', 'SIMU', 'SIZE', 'SPEC', 'STIR', 'SUMP', 'SWAT',
    'SYMM', 'TEMP', 'TIME', 'TITL', 'TWIN', 'UNIT', 'WGHT', 'WPDB', 'ZERR'
  ]])

  def __init__(self, command_stream, builder):
    self.command_stream = command_stream
    self.builder = builder

  def filtered_commands(self):
    self.label_for_sfac = None
    scatterer_index = 0
    for command in self.command_stream:
      cmd, args = command[0], command[-1]
      if cmd == 'SFAC':
        self.builder.make_structure()
        self.label_for_sfac = ('*',) + args # (a) working around
                                            #     ShelXL 1-based indexing
      elif cmd == 'FVAR':
        self.overall_scale = args[0]
        self.free_variable = args # (b) ShelXL indexes into the whole array
      elif cmd == 'PART' and len(args) == 2:
        raise NotImplementedError
      elif len(cmd) < 4 or cmd not in self.shelx_commands:
        if self.label_for_sfac is None:
          raise errors.missing_sfac_error
        scatterer, behaviour_of_variable = self.lex_scatterer(
          cmd, args, scatterer_index)
        self.builder.add_scatterer(scatterer, behaviour_of_variable)
        scatterer_index += 1
      else:
        yield command

  def lex_scatterer(self, name, args, scatterer_index):
    try:
      n = int(args[0])
      n_vars = len(args) - 1
      if n_vars == 5:
        values, behaviours = self.decode_variables(
          args[1:],
          u_iso_idx=n_vars-1)
        u = values[-1]
        isotropic = True
      elif n_vars == 10:
        unit_cell = self.builder.crystal_symmetry.unit_cell()
        values, behaviours = self.decode_variables(
          args[1:-3] + (args[-1], args[-2], args[-3]),
          u_iso_idx=None)
        u = adptbx.u_cif_as_u_star(unit_cell, values[-6:])
        isotropic = False
      else:
        raise errors.illegal_scatterer_error
      site = values[0:3]
      occ = values[3]
      scattering_type = eltbx.xray_scattering.get_standard_label(
        self.label_for_sfac[n], # works thank to (a)
        exact=True)
      scatterer = xray.scatterer(
        label           = name,
        site            = site,
        occupancy       = occ,
        u               = u,
        scattering_type = scattering_type)
      if not isotropic or behaviours[-1] != self.p_times_previous_u_eq:
        self.scatterer_to_bind_u_eq_to = (scatterer, scatterer_index)
      return scatterer, behaviours
    except errors.illegal_scatterer_error, e:
      e.args = (name,) + e.args
      raise

  def decode_variables(self, coded_variables, u_iso_idx=None):
    values = []
    behaviours = []
    for i,coded_variable in enumerate(coded_variables):
      try:
        m,p = scitbx.math.divmod(coded_variable, 10)
      except ArgumentError:
        raise errors.illegal_scatterer_error
      if m <= -2:
        # p*(fv_{-m} - 1)
        m = -m-1 # indexing thanks to (b) above
        values.append( p*(self.free_variable[m] - 1) )
        behaviours.append((self.p_times_fv_minus_1, p, m))
      elif m == 0:
        if i == u_iso_idx and p < -0.5:
          # p * (U_eq of the previous atom not constrained in this way)
          scatt, scatt_idx = self.scatterer_to_bind_u_eq_to
          u_iso = scatt.u_eq(self.builder.crystal_symmetry.unit_cell())
          values.append( -p*u_iso )
          behaviours.append((self.p_times_previous_u_eq, scatt_idx))
        else:
          # p (free to refine)
          values.append(p)
          behaviours.append(self.free)
      elif m == 1:
        # p (fixed variable)
        values.append(p)
        behaviours.append(self.fixed)
      elif m >= 2:
        # p*fv_m
        m = m-1 # indexing thanks to (b) above
        values.append(p*self.free_variable[m])
        behaviours.append((self.p_times_fv, p, m))
      else:
        # m == -1
        # undocumented, rather pathological case
        # but I carefully checked that ShelXL does indeed behave so!
        values.append(0)
        behaviours.append(self.fixed)
    return values, behaviours
