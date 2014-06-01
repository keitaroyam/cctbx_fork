
from __future__ import division
from mmtbx.command_line import molprobity
from libtbx.easy_pickle import loads, dumps, dump
from libtbx.test_utils import show_diff, approx_equal
from libtbx.utils import null_out
import libtbx.load_env
from cStringIO import StringIO
import os.path as op
import os

def exercise_protein () :

  pdb_file = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/pdb/3ifk.pdb",
    test=op.isfile)
  hkl_file = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/reflection_files/3ifk.mtz",
    test=op.isfile)
  if (pdb_file is None) :
    print "phenix_regression not available, skipping."
    return
  args1 = [
    pdb_file,
    "outliers_only=True",
    "output.prefix=tst_molprobity",
    "--pickle",
  ]
  result = molprobity.run(args=args1, out=null_out()).validation
  out1 = StringIO()
  result.show(out=out1)
  result = loads(dumps(result))
  out2 = StringIO()
  result.show(out=out2)
  assert (result.nqh_flips.n_outliers == 1)
  assert (not "RNA validation" in out2.getvalue())
  assert (out2.getvalue() == out1.getvalue())
  dump("tst_molprobity.pkl", result)
  mc = result.as_multi_criterion_view()
  # percentiles
  out4 = StringIO()
  result.show_summary(out=out4, show_percentiles=True)
  assert ("""  Clashscore            =  49.96 (percentile: 1.0)""" in
    out4.getvalue())
  # misc
  assert approx_equal(result.r_work(), 0.237) # from PDB header
  assert approx_equal(result.r_free(), 0.293) # from PDB header
  assert approx_equal(result.d_min(), 2.03)   # from PDB header
  assert (result.d_max_min() is None)
  assert approx_equal(result.rms_bonds(), 0.02585)
  assert approx_equal(result.rms_angles(), 2.372306)
  assert approx_equal(result.rama_favored(), 96.47059)
  assert (result.cbeta_outliers() == 10)
  assert approx_equal(result.molprobity_score(), 3.3725, eps=0.0001)
  summary = result.summarize()
  gui_fields = list(summary.iter_molprobity_gui_fields())
  assert (len(gui_fields) == 6)
  #result.show()
  assert (str(mc.data()[2]) == ' A   5  THR  rota,cb,clash')
  import mmtbx.validation.molprobity
  from iotbx import file_reader
  pdb_in = file_reader.any_file(pdb_file)
  hierarchy = pdb_in.file_object.construct_hierarchy()
  flags = mmtbx.validation.molprobity.molprobity_flags()
  flags.clashscore = False
  flags.model_stats = False
  flags.cbetadev = False
  result = mmtbx.validation.molprobity.molprobity(
    pdb_hierarchy=hierarchy,
    flags=flags)
  out3 = StringIO()
  result.show_summary(out=out3)
  assert not show_diff(out3.getvalue(), """\
  Ramachandran outliers =   1.76 %
                favored =  96.47 %
  Rotamer outliers      =  18.67 %
""")
  # now with data
  args2 = args1 + [ hkl_file, "--maps" ]
  result = molprobity.run(args=args2, out=null_out()).validation
  out = StringIO()
  result.show(out=out)
  assert approx_equal(result.r_work(), 0.2276, eps=0.001)
  assert approx_equal(result.r_free(), 0.2805, eps=0.001)
  assert approx_equal(result.d_min(), 2.0302, eps=0.0001)
  assert approx_equal(result.d_max_min(), [34.546125, 2.0302], eps=0.0001)
  assert approx_equal(result.rms_bonds(), 0.02585)
  assert approx_equal(result.rms_angles(), 2.372306)
  assert approx_equal(result.rama_favored(), 96.47059)
  assert (result.cbeta_outliers() == 10)
  assert approx_equal(result.unit_cell().parameters(),
          (55.285, 58.851, 67.115,90,90,90))
  assert (str(result.space_group_info()) == "P 21 21 21")
  bins = result.fmodel_statistics_by_resolution()
  assert (len(bins) == 10)
  assert approx_equal(result.atoms_to_observations_ratio(), 0.09755,
    eps=0.0001)
  assert op.isfile("tst_molprobity_maps.mtz")

def exercise_rna () :
  regression_pdb = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/pdb/pdb2goz_refmac_tls.ent",
    test=op.isfile)
  if (regression_pdb is None):
    print "Skipping exercise_regression(): input pdb (pdb2goz_refmac_tls.ent) not available"
    return
  result = molprobity.run(args=[regression_pdb], out=null_out()).validation
  assert (result.rna is not None)
  out = StringIO()
  result.show(out=out)
  assert ("2/58 pucker outliers present" in out.getvalue())
  result = loads(dumps(result))
  out2 = StringIO()
  result.show(out=out2)
  assert (out2.getvalue() == out.getvalue())

if (__name__ == "__main__") :
  if (not libtbx.env.has_module(name="probe")):
    print "Skipping tests: probe not configured"
  else :
    exercise_protein()
    if (not libtbx.env.has_module(name="suitename")) :
      print "Skipping RNA test: suitename not available"
    else :
      exercise_rna()
    print "OK"
