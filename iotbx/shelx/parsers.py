""" Lexing of ins/res files """

from __future__ import division

import itertools
from boost import rational

from cctbx import uctbx
from cctbx import sgtbx
from cctbx import xray
from cctbx import eltbx
from cctbx import adptbx

import scitbx.math

from iotbx.shelx.errors import error as shelx_error
import iotbx.constrained_parameters

class parser(object):

  def __init__(self, command_stream, builder=None):
    self.command_stream = command_stream
    self.builder = builder

  def parse(self):
    for command, line in self.filtered_commands(): pass


class instruction_parser(parser):
  """ A parser for extracting from the command stream miscellaneous
      shelxl commands that do not concern other parsers.

      If this parser is constructed with a real builder, the wt and m
      arguments to HKLF are not supported.

      This parser is unusual in that it does not rely entirely on its
      builder: it builds a dictionary containing the parsed information.
  """

  def __init__(self, command_stream, builder=None):
    from libtbx import object_oriented_patterns as oop
    if builder is None: builder = oop.null()
    parser.__init__(self, command_stream, builder)
    self.instructions = {}

  def filtered_commands(self):
    from scitbx.math import continued_fraction
    temperature = 20
    for command, line in self.command_stream:
      cmd, args = command[0], command[-1]
      n_args = len(args)
      if cmd == 'OMIT':
        if n_args == 3 and isinstance(args[0], float):
          self.instructions.setdefault('omit_hkl', [])
          self.instructions['omit_hkl'].append([int(i) for i in args])
        elif n_args == 2 and isinstance(args[0], float):
          self.instructions['omit'] = {
            's': args[0],
            'two_theta': args[1]}
        else:
          yield command, line
      elif cmd == 'SHEL':
        if args:
          shel = {'lowres': args[0]}
          if n_args > 1:
            shel['highres'] = args[1]
      elif cmd == 'MERG':
        if args:
          self.instructions['merg'] = args[0]
      elif cmd == 'TEMP':
        if len(args) > 1:
          raise shelx_error("TEMP takes at most 1 argument")
        if args: temperature = args[0]
        self.instructions['temp'] = temperature
        self.builder.temperature_in_celsius = temperature
      elif cmd == 'WGHT':
        if n_args > 6:
          raise shelx_error("Too many argument for %s" % cmd, line)
        default_weighting_scheme = { 'a': 0.1,
                                     'b': 0,
                                     'c': 0,
                                     'd': 0,
                                     'e': 0,
                                     'f': 1/3 }
        weighting_scheme = dict([
          (key, (arg is not None and arg) or default_weighting_scheme[key])
          for key, arg in itertools.izip_longest('abcdef', args) ])
        self.instructions['wght'] = weighting_scheme
        self.builder.make_shelx_weighting_scheme(**weighting_scheme)
      elif cmd == 'HKLF':
        # only ONE HKLF instruction allowed
        assert 'hklf' not in self.instructions
        hklf = {'s': 1, 'matrix': sgtbx.rot_mx()}
        hklf['n'] = args[0]
        if n_args > 1:
          hklf['s'] = args[1]
          if n_args > 2:
            assert n_args > 10
            mx = [ continued_fraction.from_real(e, eps=1e-3).as_rational()
                   for e in args[2:11] ]
            den = reduce(rational.lcm, [ r.denominator() for r in mx ])
            nums = [ r.numerator()*(den//r.denominator()) for r in mx ]
            hklf['matrix'] = sgtbx.rot_mx(nums, den)
            if n_args > 11:
              hklf['wt'] = args[11]
              if n_args == 13:
                hklf['m'] = args[12]
        self.instructions['hklf'] = hklf
        assert not self.builder or ('wt' not in hklf and 'm' not in hklf)
        self.builder.create_shelx_reflection_data_source(
          format=hklf['n'],
          indices_transform=hklf['matrix'],
          data_scale=hklf['s'])
        if 'basf' in self.instructions and hklf['n'] == 5:
          self.builder.make_non_merohedral_twinning_with_transformed_hkl(
            fractions=self.instructions['basf'])
      elif cmd == 'TWIN':
        # only ONE twin instruction allowed
        assert 'twin' not in self.instructions
        twin = {}
        if n_args > 0:
          assert n_args >= 9
          twin['matrix'] = sgtbx.rt_mx(
            sgtbx.rot_mx([int(i) for i in args[0:9]]))
          if n_args > 9:
            twin['n'] = args[9]
        self.instructions['twin'] = twin
        if 'basf' in self.instructions: self.issue_merohedral_twinning()
      elif cmd == 'BASF':
        self.instructions['basf'] = args
        if 'twin' in self.instructions: self.issue_merohedral_twinning()
      elif cmd == 'EXTI':
        if len(args) == 1:
          self.instructions['exti'] = args[0]
      else:
        yield command, line
    else:
      # All token have been read without errors or early bailout
      assert 'hklf' in self.instructions, "Missing HKLF instruction"

  def issue_merohedral_twinning(self):
    twin_law = self.instructions['twin'].get('matrix',
                                             sgtbx.rt_mx('-x,-y,-z'))
    n = self.instructions['twin'].get('n', 2)
    assert n - 1 == len(self.instructions['basf'])
    self.builder.make_merohedral_twinning(
      fractions=self.instructions['basf'],
      twin_law=twin_law)



class crystal_symmetry_parser(parser):
  """ A parser pulling out the crystal symmetry info from a command stream """

  def filtered_commands(self):
    """ Yields those command in self.command_stream
        that this parser is not concerned with. On the contrary,
        LATT, SYMM are swallowed (CELL is yielded because it carries
        the wavelength too).
    """
    unit_cell = None
    space_group = sgtbx.space_group()
    for command, line in self.command_stream:
      cmd, args = command[0], command[-1]
      if cmd == 'CELL':
        assert unit_cell is None
        unit_cell = uctbx.unit_cell(args[1:])
        yield command, line
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


class wavelength_parser(parser):
  """ A parser pulling out the wavelength info from a command stream """

  def filtered_commands(self):
    for command, line in self.command_stream:
      cmd, args = command[0], command[-1]
      if cmd == 'CELL':
        self.builder.wavelength_in_angstrom = args[0]
      yield command, line

def decode_variables(
      free_variable,
      coded_variables,
      u_iso_idx=None,
      line=None,
      strictly_shelxl=True,
      variable_decoder=None):
  cpar = iotbx.constrained_parameters
  values = []
  behaviours = []
  for i_cv, coded_variable in enumerate(coded_variables):
    def raise_parameter_error():
      raise shelx_error(
        "scatterer parameter #%d '%s'", line, i_cv+1, coded_variable)
    try:
      m,p = scitbx.math.divmod(coded_variable, 10)
    except ArgumentError:
      raise_parameter_error()
    if m <= -2:
      # p*(fv_{-m} - 1)
      m = -m-1 # indexing thanks to (b) above
      values.append( p*(free_variable[m] - 1) )
      behaviours.append(
        (cpar.constant_times_independent_scalar_parameter_minus_1, p, m))
    elif m == 0:
      if u_iso_idx is not None and i_cv == u_iso_idx and p < -0.5:
        assert variable_decoder is not None
        # p * (U_eq of the previous atom not constrained in this way)
        scatt, scatt_idx = variable_decoder.scatterer_to_bind_u_eq_to
        u_iso = scatt.u_iso_or_equiv(
          variable_decoder.builder.crystal_symmetry.unit_cell())
        values.append( -p*u_iso )
        behaviours.append((cpar.constant_times_u_eq, -p, scatt_idx))
      else:
        # p (free to refine)
        values.append(p)
        behaviours.append(cpar.independent_parameter)
    elif m == 1:
      # p (fixed variable)
      values.append(p)
      behaviours.append(cpar.constant_parameter)
    elif m >= 2:
      # p*fv_m
      m = m-1 # indexing thanks to (b) above
      values.append(p*free_variable[m])
      behaviours.append(
        (cpar.constant_times_independent_scalar_parameter, p, m))
    else:
      assert m == -1
      if (not strictly_shelxl):
        raise_parameter_error()
      # undocumented, rather pathological case
      # but I carefully checked that ShelXL does indeed behave so!
      values.append(0)
      behaviours.append(cpar.constant_parameter)
  return values, behaviours

class variable_decoder(object):

  def decode_variables(self, coded_variables, u_iso_idx=None):
    return decode_variables(
      free_variable=self.free_variable,
      coded_variables=coded_variables,
      u_iso_idx=u_iso_idx,
      line=self.line,
      strictly_shelxl=self.strictly_shelxl,
      variable_decoder=self)

  def decode_one_variable(self, coded_variable, u_iso_idx=None):
    values, behaviours = self.decode_variables((coded_variable,), u_iso_idx)
    return values[0], behaviours[0]

class atom_parser(parser, variable_decoder):
  """ A parser pulling out the scatterer info from a command stream """

  overall_scale=None
  scatterer_label_to_index = {}

  def __init__(self, command_stream, builder=None, strictly_shelxl=True):
    parser.__init__(self, command_stream, builder)
    self.free_variable = None
    self.strictly_shelxl = strictly_shelxl

  def filtered_commands(self):
    self.label_for_sfac = None
    scatterer_index = 0
    conformer_index = 0
    sym_excl_index = 0
    part_sof = None
    for command, line in self.command_stream:
      self.line = line
      cmd, args = command[0], command[-1]
      if cmd == 'SFAC':
        self.builder.make_structure()
        if len(args) == 15 and isinstance(args[1], float):
          raise NotImplementedError(
            '''SFAC label a1 b1 a2 b2 a3 b3 a4 b4 c f' f" mu r wt''')
        self.label_for_sfac = ('*',) + args # (a) working around
                                            #     ShelXL 1-based indexing
      elif cmd == 'FVAR':
        if self.overall_scale is None:
          self.overall_scale = args[0]
          self.free_variable = args # (b) ShelXL indexes into the whole array
        else:
          # ShelXL allows for more than one FVAR instruction
          self.free_variable = self.free_variable + args
      elif cmd == 'PART':
        part_sof = None
        conformer_index = 0
        sym_excl_index = 0
        part_number = 0
        if args:
          part_number = int(args[0])
        if len(args) == 2:
          part_sof = self.decode_one_variable(args[1])
        if part_number > 0: conformer_index = part_number
        elif part_number < 0: sym_excl_index = abs(part_number)
      elif cmd == '__ATOM__':
        if self.label_for_sfac is None:
          raise shelx_error("missing sfac", self.line)
        scatterer, behaviour_of_variable = self.lex_scatterer(
          args, scatterer_index)
        if (conformer_index or sym_excl_index) and part_sof:
          scatterer.occupancy, behaviour_of_variable[3] = part_sof
        self.builder.add_scatterer(scatterer, behaviour_of_variable,
                                   occupancy_includes_symmetry_factor=True,
                                   conformer_index=conformer_index,
                                   sym_excl_index=sym_excl_index)
        scatterer_index += 1
      elif cmd == '__Q_PEAK__':
        assert not self.strictly_shelxl,\
               "Q-peaks amidst atoms in strict ShelXL model"
        self.builder.add_electron_density_peak(site = args[2:5],
                                               height = args[-1])
      else:
        yield command, line

  def lex_scatterer(self, args, scatterer_index):
    cpar = iotbx.constrained_parameters
    name = args[0]
    self.scatterer_label_to_index.setdefault(name.lower(), scatterer_index)
    n = int(args[1])
    n_vars = len(args) - 2
    if n_vars == 5 or (not self.strictly_shelxl and n_vars == 6):
      values, behaviours = self.decode_variables(
        args[2:7],
        u_iso_idx=n_vars-1)
      u = values[4]
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
        or behaviours[-1][0] != cpar.constant_times_u_eq):
      self.scatterer_to_bind_u_eq_to = (scatterer, scatterer_index)
    return scatterer, behaviours


class afix_parser(parser):
  """ It must be before an atom parser """

  constraints = {
  # AFIX mn : some of them use a pivot whose position is given wrt
  #           the first constrained scatterer site
  # m:    type                                    , pivot position
    1:  ("tertiary_xh_site"                        , -1),
    2:  ("secondary_xh2_sites"                     , -1),
    3:  ("staggered_terminal_tetrahedral_xh3_sites", -1),
    4:  ("secondary_planar_xh_site"                , -1),
    8:  ("staggered_terminal_tetrahedral_xh_site"  , -1),
    9:  ("terminal_planar_xh2_sites"               , -1),
    13: ("terminal_tetrahedral_xh3_sites"          , -1),
    14: ("terminal_tetrahedral_xh_site"            , -1),
    15: ("polyhedral_bh_site"                      , -1),
    16: ("terminal_linear_ch_site"                 , -1),
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
          self.builder.end_geometrical_constraint()
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
        info = self.constraints.get(m)
        if info is not None:
          constraint_name, pivot_relative_pos = info
          constraint_type = self.builder.make_geometrical_constraint_type(
            constraint_name)
          self.builder.start_geometrical_constraint(
            type_=constraint_type,
            bond_length=d,
            rotating=n in (7, 8),
            stretching=n in (4, 8),
            pivot_relative_pos=pivot_relative_pos)
          n_expected_afixed = constraint_type.n_constrained_sites
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


class restraint_parser(atom_parser):
  """ It must be after an atom parser """

  restraint_types = {
    'DFIX':'bond',
    'DANG':'bond',
    'FLAT':'planarity',
    'CHIV':'chirality',
    'SADI':'bond_similarity',
    'SIMU':'adp_similarity',
    'DELU':'rigid_bond',
    'ISOR':'isotropic_adp',
  }

  def filtered_commands(self):
    self.cached_restraints = {}
    self.symmetry_operations = {}
    for command, line in self.command_stream:
      cmd, args = command[0], command[-1]
      if cmd in self.restraint_types:
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
          restraint_type = self.restraint_types.get(cmd)
          if cmd in ('DFIX','DANG'):
            div, mod = divmod(len(args), 2)
            distance_ideal = float(args[0])
            if mod == 0:
              sigma = float(args[1])
              atoms = args[2:]
            else:
              if cmd == 'DFIX': sigma = 0.02
              else: sigma = 0.04
              atoms = args[1:]
            assert len(atoms) > 1
            weight = 1/(sigma**2)
            for i in range(div-(1-mod)):
              atom_pair = atoms[i*2:(i+1)*2]
              i_seqs = [self.scatterer_label_to_index[
                atom[1].lower()] for atom in atom_pair]
              sym_ops = [
                self.symmetry_operations.get(atom[2]) for atom in atom_pair]
              self.builder.process_restraint(restraint_type,
                                             distance_ideal=distance_ideal,
                                             weight=weight,
                                             i_seqs=i_seqs,
                                             sym_ops=sym_ops)
          if cmd == 'SADI':
            assert len(args) > 3
            div, mod = divmod(len(args), 2)
            value = args[0]
            if mod == 1:
              sigma = args[0]
              atom_pairs = args[1:]
            else:
              sigma = 0.02
              atom_pairs = args
            i_seqs = []
            sym_ops = []
            for i in range(div):
              atom_pair = atom_pairs[i*2:(i+1)*2]
              i_seqs.append([self.scatterer_label_to_index[
                atom[1].lower()] for atom in atom_pair])
              sym_ops.append(
                [self.symmetry_operations.get(atom[2]) for atom in atom_pair])
            weights = [1/(sigma**2)]*len(i_seqs)
            self.builder.process_restraint(restraint_type,
                                           weights=weights,
                                           i_seqs=i_seqs,
                                           sym_ops=sym_ops)
          elif cmd == 'FLAT':
            try:
              sigma = float(args[0])
              atoms = args[1:]
            except TypeError:
              sigma = 0.1
              atoms = args
            assert len(atoms) > 3
            i_seqs = [self.scatterer_label_to_index[i[1].lower()] for i in atoms]
            sym_ops = [self.symmetry_operations.get(i) for i in atoms]
            weights = [1/(sigma**2)]*len(i_seqs)
            self.builder.process_restraint(restraint_type,
                                           weights=weights,
                                           i_seqs=i_seqs,
                                           sym_ops=sym_ops)
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
              i_seqs = [
                self.scatterer_label_to_index[atom[1].lower()] for atom in atoms]
            else:
              i_seqs = None
            if s1 is None:
              if cmd == 'SIMU': s1 = 0.04
              elif cmd == 'DELU': s1 = 0.01
              else: s1 = 0.1
            if cmd == 'DELU':
              self.builder.process_restraint(restraint_type,
                                             sigma_12=s1,
                                             sigma_13=s2,
                                             i_seqs=i_seqs)
            else:
              self.builder.process_restraint(restraint_type,
                                             sigma=s1,
                                             sigma_terminal=s2,
                                             i_seqs=i_seqs)
          else:
            pass
        except (TypeError, AssertionError):
          raise shelx_error("Invalid %s instruction" %cmd, line)
