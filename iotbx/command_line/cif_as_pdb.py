from __future__ import division
import os
import iotbx.pdb
import iotbx.pdb.mmcif

def run(args):
  for file_name in args:
    try:
      assert os.path.exists(file_name)
      cif_input = iotbx.pdb.mmcif.cif_input(file_name=file_name)
      hierarchy = cif_input.construct_hierarchy()
      f = open(file_name+".pdb", "wb")
      print >> f, hierarchy.as_pdb_string(
        crystal_symmetry=cif_input.crystal_symmetry())
      f.close()
    except Exception, e:
      print "Error converting %s to PDB format:" %file_name
      print " ", str(e)
      continue

if __name__ == '__main__':
  import sys
  run(sys.argv[1:])
