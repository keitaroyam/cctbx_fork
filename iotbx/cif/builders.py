from cctbx import adptbx, crystal, miller, sgtbx, uctbx, xray
from cctbx.array_family import flex
import iotbx.cif
from iotbx.cif import model
from libtbx.utils import Sorry
from libtbx.containers import OrderedDict, OrderedSet


class CifBuilderError(Sorry):
  __module__ = Exception.__module__


class cif_model_builder(object):

  def __init__(self, cif_object=None):
    self._model = cif_object
    if self._model is None:
      self._model = model.cif()
    self._current_block = None
    self._current_save = None

  def add_data_block(self, data_block_heading):
    self._current_block = model.block()
    if data_block_heading.lower() == 'global_':
      block_name = data_block_heading
    else:
      block_name = data_block_heading[data_block_heading.find('_')+1:]
    self._model[block_name] = self._current_block

  def add_loop(self, header, data):
    if self._current_save is not None:
      block = self._current_save
    else:
      block = self._current_block
    loop = model.loop()
    n_columns = len(header)
    assert len(data) % n_columns == 0, "Wrong number of data items for loop"
    if n_columns == 1:
      columns = [data]
    else:
      columns = iotbx.cif.ext.looped_data_as_columns(data, n_columns)
    for i in range(n_columns):
      loop[header[i]] = columns[i]
    block.add_loop(loop)

  def add_data_item(self, key, value):
    if self._current_save is not None:
      self._current_save[key] = value
    elif self._current_block is not None:
      self._current_block[key] = value
    else: # support for global_ blocks in non-strict mode
      pass

  def start_save_frame(self, save_frame_heading):
    assert self._current_save is None
    self._current_save = model.save()
    save_name = save_frame_heading[save_frame_heading.find('_')+1:]
    self._current_block[save_name] = self._current_save

  def end_save_frame(self):
    self._current_save = None

  def model(self):
    return self._model


class builder_base(object):

  __equivalents__ = {
    '_space_group_symop_operation_xyz': ('_symmetry_equiv_pos_as_xyz',
                                         '_space_group_symop.operation_xyz',
                                         '_symmetry_equiv.pos_as_xyz'),
    '_space_group_symop_id': ('_symmetry_equiv_pos_site_id',
                              '_space_group_symop.id',
                              '_symmetry_equiv.id'),
    '_space_group_name_Hall': ('_symmetry_space_group_name_Hall',
                               '_space_group.name_Hall',
                               '_symmetry.space_group_name_Hall'),
    '_space_group_name_H-M_alt': ('_symmetry_space_group_name_H-M',
                                  '_space_group.name_H-M_alt',
                                  '_symmetry.space_group_name_H-M'),
    '_space_group_IT_number': ('_symmetry_Int_Tables_number',
                                 '_symmetry.Int_Tables_number'
                                 '_space_group.IT_number'),
    '_cell_length_a': ('_cell.length_a',),
    '_cell_length_b': ('_cell.length_b',),
    '_cell_length_c': ('_cell.length_c',),
    '_cell_angle_alpha': ('_cell.angle_alpha',),
    '_cell_angle_beta': ('_cell.angle_beta',),
    '_cell_angle_gamma': ('_cell.angle_gamma',),
    '_cell_angle_gamma': ('_cell.angle_gamma',),
    '_cell_volume': ('_cell.volume',),
    '_refln_index_h': ('_refln.index_h',),
    '_refln_index_k': ('_refln.index_k',),
    '_refln_index_l': ('_refln.index_l',),
  }

  def get_cif_item(self, key, default=None):
    value = self.cif_block.get(key)
    if value is not None: return value
    for equiv in self.__equivalents__.get(key, []):
      value = self.cif_block.get(equiv)
      if value is not None: return value
    return default


class crystal_symmetry_builder(builder_base):

  def __init__(self, cif_block, strict=False):
    # The order of priority for determining space group is:
    #   sym_ops, hall symbol, H-M symbol, space group number
    self.cif_block = cif_block
    sym_ops = self.get_cif_item('_space_group_symop_operation_xyz')
    sym_op_ids = self.get_cif_item('_space_group_symop_id')
    space_group = None
    if sym_ops is not None:
      if isinstance(sym_ops, basestring):
        sym_ops = flex.std_string([sym_ops])
      if sym_op_ids is not None:
        if isinstance(sym_op_ids, basestring):
          sym_op_ids = flex.std_string([sym_op_ids])
        assert len(sym_op_ids) == len(sym_ops)
      self.sym_ops = {}
      space_group = sgtbx.space_group()
      if isinstance(sym_ops, basestring): sym_ops = [sym_ops]
      for i, op in enumerate(sym_ops):
        try:
          s = sgtbx.rt_mx(op)
        except RuntimeError, e:
          str_e = str(e)
          if "Parse error: " in str_e:
            raise CifBuilderError("Error interpreting symmetry operator: %s" %(
              str_e.split("Parse error: ")[-1]))
          else:
            raise
        if sym_op_ids is None:
          sym_op_id = i+1
        else:
          try:
            sym_op_id = int(sym_op_ids[i])
          except ValueError, e:
            raise CifBuilderError("Error interpreting symmetry operator id: %s" %(
              str(e)))
        self.sym_ops[sym_op_id] = s
        space_group.expand_smx(s)
    else:
      hall_symbol = self.get_cif_item('_space_group_name_Hall')
      hm_symbol = self.get_cif_item('_space_group_name_H-M_alt')
      sg_number = self.get_cif_item('_space_group_IT_number')
      if space_group is None and hall_symbol not in (None, '?'):
        try: space_group = sgtbx.space_group(hall_symbol)
        except Exception: pass
      if space_group is None and hm_symbol not in (None, '?'):
        try: space_group = sgtbx.space_group_info(symbol=hm_symbol).group()
        except Exception: pass
      if space_group is not None and sg_number not in (None, '?'):
        try: space_group = sgtbx.space_group_info(number=sg_number).group()
        except Exception: pass
      if (space_group is None and strict):
        raise CifBuilderError(
          "No symmetry instructions could be extracted from the cif block")
    items = [self.get_cif_item("_cell_length_"+s) for s in "abc"]
    for i, item in enumerate(items):
      if isinstance(item, flex.std_string):
        raise CifBuilderError(
          "Data item _cell_length_%s cannot be declared in a looped list"
          %("abc"[i]))
    for s in ["alpha", "beta", "gamma"]:
      item = self.get_cif_item("_cell_angle_"+s)
      if isinstance(item, flex.std_string):
        raise CifBuilderError(
          "Data item _cell_angle_%s cannot be declared in a looped list" %s)
      if (item == "?"):
        item = "90" # enumeration default for angles is 90 degrees
      items.append(item)
    ic = items.count(None)
    if (ic == 6):
      if (strict):
        raise CifBuilderError(
          "Unit cell parameters not found in the cif file")
      unit_cell = None
    elif (ic == 0):
      try:
        vals = [float_from_string(s) for s in items]
      except ValueError:
        raise CifBuilderError("Invalid unit cell parameters are given")
      try:
        unit_cell = uctbx.unit_cell(vals)
      except RuntimeError, e:
        if "cctbx Error: Unit cell" in str(e):
          raise CifBuilderError(e)
        else:
          raise
    elif (space_group is not None):
      unit_cell = uctbx.infer_unit_cell_from_symmetry(
        [float_from_string(s) for s in items if s is not None], space_group)
    else:
      raise CifBuilderError(
        "Not all unit cell parameters are given in the cif file")
    if (unit_cell is not None and space_group is not None
        and not space_group.is_compatible_unit_cell(unit_cell)):
      raise CifBuilderError(
        "Space group is incompatible with unit cell parameters")
    self.crystal_symmetry = crystal.symmetry(unit_cell=unit_cell,
                                             space_group=space_group)

class crystal_structure_builder(crystal_symmetry_builder):

  def __init__(self, cif_block):
    # XXX To do: interpret _atom_site_refinement_flags
    crystal_symmetry_builder.__init__(self, cif_block, strict=True)
    atom_sites_frac = [as_double_or_none_if_all_question_marks(
      _, column_name='_atom_site_fract_%s' %axis)
                       for _ in [cif_block.get('_atom_site_fract_%s' %axis)
                                 for axis in ('x','y','z')]]
    if atom_sites_frac.count(None) == 3:
      atom_sites_cart = [as_double_or_none_if_all_question_marks(
        _, column_name='_atom_site_Cartn_%s' %axis)
                         for _ in [cif_block.get('_atom_site_Cartn_%s' %axis)
                                   for axis in ('x','y','z')]]
      if atom_sites_cart.count(None) != 0:
        raise CifBuilderError("No atomic coordinates could be found")
      atom_sites_cart = flex.vec3_double(*atom_sites_cart)
      # XXX do we need to take account of _atom_sites_Cartn_tran_matrix_ ?
      atom_sites_frac = self.crystal_symmetry.unit_cell().fractionalize(
        atom_sites_cart)
    else:
      if atom_sites_frac.count(None) != 0:
        raise CifBuilderError("No atomic coordinates could be found")
      atom_sites_frac = flex.vec3_double(*atom_sites_frac)
    labels = cif_block.get('_atom_site_label')
    type_symbol = cif_block.get('_atom_site_type_symbol')
    U_iso_or_equiv = flex_double_else_none(
      cif_block.get('_atom_site_U_iso_or_equiv',
      cif_block.get('_atom_site_U_equiv_geom_mean')))
    if U_iso_or_equiv is None:
      B_iso_or_equiv = flex_double_else_none(
        cif_block.get('_atom_site_B_iso_or_equiv',
        cif_block.get('_atom_site_B_equiv_geom_mean')))
    adp_type = cif_block.get('_atom_site_adp_type')
    occupancy = flex_double_else_none(cif_block.get('_atom_site_occupancy'))
    scatterers = flex.xray_scatterer()
    atom_site_aniso_label = flex_std_string_else_none(
      cif_block.get('_atom_site_aniso_label'))
    if atom_site_aniso_label is not None:
      atom_site_aniso_label = atom_site_aniso_label
      adps = [cif_block.get('_atom_site_aniso_U_%i' %i)
              for i in (11,22,33,12,13,23)]
      have_Bs = False
      if adps.count(None) > 0:
        adps = [cif_block.get('_atom_site_aniso_B_%i' %i)
                for i in (11,22,33,12,13,23)]
        have_Bs = True
      if adps.count(None) == 6:
        adps = None
      elif adps.count(None) > 0:
        CifBuilderError("Some ADP items are missing")
      else:
        sel = None
        for adp in adps:
          f = (adp == "?")
          if (sel is None): sel = f
          else:             sel &= f
        sel = ~sel
        atom_site_aniso_label = atom_site_aniso_label.select(sel)
        try:
          adps = [flex.double(adp.select(sel)) for adp in adps]
        except ValueError, e:
          raise CifBuilderError("Error interpreting ADPs: " + str(e))
        adps = flex.sym_mat3_double(*adps)
    for i in range(len(atom_sites_frac)):
      kwds = {}
      if labels is not None:
        kwds.setdefault('label', str(labels[i]))
      if type_symbol is not None:
        kwds.setdefault('scattering_type', str(type_symbol[i]))
      if (atom_site_aniso_label is not None
          and adps is not None
          and labels is not None
          and labels[i] in atom_site_aniso_label):
        adp = adps[flex.first_index(atom_site_aniso_label, labels[i])]
        if have_Bs: adp = adptbx.b_as_u(adp)
        kwds.setdefault('u', adptbx.u_cif_as_u_star(
          self.crystal_symmetry.unit_cell(), adp))
      elif U_iso_or_equiv is not None:
        kwds.setdefault('u', float_from_string(U_iso_or_equiv[i]))
      elif B_iso_or_equiv is not None:
        kwds.setdefault('b', float_from_string(B_iso_or_equiv[i]))
      if occupancy is not None:
        kwds.setdefault('occupancy', float_from_string(occupancy[i]))
      scatterers.append(xray.scatterer(**kwds))
    scatterers.set_sites(atom_sites_frac)

    self.structure = xray.structure(crystal_symmetry=self.crystal_symmetry,
                                    scatterers=scatterers)

class miller_array_builder(crystal_symmetry_builder):

  observation_types = {
    '_refln_F_squared': xray.intensity(),
    '_refln_intensity': xray.intensity(),
    '_refln_F': xray.amplitude(),
    '_refln_A': None,
  }

  def __init__(self, cif_block, base_array_info=None):
    crystal_symmetry_builder.__init__(self, cif_block)
    if base_array_info is not None:
      self.crystal_symmetry = self.crystal_symmetry.join_symmetry(
        other_symmetry=base_array_info.crystal_symmetry_from_file,
      force=True)
    self._arrays = OrderedDict()
    if base_array_info is None:
      base_array_info = miller.array_info(source_type="cif")
    refln_containing_loops = self.get_miller_indices_containing_loops()
    for self.indices, refln_loop in refln_containing_loops:
      self.wavelength_id_array = None
      self.crystal_id_array = None
      self.scale_group_array = None
      wavelength_ids = [None]
      crystal_ids = [None]
      scale_groups = [None]
      for key, value in refln_loop.iteritems():
        # need to get these arrays first
        if (key.endswith('wavelength_id') or
            key.endswith('crystal_id') or
            key.endswith('scale_group_code')):
          data = as_int_or_none_if_all_question_marks(value, column_name=key)
          if data is None: continue
          counts = data.counts()
          if len(counts) == 1: continue
          array = miller.array(
            miller.set(self.crystal_symmetry, self.indices).auto_anomalous(), data)
          if key.endswith('wavelength_id'):
            self.wavelength_id_array = array
            wavelength_ids = counts.keys()
          elif key.endswith('crystal_id'):
            self.crystal_id_array = array
            crystal_ids = counts.keys()
          elif key.endswith('scale_group_code'):
            self.scale_group_array = array
            scale_groups = counts.keys()
      for label, value in sorted(refln_loop.items()):
        for w_id in wavelength_ids:
          for crys_id in crystal_ids:
            for scale_group in scale_groups:
              if 'index_' in label: continue
              key = label
              labels = [label]
              if (key.endswith('wavelength_id') or
                    key.endswith('crystal_id') or
                    key.endswith('scale_group_code')):
                w_id = None
                crys_id = None
                scale_group = None
              key_suffix = ''
              if w_id is not None:
                key_suffix += '_%i' %w_id
                labels.insert(0, "wavelength_id=%i" %w_id)
              if crys_id is not None:
                key_suffix += '_%i' %crys_id
                labels.insert(0, "crystal_id=%i" %crys_id)
              if scale_group is not None:
                key_suffix += '_%i' %scale_group
                labels.insert(0, "scale_group_code=%i" %scale_group)
              key += key_suffix
              sigmas = None
              if key in self._arrays: continue
              array = self.flex_std_string_as_miller_array(
                value, wavelength_id=w_id, crystal_id=crys_id,
                scale_group_code=scale_group)
              if array is None: continue
              if '_sigma' in key:
                sigmas_label = label
                key = None
                for suffix in ('', '_meas', '_calc'):
                  if sigmas_label.replace('_sigma', suffix) in refln_loop:
                    key = sigmas_label.replace('_sigma', suffix) + key_suffix
                    break
                if key is None:
                  key = sigmas_label + key_suffix
                elif key in self._arrays and self._arrays[key].sigmas() is None:
                  sigmas = array
                  array = self._arrays[key]
                  check_array_sizes(array, sigmas, key, sigmas_label)
                  sigmas = as_flex_double(sigmas, sigmas_label)
                  array.set_sigmas(sigmas.data())
                  info = array.info()
                  array.set_info(
                    info.customized_copy(labels=info.labels+[sigmas_label]))
                  continue
              elif key.endswith('PHWT'):
                phwt_label = label
                fwt_label = label[:-4] + 'FWT'
                if fwt_label not in refln_loop: continue
                phwt_array = array
                if fwt_label in self._arrays:
                  array = self._arrays[fwt_label]
                  check_array_sizes(array, phwt_array, fwt_label, phwt_label)
                  phases = as_flex_double(phwt_array, phwt_label)
                  info = array.info()
                  array = array.phase_transfer(phases, deg=True)
                  array.set_info(
                    info.customized_copy(labels=info.labels+[phwt_label]))
                  self._arrays[fwt_label] = array
                  continue
              elif 'HL_' in key:
                hl_letter = key[key.find('HL_')+3]
                hl_key = 'HL_' + hl_letter
                key = key.replace(hl_key, 'HL_A')
                if key in self._arrays:
                  continue # this array is already dealt with
                hl_labels = [label.replace(hl_key, 'HL_'+letter) for letter in 'ABCD']
                hl_keys = [key.replace(hl_key, 'HL_'+letter) for letter in 'ABCD']
                hl_values = [cif_block.get(hl_key) for hl_key in hl_labels]
                if hl_values.count(None) == 0:
                  selection = self.get_selection(
                    hl_values[0], wavelength_id=w_id,
                    crystal_id=crys_id, scale_group_code=scale_group)
                  hl_values = [as_double_or_none_if_all_question_marks(
                    hl.select(selection), column_name=lab)
                               for hl, lab in zip(hl_values, hl_labels)]
                  array = miller.array(miller.set(
                    self.crystal_symmetry, self.indices.select(selection)
                    ).auto_anomalous(), flex.hendrickson_lattman(*hl_values))
                  labels = labels[:-1]+hl_labels
              elif '.B_' in key or '_B_' in key:
                if '.B_' in key:
                  key, key_b = key.replace('.B_', '.A_'), key
                  label, label_b = label.replace('.B_', '.A_'), label
                elif '_B_' in key:
                  key, key_b = key.replace('_B', '_A'), key
                  label, label_b = label.replace('_B', '_A'), label
                if key in refln_loop and key_b in refln_loop:
                  b_part = array.data()
                  if key in self._arrays:
                    info = self._arrays[key].info()
                    a_part = self._arrays[key].data()
                    self._arrays[key] = self._arrays[key].array(
                      data=flex.complex_double(a_part, b_part))
                    self._arrays[key].set_info(
                      info.customized_copy(labels=info.labels+[key_b]))
                    continue
              elif ('phase_' in key and not key.endswith('_meas') and
                    self.crystal_symmetry.space_group() is not None):
                alt_key1 = label.replace('phase_', 'F_')
                alt_key2 = alt_key1 + '_au'
                if alt_key1 in refln_loop:
                  phase_key = label
                  key = alt_key1+key_suffix
                elif alt_key2 in refln_loop:
                  phase_key = label
                  key = alt_key2+key_suffix
                else: phase_key = None
                if phase_key is not None:
                  phases = array.data()
                  if key in self._arrays:
                    array = self._arrays[key]
                    array = as_flex_double(array, key)
                    check_array_sizes(array, phases, key, phase_key)
                    info = self._arrays[key].info()
                    self._arrays[key] = array.phase_transfer(phases, deg=True)
                    self._arrays[key].set_info(
                      info.customized_copy(labels=info.labels+[phase_key]))
                  else:
                    array = self.flex_std_string_as_miller_array(
                      refln_loop[label], wavelength_id=w_id, crystal_id=crys_id,
                      scale_group_code=scale_group)
                    check_array_sizes(array, phases, key, phase_key)
                    array.phase_transfer(phases, deg=True)
                    labels = labels+[label, phase_key]
              if base_array_info.labels is not None:
                labels = base_array_info.labels + labels
              # determine observation type
              stripped_key = key.rstrip(key_suffix).rstrip('_au').rstrip('_meas')\
                           .rstrip('_calc').rstrip('_plus').rstrip('_minus')
              if (stripped_key.endswith('F_squared') or
                  stripped_key.endswith('intensity') or
                  stripped_key.endswith('.I') or
                  stripped_key.endswith('_I')) and (
                    array.is_real_array() or array.is_integer_array()):
                array.set_observation_type_xray_intensity()
              elif (stripped_key.endswith('F') and (
                array.is_real_array() or array.is_integer_array())):
                array.set_observation_type_xray_amplitude()
              if (array.is_xray_amplitude_array() or
                  array.is_xray_amplitude_array()):
                # e.g. merge_equivalents treats integer arrays differently, so must
                # convert integer observation arrays here to be safe
                if isinstance(array.data(), flex.int):
                  array = array.customized_copy(data=array.data().as_double())
              array.set_info(base_array_info.customized_copy(labels=labels))
              self._arrays.setdefault(key, array)
    for key, array in self._arrays.copy().iteritems():
      if (   key.endswith('_minus') or '_minus_' in key
          or key.endswith('_plus') or '_plus_' in key):
        if '_minus' in key:
          minus_key = key
          plus_key = key.replace('_minus', '_plus')
        elif '_plus' in key:
          plus_key = key
          minus_key = key.replace('_plus', '_minus')
        if plus_key in self._arrays and minus_key in self._arrays:
          plus_array = self._arrays.pop(plus_key)
          minus_array = self._arrays.pop(minus_key)
          minus_array = minus_array.customized_copy(
            indices=-minus_array.indices()).set_info(minus_array.info())
          array = plus_array.concatenate(
            minus_array, assert_is_similar_symmetry=False)
          array = array.customized_copy(anomalous_flag=True)
          array.set_info(minus_array.info().customized_copy(
            labels=OrderedSet(plus_array.info().labels+minus_array.info().labels)))
          array.set_observation_type(plus_array.observation_type())
          self._arrays.setdefault(key, array)

    if len(self._arrays) == 0:
      raise CifBuilderError("No reflection data present in cif block")

  def get_miller_indices_containing_loops(self):
    loops = []
    for loop in self.cif_block.loops.values():
      for key in loop.keys():
        if 'index_h' not in key: continue
        hkl_str = [loop.get(key.replace('index_h', 'index_%s' %i)) for i in 'hkl']
        if hkl_str.count(None) > 0:
          raise CifBuilderError(
            "Miller indices missing from current CIF block (%s)"
            %key.replace('index_h', 'index_%s' %'hkl'[hkl_str.index(None)]))
        hkl_int = []
        for i,h_str in enumerate(hkl_str):
          try:
            h_int = flex.int(h_str)
          except ValueError, e:
            raise CifBuilderError(
              "Invalid item for Miller index %s: %s" % ("HKL"[i], str(e)))
          hkl_int.append(h_int)
        indices = flex.miller_index(*hkl_int)
        loops.append((indices, loop))
        break
    return loops

  def get_selection(self, value,
                    wavelength_id=None,
                    crystal_id=None,
                    scale_group_code=None):
    selection = ~((value == '.') | (value == '?'))
    if self.wavelength_id_array is not None and wavelength_id is not None:
      selection &= (self.wavelength_id_array.data() == wavelength_id)
    if self.crystal_id_array is not None and crystal_id is not None:
      selection &= (self.crystal_id_array.data() == crystal_id)
    if self.scale_group_array is not None and scale_group_code is not None:
      selection &= (self.scale_group_array.data() == scale_group_code)
    return selection

  def flex_std_string_as_miller_array(self, value,
                                      wavelength_id=None,
                                      crystal_id=None,
                                      scale_group_code=None):
    selection = self.get_selection(
      value, wavelength_id=wavelength_id,
      crystal_id=crystal_id, scale_group_code=scale_group_code)
    data = value.select(selection)
    try:
      data = flex.int(data)
      indices = self.indices.select(selection)
    except ValueError:
      try:
        data = flex.double(data)
        indices = self.indices.select(selection)
      except ValueError:
        # if flex.std_string return all values including '.' and '?'
        data = value
        indices = self.indices
    if data.size() == 0: return None
    return miller.array(
      miller.set(self.crystal_symmetry, indices).auto_anomalous(), data)

  def arrays(self):
    return self._arrays


class pdb_hierarchy_builder(crystal_symmetry_builder):

  def __init__(self, cif_block):
    crystal_symmetry_builder.__init__(self, cif_block)
    from iotbx.pdb import hierarchy

    self.hierarchy = hierarchy.root()

    # These items are mandatory for the _atom_site loop, all others are optional
    type_symbol = cif_block.get("_atom_site.type_symbol")
    atom_labels = cif_block.get("_atom_site.label_atom_id") # corresponds to chem comp atom name
    alt_id = cif_block.get("_atom_site.label_alt_id") # alternate conformer id
    asym_id = cif_block.get("_atom_site.label_asym_id") # chain id
    comp_id = cif_block.get("_atom_site.label_comp_id") # residue name
    entity_id = cif_block.get("_atom_site.label_entity_id")
    seq_id = cif_block.get("_atom_site.label_seq_id") # residue number
    assert [atom_labels, alt_id, asym_id, comp_id, entity_id, seq_id].count(None) == 0
    assert type_symbol is not None

    model_ids = cif_block.get("_atom_site.pdbx_PDB_model_num")
    atom_site_id = cif_block.get("_atom_site.id")
    # only permitted values are ATOM or HETATM
    group_PDB = cif_block.get("_atom_site.group_PDB")

    # TODO: read esds
    B_iso_or_equiv = flex.double(cif_block.get("_atom_site.B_iso_or_equiv"))
    cart_x = flex.double(cif_block.get("_atom_site.Cartn_x"))
    cart_y = flex.double(cif_block.get("_atom_site.Cartn_y"))
    cart_z = flex.double(cif_block.get("_atom_site.Cartn_z"))
    occu = flex.double(cif_block.get("_atom_site.occupancy"))
    # TODO: read charge

    # anisotropic b-factors
    # TODO: read esds
    anisotrop_id = cif_block.get("_atom_site_anisotrop.id")
    adps = None
    if anisotrop_id is not None:
      u_ij = [cif_block.get("_atom_site_anisotrop.U[%s][%s]" %(ij[0], ij[1]))
              for ij in ("11", "22", "33", "12", "13", "23")]
      assert u_ij.count(None) in (0, 6)
      if u_ij.count(None) == 0:
        adps = u_ij
      else:
        assert u_ij.count(None) == 6
        b_ij = [cif_block.get("_atom_site_anisotrop.B[%s][%s]" %(ij[0], ij[1]))
                for ij in ("11", "22", "33", "12", "13", "23")]
        assert b_ij.count(None) in (0, 6)
        if b_ij.count(None) == 0:
          adps = adptbx.b_as_u(b_ij)
        assert not (u_ij.count(None) and b_ij.count(None)) # illegal for both to be present
      if adps is not None:
        try:
          adps = [flex.double(adp) for adp in adps]
        except ValueError, e:
          raise CifBuilderError("Error interpreting ADPs: " + str(e))
        adps = flex.sym_mat3_double(*adps)

    # XXX What if _atom_site.pdbx_PDB_model_num is not given?
    unique_model_ids = OrderedSet(model_ids) # XXX more efficient way to do this?
    self.hierarchy.pre_allocate_models(len(unique_model_ids))
    for i_model in unique_model_ids:
      model_sel = (model_ids == i_model)
      model = hierarchy.model(id=i_model)
      self.hierarchy.append_model(model)
      unique_chain_ids = OrderedSet(asym_id.select(model_sel))
      model.pre_allocate_chains(len(unique_chain_ids))
      for i_chain in unique_chain_ids:
        chain_sel = (asym_id == i_chain) & model_sel
        chain = hierarchy.chain(id=i_chain)
        model.append_chain(chain)
        unique_residue_ids = OrderedSet(seq_id.select(chain_sel))
        chain.pre_allocate_residue_groups(len(unique_residue_ids))
        # XXX do we need to sort the residue ids, or leave them in the order we found them?
        for i_residue in unique_residue_ids:
          residue_sel = (seq_id == i_residue) & chain_sel
          residue_group = hierarchy.residue_group(resseq=i_residue)
          chain.append_residue_group(residue_group)
          unique_altloc_ids = OrderedSet(alt_id.select(residue_sel))
          residue_group.pre_allocate_atom_groups(len(unique_altloc_ids))
          for i_altloc in unique_altloc_ids:
            atom_group_sel = (alt_id == i_altloc) & residue_sel
            resnames = comp_id.select(atom_group_sel)
            assert len(set(resnames)) == 1 # should all in the atom group have the same resname?
            if i_altloc == ".": i_altloc = "" # Main chain atoms
            atom_group = hierarchy.atom_group(altloc=i_altloc, resname=resnames[0])
            residue_group.append_atom_group(atom_group)
            atom_group_isel = atom_group_sel.iselection()
            atom_group.pre_allocate_atoms(len(atom_group_isel))
            for i_atom in atom_group_isel:
              atom = hierarchy.atom()
              atom_group.append_atom(atom)
              atom.set_element(type_symbol[i_atom])
              atom.set_name(atom_labels[i_atom])
              atom.set_xyz(
                new_xyz=(cart_x[i_atom], cart_y[i_atom], cart_z[i_atom]))
              atom.set_b(B_iso_or_equiv[i_atom])
              atom.set_occ(occu[i_atom])
              atom.set_serial(atom_site_id[i_atom])
              if anisotrop_id is not None and adps is not None:
                u_ij_index = flex.first_index(anisotrop_id, atom.serial)
                if u_ij_index is not None:
                  u_ij = adps[u_ij_index]
                  atom.set_uij(u_ij)
                else:
                  pass


def as_flex_double(array, key):
  if isinstance(array.data(), flex.double):
    return array
  elif isinstance(array.data(), flex.int):
    return array.customized_copy(
      data=array.data().as_double()).set_info(array.info())
  else:
    try:
      flex.double(array.data())
    except ValueError, e:
      e_str = str(e)
      if e_str.startswith("Invalid floating-point value: "):
        i = e_str.find(":") + 2
        raise CifBuilderError("Invalid floating-point value for %s: %s"
                              %(key, e_str[i:].strip()))
      else:
        raise CifBuilderError(e_str)

def check_array_sizes(array1, array2, key1, key2):
  if array1.size() != array2.size():
    raise CifBuilderError(
      "Miller arrays '%s' and '%s' are of different sizes" %(
        key1, key2))

def none_if_all_question_marks_or_period(cif_block_item):
  if (cif_block_item is None): return None
  result = cif_block_item
  if (result.all_eq("?")): return None
  elif (result.all_eq(".")): return None
  return result

def as_int_or_none_if_all_question_marks(cif_block_item, column_name=None):
  strings = none_if_all_question_marks_or_period(cif_block_item)
  if (strings is None): return None
  try:
    return flex.int(strings)
  except ValueError, e:
    # better error message if column_name is given
    e_str = str(e)
    if column_name is not None and e_str.startswith(
      "Invalid integer value: "):
      i = e_str.find(":") + 2
      raise CifBuilderError("Invalid integer value for %s: %s"
                            %(column_name, e_str[i:].strip()))
    else:
      raise CifBuilderError(e_str)

def as_double_or_none_if_all_question_marks(cif_block_item, column_name=None):
  strings = none_if_all_question_marks_or_period(cif_block_item)
  if (strings is None): return None
  try:
    return flex.double(strings)
  except ValueError, e:
    # better error message if column_name is given
    e_str = str(e)
    if column_name is not None and e_str.startswith(
      "Invalid floating-point value: "):
      i = e_str.find(":") + 2
      raise CifBuilderError("Invalid floating-point value for %s: %s"
                            %(column_name, e_str[i:].strip()))
    else:
      raise CifBuilderError(e_str)

def flex_double(flex_std_string):
  try:
    return flex.double(flex_std_string)
  except ValueError, e:
    raise CifBuilderError(str(e))

def flex_double_else_none(cif_block_item):
  strings = none_if_all_question_marks_or_period(cif_block_item)
  if (strings is None): return None
  try:
    return flex.double(strings)
  except ValueError:
    pass
  return None

def flex_std_string_else_none(cif_block_item):
  if isinstance(cif_block_item, flex.std_string):
    return cif_block_item
  else:
    return None

def float_from_string(string):
  """a cif string may be quoted,
and have an optional esd in brackets associated with it"""
  if isinstance(string, float):
    return string
  return float(string.strip('\'').strip('"').split('(')[0])
