""" Lexing of ins/res files """

from cctbx import uctbx
from cctbx import sgtbx
from cctbx import xray
from cctbx import eltbx
from cctbx import adptbx

from cctbx import geometry_restraints
from cctbx import adp_restraints

import scitbx.math

from libtbx import forward_compatibility
from libtbx import adopt_init_args
import libtbx.load_env

from iotbx.shelx import util
from iotbx.shelx.errors import error as shelx_error

if (not libtbx.env.has_module(name="smtbx")):
  smtbx = None
else:
  import smtbx
  import smtbx.refinement.constraints as smtbx_constraints


class parser(object):

  def __init__(self, command_stream, builder=None):
    self.command_stream = command_stream
    self.builder = builder

  def parse(self):
    for command, line in self.filtered_commands(): pass


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
    for command, line in self.command_stream:
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
        yield command, line

  def parse(self):
    for command, line in self.filtered_commands():
      if command[0] == 'SFAC': break


class variable_decoder(util.behaviour_of_variable):

  def decode_variables(self, coded_variables, u_iso_idx=None):
    values = []
    behaviours = []
    for i, coded_variable in enumerate(coded_variables):
      try:
        m,p = scitbx.math.divmod(coded_variable, 10)
      except ArgumentError:
        raise shelx_error("%i-th scatterer parameter '%s'",
                          self.line, i, coded_variable)
      if m <= -2:
        # p*(fv_{-m} - 1)
        m = -m-1 # indexing thanks to (b) above
        values.append( p*(self.free_variable[m] - 1) )
        behaviours.append((self.p_times_fv_minus_1, p, m))
      elif m == 0:
        if i == u_iso_idx and p < -0.5:
          # p * (U_eq of the previous atom not constrained in this way)
          scatt, scatt_idx = self.builder.scatterer_to_bind_u_eq_to
          u_iso = scatt.u_iso_or_equiv(
            self.builder.crystal_symmetry.unit_cell())
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

  def decode_one_variable(self, coded_variable, u_iso_idx=None):
    values, behaviours = self.decode_variables((coded_variable,), u_iso_idx)
    return values[0], behaviours[0]


class atom_parser(parser, variable_decoder):
  """ A parser pulling out the scatterer info from a command stream """

  scatterer_label_to_index = {}

  def filtered_commands(self):
    self.label_for_sfac = None
    scatterer_index = 0
    part_number = 0
    part_sof = None
    for command, line in self.command_stream:
      self.line = line
      cmd, args = command[0], command[-1]
      if cmd == 'SFAC':
        self.builder.make_structure()
        self.label_for_sfac = ('*',) + args # (a) working around
                                            #     ShelXL 1-based indexing
      elif cmd == 'FVAR':
        self.overall_scale = args[0]
        self.free_variable = args # (b) ShelXL indexes into the whole array
      elif cmd == 'PART':
        part_sof = None
        part_number = 0
        if args:
          part_number = args[0]
        if len(args) == 2:
          part_sof = self.decode_one_variable(args[1])
      elif cmd == '__ATOM__':
        if self.label_for_sfac is None:
          raise shelx_error("missing sfac", self.line)
        scatterer, behaviour_of_variable = self.lex_scatterer(
          args, scatterer_index)
        if part_number and part_sof:
          scatterer.occupancy, behaviour_of_variable[3] = part_sof
        self.builder.add_scatterer(scatterer, behaviour_of_variable)
        scatterer_index += 1
      else:
        yield command, line

  def lex_scatterer(self, args, scatterer_index):
    name = args[0]
    self.scatterer_label_to_index.setdefault(name, scatterer_index)
    n = int(args[1])
    n_vars = len(args) - 2
    if n_vars == 5:
      values, behaviours = self.decode_variables(
        args[2:],
        u_iso_idx=n_vars-1)
      u = values[-1]
      isotropic = True
    elif n_vars == 10:
      unit_cell = self.builder.crystal_symmetry.unit_cell()
      values, behaviours = self.decode_variables(
        args[2:-3] + (args[-1], args[-2], args[-3]),
        u_iso_idx=None)
      u = adptbx.u_cif_as_u_star(unit_cell, values[-6:])
      isotropic = False
    else:
      raise shelx_error("wrong number of parameters for scatterer",
                        self.line)
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
    if (not isotropic
        or not isinstance(behaviours[-1], tuple)
        or behaviours[-1][0] != self.p_times_previous_u_eq):
      self.builder.scatterer_to_bind_u_eq_to = (scatterer, scatterer_index)
    return scatterer, behaviours


if smtbx is not None:

  class afix_parser(parser):
    """ It must be before an atom parser """

    constraint = {
      1:  (smtbx_constraints.tertiary_CH, 1),
      2:  (smtbx_constraints.secondary_CH2, 2),
      3:  (smtbx_constraints.staggered_terminal_tetrahedral_XHn, 3),
      4:  (smtbx_constraints.aromatic_CH_or_amide_NH, 1),
      8:  (smtbx_constraints.staggered_terminal_tetrahedral_XHn, 1),
      9:  (smtbx_constraints.terminal_trihedral_XH2, 2),
      13: (smtbx_constraints.terminal_tetrahedral_XHn, 3),
      14: (smtbx_constraints.terminal_tetrahedral_XHn, 1),
      15: (smtbx_constraints.polyhedral_BH, 1),
      16: (smtbx_constraints.acetylenic_CH, 1),
      }

    def filtered_commands(self):
      active_afix = False
      for command, line in self.command_stream:
        cmd, args = command[0], command[-1]
        if cmd in ('AFIX', 'HKLF'):
          if cmd == 'AFIX' and not args:
            raise shelx_error("too few arguments", line)
          if active_afix:
            if n_afixed != n_expected_afixed:
              raise shelx_error("wrong number of afixed atoms", line)
            self.builder.end_afix()
            active_afix = False
            n_afixed = 0
          if cmd == 'HKLF':
            yield command, line
            continue
          mn = args[0]
          if mn == 0: continue
          m,n = divmod(mn, 10)
          d, sof, u = (None,)*3
          params = args[1:]
          if not params: pass
          elif len(params) == 1: d = params[0]
          elif len(params) == 3: d, sof = params[0:]
          elif len(params) == 4: d, sof, u = params[0:]
          else: raise shelx_error("too many arguments", line)
          info = self.constraint.get(m)
          if info is not None:
            constraint_type, n_expected_afixed = info
            kwds = {}
            if d is not None: kwds['bond_length'] = d
            if (n in (7,8)
                and not constraint_type.__name__.startswith('staggered')):
              kwds['rotating'] = True
            self.builder.start_afix(constraint_type, kwds)
            active_afix = True
            n_afixed = 0
        elif cmd == '__ATOM__':
          if active_afix:
            if sof is not None: args[4] = sof
            if u is not None and len(args) == 6: args[-1] = u
            n_afixed += 1
          yield command, line
        else:
          yield command, line
      self.builder.finish()

  class restraint_parser(atom_parser):
    """ It must be after an atom parser """

    shelx_restraints = {
      'DFIX': {'d': None, 's': 0.02, 'i_seqs': None, 'sym ops': None},
      'DANG': {'d': None, 's': 0.04, 'i_seqs': None, 'sym ops': None},
      'FLAT': {'s': 0.1, 'atoms': None, 'sym ops': None},
      'CHIV': {'V': 0, 's': 0.1, 'atoms': None, 'sym ops': None},
      'SADI': {'s': 0.02, 'i_seqs': None, 'sym ops': None},
      'SIMU': {'sigma': 0.04, 'sigma_terminal': None, 'i_seqs': None},
      'DELU': {'sigma_12': 0.01, 'sigma_13': None, 'i_seqs': None},
      'ISOR': {'sigma': 0.1, 'sigma_terminal': None, 'i_seqs': None},
    }

    def filtered_commands(self):
      self.cached_restraints = {}
      self.symmetry_operations = {}
      for command, line in self.command_stream:
        cmd, args = command[0], command[-1]
        if cmd in self.shelx_restraints.keys():
          self.cache_restraint(cmd, line, args)
        elif cmd == 'EQIV':
          self.symmetry_operations.setdefault(args[0], args[1])
        else:
          yield command, line
      self.parse_restraints()

    def cache_restraint(self, cmd, line, args):
      if cmd not in self.cached_restraints.keys():
        self.cached_restraints.setdefault(cmd, {})
      self.cached_restraints[cmd].setdefault(line, args)

    def parse_restraints(self):
      for cmd, restraints in self.cached_restraints.items():
        for line, args in restraints.iteritems():
          try:
            kwds = self.shelx_restraints[cmd].copy()
            if cmd in ('DFIX','DANG'):
              div, mod = divmod(len(args), 2)
              kwds['d'] = float(args[0])
              if mod == 0:
                kwds['s'] = float(args[1])
                atoms = args[2:]
              else:
                atoms = args[1:]
              assert len(atoms) > 1
              for i in range(div-(1-mod)):
                atom_pair = atoms[i*2:(i+1)*2]
                kwds['i_seqs'] = [self.scatterer_label_to_index[atom[1]] for atom in atom_pair]
                kwds['sym ops'] = [self.symmetry_operations.get(atom[2]) for atom in atom_pair]
              self.builder.process_restraint(cmd, kwds)
            if cmd == 'SADI':
              assert len(args) > 3
              div, mod = divmod(len(args), 2)
              value = args[0]
              if mod == 1:
                kwds['s'] = args[0]
                atom_pairs = args[1:]
              else:
                atom_pairs = args
              i_seqs = []
              sym_ops = []
              weights = []
              for i in range(div):
                atom_pair = atom_pairs[i*2:(i+1)*2]
                i_seqs.append([self.scatterer_label_to_index[atom[1]] for atom in atom_pair])
                sym_ops.append([self.symmetry_operations.get(atom[2]) for atom in atom_pair])
              kwds['i_seqs'] = i_seqs
              kwds['sym ops'] = sym_ops
              self.builder.process_restraint(cmd, kwds)
            elif cmd == 'FLAT':
              try:
                kwds['s'] = float(args[0])
                atoms = args[1:]
              except TypeError:
                atoms = args
              assert len(atoms) > 3
              kwds['i_seqs'] = [self.scatterer_label_to_index[i[1]] for i in atoms]
              self.builder.process_restraint(cmd, kwds)
            elif cmd == 'CHIV':
              pass
            elif cmd in ('DELU', 'ISOR', 'SIMU'):
              atoms = None
              s1 = s2 = dmax = None
              if len(args) > 0:
                try:
                  s1 = float(args[0])
                except TypeError:
                  atoms = args
                if not atoms and len(args) > 1:
                  try:
                    s2 = float(args[1])
                  except TypeError:
                    atoms = args[1:]
                  if not atoms and len(args) > 2:
                    if cmd != 'SIMU':
                      atoms = args[2:]
                    else:
                      try:
                        dmax = float(args[2])
                      except TypeError:
                        if not atoms:
                          atoms = args[2:]
                      if not atoms and len(args) > 3:
                        atoms = args[3:]
              if atoms:
                kwds['i_seqs'] = [self.scatterer_label_to_index[atom[1]] for atom in atoms]
              if s1 is not None:
                if cmd == 'DELU':
                  kwds['sigma_12'] = s1
                  kwds['sigma_13'] = s2
                else:
                  kwds['sigma'] = s1
                  kwds['sigma_terminal'] = s2
              self.builder.process_restraint(cmd, kwds)
            else:
              pass
          except (TypeError, AssertionError):
            raise shelx_error("Invalid %s instruction" %cmd, line)
