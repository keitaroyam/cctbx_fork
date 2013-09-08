
from __future__ import division
from libtbx.utils import Sorry
import time
import sys

def run (args, out=sys.stdout) :
  from mmtbx.secondary_structure import dssp
  from iotbx.file_reader import any_file
  import iotbx.phil
  cmdline = iotbx.phil.process_command_line_with_files(
    args=args,
    master_phil=dssp.master_phil,
    pdb_file_def="file_name")
  params = cmdline.work.extract()
  if (params.file_name is None) :
    raise Sorry("Please specify a PDB file.")
  f = any_file(params.file_name, force_type="pdb")
  pdb_hierarchy = f.file_object.construct_hierarchy()
  xray_structure = f.file_object.xray_structure_simple()
  pdb_atoms = pdb_hierarchy.atoms()
  pdb_atoms.reset_i_seq()
  t1 = time.time()
  SS = dssp.dssp(
    pdb_hierarchy=pdb_hierarchy,
    pdb_atoms=pdb_atoms,
    xray_structure=xray_structure,
    params=params,
    out=out,
    log=sys.stderr)
  t2 = time.time()
  #print "runtime: %.3fs" % (t2-t1)
  return SS

if (__name__ == "__main__") :
  run(sys.argv[1:])
