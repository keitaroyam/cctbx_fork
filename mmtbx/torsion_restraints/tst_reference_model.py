from __future__ import division
from mmtbx import monomer_library
from mmtbx.torsion_restraints.reference_model import reference_model
from mmtbx.torsion_restraints import utils
from mmtbx.validation.rotalyze import rotalyze
from cctbx.array_family import flex
import iotbx.phil
import iotbx.utils
import iotbx.pdb
import libtbx.load_env
import cStringIO
import sys, os, time

model_raw_records = """\
CRYST1   41.566   72.307   92.870 108.51  93.02  90.06 P 1           4
ATOM   5466  N   ASN C 236      17.899  72.943  29.028  1.00 60.13           N
ATOM   5467  CA  ASN C 236      16.519  72.435  29.114  1.00 60.52           C
ATOM   5468  C   ASN C 236      16.377  70.925  29.327  1.00 60.49           C
ATOM   5469  O   ASN C 236      15.429  70.294  28.863  1.00 60.60           O
ATOM   5470  CB  ASN C 236      15.689  72.896  27.916  1.00 60.55           C
ATOM   5471  CG  ASN C 236      14.357  73.447  28.338  1.00 61.75           C
ATOM   5472  OD1 ASN C 236      14.256  74.609  28.768  1.00 62.86           O
ATOM   5473  ND2 ASN C 236      13.319  72.616  28.247  1.00 61.22           N
ATOM   5474  N   LEU C 237      17.316  70.364  30.068  1.00 60.55           N
ATOM   5475  CA  LEU C 237      17.444  68.931  30.166  1.00 60.48           C
ATOM   5476  C   LEU C 237      17.815  68.555  31.581  1.00 60.06           C
ATOM   5477  O   LEU C 237      17.335  67.547  32.097  1.00 60.41           O
ATOM   5478  CB  LEU C 237      18.518  68.464  29.178  1.00 60.91           C
ATOM   5479  CG  LEU C 237      18.542  67.095  28.491  1.00 62.25           C
ATOM   5480  CD1 LEU C 237      17.407  66.153  28.923  1.00 63.18           C
ATOM   5481  CD2 LEU C 237      18.563  67.309  26.965  1.00 62.89           C
"""

reference_raw_records = """\
CRYST1   40.688   71.918   93.213 108.16  93.25  90.40 P 1           4
ATOM   5485  N   ASN C 236      16.417  72.834  29.095  1.00  7.17           N
ATOM   5486  CA  ASN C 236      15.051  72.312  29.173  1.00  7.74           C
ATOM   5487  C   ASN C 236      15.000  70.818  29.431  1.00  7.38           C
ATOM   5488  O   ASN C 236      14.047  70.141  29.024  1.00  7.80           O
ATOM   5489  CB  ASN C 236      14.281  72.645  27.887  1.00  8.78           C
ATOM   5490  CG  ASN C 236      12.769  72.657  28.088  1.00 13.44           C
ATOM   5491  OD1 ASN C 236      12.265  73.196  29.082  1.00 20.19           O
ATOM   5492  ND2 ASN C 236      12.032  72.114  27.109  1.00 16.07           N
ATOM   5493  N   LEU C 237      16.010  70.282  30.134  1.00  6.60           N
ATOM   5494  CA  LEU C 237      16.122  68.825  30.270  1.00  7.41           C
ATOM   5495  C   LEU C 237      16.481  68.430  31.697  1.00  6.01           C
ATOM   5496  O   LEU C 237      15.944  67.448  32.224  1.00  6.47           O
ATOM   5497  CB  LEU C 237      17.151  68.239  29.297  1.00  8.10           C
ATOM   5498  CG  LEU C 237      17.384  66.726  29.347  1.00 10.94           C
ATOM   5499  CD1 LEU C 237      16.055  65.956  29.107  1.00 13.10           C
ATOM   5500  CD2 LEU C 237      18.455  66.271  28.343  1.00 11.63           C
"""

reference_raw_records_alt_seq = """\
CRYST1   40.688   71.918   93.213 108.16  93.25  90.40 P 1           4
ATOM   5485  N   ASN B 246      16.417  72.834  29.095  1.00  7.17           N
ATOM   5486  CA  ASN B 246      15.051  72.312  29.173  1.00  7.74           C
ATOM   5487  C   ASN B 246      15.000  70.818  29.431  1.00  7.38           C
ATOM   5488  O   ASN B 246      14.047  70.141  29.024  1.00  7.80           O
ATOM   5489  CB  ASN B 246      14.281  72.645  27.887  1.00  8.78           C
ATOM   5490  CG  ASN B 246      12.769  72.657  28.088  1.00 13.44           C
ATOM   5491  OD1 ASN B 246      12.265  73.196  29.082  1.00 20.19           O
ATOM   5492  ND2 ASN B 246      12.032  72.114  27.109  1.00 16.07           N
ATOM   5493  N   LEU B 247      16.010  70.282  30.134  1.00  6.60           N
ATOM   5494  CA  LEU B 247      16.122  68.825  30.270  1.00  7.41           C
ATOM   5495  C   LEU B 247      16.481  68.430  31.697  1.00  6.01           C
ATOM   5496  O   LEU B 247      15.944  67.448  32.224  1.00  6.47           O
ATOM   5497  CB  LEU B 247      17.151  68.239  29.297  1.00  8.10           C
ATOM   5498  CG  LEU B 247      17.384  66.726  29.347  1.00 10.94           C
ATOM   5499  CD1 LEU B 247      16.055  65.956  29.107  1.00 13.10           C
ATOM   5500  CD2 LEU B 247      18.455  66.271  28.343  1.00 11.63           C
"""

reference_raw_records_match = """\
CRYST1   40.688   71.918   93.213 108.16  93.25  90.40 P 1           4
ATOM   5485  N   ASN C 270      16.417  72.834  29.095  1.00  7.17           N
ATOM   5486  CA  ASN C 270      15.051  72.312  29.173  1.00  7.74           C
ATOM   5487  C   ASN C 270      15.000  70.818  29.431  1.00  7.38           C
ATOM   5488  O   ASN C 270      14.047  70.141  29.024  1.00  7.80           O
ATOM   5489  CB  ASN C 270      14.281  72.645  27.887  1.00  8.78           C
ATOM   5490  CG  ASN C 270      12.769  72.657  28.088  1.00 13.44           C
ATOM   5491  OD1 ASN C 270      12.265  73.196  29.082  1.00 20.19           O
ATOM   5492  ND2 ASN C 270      12.032  72.114  27.109  1.00 16.07           N
ATOM   5493  N   ALA C 271      16.010  70.282  30.134  1.00  6.60           N
ATOM   5494  CA  ALA C 271      16.122  68.825  30.270  1.00  7.41           C
ATOM   5495  C   ALA C 271      16.481  68.430  31.697  1.00  6.01           C
ATOM   5496  O   ALA C 271      15.944  67.448  32.224  1.00  6.47           O
ATOM   5497  CB  ALA C 271      17.151  68.239  29.297  1.00  8.10           C
"""

def get_master_phil():
  return iotbx.phil.parse(
    input_string="""\
reference_model
{
  include \
    scope mmtbx.torsion_restraints.reference_model.reference_model_params
}
""", process_includes=True)

def exercise_reference_model(args, mon_lib_srv, ener_lib):
  log = cStringIO.StringIO()
  master_phil = get_master_phil()
  input_objects = iotbx.utils.process_command_line_inputs(
    args=args,
    master_phil=master_phil,
    input_types=("mtz", "pdb", "cif"))
  work_phil = master_phil.fetch(sources=input_objects["phil"])
  master_phil_str_overrides = """
  reference_model {
    fix_outliers=False
  }
  """
  phil_objects = [
    iotbx.phil.parse(input_string=master_phil_str_overrides)]
  work_params = master_phil.fetch(sources=phil_objects).extract()
  pdb_hierarchy = iotbx.pdb.input(
    source_info=None,
    lines=flex.split_lines(model_raw_records)).construct_hierarchy()
  reference_hierarchy_list = []
  tmp_hierarchy = iotbx.pdb.input(
    source_info=None,
    lines=flex.split_lines(reference_raw_records)).construct_hierarchy()

  reference_hierarchy_list.append(tmp_hierarchy)
  rm = reference_model(
         pdb_hierarchy=pdb_hierarchy,
         reference_hierarchy_list=reference_hierarchy_list,
         params=work_params.reference_model,
         log=log)
  assert len(rm.reference_dihedral_proxies) == 7

  reference_hierarchy_list_alt_seq = []
  tmp_hierarchy = iotbx.pdb.input(
    source_info=None,
    lines=flex.split_lines(reference_raw_records_alt_seq)).\
            construct_hierarchy()
  reference_hierarchy_list_alt_seq.append(tmp_hierarchy)
  reference_hierarchy_list_ref_match = []
  tmp_hierarchy = iotbx.pdb.input(
    source_info=None,
    lines=flex.split_lines(reference_raw_records_match)).\
            construct_hierarchy()
  reference_hierarchy_list_ref_match.append(tmp_hierarchy)

  i_seq_name_hash = utils.build_name_hash(
    pdb_hierarchy=pdb_hierarchy)
  assert i_seq_name_hash == \
    {0: ' N   ASN C 236     ', 1: ' CA  ASN C 236     ',
     2: ' C   ASN C 236     ', 3: ' O   ASN C 236     ',
     4: ' CB  ASN C 236     ', 5: ' CG  ASN C 236     ',
     6: ' OD1 ASN C 236     ', 7: ' ND2 ASN C 236     ',
     8: ' N   LEU C 237     ', 9: ' CA  LEU C 237     ',
     10: ' C   LEU C 237     ', 11: ' O   LEU C 237     ',
     12: ' CB  LEU C 237     ', 13: ' CG  LEU C 237     ',
     14: ' CD1 LEU C 237     ', 15: ' CD2 LEU C 237     '}
  i_seq_element_hash = utils.build_element_hash(
    pdb_hierarchy=pdb_hierarchy)
  assert i_seq_element_hash == \
    {0: ' N', 1: ' C', 2: ' C', 3: ' O', 4: ' C', 5: ' C', 6: ' O', 7: ' N',
     8: ' N', 9: ' C', 10: ' C', 11: ' O', 12: ' C', 13: ' C', 14: ' C',
     15: ' C'}

  ref_pdb_hierarchy = reference_hierarchy_list[0]
  dihedral_proxies = \
    utils.get_complete_dihedral_proxies(pdb_hierarchy=ref_pdb_hierarchy)
  sites_cart_ref = ref_pdb_hierarchy.atoms().extract_xyz()
  dihedral_hash = rm.build_dihedral_hash(
    dihedral_proxies=dihedral_proxies,
    sites_cart=sites_cart_ref,
    pdb_hierarchy=ref_pdb_hierarchy,
    include_hydrogens=False,
    include_main_chain=True,
    include_side_chain=True)
  assert len(dihedral_hash) == 7
  reference_dihedral_proxies = rm.reference_dihedral_proxies.deep_copy()
  assert reference_dihedral_proxies is not None
  assert len(reference_dihedral_proxies) == len(dihedral_hash)
  for rdp in reference_dihedral_proxies:
    assert rdp.limit == work_params.reference_model.limit

  r = rotalyze()
  rot_list_model, coot_model = \
    r.analyze_pdb(
      hierarchy=pdb_hierarchy)
  rot_list_reference, coot_reference = \
    r.analyze_pdb(
      hierarchy=ref_pdb_hierarchy)

  assert rot_list_model == """\
C 236  ASN:1.00:1.2:227.3:80.2:::t30
C 237  LEU:1.00:0.0:209.6:357.2:::OUTLIER"""

  assert rot_list_reference == """\
C 236  ASN:1.00:41.4:203.2:43.6:::t30
C 237  LEU:1.00:52.8:179.1:57.3:::tp"""

  xray_structure = pdb_hierarchy.extract_xray_structure()
  rm.set_rotamer_to_reference(
    xray_structure=xray_structure,
    quiet=True)
  pdb_hierarchy.adopt_xray_structure(xray_structure)
  rot_list_model, coot_model = \
    r.analyze_pdb(
      hierarchy=pdb_hierarchy)
  assert rot_list_model == """\
C 236  ASN:1.00:1.2:227.3:80.2:::t30
C 237  LEU:1.00:52.8:179.1:57.3:::tp"""

  match_map = rm.match_map['ref1']
  assert match_map == \
  {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11,
   12: 12, 13: 13, 14: 14, 15: 15}

  master_phil_str_overrides = """
  reference_model.reference_group {
    reference= chain B and resseq 246:247
    selection= chain C and resid 236:237
  }
  """
  phil_objects = [
    iotbx.phil.parse(input_string=master_phil_str_overrides)]
  work_params_alt = master_phil.fetch(sources=phil_objects).extract()
  rm = reference_model(
         pdb_hierarchy=pdb_hierarchy,
         reference_hierarchy_list=reference_hierarchy_list_alt_seq,
         params=work_params_alt.reference_model,
         log=log)
  match_map = rm.match_map
  assert match_map['ref1'] == \
  {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11,
   12: 12, 13: 13, 14: 14, 15: 15}

  pdb_file = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/pdb/1ywf.pdb",
    test=os.path.isfile)
  pdb_hierarchy = iotbx.pdb.input(file_name=pdb_file).construct_hierarchy()
  reference_file_list = []
  reference_file_list.append(pdb_file)
  work_phil = master_phil.fetch(sources=input_objects["phil"])
  master_phil_str_overrides = """
  reference_model {
    fix_outliers=False
  }
  """
  phil_objects = [
    iotbx.phil.parse(input_string=master_phil_str_overrides)]
  work_params = master_phil.fetch(sources=phil_objects).extract()
  rm = reference_model(
         pdb_hierarchy=pdb_hierarchy,
         reference_file_list=reference_file_list,
         params=work_params.reference_model,
         log=log)
  reference_dihedral_proxies = rm.reference_dihedral_proxies
  standard_weight = 0
  for dp in reference_dihedral_proxies:
    if dp.weight == 1.0:
      standard_weight += 1
  assert standard_weight == 1181
  if (not libtbx.env.has_module(name="ksdssp")):
    print "Skipping KSDSSP tests: ksdssp module not available."
  else:
    master_phil_str_overrides = """
    reference_model {
      secondary_structure_only = True
    }
    """
    phil_objects = [
      iotbx.phil.parse(input_string=master_phil_str_overrides)]
    work_params_ss = master_phil.fetch(sources=phil_objects).extract()
    rm.params = work_params_ss.reference_model
    rm.get_reference_dihedral_proxies()
    reference_dihedral_proxies = rm.reference_dihedral_proxies
    ss_weight = 0
    for dp in reference_dihedral_proxies:
      if dp.weight == 1.0:
        ss_weight += 1
    assert ss_weight == 694

  #test SSM alignment
  pdb_file = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/ncs/rnase-s.pdb",
    test=os.path.isfile)
  pdb_hierarchy = iotbx.pdb.input(file_name=pdb_file).construct_hierarchy()
  reference_file_list = []
  reference_file_list.append(pdb_file)
  pdb_hierarchy.reset_i_seq_if_necessary()

  import ccp4io_adaptbx
  ssm = ccp4io_adaptbx.SecondaryStructureMatching(
    reference=pdb_hierarchy.models()[0].chains()[0],
    moving=pdb_hierarchy.models()[0].chains()[1])
  alignment = ccp4io_adaptbx.SSMAlignment.residue_groups(match=ssm)
  assert ssm.GetQvalues()[0] > 0.98

def run(args):
  t0 = time.time()
  import mmtbx.monomer_library
  mon_lib_srv = mmtbx.monomer_library.server.server()
  ener_lib = mmtbx.monomer_library.server.ener_lib()
  exercise_reference_model(args, mon_lib_srv, ener_lib)
  print "OK. Time: %8.3f"%(time.time()-t0)

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
