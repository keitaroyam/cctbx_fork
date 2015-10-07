
from __future__ import division
import os
from mmtbx.validation import restraints
from mmtbx.monomer_library import server, pdb_interpretation
import iotbx.phil
from cStringIO import StringIO

def get_master_phil():
  return iotbx.phil.parse(
    input_string="""
  mp_geo {
    pdb = None
      .type = path
    out_file = None
      .type = path
    bonds_and_angles = False
      .type = bool
    kinemage = False
      .type = bool
    rna_backbone = False
      .type = bool
    outliers_only = False
      .type = bool
    cdl = False
      .type = bool
  }
  """,process_includes=True)

def get_bond_and_angle_outliers(
      pdb_hierarchy,
      xray_structure,
      geometry_restraints_manager,
      use_segids,
      outliers_only=False,
      type=None):
  rc = restraints.combined(
         pdb_hierarchy=pdb_hierarchy,
         xray_structure=xray_structure,
         geometry_restraints_manager=geometry_restraints_manager,
         ignore_hd=True,
         outliers_only=outliers_only,
         use_segids_in_place_of_chainids=use_segids)
  return rc

def get_atoms_str(atoms_info):
  return_str = ""
  connector = ""
  # bond
  if len(atoms_info) == 2:
    connector = '--'
  # angle
  elif len(atoms_info) == 3:
    connector = '-'
  for atom_info in atoms_info:
    return_str = return_str+atom_info.name.strip()+connector
  return return_str.strip('-')

def get_altloc(atoms_info):
  altloc = ' '
  for atom_info in atoms_info:
    if altloc == ' ':
      if atom_info.altloc != '':
        altloc = atom_info.altloc
  return altloc

def run(args):
  master_phil = get_master_phil()
  import iotbx.utils
  input_objects = iotbx.utils.process_command_line_inputs(
    args=args,
    master_phil=master_phil,
      input_types=("pdb",))
  work_phil = master_phil.fetch(sources=input_objects["phil"])
  work_params = work_phil.extract()
  file_name = work_params.mp_geo.pdb
  out_file = None
  if work_params.mp_geo.out_file != None:
    out_file = work_params.mp_geo.out_file
  do_bonds_and_angles = work_params.mp_geo.bonds_and_angles
  do_kinemage = work_params.mp_geo.kinemage
  do_rna_backbone = work_params.mp_geo.rna_backbone
  outliers_only = work_params.mp_geo.outliers_only
  use_cdl = work_params.mp_geo.cdl
  log = StringIO()
  basename = os.path.basename(file_name)
  if do_bonds_and_angles:
    out = file(out_file, 'w')
  elif do_kinemage:
    out = file(out_file, 'a')
  elif do_rna_backbone:
    if out_file == None:
      import sys
      out = sys.stdout
    else:
      out = file(out_file, 'w')
  restraints_loading_flags = {}
  restraints_loading_flags["use_neutron_distances"]=False
  from mmtbx.validation import utils
  params = pdb_interpretation.master_params.extract()
  params.restraints_library.cdl = use_cdl
  params.clash_guard.nonbonded_distance_threshold = None
  processed_pdb_file = pdb_interpretation.process(
    params                   = params,
    mon_lib_srv              = server.server(),
    ener_lib                 = server.ener_lib(),
    file_name                = file_name,
    strict_conflict_handling = True,
    restraints_loading_flags = restraints_loading_flags,
    force_symmetry           = True,
    substitute_non_crystallographic_unit_cell_if_necessary=True,
    log                      = log)
  grm = processed_pdb_file.geometry_restraints_manager()
  use_segids = utils.use_segids_in_place_of_chainids(
                 hierarchy=processed_pdb_file.all_chain_proxies.pdb_hierarchy)
  if do_bonds_and_angles or do_kinemage:
    rc = get_bond_and_angle_outliers(
           pdb_hierarchy=processed_pdb_file.all_chain_proxies.pdb_hierarchy,
           xray_structure=processed_pdb_file.xray_structure(),
           geometry_restraints_manager=grm,
           use_segids=use_segids,
           outliers_only=outliers_only)
    #get chain types
    chain_types = {}
    for chain in processed_pdb_file.all_chain_proxies.\
                   pdb_hierarchy.models()[0].chains() :
      if use_segids:
        chain_id = utils.get_segid_as_chainid(chain=chain)
      else:
        chain_id = chain.id
      main_conf = chain.conformers()[0]
      if chain_types.get(chain_id) not in ["NA", "PROTEIN"]:
        if (main_conf.is_na()) :
          chain_types[chain_id] = "NA"
        elif (main_conf.is_protein()):
          chain_types[chain_id] = "PROTEIN"
        else:
          chain_types[chain_id] = "UNK"
    outliers = []
    #bonds
    for result in rc.bonds.results:
      atom_info = result.atoms_info[0]
      # label:chain:number:ins:alt:type:measure:value:sigmas:class
      atoms_str = get_atoms_str(atoms_info=result.atoms_info)
      altloc = get_altloc(atoms_info=result.atoms_info)
      chain_id = atom_info.chain_id
      outliers.append( [chain_id,
                        atom_info.resseq,
                        atom_info.icode,
                        altloc,
                        atom_info.resname,
                        atoms_str,
                        result.model,
                        result.score,
                        chain_types[atom_info.chain_id]] )
    #angles
    for result in rc.angles.results:
      atom_info = result.atoms_info[0]
      # label:chain:number:ins:alt:type:measure:value:sigmas:class
      atoms_str = get_atoms_str(atoms_info=result.atoms_info)
      altloc = get_altloc(atoms_info=result.atoms_info)
      chain_id = atom_info.chain_id
      outliers.append( [chain_id,
                        atom_info.resseq,
                        atom_info.icode,
                        altloc,
                        atom_info.resname,
                        atoms_str,
                        result.model,
                        result.score,
                        chain_types[atom_info.chain_id]] )

    if do_bonds_and_angles:
      for outlier in outliers:
        print >> out, "%s:%2s:%s:%s:%s:%s:%s:%.3f:%.3f:%s" % (
          basename, outlier[0], outlier[1], outlier[2], outlier[3],
          outlier[4], outlier[5], outlier[6], outlier[7], outlier[8])
    elif do_kinemage:
      print >> out, rc.bonds.kinemage_header
      for result in rc.bonds.results:
        print >> out, result.as_kinemage()
      print >> out, rc.angles.kinemage_header
      for result in rc.angles.results:
        print >> out, result.as_kinemage()
    out.close()
  elif do_rna_backbone:
    from mmtbx.validation import utils
    rna_bb = utils.get_rna_backbone_dihedrals(processed_pdb_file)
    print >> out, rna_bb
    if out_file is not None:
      out.close()
