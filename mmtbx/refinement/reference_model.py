import cctbx.geometry_restraints
from mmtbx.validation.rotalyze import rotalyze
from mmtbx.validation.cbetadev import cbetadev
from mmtbx.refinement import fit_rotamers
from mmtbx.rotamer.sidechain_angles import SidechainAngles
import mmtbx.monomer_library
from cctbx.array_family import flex
import sys, os

def build_name_hash(pdb_hierarchy):
  i_seq_name_hash = dict()
  for atom in pdb_hierarchy.atoms():
    i_seq_name_hash[atom.i_seq]=atom.pdb_label_columns()
  return i_seq_name_hash

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
    #key = temp[3].lstrip()+temp[4].rstrip()+temp[1]+temp[2].upper()
    key = temp[1]+temp[2].upper()+temp[3]+temp[4].rstrip()
    cbetadev_hash[key] = dev
  return cbetadev_hash

def build_dihedral_hash(geometry=None,
                        sites_cart=None,
                        pdb_hierarchy=None,
                        include_hydrogens=False,
                        include_main_chain=True,
                        include_side_chain=True):
  if not include_hydrogens:
    i_seq_element_hash = build_element_hash(pdb_hierarchy=pdb_hierarchy)
  i_seq_name_hash = build_name_hash(pdb_hierarchy=pdb_hierarchy)
  dihedral_hash = dict()

  for dp in geometry.dihedral_proxies:
    try:
      #check for H atoms if required
      if not include_hydrogens:
        for i_seq in dp.i_seqs:
          if i_seq_element_hash[i_seq] == " H":
            raise StopIteration()
      #ignore backbone dihedrals
      if not include_main_chain:
        sc_atoms = False
        for i_seq in dp.i_seqs:
          if i_seq_name_hash[i_seq][0:4] not in [' CA ', ' N  ', ' C  ', ' O  ']:
            sc_atoms = True
            break
        if not sc_atoms:
          raise StopIteration()
      if not include_side_chain:
        sc_atoms = False
        for i_seq in dp.i_seqs:
          if i_seq_name_hash[i_seq][0:4] not in [' CA ', ' N  ', ' C  ', ' O  ']:
            sc_atoms = True
            break
        if sc_atoms:
          raise StopIteration()
      key = ""
      for i_seq in dp.i_seqs:
        key = key+i_seq_name_hash[i_seq]
      di = cctbx.geometry_restraints.dihedral(sites_cart=sites_cart, proxy=dp)
      dihedral_hash[key] = di.angle_model
    except StopIteration:
      pass

  #add dihedral for CB
  cbetadev_hash = build_cbetadev_hash(pdb_hierarchy=pdb_hierarchy)
  for cp in geometry.chirality_proxies:
    c_beta = True
    key = ""
    CAxyz = None
    Cxyz = None
    Nxyz = None
    CBxyz = None
    for i_seq in cp.i_seqs:
      key = key+i_seq_name_hash[i_seq]
      if i_seq_name_hash[i_seq][0:4] not in [' CA ', ' N  ', ' C  ', ' CB ']:
        c_beta = False
      if i_seq_name_hash[i_seq][0:4] == ' CA ':
        CAxyz = sites_cart[i_seq]
      elif i_seq_name_hash[i_seq][0:4] == ' C  ':
        Cxyz = sites_cart[i_seq]
      elif i_seq_name_hash[i_seq][0:4] == ' N  ':
        Nxyz = sites_cart[i_seq]
      elif i_seq_name_hash[i_seq][0:4] == ' CB ':
        CBxyz = sites_cart[i_seq]
        if float(cbetadev_hash[i_seq_name_hash[i_seq][4:14]]) >= 0.25:
          c_beta = False
          print "skipping C-beta restraint for %s" % i_seq_name_hash[i_seq][4:14]
    if c_beta:
      assert CAxyz is not None
      assert Cxyz is not None
      assert Nxyz is not None
      assert CBxyz is not None
      sites = [Cxyz, Nxyz, CAxyz, CBxyz]
      d = cctbx.geometry_restraints.dihedral(
        sites=sites,
        angle_ideal=0,
        weight=1)
      dihedral_hash[key] = d.angle_model
  return dihedral_hash

def get_home_dihedral_proxies(work_params,
                              geometry,
                              pdb_hierarchy,
                              geometry_ref,
                              sites_cart_ref,
                              pdb_hierarchy_ref):
  reference_dihedral_proxies = cctbx.geometry_restraints.shared_dihedral_proxy()
  sigma = work_params.sigma
  limit = work_params.limit
  i_seq_name_hash = build_name_hash(pdb_hierarchy=pdb_hierarchy)
  reference_dihedral_hash = build_dihedral_hash(
                         geometry=geometry_ref,
                         sites_cart=sites_cart_ref,
                         pdb_hierarchy=pdb_hierarchy_ref,
                         include_hydrogens=work_params.hydrogens,
                         include_main_chain=work_params.main_chain,
                         include_side_chain=work_params.side_chain)
  for dp in geometry.dihedral_proxies:
    key = ""
    for i_seq in dp.i_seqs:
      key = key+i_seq_name_hash[i_seq]
    try:
      reference_angle = reference_dihedral_hash[key]
    except:
      continue
    dp_add = cctbx.geometry_restraints.dihedral_proxy(
      i_seqs=dp.i_seqs,
      angle_ideal=reference_angle,
      weight=1/sigma**2,
      limit=limit)
    reference_dihedral_proxies.append(dp_add)
  for cp in geometry.chirality_proxies:
    key = ""
    CAsite = None
    Csite = None
    Nsite = None
    CBsite = None
    for i_seq in cp.i_seqs:
      key = key+i_seq_name_hash[i_seq]
      if i_seq_name_hash[i_seq][0:4] == ' CA ':
        CAsite = i_seq
      elif i_seq_name_hash[i_seq][0:4] == ' CB ':
        CBsite = i_seq
      elif i_seq_name_hash[i_seq][0:4] == ' C  ':
        Csite = i_seq
      elif i_seq_name_hash[i_seq][0:4] == ' N  ':
        Nsite = i_seq

    try:
      reference_angle = reference_dihedral_hash[key]
    except:
      continue
    assert CAsite is not None
    assert Csite is not None
    assert CBsite is not None
    assert Nsite is not None
    i_seqs = [Csite, Nsite, CAsite, CBsite]
    dp_add = cctbx.geometry_restraints.dihedral_proxy(
      i_seqs=i_seqs,
      angle_ideal=reference_angle,
      weight=1/sigma**2,
      limit=limit)
    reference_dihedral_proxies.append(dp_add)
  return reference_dihedral_proxies

def add_reference_dihedral_proxies(geometry, reference_dihedral_proxies):
  geometry.reference_dihedral_proxies=reference_dihedral_proxies

def set_rotamer_to_reference(pdb_hierarchy,
                             pdb_hierarchy_ref,
                             xray_structure,
                             quiet=False):
  r = rotalyze()
  sa = SidechainAngles(False)
  mon_lib_srv = mmtbx.monomer_library.server.server()
  rot_list_model, coot_model = r.analyze_pdb(hierarchy=pdb_hierarchy)
  rot_list_reference, coot_reference = r.analyze_pdb(hierarchy=pdb_hierarchy_ref)
  model_hash = {}
  model_chis = {}
  reference_hash = {}
  reference_chis = {}
  for line in rot_list_model.splitlines():
    res, rotamericity, chi1, chi2, chi3, chi4, name = line.split(':')
    model_hash[res]=name

  for line in rot_list_reference.splitlines():
    res, rotamericity, chi1, chi2, chi3, chi4, name = line.split(':')
    reference_hash[res]=name

  for model in pdb_hierarchy.models():
    for chain in model.chains():
      for residue_group in chain.residue_groups():
          all_dict = r.construct_complete_sidechain(residue_group)
          for atom_group in residue_group.atom_groups():
            try:
              atom_dict = all_dict.get(atom_group.altloc)
              chis = sa.measureChiAngles(atom_group, atom_dict)
              if chis is not None:
                key = '%s%4s %s' % (
                    chain.id, residue_group.resseq,
                    atom_group.altloc+atom_group.resname)
                model_chis[key] = chis
            except:
              print '%s%4s %s is missing some sidechain atoms, could not measure chis' % (
                    chain.id, residue_group.resseq,
                    atom_group.altloc+atom_group.resname)

  for model in pdb_hierarchy_ref.models():
    for chain in model.chains():
      for residue_group in chain.residue_groups():
          all_dict = r.construct_complete_sidechain(residue_group)
          for atom_group in residue_group.atom_groups():
            try:
              atom_dict = all_dict.get(atom_group.altloc)
              chis = sa.measureChiAngles(atom_group, atom_dict)
              if chis is not None:
                key = '%s%4s %s' % (
                    chain.id, residue_group.resseq,
                    atom_group.altloc+atom_group.resname)
                reference_chis[key] = chis
            except:
              print '%s%4s %s is missing some sidechain atoms, could not measure chis' % (
                    chain.id, residue_group.resseq,
                    atom_group.altloc+atom_group.resname)

  sites_cart_start = xray_structure.sites_cart()
  for model in pdb_hierarchy.models():
    for chain in model.chains():
      for residue_group in chain.residue_groups():
        for atom_group in residue_group.atom_groups():
          key = '%s%4s %s' % (
                    chain.id, residue_group.resseq,
                    atom_group.altloc+atom_group.resname)
          try:
            if model_hash[key] == 'OUTLIER' and reference_hash[key] != 'OUTLIER':
              axis_and_atoms_to_rotate=fit_rotamers.axes_and_atoms_aa_specific(
                    residue=atom_group,
                    mon_lib_srv=mon_lib_srv,
                    remove_clusters_with_all_h=False,
                    log=None)
              m_chis = model_chis[key]
              r_chis = reference_chis[key]
              assert len(m_chis) == len(r_chis)
              assert len(m_chis) == len(axis_and_atoms_to_rotate)
              counter = 0
              residue_iselection = atom_group.atoms().extract_i_seq()
              sites_cart_residue = xray_structure.sites_cart().select(residue_iselection)
              for aa in axis_and_atoms_to_rotate:
                axis = aa[0]
                atoms = aa[1]
                atom_group.atoms().set_xyz(new_xyz=sites_cart_residue)
                new_xyz = flex.vec3_double()
                angle_deg = r_chis[counter] - m_chis[counter]
                if angle_deg < 0:
                  angle_deg += 360.0
                for atom in atoms:
                  new_xyz = fit_rotamers.rotate_point_around_axis(
                                                      axis_point_1=sites_cart_residue[axis[0]],
                                                      axis_point_2=sites_cart_residue[axis[1]],
                                                      point=sites_cart_residue[atom],
                                                      angle_deg=angle_deg)
                  sites_cart_residue[atom] = new_xyz
                sites_cart_start = sites_cart_start.set_selected(
                      residue_iselection, sites_cart_residue)
                counter += 1
              xray_structure.set_sites_cart(sites_cart_start)
          except:
            pass

  if not quiet:
    for key in model_hash:
      try:
        if model_hash[key] == 'OUTLIER':
          if reference_hash[key] != 'OUTLIER':
            print key, reference_hash[key]
      except:
        pass
