from __future__ import division
import cctbx.geometry_restraints
from cctbx.array_family import flex
from iotbx.pdb.amino_acid_codes import three_letter_l_given_three_letter_d
from libtbx.utils import Sorry

def get_c_beta_torsion_proxies(pdb_hierarchy,
                               selection=None,
                               sigma=2.5):
  if (selection is not None):
    if (isinstance(selection, flex.bool)):
      actual_bselection = selection
    elif (isinstance(selection, flex.size_t)):
      actual_bselection = flex.bool(pdb_hierarchy.atoms_size(), False)
      actual_bselection.set_selected(selection, True)
    else:
      raise Sorry("Bad selection supplied for c_beta restraints")
  if selection is None:
    actual_bselection = flex.bool(pdb_hierarchy.atoms_size(), True)
  cache = pdb_hierarchy.atom_selection_cache()
  sel = cache.selection("name N or name CA or name C or name CB")
  c_beta_dihedral_proxies = \
      cctbx.geometry_restraints.shared_dihedral_proxy()
  for model in pdb_hierarchy.select(sel).models():
    for chain in model.chains():
      if chain.is_protein():
        for rg in chain.residue_groups():
          for conformer in rg.conformers():
            for residue in conformer.residues():
              if residue.resname in three_letter_l_given_three_letter_d:
                continue
              N_atom  = residue.find_atom_by(name=" N  ")
              CA_atom = residue.find_atom_by(name=" CA ")
              C_atom  = residue.find_atom_by(name=" C  ")
              CB_atom = residue.find_atom_by(name=" CB ")
              if (N_atom is not None and CA_atom is not None
                  and C_atom is not None and CB_atom is not None):
                if not (actual_bselection[N_atom.i_seq] and
                    actual_bselection[CA_atom.i_seq] and
                    actual_bselection[C_atom.i_seq] and
                    actual_bselection[CB_atom.i_seq] ):
                  continue
                dihedralNCAB, dihedralCNAB = get_cb_target_angle_pair(
                                               resname=residue.resname)
                #NCAB
                i_seqs = [N_atom.i_seq,
                          C_atom.i_seq,
                          CA_atom.i_seq,
                          CB_atom.i_seq]
                dp_add = cctbx.geometry_restraints.dihedral_proxy(
                  i_seqs=i_seqs,
                  angle_ideal=dihedralNCAB,
                  weight=1/sigma**2,
                  origin_id=1)
                c_beta_dihedral_proxies.append(dp_add)
                #CNAB
                i_seqs = [C_atom.i_seq,
                          N_atom.i_seq,
                          CA_atom.i_seq,
                          CB_atom.i_seq]
                dp_add = cctbx.geometry_restraints.dihedral_proxy(
                  i_seqs=i_seqs,
                  angle_ideal=dihedralCNAB,
                  weight=1/sigma**2,
                  origin_id=1)
                c_beta_dihedral_proxies.append(dp_add)
  return c_beta_dihedral_proxies

def get_cb_target_angle_pair(resname):
  target_angle_dict = {
    "ALA" : (122.9, -122.6),
    "PRO" : (115.1, -120.7),
    "VAL" : (123.4, -122.0),
    "THR" : (123.4, -122.0),
    "ILE" : (123.4, -122.0),
    "GLY" : (121.6, -121.6)
  }
  dihedralNCAB, dihedralCNAB = target_angle_dict.get(resname, (122.8, -122.6))
  return dihedralNCAB, dihedralCNAB
