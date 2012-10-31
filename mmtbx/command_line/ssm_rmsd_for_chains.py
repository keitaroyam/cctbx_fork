# LIBTBX_SET_DISPATCHER_NAME mmtbx.ssm_rmsd_for_chains
from __future__ import division
import sys
from mmtbx.torsion_restraints import utils
from libtbx.utils import Sorry

def run(args):
  if len(args) != 2:
    raise Sorry("mmtbx.ssm_rmsd_for_chains requires two PDB files as input")
  file1 = args[0]
  file2 = args[1]
  import iotbx.pdb
  pdb1 = iotbx.pdb.input(file_name=file1).construct_hierarchy()
  pdb2 = iotbx.pdb.input(file_name=file2).construct_hierarchy()
  chains1 = []
  chains2 = []

  for model in pdb1.models():
    for i, chain_i in enumerate(model.chains()):
      found_conformer = False
      for conformer in chain_i.conformers():
        if not conformer.is_protein() and not conformer.is_na():
          continue
        else:
          found_conformer = True
      if not found_conformer:
        continue
      chains1.append(chain_i)

  for model in pdb2.models():
    for i, chain_i in enumerate(model.chains()):
      found_conformer = False
      for conformer in chain_i.conformers():
        if not conformer.is_protein() and not conformer.is_na():
          continue
        else:
          found_conformer = True
      if not found_conformer:
        continue
      chains2.append(chain_i)

  print "### SSM RMSD for chains"
  print
  print "PDB_1 = %s" % file1
  print "PDB_2 = %s" % file2
  print
  print "PDB_1 chainID     PDB_2 chainID     SSM RMSD"
  print "--------------------------------------------"
  for i, chain_i in enumerate(chains1):
    for j, chain_j in enumerate(chains2):
      ssm = None
      try: #do SSM alignment
        ssm, ssm_align = utils._ssm_align(
                           reference_chain = chain_i,
                           moving_chain = chain_j)
      except RuntimeError, e:
        if (str(e) != "can't make graph for first structure" and \
            str(e) != "secondary structure does not match"):
          raise e
      if ssm is not None:
        print "%13s"%chain_i.id, "%17s"%chain_j.id, "%12.3f"%ssm.ssm.rmsd
      else:
        print "%13s"%chain_i.id, "%17s"%chain_j.id, "%12s"% ("None")

if __name__ == "__main__":
  run(args=sys.argv[1:])
