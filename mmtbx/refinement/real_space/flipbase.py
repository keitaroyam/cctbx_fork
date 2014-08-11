from __future__ import division
import os,sys
from iotbx import pdb
from iotbx import reflection_file_reader
from iotbx import file_reader
from mmtbx.secondary_structure import base_pairing
from mmtbx.refinement.real_space import individual_sites
import mmtbx
import libtbx.phil.command_line

master_phil = libtbx.phil.parse("""
flip_base {
  pdb_file = None
    .type = path
    .help = '''input PDB file'''
  reflection_file = None
    .type = path
    .help = '''Reflection file'''
  out_pdb_file = None
    .type = str
    .help = '''input PDB file'''
  chain = None
    .type = str
    .help = '''Chain of the residue that is to be flipped'''
  alt_loc = None
    .type = str
    .help = '''Alternate location of the residue that is to be flipped'''
  res_num = None
    .type = int
    .help = '''Residue number of the residue that is to be flipped'''
  n_refine_cycles = 3
    .type = int
    .help = '''Number of real-space refinement cycles'''
  help = False
    .type = bool
    .help = '''Show help message'''
}
""", process_includes=True)

def usage(msg='', log=sys.stderr) :
  s = '''
******************************************************************************
Usage :
  python.phenix flipbase.py xxxx.mtz yyyy.pdb chain=A res_num=1

Will flip base of chain A residue 1 of yyyy.pdb and do a real-space
refinement using xxxx.mtz.

Required :
  pdb_file           input PDB file
  reflection_file    Reflection file
  chain              Chain of the residue that is to be flipped
  res_num            Residue number of the residue that is to be flipped

Options :
  out_pdb_file       input PDB file
  alt_loc            Alternate location of the residue that is to be flipped
  n_refine_cycles    Number of real-space refinement cycles
  help               Show help message
******************************************************************************

'''
  if msg != '' :
    s = '*'*79 + '\n\n!!!!!  %s  !!!!!\n' % msg + s
  print s;sys.exit()

def get_target_map(reflection_file_name,  log=sys.stderr) :
  miller_arrays = reflection_file_reader.any_reflection_file(file_name =
    reflection_file_name).as_miller_arrays()
  ma = miller_arrays[0]
  fft_map = ma.fft_map(resolution_factor=0.25)
  fft_map.apply_sigma_scaling()
  print >> log, "\nUsing sigma scaled map.\n"
  target_map = fft_map.real_map_unpadded()
  return target_map

def flip_and_refine(pdb_hierarchy,
                    xray_structure,
                    target_map,
                    geometry_restraints_manager,
                    chain,
                    res_num,
                    alt_loc = None,
                    n_refine_cycles = 3,
                    log = sys.stdout) :
  sites_cart = xray_structure.sites_cart()
  ero = False
  for ch in pdb_hierarchy.chains():
    if ch.id.strip() != chain : continue
    for rg in ch.residue_groups():
      if rg.resseq_as_int() != res_num : continue
      if rg.have_conformers() and not alt_loc :
        s = 'Specified residue has alternate conformations. Please specify '
        raise RuntimeError(s + 'alt_loc on the command line')
      for residue in rg.atom_groups():
        if alt_loc and alt_loc != residue.altloc.strip():
          continue
        base_pairing.flip_base(residue, angle=180)

        sites_cart.set_selected(residue.atoms().extract_i_seq(),
          residue.atoms().extract_xyz())
        xray_structure = xray_structure.replace_sites_cart(sites_cart)
        sele = residue.atoms().extract_i_seq()
        print >> log, 'real-space refinement BEGIN'.center(79,'*')
        for i in range(n_refine_cycles):
          print >> log, 'real-space refinement cycle %i...' % (i + 1)
          ero = individual_sites.easy(
            map_data                    = target_map,
            xray_structure              = xray_structure,
            pdb_hierarchy               = pdb_hierarchy,
            geometry_restraints_manager = geometry_restraints_manager,
            selection                   = sele)
        print >> log, 'real-space refinement FINISHED'.center(79,'*')
  if not ero : raise RuntimeError('Specified residue not found')
  return ero.pdb_hierarchy

def run(args) :

  # phil parsing----------------------------------------------------------
  interpreter = libtbx.phil.command_line.argument_interpreter(master_phil=master_phil)
  sources = []
  for arg in args:
    if os.path.isfile(arg): #Handles loose filenames
      input_file = file_reader.any_file(arg)
      if (input_file.file_type == "pdb"):
        sources.append(interpreter.process(arg="pdb_file=\"%s\"" % arg))
      if (input_file.file_type == "hkl"):
        sources.append(interpreter.process(arg="reflection_file=\"%s\"" % arg))
      elif (input_file.file_type == "phil"):
        sources.append(input_file.file_object)
    else: #Handles arguments with xxx=yyy formatting
      arg_phil = interpreter.process(arg=arg)
      sources.append(arg_phil)
  work_phil = master_phil.fetch(sources=sources)
  work_params = work_phil.extract()
  params = work_params.flip_base
  if work_params.flip_base.pdb_file == None :
    usage('PDB file not provided!')
  if work_params.flip_base.reflection_file == None :
    usage('Reflection file not provided!')
  if work_params.flip_base.chain == None :
    usage('chain not provided!')
  if work_params.flip_base.res_num == None :
    usage('res_num file not provided!')
  if work_params.flip_base.out_pdb_file == None :
    fn = work_params.flip_base.pdb_file.replace('.pdb','_baseflip.pdb')
    work_params.flip_base.out_pdb_file = fn
    #usage('out_pdb_file file not provided!')
  params = work_params.flip_base

  if params.help:
    usage()
    sys.exit()
  # end phil parsing ------------------------------------------------------

  pdb_file_name = params.pdb_file
  reflection_file_name = params.reflection_file
  log = sys.stdout
  print >> log, '\ngettinsg target_map...\n'
  target_map = get_target_map(reflection_file_name, log)
  ppf = mmtbx.utils.process_pdb_file_srv(log=False).process_pdb_files(
    [pdb_file_name])[0]
  grm = mmtbx.restraints.manager(
      geometry      = ppf.geometry_restraints_manager(show_energies = False),
      normalization = True)
  pdb_hierarchy  = ppf.all_chain_proxies.pdb_hierarchy
  pdb_hierarchy.atoms().reset_i_seq()
  xray_structure = ppf.xray_structure(show_summary = False)
  flip_hierarchy = flip_and_refine(pdb_hierarchy,
                  xray_structure,
                  target_map = target_map,
                  geometry_restraints_manager = grm,
                  chain = params.chain,
                  res_num = params.res_num,
                  alt_loc = params.alt_loc,
                  n_refine_cycles = params.n_refine_cycles,
                  log= log)

  flip_hierarchy.write_pdb_file(params.out_pdb_file)
  print >> log, '\nOut written to %s' % params.out_pdb_file

if __name__ == "__main__":
  run(sys.argv[1:])
