
from __future__ import division
from libtbx.utils import null_out
from cStringIO import StringIO
import os.path

def exercise_model_only () :
  from mmtbx.building import extend_sidechains
  import iotbx.pdb.hierarchy
  pdb_in = iotbx.pdb.hierarchy.input(pdb_string="""
ATOM     65  N   LYS A   7       6.033   4.704   1.582  1.00 17.49           N
ATOM     66  CA  LYS A   7       5.159   5.427   2.499  1.00 18.23           C
ATOM     67  C   LYS A   7       4.673   4.437   3.507  1.00 14.78           C
ATOM     68  O   LYS A   7       4.777   3.208   3.297  1.00 15.83           O
ATOM     69  CB  LYS A   7       3.959   6.057   1.760  1.00 23.56           C
ATOM     70  CG  LYS A   7       4.345   7.215   0.830  1.00 33.58           C
ATOM     71  CD  LYS A   7       3.213   7.570  -0.123  1.00 41.39           C
ATOM     72  CE  LYS A   7       2.976   6.471  -1.165  1.00 48.81           C
""")
  extend_sidechains.extend_protein_model(
    pdb_hierarchy=pdb_in.hierarchy,
    modify_segids=False,
    log=null_out())
  assert (pdb_in.hierarchy.as_pdb_string() == """\
ATOM      1  N   LYS A   7       6.033   4.704   1.582  1.00 17.49           N
ATOM      2  CA  LYS A   7       5.159   5.427   2.499  1.00 18.23           C
ATOM      3  C   LYS A   7       4.673   4.437   3.507  1.00 14.78           C
ATOM      4  O   LYS A   7       4.777   3.208   3.297  1.00 15.83           O
ATOM      5  CB  LYS A   7       3.959   6.057   1.760  1.00 23.56           C
ATOM      6  CG  LYS A   7       4.368   7.206   0.851  1.00 33.58           C
ATOM      7  CD  LYS A   7       3.242   7.559  -0.108  1.00 41.39           C
ATOM      8  CE  LYS A   7       3.009   6.453  -1.124  1.00 48.81           C
ATOM      9  NZ  LYS A   7       1.909   6.785  -2.070  1.00 48.81           N
TER
""")

def exercise_cmdline () :
  from mmtbx.command_line import extend_sidechains
  from mmtbx.regression import model_1yjp
  import iotbx.pdb.hierarchy
  pdb_file = "tst_extend_sidechains.pdb"
  mtz_file = "tst_extend_sidechains.mtz"
  pdb_in = iotbx.pdb.hierarchy.input(pdb_string=model_1yjp)
  xrs = pdb_in.input.xray_structure_simple()
  f_calc = abs(xrs.structure_factors(d_min=1.5).f_calc())
  sel = pdb_in.hierarchy.atom_selection_cache().selection(
    "not (resname TYR and not (name c or name o or name n or name oxt or name ca or name cb))")
  hierarchy = pdb_in.hierarchy.select(sel)
  f = open(pdb_file, "w")
  f.write(hierarchy.as_pdb_string(crystal_symmetry=xrs))
  f.close()
  flags = f_calc.generate_r_free_flags(fraction=0.1)
  mtz = f_calc.as_mtz_dataset(column_root_label="F")
  mtz.add_miller_array(flags, column_root_label="FreeR_flag")
  mtz.mtz_object().write(mtz_file)
  pdb_out = "tst_extend_sidechains_out.pdb"
  if os.path.isfile(pdb_out) :
    os.remove(pdb_out)
  out = StringIO()
  extend_sidechains.run(
    args=[pdb_file, mtz_file, "output_model=%s" % pdb_out],
    out=out)
  assert ("1 sidechains extended." in out.getvalue())
  from mmtbx.validation import rotalyze
  pdb_new = iotbx.pdb.hierarchy.input(file_name=pdb_out)
  r1 = rotalyze.rotalyze(pdb_hierarchy=pdb_in.hierarchy, outliers_only=False)
  r2 = rotalyze.rotalyze(pdb_hierarchy=pdb_new.hierarchy, outliers_only=False)
  for o1, o2 in zip(r1.results, r2.results) :
    assert o1.rotamer_name == o2.rotamer_name
  # Part 2: with sequence corrections
  seq_file = "tst_extend_sidechains.fa"
  open(seq_file, "w").write(">1yjp_new\nGNDQQNY")
  pdb_out = "tst_extend_sidechains_out2.pdb"
  extend_sidechains.run(
    args=[pdb_file, mtz_file, seq_file, "output_model=%s" % pdb_out],
    out=out)
  assert ("2 sidechains extended." in out.getvalue())

def exercise_correct_sequence () :
  from mmtbx.building import extend_sidechains
  from mmtbx.regression import model_1yjp
  import iotbx.pdb.hierarchy
  import iotbx.bioinformatics
  pdb_in = iotbx.pdb.hierarchy.input(pdb_string=model_1yjp)
  sequences = [ iotbx.bioinformatics.sequence("GNDQQNY") ]
  out = StringIO()
  n_changed = extend_sidechains.correct_sequence(
    pdb_hierarchy=pdb_in.hierarchy.deep_copy(),
    sequences=sequences,
    out=out)
  assert (n_changed == 1)
  assert ("  chain 'A'    3  ASP --> ASP (1 atoms removed)" in out.getvalue())
  out = StringIO()
  n_changed = extend_sidechains.correct_sequence(
    pdb_hierarchy=pdb_in.hierarchy.deep_copy(),
    sequences=sequences,
    truncate_to_cbeta=True,
    out=out)
  assert (n_changed == 1)
  assert ("  chain 'A'    3  ASP --> ASP (3 atoms removed)" in out.getvalue())

if (__name__ == "__main__") :
  exercise_model_only()
  exercise_correct_sequence()
  exercise_cmdline()
  print "OK"
