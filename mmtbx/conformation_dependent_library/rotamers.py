
from __future__ import division
import sys
import time

from mmtbx.conformation_dependent_library.rdl_database import rdl_database

from mmtbx.validation import rotalyze

def get_rotamer_data(atom_group,
                     sa,
                     rotamer_evaluator,
                     rotamer_id,
                     all_dict,
                     sites_cart,
                     ):
  if atom_group.resname not in rdl_database.keys(): return None
  if atom_group.resname in ["PRO", "GLY"]: return None
  model_rot, m_chis, value = rotalyze.evaluate_rotamer(
    atom_group=atom_group,
    sidechain_angles=sa,
    rotamer_evaluator=rotamer_evaluator,
    rotamer_id=rotamer_id,
    all_dict=all_dict,
    sites_cart=sites_cart,
    )
  return model_rot, m_chis, value

def setup_restraints():
  return None

def generate_rotamer_data(pdb_hierarchy,
                          exclude_outliers=True,
                          data_version="500",
                          ):
  r = rotalyze.rotalyze(pdb_hierarchy=pdb_hierarchy,
                        data_version=data_version)
  for rot in r.results:
    #if rot.outlier:
    #  print (rot.resname,
    #       rot.id_str(),
    #       rot.chain_id,
    #       rot.altloc,
    #       rot.rotamer_name)
    #  assert 0
    if exclude_outliers and rot.outlier: continue
    yield (rot.resname,
           rot.id_str(),
           rot.chain_id,
           rot.altloc,
           rot.rotamer_name)

def adjust_rotamer_restraints(pdb_hierarchy,
                              geometry_restraints_manager,
                              i_seqs_restraints=None,
                              log=None,
                              verbose=False,
                              data_version="500",
                              ):
  assert 0
  if log is None: log = sys.stdout
  t0=time.time()
  print >> log, "  Rotamer Conformation Library"
  def _get_i_seqs_restraints(pdb_hierarchy):
    name_restraints = {}
    chains=[]
    residues=[]
    for item in generate_rotamer_data(pdb_hierarchy=pdb_hierarchy,
                                      data_version=data_version):
      resname, id_str, chain, altloc, rotamer = item
      if resname not in rdl_database: continue
      if rotamer not in rdl_database[resname]: continue
      if verbose:
        print "resn %s chain %s id %s altloc %s rotamer %s" % (resname,
                                                               chain,
                                                               id_str,
                                                               altloc,
                                                               rotamer,
                                                               )
      restraints = rdl_database[resname][rotamer]
      defaults = rdl_database[resname]["default"]
      name_restraints[id_str] = (chain,
                                resname,
                                altloc,
                                restraints,
                                defaults,
        )
      chains.append(chain)
      residues.append(resname)
    #
    i_seqs_restraints = {}
    i_seqs_restraints_reversal = {}
    #
    for model in pdb_hierarchy.models():
      #if verbose: print 'model: "%s"' % model.id
      for chain in model.chains():
        if chain.id.strip() not in chains: continue
        #if verbose: print 'chain: "%s"' % chain.id
        for conformer in chain.conformers():
          #if verbose: print '  conformer: altloc="%s" only_residue="%s"' % (
          #  conformer.altloc, conformer.only_residue)
          for residue in conformer.residues():
            if residue.resname not in residues: continue
            #if verbose:
            #  if residue.resname not in ["HOH"]:
            #    print '    residue: resname="%s" resid="%s"' % (
            #      residue.resname, residue.resid())
            #    for atom in residue.atoms():
            #      if verbose: print '         atom: name="%s"' % (atom.name)
            for id_str, values in name_restraints.items():
              chain_id, resname, altloc, restraints, defaults = values
              if chain_id.strip()!=chain.id: continue
              if resname.strip() !=residue.resname.strip(): continue
              if altloc.strip()  !=conformer.altloc.strip(): continue
              for names, values in restraints.items():
                i_seqs = []
                for name in names:
                  for atom in residue.atoms():
                    if name.strip()==atom.name.strip():
                      i_seqs.append(atom.i_seq)
                      break
                i_seqs_restraints[tuple(i_seqs)] = values
                i_seqs_restraints_reversal[tuple(i_seqs)] = defaults[names]
                i_seqs.reverse()
                i_seqs_restraints[tuple(i_seqs)] = values
                i_seqs_restraints_reversal[tuple(i_seqs)] = defaults[names]
    return i_seqs_restraints, i_seqs_restraints_reversal
  #
  i_seqs_restraints_reversal = None
  if i_seqs_restraints is None:
    i_seqs_restraints, i_seqs_restraints_reversal = _get_i_seqs_restraints(
      pdb_hierarchy,
      )
  count = 0
  if verbose:
    atoms = pdb_hierarchy.atoms()
  for angle_proxy in geometry_restraints_manager.angle_proxies:
    if angle_proxy.i_seqs in i_seqs_restraints:
      if verbose: print " i_seqs %-15s initial %12.3f %12.3f :%s-%s-%s" % (
          angle_proxy.i_seqs,
          angle_proxy.angle_ideal,
          angle_proxy.weight,
          atoms[angle_proxy.i_seqs[0]].quote()[11:-12],
          atoms[angle_proxy.i_seqs[1]].quote()[11:-12],
          atoms[angle_proxy.i_seqs[2]].quote()[11:-12],
        )
      angle_proxy.angle_ideal = i_seqs_restraints[angle_proxy.i_seqs][0]
      angle_proxy.weight = 1/i_seqs_restraints[angle_proxy.i_seqs][1]**2
      if verbose: print " i_seqs %-15s final   %12.3f %12.3f" % (
        angle_proxy.i_seqs,
        angle_proxy.angle_ideal,
        angle_proxy.weight,
        )
      count += 1
  print >> log, "    Number of angles RDL adjusted : %d" % count
  print >> log, "    Time to adjust                : %0.3f" % (time.time()-t0)
  return i_seqs_restraints, i_seqs_restraints_reversal

def update_restraints(hierarchy,
                      geometry, # restraints_manager,
                      current_geometry=None, # xray_structure!!
                      sites_cart=None,
                      rdl_proxies=None,
                      esd_factor=1.,
                      exclude_backbone=False,
                      log=None,
                      verbose=False,
                      data_version="500",
                      ):
  from mmtbx.rotamer.sidechain_angles import SidechainAngles
  from mmtbx.rotamer import rotamer_eval
  from mmtbx.validation import rotalyze
  #
  def _set_or_reset_angle_restraints(geometry,
                                     lookup,
                                     verbose=False,
                                     ):
    count = 0
    for angle_proxy in geometry.angle_proxies:
      if angle_proxy.i_seqs in lookup:
        if verbose: print " i_seqs %-15s initial %12.3f %12.3f" % (
          angle_proxy.i_seqs,
          angle_proxy.angle_ideal,
          angle_proxy.weight,
          )
        angle_proxy.angle_ideal = lookup[angle_proxy.i_seqs][0]
        angle_proxy.weight = esd_factor/lookup[angle_proxy.i_seqs][1]**2
        if verbose: print " i_seqs %-15s final   %12.3f %12.3f" % (
          angle_proxy.i_seqs,
          angle_proxy.angle_ideal,
          angle_proxy.weight,
          )
        count += 1
    return count
  #
  def _set_or_reset_dihedral_restraints(geometry,
                                        lookup,
                                        verbose=False,
                                        ):
    count = 0
    for angle_proxy in geometry.dihedral_proxies:
      if angle_proxy.i_seqs in lookup:
        if verbose: print " i_seqs %-15s initial %12.3f %12.3f %d" % (
          angle_proxy.i_seqs,
          angle_proxy.angle_ideal,
          angle_proxy.weight,
          angle_proxy.periodicity,
          )
        angle_proxy.angle_ideal = lookup[angle_proxy.i_seqs][0]
        angle_proxy.weight = esd_factor/lookup[angle_proxy.i_seqs][1]**2
        angle_proxy.periodicity = lookup[angle_proxy.i_seqs][2]
        if verbose: print " i_seqs %-15s final   %12.3f %12.3f %d" % (
          angle_proxy.i_seqs,
          angle_proxy.angle_ideal,
          angle_proxy.weight,
          angle_proxy.periodicity,
          )
        count += 1
    return count
  #
  t0=time.time()
  sa = SidechainAngles(False)
  rotamer_id = rotamer_eval.RotamerID()
  rotamer_evaluator = rotamer_eval.RotamerEval(data_version=data_version)
  sites_cart = None
  if current_geometry:
    sites_cart = current_geometry.sites_cart()
  #
  if rdl_proxies is None:
    rdl_proxies = []
  i_seqs_restraints = {}
  i_seqs_restraints_reverse = {}
  #
  for model in hierarchy.models():
    if verbose: print 'model: "%s"' % model.id
    for chain in model.chains():
      if verbose: print 'chain: "%s"' % chain.id
      for residue_group in chain.residue_groups():
        all_dict = rotalyze.construct_complete_sidechain(residue_group)
        for atom_group in residue_group.atom_groups():
          rc = get_rotamer_data(atom_group,
                                sa,
                                rotamer_evaluator,
                                rotamer_id,
                                all_dict=all_dict,
                                sites_cart=sites_cart,
            )
          if rc is None: continue
          rotamer_name, chis, value = rc
          if rotamer_name not in rdl_database[atom_group.resname]: continue
          restraints = rdl_database[atom_group.resname][rotamer_name]
          defaults = rdl_database[atom_group.resname]["default"]
          rdl_proxies.append(atom_group.id_str())
          for names, values in restraints.items():
            i_seqs = []
            if exclude_backbone and names[1] in ["N", "CA", "C"]: continue
            for name in names:
              for atom in atom_group.atoms():
                if name.strip()==atom.name.strip():
                  i_seqs.append(atom.i_seq)
                  break
            i_seqs_restraints[tuple(i_seqs)] = values
            if names in defaults:
              i_seqs_restraints_reverse[tuple(i_seqs)] = defaults[names]
  #
  count = _set_or_reset_dihedral_restraints(geometry,
                                            i_seqs_restraints_reverse,
                                            )
  count = _set_or_reset_dihedral_restraints(geometry,
                                            i_seqs_restraints,
                                            )
  count = _set_or_reset_angle_restraints(geometry,
                                         i_seqs_restraints_reverse,
                                         )
  count = _set_or_reset_angle_restraints(geometry,
                                         i_seqs_restraints,
                                         )
  #
  print >> log, "    Number of angles RDL adjusted : %d" % count
  print >> log, "    Time to adjust                : %0.3f" % (time.time()-t0)
  return rdl_proxies

def run(pdb_filename):
  from iotbx import pdb
  print pdb_filename
  pdb_inp = pdb.input(pdb_filename)
  pdb_hieratchy = pdb_inp.construct_hierarchy()
  for residue_group in pdb_hieratchy.residue_groups():
    rotamer_name, chis, value = get_rotamer_data(residue_group,
                                                 sa,
                                                 rotamer_evaluator,
                                                 rotamer_id,
      )
    print rotamer_name

if __name__=="__main__":
  run(sys.argv[1])
