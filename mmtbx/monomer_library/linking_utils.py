from __future__ import division
import iotbx

from scitbx.array_family import flex
from mmtbx.chemical_components import get_type

get_class = iotbx.pdb.common_residue_names_get_class

sugar_types = ["SACCHARIDE",
               "D-SACCHARIDE",
               ]
amino_types = ['"L-PEPTIDE LINKING"',
               '"D-PEPTIDE LINKING"',
               "L-PEPTIDE LINKING",
               "D-PEPTIDE LINKING",
               ]
n_linking_residues = [
  "ASN",
  ]
o_linking_residues = [
  "SER",
  "THR",
  ]
standard_n_links = [
  "NAG-ASN",
  ]
standard_o_links = [
  "NAG-SER",
  "NAG-THR",
  "MAN-SER",
  "MAN-THR",
  "XYS-SER",
  "XYS-THR",
  ]
#################################################
# saccharides that have non-standard atom names #
#  in the names in the standard links           #
#################################################
not_correct_sugars = [
  "FU4",
  ]

# see iotbx/pdb/common_residue_names.h; additionally here only: U I
ad_hoc_single_metal_residue_element_types = """\
ZN CA MG NA MN K FE CU CD HG NI CO SR CS PT BA TL PB SM AU RB YB LI
MO LU CR OS GD TB LA AG HO GA CE W RU RE PR IR EU AL V PD U
""".split()
#from elbow.chemistry import AtomClass
#for e in ad_hoc_single_metal_residue_element_types:
#  atom = AtomClass.AtomClass(e)
#  print atom
#  assert atom.isMetal()
ad_hoc_non_linking_elements = "H D F Cl Br I At".split()

class empty:
  def __repr__(self):
    outl = ""
    for attr in self.__dict__:
      outl += "  %s : %s\n" % (attr, getattr(self, attr))
    return outl

def get_distance2(atom1, atom2):
  d2 = (atom1.xyz[0]-atom2.xyz[0])**2
  d2 += (atom1.xyz[1]-atom2.xyz[1])**2
  d2 += (atom1.xyz[2]-atom2.xyz[2])**2
  return d2

def get_chiral_volume(centre, atom1, atom2, atom3):
  #if 1:
  #  from elbow.chemistry.xyzClass import xyzClass
  #  abc = []
  #  abc.append(xyzClass(atom1.xyz)-xyzClass(centre.xyz))
  #  abc.append(xyzClass(atom2.xyz)-xyzClass(centre.xyz))
  #  abc.append(xyzClass(atom3.xyz)-xyzClass(centre.xyz))
  #  volume = abc[0].DotProduct(abc[1].CrossProduct(abc[2]))
  abc = []
  abc.append(flex.double(atom1.xyz)-flex.double(centre.xyz))
  abc.append(flex.double(atom2.xyz)-flex.double(centre.xyz))
  abc.append(flex.double(atom3.xyz)-flex.double(centre.xyz))
  a = flex.vec3_double(abc[1])
  b = flex.vec3_double(abc[2])
  volume = abc[0].dot(flex.double(a.cross(b)[0]))
  return volume

def is_glyco_bond(atom1, atom2, verbose=False):
  if verbose:
    print '----- is_glyco_bond -----'
    print atom1.quote()
    print atom2.quote()
    print get_type(atom1.parent().resname)
    print get_type(atom2.parent().resname)
    print sugar_types
    print get_type(atom1.parent().resname).upper()
    print get_type(atom2.parent().resname).upper()
  if get_type(atom1.parent().resname) is None: return False
  if get_type(atom2.parent().resname) is None: return False
  if not get_type(atom1.parent().resname).upper() in sugar_types: return False
  if not get_type(atom2.parent().resname).upper() in sugar_types: return False
  #
  if atom2.parent().resname in not_correct_sugars: return False
  return True

def is_glyco_amino_bond(atom1, atom2, verbose=False):
  if verbose:
    print '----- is_glyco_amino_bond -----'
    print atom1.quote()
    print atom2.quote()
    print get_type(atom1.parent().resname)
    print get_type(atom2.parent().resname)
    print sugar_types
    print get_type(atom1.parent().resname).upper()
    print get_type(atom2.parent().resname).upper()
  if get_type(atom1.parent().resname) is None: return False
  if get_type(atom2.parent().resname) is None: return False
  sugars = 0
  aminos = 0
  if get_type(atom1.parent().resname).upper() in sugar_types:
    sugars+=1
  elif get_type(atom1.parent().resname).upper() in amino_types:
    aminos+=1
  if get_type(atom2.parent().resname).upper() in sugar_types:
    sugars+=1
  elif get_type(atom2.parent().resname).upper() in amino_types:
    aminos+=1
  if sugars==1 and aminos==1:
    return True
  return False

def is_n_glyco_bond(atom1, atom2):
  if get_type(atom1.parent().resname) is None: return False
  if get_type(atom2.parent().resname) is None: return False
  sugars = 0
  n_links = 0
  if get_type(atom1.parent().resname).upper() in sugar_types:
    sugars+=1
  elif atom1.parent().resname in n_linking_residues:
    n_links+=1
  if get_type(atom2.parent().resname).upper() in sugar_types:
    sugars+=1
  elif atom2.parent().resname in n_linking_residues:
    n_links+=1
  if sugars==1 and n_links==1:
    return True
  return False

def is_o_glyco_bond(atom1, atom2):
  if get_type(atom1.parent().resname) is None: return False
  if get_type(atom2.parent().resname) is None: return False
  sugars = 0
  o_links = 0
  if get_type(atom1.parent().resname).upper() in sugar_types:
    sugars+=1
  elif atom1.parent().resname in o_linking_residues:
    o_links+=1
  if get_type(atom2.parent().resname).upper() in sugar_types:
    sugars+=1
  elif atom2.parent().resname in o_linking_residues:
    o_links+=1
  if sugars==1 and o_links==1:
    return True
  return False

def get_hand(c_atom, o_atom, angles, verbose=False):
  def _sort_by_name(a1, a2):
    if a1.name<a2.name: return -1
    else: return 1
  others = []
  for angle in angles:
    for atom in angle:
      if atom.element.strip() in ["H", "D", "T"]: continue
      if atom.parent().parent().resseq!=c_atom.parent().parent().resseq: continue
      if atom.name==c_atom.name: continue
      if atom.name==o_atom.name: continue
      others.append(atom)
  others.sort(_sort_by_name)
  others.insert(0, o_atom)
  others.insert(0, c_atom)
  if len(others)!=4:
    if verbose:
      print '-'*80
      for atom in others:
        print atom.format_atom_record()
      print '-'*80
    return None
  v = get_chiral_volume(*others)
  if v<0:
    return "BETA"
  else:
    return "ALPHA"

def get_classes(atom, verbose=False):
  attrs = [
    "common_sugar", # not in get_class
    "common_water",
    "common_element",
    "common_small_molecule",
    "common_amino_acid",
    "common_rna_dna",
    "other",
    "unknown",
    ]
  atom_group = atom.parent()
  classes = empty()
  for attr in attrs:
    setattr(classes, attr, False)
  if verbose:
    print '    atom_group1: altloc="%s" resname="%s" class="%s"' % (
      atom_group.altloc,
      atom_group.resname,
      get_class(atom_group.resname),
      )
  gc = get_class(atom_group.resname)
  for i, attr in enumerate(attrs):
    rc = None
    if i:
      rc = gc
    else:
      if(get_type(atom_group.resname) is not None and
         get_type(atom_group.resname).upper() in sugar_types):
        rc = attr
    if rc==attr:
      setattr(classes, attr, True)
  return classes

def get_closest_atoms(atom_group1,
                      atom_group2,
                      ignore_hydrogens=True,
                      ):
  min_d2 = 1e5
  min_atom1 = None
  min_atom2 = None
  for i, atom1 in enumerate(atom_group1.atoms()):
    if ignore_hydrogens:
      if atom1.element.strip() in ad_hoc_non_linking_elements: continue
    for j, atom2 in enumerate(atom_group2.atoms()):
      if ignore_hydrogens:
        if atom2.element.strip() in ad_hoc_non_linking_elements: continue
      #if i>=j: continue
      d2 = get_distance2(atom1, atom2)
      if d2<min_d2:
        min_atom1 = atom1
        min_atom2 = atom2
        min_d2 = d2
  return min_atom1, min_atom2

def get_link_atoms(atom_group1,
                   atom_group2,
                   bond_cutoff=2.75,
                   ignore_hydrogens=True,
                   ):
  bond_cutoff *= bond_cutoff
  link_atoms = []
  for i, atom1 in enumerate(atom_group1.atoms()):
    if ignore_hydrogens:
      if atom1.element.strip() in ad_hoc_non_linking_elements: continue
    for j, atom2 in enumerate(atom_group2.atoms()):
      if ignore_hydrogens:
        if atom2.element.strip() in ad_hoc_non_linking_elements: continue
      #if i>=j: continue
      d2 = get_distance2(atom1, atom2)
      if d2<bond_cutoff:
        link_atoms.append([atom1, atom2])
  return link_atoms

def get_nonbonded(pdb_inp,
                  pdb_hierarchy,
                  geometry_restraints_manager,
                  ):
  site_labels = [atom.id_str()
     for atom in pdb_hierarchy.atoms()]
  pair_proxies = geometry_restraints_manager.pair_proxies(
     sites_cart=pdb_inp.xray_structure_simple().sites_cart(),
     site_labels=site_labels,
     )
  #print dir(pair_proxies)
  #print pair_proxies.nonbonded_proxies
  #print dir(pair_proxies.nonbonded_proxies)
  #print pair_proxies.nonbonded_proxies.simple
  #print dir(pair_proxies.nonbonded_proxies.simple)
  #assert 0
  sites_cart = geometry_restraints_manager.sites_cart_used_for_pair_proxies()
  #pair_proxies.nonbonded_proxies.show_sorted(
  #  by_value="delta",
  #  sites_cart=sites_cart,
  #  )
  site_labels = [atom.id_str()
     for atom in pdb_hierarchy.atoms()]
  sorted_nonbonded_proxies, not_shown = pair_proxies.nonbonded_proxies.get_sorted(
    by_value="delta",
    sites_cart=sites_cart,
    site_labels=site_labels,
    #f=sio,
    #prefix="*",
    #max_items=0,
    )
  if 0:
    pair_proxies.nonbonded_proxies.show_sorted(
      by_value="delta",
      sites_cart=sites_cart,
      site_labels=site_labels,
      #f=sio,
      #prefix="*",
      #max_items=0,
      )
  #bond_proxies_simple = geometry_restraints_manager.pair_proxies(
  #  sites_cart = sites_cart).bond_proxies.simple
  #print dir(bond_proxies_simple)
  #assert 0
  return sorted_nonbonded_proxies

def is_atom_pair_linked(atom1,
                        atom2,
                        bond_cutoff=2.75,
                        amino_acid_bond_cutoff=1.9,
                        rna_dna_bond_cutoff=3.5,
                        intra_residue_bond_cutoff=1.99,
                        metal_coordination_cutoff=3.5,
                        verbose=False,
                        ):
  #if atom1.parent().parent()==atom2.parent().parent(): return False
  #skip_if_one = ["common_water"]
  skip_if_both = [
    ["common_water", "common_water"],
    ]
  skip_if_longer = {
    ("common_amino_acid", "common_amino_acid") : amino_acid_bond_cutoff*amino_acid_bond_cutoff,
    }
  class1 = get_class(atom1.parent().resname)
  class2 = get_class(atom2.parent().resname)
  print class1, class2
  lookup = [class1, class2]
  lookup.sort()
  if lookup in skip_if_both: return False
  lookup = tuple(lookup)
  limit = skip_if_longer.get(lookup, None)
  d2 = get_distance2(atom1, atom2)
  if limit and limit<d2: return False
  #if class1 in skip_if_one or class2 in skip_if_one: return False
  # metals
  metal_coordination_cutoff *= metal_coordination_cutoff
  #amino_acid_bond_cutoff *= amino_acid_bond_cutoff
  #print 'd2',d2,metal_coordination_cutoff,amino_acid_bond_cutoff
  if d2>metal_coordination_cutoff: return False
  if class1=="common_element" and class2=="common_element":
    assert 0


  if class1=="common_element" or class2=="common_element":
    return True
  if d2>amino_acid_bond_cutoff: return False
  if class1=="common_amino_acid" and class2=="common_amino_acid":
    pass # rint "AMINO ACIDS",atom1.quote(), atom2.quote()
  return False

def process_nonbonded_for_linking(pdb_inp,
                                  pdb_hierarchy,
                                  geometry_restaints_manager,
                                  verbose=False,
                                  ):
  verbose=1
  sorted_nonbonded_proxies = get_nonbonded(pdb_inp,
                                           pdb_hierarchy,
                                           geometry_restaints_manager,
                                           )
  atoms = pdb_hierarchy.atoms()
  print '-'*80
  result = []
  for item in sorted_nonbonded_proxies:
    labels, i_seq, j_seq, distance, vdw_distance, sym_op, rt_mx_ji = item
    item = empty()
    item.labels = labels
    item.i_seq = i_seq
    item.j_seq = j_seq
    item.distance = distance
    if item.distance>2.75: break
    item.sym_op = sym_op
    item.rt_mx_ji = rt_mx_ji
    atom1 = atoms[i_seq]
    atom2 = atoms[j_seq]
    if verbose:
      print " Nonbonded: %s %s %0.3f %s %s" % (atoms[item.i_seq].id_str(),
                                               atoms[item.j_seq].id_str(),
                                               item.distance,
                                               item.sym_op,
                                               item.rt_mx_ji,
                                               ),

    if is_atom_pair_linked(atom1, atom2):
      print " Linking?"
      result.append(item)
    else:
      print
  print result
  return result

def get_bonded(hierarchy,
               atom,
               bond_cutoff=None,
               verbose=False,
               ):
  atoms=None
  if bond_cutoff:
    bond_cutoff *= bond_cutoff
    atoms = []
  target_atom_group = atom.parent()
  target_residue_group = target_atom_group.parent()
  target_chain = target_residue_group.parent()
  target_model = target_chain.parent()
  for model in hierarchy.models():
    if model.id!=target_model.id: continue
    if verbose: print 'model: "%s"' % model.id
    for chain in model.chains():
      if chain.id!=target_chain.id: continue
      if verbose: print 'chain: "%s"' % chain.id
      for residue_group in chain.residue_groups():
        if residue_group.resseq!=target_residue_group.resseq: continue
        if verbose: print '  residue_group: resseq="%s" icode="%s"' % (
          residue_group.resseq, residue_group.icode)
        yield_residue_group = False
        for atom_group_i, atom_group in enumerate(residue_group.atom_groups()):
          if atom_group.resname!=target_atom_group.resname: continue
          if verbose: print '    atom_group: altloc="%s" resname="%s"' % (
            atom_group.altloc, atom_group.resname)
          if bond_cutoff:
            for a in atom_group.atoms():
              if a.name==atom.name: continue
              d2 = get_distance2(atom, a)
              if d2<=bond_cutoff:
                atoms.append(a)
            return atoms
          else:
            min_d2 = 1000
            min_atom = None
            for a in atom_group.atoms():
              if a.name==atom.name: continue
              d2 = get_distance2(atom, a)
              if d2<min_d2:
                min_d2 = d2
                min_atom = a
            if min_atom:
              return min_atom
  return None

def get_angles_from_included_bonds(hierarchy,
                                   bonds,
                                   bond_cutoff=None,
                                   verbose=False,
                                   ):
  tmp = []
  for bond in bonds:
    for i, atom in enumerate(bond):
      rc = get_bonded(hierarchy,
                      atom,
                      bond_cutoff=bond_cutoff,
                      verbose=verbose,
                      )
      if rc:
        for rca in rc:
          if i:
            other = bond[0]
          else:
            other = bond[1]
          tmp.append([other, atom, rca])
  if verbose:
    for angle in tmp:
      for atom in angle:
        print atom.name,
      print get_distance2(angle[0], angle[1]),
      print get_distance2(angle[1], angle[2])
  return tmp

def process_atom_groups_for_linking(pdb_hierarchy,
                                    atom1,
                                    atom2,
                                    classes1,
                                    classes2,
                                    #bond_cutoff=2.75,
                                    amino_acid_bond_cutoff=1.9,
                                    rna_dna_bond_cutoff=3.5,
                                    intra_residue_bond_cutoff=1.99,
                                    verbose=False,
                                    ):
  #bond_cutoff *= bond_cutoff
  intra_residue_bond_cutoff *= intra_residue_bond_cutoff
  atom_group1 = atom1.parent()
  atom_group2 = atom2.parent()
  residue_group1 = atom_group1.parent()
  residue_group2 = atom_group2.parent()
  if(atom1.element.upper().strip() in ad_hoc_single_metal_residue_element_types or
     atom2.element.upper().strip() in ad_hoc_single_metal_residue_element_types):
    if verbose: print "Returning None because of metal"
    return None # if metal
    link_atoms = get_link_atoms(residue_group1, residue_group2)
    if link_atoms:
      return process_atom_groups_for_linking_multiple_links(pdb_hierarchy,
                                                            link_atoms,
                                                            verbose=verbose,
                                                            )
    else: return None
  else:
    atom1, atom2 = get_closest_atoms(residue_group1, residue_group2)
    #if get_distance2(atom1, atom2)>bond_cutoff:
    if atom1 is None or atom2 is None: return None
    if get_distance2(atom1, atom2)>intra_residue_bond_cutoff:
      if verbose: print "atoms too far apart %s %s %0.1f %0.1f" % (
        atom1.quote(),
        atom2.quote(),
        get_distance2(atom1, atom2),
        intra_residue_bond_cutoff,
        )
      return None
    return process_atom_groups_for_linking_single_link(
      pdb_hierarchy,
      atom1,
      atom2,
      intra_residue_bond_cutoff=intra_residue_bond_cutoff,
      verbose=verbose,
      )

def process_atom_groups_for_linking_single_link(pdb_hierarchy,
                                                atom1,
                                                atom2,
                                                intra_residue_bond_cutoff=1.99,
                                                verbose=False,
                                                ):
  if is_glyco_bond(atom1, atom2):
    # glyco bonds need to be in certain order
    if atom1.name.find("C")>-1:
      tmp_atom = atom1
      atom1 = atom2
      atom2 = tmp_atom

  elif is_glyco_amino_bond(atom1, atom2):
    # problem in 3sgk
#------------------------------------------------------------------
#ATOM   3803  OD1 ASP C  64      19.148  52.821 -19.425  1.00 70.10
#HETATM 5030  O6  NAG C1461      19.450  52.248 -18.258  1.00 60.78
#distance 1.33469921705
#------------------------------------------------------------------
    if atom1.element.strip()=="O" and atom2.element.strip()=="O": return None
    if atom2.name.find("C")>-1: # needs to be better using get_class???
      tmp_atom = atom1
      atom1 = atom2
      atom2 = tmp_atom

  long_tmp_key = "%s:%s-%s:%s" % (atom1.parent().resname.strip(),
                                  atom1.name.strip(),
                                  atom2.parent().resname.strip(),
                                  atom2.name.strip(),
    )
  tmp_key = "%s-%s" % (atom1.parent().resname.strip(),
                       atom2.parent().resname.strip(),
    )
  if verbose:
    print "tmp_key %s" % tmp_key
    print "long_tmp_key %s" % long_tmp_key
    print atom1.quote()
    print atom2.quote()
    print is_n_glyco_bond(atom1, atom2)
    print is_o_glyco_bond(atom1, atom2)
    print is_glyco_bond(atom1, atom2)
  if is_n_glyco_bond(atom1, atom2):
    if tmp_key in standard_n_links:
      data_links = ""
    key = tmp_key
  elif is_o_glyco_bond(atom1, atom2):
    if tmp_key in standard_o_links:
      data_links = ""
    key = tmp_key
  elif is_glyco_bond(atom1, atom2):
    data_links = ""
    c_atom = None
    o_atom = None
    if atom1.name.find("C")>-1:
      c_atom = atom1
    elif atom2.name.find("C")>-1:
      c_atom = atom2
    if atom1.name.find("O")>-1:
      o_atom = atom1
    elif atom2.name.find("O")>-1:
      o_atom = atom2
    if c_atom and o_atom:
      angles = get_angles_from_included_bonds(
        pdb_hierarchy,
        [[atom1, atom2]],
        bond_cutoff=1.75, #intra_residue_bond_cutoff,
        )
      if verbose:
        print 'get_hand'
        print c_atom, o_atom, angles
      hand = get_hand(c_atom, o_atom, angles, verbose=verbose) #"ALPHA"
      if hand is None:
        key = long_tmp_key
      else:
        data_link_key = "%s%s-%s" % (hand,
                                     c_atom.name.strip()[-1],
                                     o_atom.name.strip()[-1],
                                     )
        if data_link_key in [
          "BETAB-B",
          ]: assert 0
        #cif_links = cif_links.replace(tmp_key, data_link_key)
        key = data_link_key
    else:
      print " %s" % ("!"*84)
      print _write_warning_line("  Possible link ignored")
      print _write_warning_line(atom1.format_atom_record())
      print _write_warning_line(atom2.format_atom_record())
      print _write_warning_line("  N-linked glycan : %s" % (is_n_glyco_bond(atom1, atom2)))
      print _write_warning_line("  O-linked glycan : %s" % (is_o_glyco_bond(atom1, atom2)))
      print _write_warning_line("  Glycan-glycan   : %s" % (is_glyco_bond(atom1, atom2)))
      if c_atom is None: print _write_warning_line("  No carbon atom found")
      if o_atom is None: print _write_warning_line("  No oxygen atom found")
      print " %s" % ("!"*84)
  else:
    key = long_tmp_key

  pdbres_pair = []
  for atom in [atom1, atom2]:
    pdbres_pair.append(atom.id_str(pdbres=True))
  if verbose:
    print "key %s" % key
    print pdbres_pair
    print atom1.quote()
    print atom2.quote()
  return [pdbres_pair], [key], [(atom1, atom2)]

def process_atom_groups_for_linking_multiple_links(pdb_hierarchy,
                                                   link_atoms,
                                                   verbose=False,
                                                   ):
  def _quote(atom):
    key = ""
    for attr in ["name", "resname", "resseq", "altloc"]:
      if getattr(atom, attr, None) is not None:
        key += "%s_" % getattr(atom, attr).strip()
      elif getattr(atom.parent(), attr, None) is not None:
        key += "%s_" % getattr(atom.parent(), attr).strip()
      elif getattr(atom.parent().parent(), attr, None) is not None:
        key += "%s_" % getattr(atom.parent().parent(), attr).strip()
      else:
        assert 0
    return key[:-1]

  pdbres_pairs = []
  keys = []
  atoms = []
  for atom1, atom2 in link_atoms:
    key = "%s-%s" % (_quote(atom1), _quote(atom2))
    pdbres_pair = []
    for atom in [atom1, atom2]:
      pdbres_pair.append(atom.id_str(pdbres=True))
    if verbose:
      print atom1.quote()
      print atom2.quote()
      print key
    pdbres_pairs.append(pdbres_pair)
    keys.append(key)
    atoms.append((atom1, atom2))
  return pdbres_pairs, keys, atoms

def print_apply(apply):
  from libtbx.introspection import show_stack
  outl = ''
  #print apply
  #print dir(apply)
  outl += "%s" % apply.data_link
  try:
    outl += " %s" % apply.pdbres_pair
    outl += " %s" % apply.atom1.quote()
    outl += " %s" % apply.atom2.quote()
    outl += " %s" % apply.automatic
    outl += " %s" % apply.was_used
  except Exception: pass
  #show_stack()
  return outl

class apply_cif_list(list):
  def __repr__(self):
    outl = "CIFs"
    for ga in self:
      outl += "\n%s" % print_apply(ga)
    outl += "\n"
    outl += '_'*80
    return outl

  def __append__(self, item):
    print 'APPEND'*10
    print item
    list.__append__(self, item)
