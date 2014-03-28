
from __future__ import division
from string import digits
from cctbx import geometry_restraints
from libtbx.utils import Sorry

beta_1_4 = """
data_link_BETA1-4
loop_
_chem_link_bond.link_id
_chem_link_bond.atom_1_comp_id
_chem_link_bond.atom_id_1
_chem_link_bond.atom_2_comp_id
_chem_link_bond.atom_id_2
_chem_link_bond.type
_chem_link_bond.value_dist
_chem_link_bond.value_dist_esd
 BETA1-4  1  O4  2  C1  single  1.439  0.020

loop_
_chem_link_angle.link_id
_chem_link_angle.atom_1_comp_id
_chem_link_angle.atom_id_1
_chem_link_angle.atom_2_comp_id
_chem_link_angle.atom_id_2
_chem_link_angle.atom_3_comp_id
_chem_link_angle.atom_id_3
_chem_link_angle.value_angle
_chem_link_angle.value_angle_esd
 BETA1-4  1  C4  1  O4  2  C1  108.700  3.000
 BETA1-4  1  O4  2  C1  2  O5  112.300  3.000
 BETA1-4  1  O4  2  C1  2  C2  109.470  3.000
 BETA1-4  1  O4  2  C1  2  H1  109.470  3.000

loop_
_chem_link_chir.link_id
_chem_link_chir.atom_centre_comp_id
_chem_link_chir.atom_id_centre
_chem_link_chir.atom_1_comp_id
_chem_link_chir.atom_id_1
_chem_link_chir.atom_2_comp_id
_chem_link_chir.atom_id_2
_chem_link_chir.atom_3_comp_id
_chem_link_chir.atom_id_3
_chem_link_chir.volume_sign
 BETA1-4  2  C1  1  O4  2  O5  2  C2  positiv

"""

from mmtbx.monomer_library import linking_utils
from mmtbx.monomer_library import glyco_chiral_values

# atoms
anomeric_carbon   = "2 C1"
ring_oxygen       = "2 O5"
link_oxygen       = "1 O4"
link_carbon       = "1 C4"
anomeric_hydrogen = "2 H1"
ring_carbon       = "2 C2"

def get_chiral_sign(code):
  return glyco_chiral_values.volumes.get(code, None)

def get_alpha_beta(code):
  # fake alpha/beta
  cs = get_chiral_sign(code)
  if cs is None: assert 0
  elif cs < 0: return "ALPHA"
  else: return "BETA"

class glyco_link_class:
  def __init__(self,
               anomeric_carbon,
               ring_oxygen=None,
               ring_carbon=None,
               link_oxygen=None,
               link_carbon=None,
               anomeric_hydrogen=None,
               ):
    self.anomeric_carbon=anomeric_carbon
    self.ring_oxygen=ring_oxygen
    self.ring_carbon=ring_carbon
    self.link_oxygen=link_oxygen
    self.link_carbon=link_carbon
    self.anomeric_hydrogen=anomeric_hydrogen
    self.anomeric_carbon_linking=None

  def __repr__(self):
    outl = "\nGlycosidic atoms\n"
    for attr in ["anomeric_carbon",
                 "ring_oxygen",
                 "ring_carbon",
                 "link_oxygen",
                 "link_carbon",
                 "anomeric_hydrogen",
                 ]:
      try: outl += "  %-20s : %s" % (attr, getattr(self, attr).quote())
      except Exception: outl += "  %-20s : ???" % (attr)
      if attr=="anomeric_carbon":
        outl += " linking : %s" % self.anomeric_carbon_linking
      outl += "\n"
    return outl

  def is_correct(self):
    if (self.anomeric_carbon is None or
        self.link_oxygen is None or
        self.ring_oxygen is None or
        #ring_carbon is None or
        self.link_carbon is None
        ):
      return False
    return True

  def get_chiral_i_seqs(self):
    i_seqs = []
    for atom in [self.anomeric_carbon,
                 self.link_oxygen,
                 self.ring_oxygen,
                 self.ring_carbon,
                 ]:
      if atom is None: return None
      i_seqs.append(getattr(atom, "i_seq"))
    return i_seqs

def get_distance2(a1, a2):
  d2 = 0
  for i in range(3):
    d2 += (a1.xyz[i]-a2.xyz[i])**2
  return d2

def generate_atoms_from_atom_groups(atom_group1, atom_group2):
  for atom in atom_group1.atoms(): yield atom
  for atom in atom_group2.atoms(): yield atom

def get_anomeric_carbon(atom_group1, atom_group2, bonds, verbose=False):
  for i, atom in enumerate(generate_atoms_from_atom_groups(atom_group1,
                                                           atom_group2)
                                                           ):
    if atom.element.strip() not in ["C"]: continue
    oxygens = []
    residues = []
    for ba in bonds.get(atom.i_seq, []):
      if ba.element.strip() in ["O"]:
        oxygens.append(ba)
        residues.append(ba.parent())
    if len(oxygens)==2:
      if residues[0].id_str() != residues[1].id_str():
        return atom, True
      else:
        return atom, False
##         raise Sorry("""
##         Trying to find the anomeric carbon but found a carbon
##         linked to two oxygens.
##           anomeric carbon %s
##           linked oxygens  %s
##                           %s
##         The anomeric carbons should link to another residue.
##         """ % (atom.quote(),
##                oxygens[0].quote(),
##                oxygens[1].quote(),
##                )
##                )
  return None

def get_C1_carbon(atom_group1, atom_group2):
  c1s = []
  for i, atom in enumerate(generate_atoms_from_atom_groups(atom_group1,
                                                           atom_group2)
                                                           ):
    if atom.name.strip()=="C1": c1s.append(atom)
  if not c1s:
    assert 0
    return None
  for c1 in c1s:
    oxygens = []
    for i, atom in enumerate(generate_atoms_from_atom_groups(atom_group1,
                                                             atom_group2)
                                                             ):
      if atom.element.strip() in ["O"]:
        d2 = get_distance2(c1, atom)
        if d2<4.: # need from outside
          oxygens.append(atom)
    if len(oxygens)==2:
      break
  else:
    outl = ""
    for atom in c1s:
      outl += "\n\t\t%s" % atom.quote()
    raise Sorry("""
        Trying to find the anomeric carbons but could not find
        a suitable candidate.
%s
        Check carbohydrate geometry.
                """ % outl
               )
  if oxygens[0].parent().id_str()!=oxygens[1].parent().id_str():
    return c1, True
  else:
    return c1, False
##     raise Sorry("""
##         Trying to find the anomeric carbon but found a carbon
##         linked to two oxygens.
##           anomeric carbon %s
##           linked oxygens  %s
##                           %s
##         """ % (c1.quote(),
##                oxygens[0].quote(),
##                oxygens[1].quote(),
##                )
##                )
  return None

def get_ring_oxygen(anomeric_carbon, bonds):
  for ba in bonds.get(anomeric_carbon.i_seq, []):
    if ba.element.strip() not in ["O"]: continue
    if ba.parent().id_str() == anomeric_carbon.parent().id_str():
      return ba

def get_ring_carbon(anomeric_carbon, bonds):
  for ba in bonds.get(anomeric_carbon.i_seq, []):
    if ba.element.strip() not in ["C"]: continue
    if ba.parent().id_str() == anomeric_carbon.parent().id_str():
      return ba

def get_anomeric_hydrogen(anomeric_carbon, bonds):
  for ba in bonds.get(anomeric_carbon.i_seq, []):
    if ba.element.strip() not in ["H"]: continue
    if ba.parent().id_str() == anomeric_carbon.parent().id_str():
      return ba

def get_link_oxygen(anomeric_carbon, bonds, verbose=False):
  if verbose:
    print anomeric_carbon.quote()
    print bonds.get(anomeric_carbon.i_seq)
  for ba in bonds.get(anomeric_carbon.i_seq, []):
    if verbose: print ba.quote()
    if ba.element.strip() not in ["O"]: continue
    if ba.parent().id_str() != anomeric_carbon.parent().id_str():
      return ba

def get_link_oxygen_on_distance(anomeric_carbon, atom_group1, atom_group2):
  link_group = None
  for atom in atom_group2.atoms():
    if atom.quote()==anomeric_carbon.quote():
      link_group = atom_group1
      break
  if link_group is None:
    for atom in atom_group1.atoms():
      if atom.quote()==anomeric_carbon.quote():
        link_group = atom_group1
        break
  if link_group is None: assert 0
  for atom in link_group.atoms():
    if atom.element.strip()!="O": continue
    d2 = get_distance2(atom, anomeric_carbon)
    if d2<4.:
      return atom
  return None

def get_link_carbon(anomeric_carbon, link_oxygen, bonds):
  for ba in bonds.get(link_oxygen.i_seq, []):
    if ba.element.strip() not in ["C"]: continue
    if ba.i_seq==anomeric_carbon.i_seq: continue
    if ba.parent().id_str() != anomeric_carbon.parent().id_str():
      return ba

def get_glyco_link_atoms(atom_group1,
                         atom_group2,
                         verbose=False,
                         ):
  # maybe should be restraints based?
  bonds = linking_utils.get_bonded_from_atom_groups(atom_group1,
                                                    atom_group2,
                                                    1.9, # XXX
    )
  rc = get_anomeric_carbon(atom_group1,
                           atom_group2,
                           bonds,
                           verbose=verbose)
  if rc is None:
    rc = get_C1_carbon(atom_group1, atom_group2)
  if rc is None: return None
  anomeric_carbon, linking_carbon = rc
  if anomeric_carbon is None:
    assert 0
    return None
  if verbose: print 'anomeric_carbon',anomeric_carbon.quote()
  ring_oxygen = get_ring_oxygen(anomeric_carbon, bonds)
  if verbose: print 'ring_oxygen',ring_oxygen.quote()
  ring_carbon = get_ring_carbon(anomeric_carbon, bonds)
  if verbose: print 'ring_carbon',ring_carbon.quote()
  anomeric_hydrogen = get_anomeric_hydrogen(anomeric_carbon, bonds)
  if verbose: print 'anomeric_hydrogen',anomeric_hydrogen
  link_oxygen = get_link_oxygen(anomeric_carbon, bonds, verbose=verbose)
  if link_oxygen is None:
    link_oxygen = get_link_oxygen_on_distance(anomeric_carbon,
                                              atom_group1,
                                              atom_group2)
  if link_oxygen is None:
    return None
  if verbose: print 'link_oxygen',link_oxygen.quote()
  link_carbon = get_link_carbon(anomeric_carbon, link_oxygen, bonds)
  if verbose:
    try: print 'link_carbon',link_carbon.quote()
    except Exception: print
  gla = glyco_link_class(anomeric_carbon,
                         ring_oxygen,
                         ring_carbon,
                         link_oxygen,
                         link_carbon,
                         anomeric_hydrogen,
                         )
  gla.anomeric_carbon_linking = linking_carbon
  return gla

def apply_glyco_link_using_proxies_and_atoms(atom_group1,
                                             atom_group2,
                                             bond_params_table,
                                             bond_asu_table,
                                             geometry_proxy_registries,
                                             rt_mx_ji,
                                             ):
  def _add_bond(i_seqs,
                bond_params_table,
                bond_asu_table,
                value,
                esd,
                rt_mx_ji,
                ):
    proxy = geometry_restraints.bond_simple_proxy(
      i_seqs=i_seqs,
      distance_ideal=value,
      weight=1/esd**2)
    bond_params_table.update(i_seq=i_seqs[0],
                             j_seq=i_seqs[1],
                             params=proxy)
    bond_asu_table.add_pair(
      i_seq=i_seqs[0],
      j_seq=i_seqs[1],
      rt_mx_ji=rt_mx_ji,
      )
  #
  def _add_angle(i_seqs, geometry_proxy_registries, value, esd):
    proxy = geometry_restraints.angle_proxy(
      i_seqs=i_seqs,
      angle_ideal=value,
      weight=1/esd**2)
    geometry_proxy_registries.angle.append_custom_proxy(proxy=proxy)
  #
  def _add_chiral(i_seqs, geometry_proxy_registries, value, esd, both_signs=False):
    proxy = geometry_restraints.chirality_proxy(
      i_seqs=i_seqs,
      volume_ideal=value,
      both_signs=both_signs,
      weight=1/esd**2,
      )
    geometry_proxy_registries.chirality.append_custom_proxy(proxy=proxy)

  def atom_group_output(atom_group):
    outl = ""
    for atom in atom_group.atoms():
      outl += "%s%s\n" % (' '*10, atom.quote())
    return outl

  ########
  from mmtbx.monomer_library import glyco_utils
#  anomeric_carbon, link_oxygen, ring_oxygen, ring_carbon, link_carbon, anomeric_hydrogen = \
#      glyco_utils.get_glyco_link_atoms(atom_group1, atom_group2)
  gla = glyco_utils.get_glyco_link_atoms(atom_group1,
                                         atom_group2)
  # checks
  if gla and not gla.is_correct():
    gla = glyco_utils.get_glyco_link_atoms(atom_group2,
                                            atom_group1)
  if gla and not gla.is_correct():
    raise Sorry("""
    Failed to get all the atoms needed for glycosidic bond between
      group 1
%s
      group 2
%s
    """ % (atom_group_output(atom_group1), atom_group_output(atom_group2)
    )
    )
  if gla is None:
    raise Sorry("""
  Unspecified problem with carbohydrate groups. Could be that the linking oxygen
  is on the linking residue instead of the docking residue.
    group 1
%s
    group 2
%s
    """ % (atom_group_output(atom_group1), atom_group_output(atom_group2)
           )
           )
  if not gla.anomeric_carbon_linking:
    raise Sorry("""
  The linking carbohydrate unit has the oxygen attached to the anomeric carbon.
  Consider replacing oxygen %s
  with an oxygen linked to  %s in the same residue
    %s""" % (gla.link_oxygen.quote(),
             gla.link_carbon.quote(),
             gla)
             )
  i_seqs = [gla.anomeric_carbon.i_seq, gla.link_oxygen.i_seq]
  # bonds
  _add_bond(i_seqs, bond_params_table, bond_asu_table, 1.439, 0.02, rt_mx_ji)
  # angles
  for i_atoms, value, esd in [
      [[gla.link_carbon, gla.link_oxygen,     gla.anomeric_carbon],   108.7,  3.],
      [[gla.link_oxygen, gla.anomeric_carbon, gla.ring_oxygen],       112.3,  3.],
      [[gla.link_oxygen, gla.anomeric_carbon, gla.ring_carbon],       109.47, 3.],
      [[gla.link_oxygen, gla.anomeric_carbon, gla.anomeric_hydrogen], 109.47, 3.],
    ]:
    if None in i_atoms: continue
    i_seqs = [atom.i_seq for atom in i_atoms]
    _add_angle(i_seqs, geometry_proxy_registries, value, esd)
  # chiral
  i_seqs = gla.get_chiral_i_seqs()
  if i_seqs is None:
    raise Sorry("""
    Unable to determine the linking chiral atoms for atom groups
    group 1
%s
    group 2
%s
    """ % (atom_group_output(atom_group1), atom_group_output(atom_group2)
    )
    )
  value = get_chiral_sign(gla.anomeric_carbon.parent().resname)
  if value:
    esd = 0.02
    _add_chiral(i_seqs, geometry_proxy_registries, value, esd)
  isomer = get_alpha_beta(gla.anomeric_carbon.parent().resname)
  if gla.anomeric_carbon.name.strip()[-1] in digits:
    isomer += gla.anomeric_carbon.name.strip()[-1]
  else:
    isomer += " %s " % gla.anomeric_carbon.name.strip()
  if gla.link_oxygen.name.strip()[-1] in digits:
    isomer += "-%s" % gla.link_oxygen.name.strip()[-1]
  else:
    isomer += "- %s " % gla.link_oxygen.name.strip()
  return isomer
