from mmtbx.monomer_library import cif_types
from mmtbx.monomer_library import mmCIF
from scitbx.python_utils import dicts
from libtbx.str_utils import show_string
from libtbx.utils import Sorry, format_exception
import libtbx.load_env
import libtbx.path
import copy
import os

class MonomerLibraryServerError(RuntimeError): pass

mon_lib_env_vars = ["MMTBX_CCP4_MONOMER_LIB", "CLIBD_MON"]

def load_mon_lib_file(mon_lib_path, relative_path_components=[]):
  if (mon_lib_path is not None):
    cif_path = os.path.join(mon_lib_path, *relative_path_components)
    if (os.path.isfile(cif_path)):
      return cif_path
  return None

def find_mon_lib_file(env_vars=mon_lib_env_vars, relative_path_components=[]):
  result = load_mon_lib_file(
    mon_lib_path=os.environ.get(env_vars[0], None),
    relative_path_components=relative_path_components)
  if (result is not None): return result
  for relative_path in ["mon_lib", "ext_ref_files/mon_lib"]:
    result = load_mon_lib_file(
      mon_lib_path=libtbx.env.find_in_repositories(
        relative_path=relative_path),
      relative_path_components=relative_path_components)
    if (result is not None): return result
  for env_var in env_vars[1:]:
    result = load_mon_lib_file(
      mon_lib_path=os.environ.get(env_var, None),
      relative_path_components=relative_path_components)
    if (result is not None): return result
  return None

class mon_lib_cif_loader(object):

  def __init__(self, path=None, relative_path_components=[], strict=False):
    self.path = path
    if (self.path is None):
      self.path = find_mon_lib_file(
        relative_path_components=relative_path_components)
      if (self.path is None):
        raise MonomerLibraryServerError(
          "Cannot find CCP4 monomer library."
          " Please define one of these environment variables: "
          + ", ".join(mon_lib_env_vars))
    self.cif = mmCIF.mmCIFFile()
    self.cif.load_file(self.path, strict=strict)

def mon_lib_list_cif(path=None, strict=False):
  return mon_lib_cif_loader(
    path=path,
    relative_path_components=["list", "mon_lib_list.cif"],
    strict=strict)

def mon_lib_ener_lib_cif(path=None, strict=False):
  return mon_lib_cif_loader(
    path=path,
    relative_path_components=["ener_lib.cif"],
    strict=strict)

class trivial_html_tag_filter(object):

  def __init__(self, file_name):
    self.f = iter(open(file_name))

  def next(self):
    while 1:
      result = self.f.next()
      if (result[0] != "<"):
        return result

  def __iter__(self):
    return self

class server(object):

  def __init__(self, list_cif=None):
    if (list_cif is None):
      list_cif = mon_lib_list_cif()
    self.root_path = os.path.dirname(os.path.dirname(list_cif.path))
    self.comp_comp_id_dict = {}
    self.convert_deriv_list_dict(list_cif.cif)
    self.convert_comp_synonym_list(list_cif.cif)
    self.convert_comp_synonym_atom_list(list_cif.cif)
    self.convert_link_list(list_cif.cif)
    self.convert_mod_list(list_cif.cif)
    self._create_rna_dna_placeholders()

  def convert_deriv_list_dict(self, list_cif):
    self.deriv_list_dict = {}
    for row in list_cif["deriv_list"]["chem_comp_deriv"]:
      deriv = cif_types.chem_comp_deriv(**row)
      self.deriv_list_dict[deriv.comp_id] = deriv

  def convert_comp_synonym_list(self, list_cif):
    self.comp_synonym_list_dict = {}
    for row in list_cif["comp_synonym_list"]["chem_comp_synonym"]:
      self.comp_synonym_list_dict[row["comp_alternative_id"]] = row["comp_id"]

  def convert_comp_synonym_atom_list(self, list_cif):
    self.comp_synonym_atom_list_dict = dicts.with_default_factory(dict)
    for row in list_cif["comp_synonym_atom_list"]["chem_comp_synonym_atom"]:
      synonym = cif_types.chem_comp_synonym_atom(**row)
      d = self.comp_synonym_atom_list_dict[synonym.comp_id]
      d[synonym.atom_alternative_id] = synonym.atom_id
      if (synonym.comp_alternative_id != ""):
        d = self.comp_synonym_atom_list_dict[synonym.comp_alternative_id]
        d[synonym.atom_alternative_id] = synonym.atom_id

  def convert_link_list(self, list_cif):
    self.link_link_id_list = []
    self.link_link_id_dict = {}
    for list_row in list_cif["link_list"]["chem_link"]:
      link = cif_types.chem_link(**list_row)
      link_def = list_cif["link_"+link.id]
      link_link_id = cif_types.link_link_id(chem_link=link)
      for loop_block,lst_name in [("chem_link_bond","bond_list"),
                                  ("chem_link_angle","angle_list"),
                                  ("chem_link_tor","tor_list"),
                                  ("chem_link_chir","chir_list"),
                                  ("chem_link_plane","plane_list")]:
        lst = getattr(link_link_id, lst_name)
        typ = getattr(cif_types, loop_block)
        for row in link_def.get(loop_block, []):
          lst.append(typ(**row))
      self.link_link_id_list.append(link_link_id)
      self.link_link_id_dict[link.id] = link_link_id

  def convert_mod_list(self, list_cif):
    self.mod_mod_id_list = []
    self.mod_mod_id_dict = {}
    for mod_row in list_cif["mod_list"]["chem_mod"]:
      mod = cif_types.chem_mod(**mod_row)
      mod_def = list_cif["mod_"+mod.id]
      mod_mod_id = cif_types.mod_mod_id(chem_mod=mod)
      for loop_block,lst_name in [("chem_mod_atom","atom_list"),
                                  ("chem_mod_tree","tree_list"),
                                  ("chem_mod_bond","bond_list"),
                                  ("chem_mod_angle","angle_list"),
                                  ("chem_mod_tor","tor_list"),
                                  ("chem_mod_chir","chir_list"),
                                  ("chem_mod_plane_atom","plane_atom_list")]:
        lst = getattr(mod_mod_id, lst_name)
        typ = getattr(cif_types, loop_block)
        for row in mod_def.get(loop_block, []):
          lst.append(typ(**row))
      self.mod_mod_id_list.append(mod_mod_id)
      self.mod_mod_id_dict[mod.id] = mod_mod_id

  def get_comp_comp_id(self, comp_id):
    comp_id = comp_id.strip()
    try: return self.comp_comp_id_dict[comp_id]
    except KeyError: pass
    std_comp_id = self.comp_synonym_list_dict.get(comp_id, comp_id)
    comp_comp_id = None
    if (len(std_comp_id) > 0):
      file_name = os.path.join(
        self.root_path, std_comp_id[0].lower(), std_comp_id+".cif")
      if (os.path.isfile(file_name)):
        comp_comp_id = read_comp_cif(file_name=file_name)
    self.comp_comp_id_dict[std_comp_id] = comp_comp_id
    self.comp_comp_id_dict[comp_id] = comp_comp_id
    return self.comp_comp_id_dict[comp_id]

  def register_custom_comp_id(self, comp_id, comp_comp_id):
    self.comp_comp_id_dict[comp_id] = comp_comp_id

  def register_preprocessed_comp_comp_ids(self, preprocessed):
    comp_ids = {}
    for comp_cif in preprocessed.values():
      comp_id = comp_cif.chem_comp.id
      previous = comp_ids.get(comp_id, None)
      if (previous is not None):
        raise Sorry(
          "Conflicting monomer definitions for residue name %s:\n"
          "  %s\n"
          "  %s" % (
            show_string(comp_id),
            show_string(previous.file_name),
            show_string(comp_cif.file_name)))
      comp_ids[comp_id] = comp_cif
      self.register_custom_comp_id(comp_id=comp_id, comp_comp_id=comp_cif)
    ids = comp_ids.keys()
    ids.sort()
    return [comp_ids[id].file_name for id in ids]

  def _create_rna_dna_placeholders(self):
    for base_code in ["A", "C", "G"]:
      rna = self.get_comp_comp_id(base_code+"r")
      dna = self.get_comp_comp_id(base_code+"d")
      chem_comp = cif_types.chem_comp(
        id=base_code+"?",
        three_letter_code=None,
        name=None,
        group="rna_dna_placeholder",
        number_atoms_all=None,
        number_atoms_nh=None,
        desc_level=None)
      comp_comp_id = cif_types.comp_comp_id(chem_comp=chem_comp)
      for atom in rna.atom_list:
        comp_comp_id.atom_list.append(copy.copy(atom))
      rna_atom_dict = rna.atom_dict()
      for atom in dna.atom_list:
        if (not rna.atom_dict().has_key(atom.atom_id)):
          comp_comp_id.atom_list.append(copy.copy(atom))
      self.comp_comp_id_dict[base_code] = comp_comp_id
      self.comp_comp_id_dict["+"+base_code] = comp_comp_id

def read_comp_cif(file_name):
  comp_cif = mmCIF.mmCIFFile()
  comp_cif.load_file(fil=trivial_html_tag_filter(file_name),strict=False)
  comp_comp_id = convert_comp_file(comp_cif=comp_cif)
  comp_comp_id.file_name = libtbx.path.canonical_path(file_name)
  comp_comp_id.set_classification()
  return comp_comp_id

def process_comp_cif(preprocessed, file_names):
  for file_name in file_names:
    if (file_name is None): continue
    file_name = libtbx.path.canonical_path(file_name=file_name)
    if (file_name not in preprocessed):
      try: comp_cif = read_comp_cif(file_name=file_name)
      except KeyboardInterrupt: raise
      except:
        raise Sorry(
          "Error reading monomer definition file:\n"
          "  %s\n"
          "  (%s)" % (show_string(file_name), format_exception()))
      preprocessed[comp_cif.file_name] = comp_cif

def convert_comp_file(comp_cif):
  rows = comp_cif["comp_list"]["chem_comp"]
  assert len(rows) == 1
  chem_comp = cif_types.chem_comp(**rows[0])
  comp_def = comp_cif["comp_"+chem_comp.id]
  comp_comp_id = cif_types.comp_comp_id(chem_comp=chem_comp)
  for loop_block,lst_name in [("chem_comp_atom","atom_list"),
                              ("chem_comp_tree","tree_list"),
                              ("chem_comp_bond","bond_list"),
                              ("chem_comp_angle","angle_list"),
                              ("chem_comp_tor","tor_list"),
                              ("chem_comp_chir","chir_list"),
                              ("chem_comp_plane_atom","plane_atom_list")]:
    lst = getattr(comp_comp_id, lst_name)
    typ = getattr(cif_types, loop_block)
    for row in comp_def.get(loop_block, []):
      lst.append(typ(**row))
  return comp_comp_id

class ener_lib(object):

  def __init__(self, ener_lib_cif=None):
    if (ener_lib_cif is None):
      ener_lib_cif = mon_lib_ener_lib_cif()
    self.convert_lib_synonym(ener_lib_cif)
    self.convert_lib_atom(ener_lib_cif)
    self.convert_lib_vdw(ener_lib_cif)

  def convert_lib_synonym(self, ener_lib_cif):
    self.lib_synonym = {}
    for row in ener_lib_cif.cif["energy"]["lib_synonym"]:
      syn = cif_types.energy_lib_synonym(**row)
      if (self.lib_synonym.get(syn.atom_alternative_type, None) is not None):
        raise AssertionError(
          "Corrupt lib_synonym %s %s in CCP4 monomer library file: %s" % (
            syn.atom_type, syn.atom_alternative_type, ener_lib_cif.path))
      self.lib_synonym[syn.atom_alternative_type] = syn.atom_type

  def convert_lib_atom(self, ener_lib_cif):
    self.lib_atom = {}
    for row in ener_lib_cif.cif["energy"]["lib_atom"]:
      entry = cif_types.energy_lib_atom(**row)
      self.lib_atom[entry.type] = entry

  def convert_lib_vdw(self, ener_lib_cif):
    self.lib_vdw = []
    for row in ener_lib_cif.cif["energy"]["lib_vdw"]:
      vdw = cif_types.energy_lib_vdw(**row)
      self.lib_vdw.append(vdw)

  def vdw_lookup(self, atom_energy_types_pair):
    atom_energy_types_pair = [self.lib_synonym.get(t,t)
      for t in atom_energy_types_pair]
    for vdw in self.lib_vdw:
      if (   (    vdw.atom_type_1 == atom_energy_types_pair[0]
              and vdw.atom_type_2 == atom_energy_types_pair[1])
          or (    vdw.atom_type_1 == atom_energy_types_pair[1]
              and vdw.atom_type_2 == atom_energy_types_pair[0])):
        return vdw.radius_min
    entries = [self.lib_atom.get(t,None) for t in atom_energy_types_pair]
    if (None not in entries):
      radii = [entry.vdw_radius for entry in entries]
      if (None not in radii):
        return radii[0] + radii[1]
    return None
