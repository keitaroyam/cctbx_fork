from libtbx.utils import format_exception, Sorry
from libtbx import Auto
from iotbx.pdb import common_residue_names_get_class
from mmtbx.validation.cbetadev import cbetadev
import ccp4io_adaptbx
import math

def selection(string, cache):
  return cache.selection(
    string=string)

def iselection(string, cache=None):
  return selection(string=string, cache=cache).iselection()

def phil_atom_selection_multiple(
      cache,
      string_list,
      allow_none=False,
      allow_auto=False,
      raise_if_empty_selection=True):
  result = []
  for string in string_list:
    if (string is None):
      if (allow_none): return None
      raise Sorry('Atom selection cannot be None:\n  =None')
    elif (string is Auto):
      if (allow_auto): return Auto
      raise Sorry('Atom selection cannot be Auto:\n  %s=Auto')
    try:
        result.append(selection(string=string, cache=cache).iselection())
    except KeyboardInterrupt: raise
    except Exception, e: # keep e alive to avoid traceback
      fe = format_exception()
      raise Sorry('Invalid atom selection:\n  %s=%s\n  (%s)' % (
        'reference_group', string, fe))
    if (raise_if_empty_selection and result.count(True) == 0):
      raise Sorry('Empty atom selection:\n  %s=%s' % (
        'reference_group', string))
  return result

def phil_atom_selections_as_i_seqs_multiple(cache,
                                            string_list):
  result = []
  iselection = phil_atom_selection_multiple(
        cache=cache,
        string_list=string_list,
        raise_if_empty_selection=False)
  for i in iselection:
    if (i.size() == 0):
      raise Sorry("No atom selected")
    for atom in i:
      result.append(atom)
  return result

def is_residue_in_selection(i_seqs, selection):
  for i_seq in i_seqs:
    if i_seq not in selection:
      return False
  return True

def get_i_seqs(atoms):
  i_seqs = []
  for atom in atoms:
    i_seqs.append(atom.i_seq)
  return i_seqs

def modernize_rna_resname(resname):
  if common_residue_names_get_class(resname,
       consider_ccp4_mon_lib_rna_dna=True) == "common_rna_dna" or \
     common_residue_names_get_class(resname,
       consider_ccp4_mon_lib_rna_dna=True) == "ccp4_mon_lib_rna_dna":
    tmp_resname = resname.strip()
    if len(tmp_resname) == 1:
      return "  "+tmp_resname
    elif len(tmp_resname) == 2:
      if tmp_resname[0:1].upper() == 'D':
        return " "+tmp_resname.upper()
      elif tmp_resname[1:].upper() == 'D':
        return " D"+tmp_resname[0:1].upper()
      elif tmp_resname[1:].upper() == 'R':
        return "  "+tmp_resname[0:1].upper()
  return resname

def modernize_rna_atom_name(atom):
   new_atom = atom.replace('*',"'")
   if new_atom == " O1P":
     new_atom = " OP1"
   elif new_atom == " O2P":
     new_atom = " OP2"
   return new_atom

def build_name_hash(pdb_hierarchy):
  i_seq_name_hash = dict()
  for atom in pdb_hierarchy.atoms():
    atom_name = atom.pdb_label_columns()[0:4]
    resname = atom.pdb_label_columns()[5:8]
    if resname.upper() == "MSE":
      resname = "MET"
      if atom_name == " SE ":
        atom_name = " SD "
    updated_resname = modernize_rna_resname(resname)
    if common_residue_names_get_class(updated_resname) == "common_rna_dna":
      updated_atom = modernize_rna_atom_name(atom=atom_name)
    else:
      updated_atom = atom_name
    key = updated_atom+atom.pdb_label_columns()[4:5]+\
          updated_resname+atom.pdb_label_columns()[8:]
    i_seq_name_hash[atom.i_seq]=key
  return i_seq_name_hash

def build_i_seq_hash(pdb_hierarchy):
  name_i_seq_hash = dict()
  for atom in pdb_hierarchy.atoms():
    atom_name = atom.pdb_label_columns()[0:4]
    resname = atom.pdb_label_columns()[5:8]
    if resname.upper() == "MSE":
      resname = "MET"
      if atom_name == " SE ":
        atom_name == " SD "
    updated_resname = modernize_rna_resname(resname)
    if common_residue_names_get_class(updated_resname) == "common_rna_dna":
      updated_atom = modernize_rna_atom_name(atom=atom_name)
    else:
      updated_atom = atom_name
    key = updated_atom+atom.pdb_label_columns()[4:5]+\
          updated_resname+atom.pdb_label_columns()[8:]
    name_i_seq_hash[key]=atom.i_seq
  return name_i_seq_hash

def build_xyz_hash(pdb_hierarchy):
  name_xyz_hash = dict()
  for atom in pdb_hierarchy.atoms():
    name_xyz_hash[atom.pdb_label_columns()]=atom.xyz
  return name_xyz_hash

def build_element_hash(pdb_hierarchy):
  i_seq_element_hash = dict()
  for atom in pdb_hierarchy.atoms():
    i_seq_element_hash[atom.i_seq]=atom.element
  return i_seq_element_hash

def build_cbetadev_hash(pdb_hierarchy):
  cb = cbetadev()
  cbetadev_hash = dict()
  cbeta_out = cb.analyze_pdb(hierarchy=pdb_hierarchy)
  for line in cbeta_out[0].splitlines():
    temp = line.split(':')
    dev = temp[5]
    if dev == "dev":
      continue
    key = temp[1].upper()+temp[2].upper()+temp[3]+temp[4].rstrip()
    cbetadev_hash[key] = dev
  return cbetadev_hash

def build_chain_hash(pdb_hierarchy):
  chain_hash = dict()
  for chain in pdb_hierarchy.chains():
    for atom in chain.atoms():
      chain_hash[atom.i_seq] = chain.id
  return chain_hash

def angle_distance(angle1, angle2):
  distance = math.fabs(angle1 - angle2)
  if distance > 180.0:
    distance -= 360.0
  return math.fabs(distance)

def get_angle_average(angles):
  n_angles = len(angles)
  sum = 0.0
  a1 = angles[0]
  if a1 > 180.0:
    a1 -= 360.0
  elif a1 < -180.0:
    a1 += 360.0
  sum += a1
  for angle in angles[1:]:
    a2 = angle
    if (a1 - a2) > 180.0:
      a2 += 360.0
    elif (a1 - a2) < -180.0:
      a2 -= 360.0
    sum += a2
  average = sum / n_angles
  return average

def _ssm_align(reference_chain,
               moving_chain):
  ssm = ccp4io_adaptbx.SecondaryStructureMatching(
          reference=reference_chain,
          moving=moving_chain)
  ssm_alignment = ccp4io_adaptbx.SSMAlignment.residue_groups(match=ssm)
  return ssm, ssm_alignment

def chain_from_selection(chain, selection):
  from iotbx.pdb.hierarchy import new_hierarchy_from_chain
  new_hierarchy = new_hierarchy_from_chain(chain=chain).select(selection)
  print dir(new_hierarchy)

def hierarchy_from_selection(pdb_hierarchy, selection):
  import iotbx.pdb.hierarchy
  temp_hierarchy = pdb_hierarchy.select(selection)
  hierarchy = iotbx.pdb.hierarchy.root()
  model = iotbx.pdb.hierarchy.model()
  for chain in temp_hierarchy.chains():
    for conformer in chain.conformers():
      if not conformer.is_protein() and not conformer.is_na():
        continue
      else:
        model.append_chain(chain.detached_copy())
  if len(model.chains()) != 1:
    raise Sorry("more than one chain in selection")
  hierarchy.append_model(model)
  return hierarchy
