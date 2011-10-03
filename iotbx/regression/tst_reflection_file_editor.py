
from iotbx import reflection_file_editor, file_reader
from iotbx.reflection_file_editor import master_phil
from cctbx import miller
from cctbx import crystal, sgtbx, uctbx
from scitbx.array_family import flex
import libtbx.load_env
from libtbx.utils import Sorry, null_out
import os.path
from libtbx.test_utils import Exception_expected, approx_equal

# this will run without phenix_regression
def exercise_basic () :
  symm = crystal.symmetry(
    space_group_info=sgtbx.space_group_info("P212121"),
    unit_cell=uctbx.unit_cell((6,7,8,90,90,90)))
  set1 = miller.build_set(
    crystal_symmetry=symm,
    anomalous_flag=True,
    d_min=1.0)
  assert (set1.indices().size() == 341)
  data1 = flex.double(set1.indices().size(), 100.)
  sigmas1 = flex.double(set1.indices().size(), 4.)
  for i in range(10) :
    data1[2+i*30] = -1
  for i in range(10) :
    data1[5+i*30] = 7.5
  array1 = set1.array(data=data1, sigmas=sigmas1)
  array1.set_observation_type_xray_intensity()
  flags = array1.generate_r_free_flags(
    use_lattice_symmetry=True).average_bijvoet_mates()
  mtz1 = array1.as_mtz_dataset(column_root_label="I-obs")
  mtz1.add_miller_array(flags, column_root_label="R-free-flags")
  mtz1.mtz_object().write("tst_data.mtz")
  # convert intensities to amplitudes
  new_phil = libtbx.phil.parse("""
mtz_file {
  output_file = tst1.mtz
  crystal_symmetry.space_group = P212121
  crystal_symmetry.unit_cell = 6,7,8,90,90,90
  miller_array {
    file_name = tst_data.mtz
    labels = I-obs(+),SIGI-obs(+),I-obs(-),SIGI-obs(-)
    output_labels = I-obs(+) SIGI-obs(+) I-obs(-) SIGI-obs(-)
  }
  miller_array {
    file_name = tst_data.mtz
    labels = R-free-flags
    output_labels = R-free-flags
  }
}""")
  params = master_phil.fetch(source=new_phil).extract()
  def run_and_reload (params, file_name) :
    p = reflection_file_editor.process_arrays(params, log=null_out())
    p.finish()
    mtz_in = file_reader.any_file(file_name)
    miller_arrays = mtz_in.file_object.as_miller_arrays()
    return miller_arrays
  params.mtz_file.miller_array[0].output_as = "amplitudes"
  try :
    miller_arrays = run_and_reload(params, "tst1.mtz")
  except Sorry, e :
    assert ("not suitable for" in str(e))
  else :
    raise Exception_expected
  params.mtz_file.miller_array[0].output_labels = ['F-obs(+)', 'SIGF-obs(+)',
    'F-obs(-)', 'SIGF-obs(-)']
  miller_arrays = run_and_reload(params, "tst1.mtz")
  assert (miller_arrays[0].info().labels == ['F-obs(+)', 'SIGF-obs(+)',
    'F-obs(-)', 'SIGF-obs(-)'])
  assert miller_arrays[0].is_xray_amplitude_array()
  data1 = miller_arrays[0].data()
  # force data type change
  params.mtz_file.miller_array[0].output_as = "auto"
  params.mtz_file.miller_array[0].force_type = "amplitudes"
  params.mtz_file.miller_array[0].output_labels = ['F-obs(+)', 'SIGF-obs(+)',
    'F-obs(-)', 'SIGF-obs(-)']
  params.mtz_file.output_file = "tst2.mtz"
  miller_arrays = run_and_reload(params, "tst2.mtz")
  mtz_orig = file_reader.any_file("tst_data.mtz")
  orig_arrays = mtz_orig.file_server.miller_arrays
  data0 = orig_arrays[0].data()
  data2 = miller_arrays[0].data()
  assert miller_arrays[0].is_xray_amplitude_array()
  assert (data0.all_eq(data2)) and (data0.all_ne(data1))
  params.mtz_file.output_file = "tst1.mtz"
  params.mtz_file.miller_array[0].force_type = "auto"
  params.mtz_file.miller_array[0].output_non_anomalous = True
  try :
    run_and_reload(params, "tst1.mtz")
  except Sorry, e :
    assert ("too many output labels" in str(e))
  else :
    raise Exception_expected
  params.mtz_file.miller_array[0].output_labels = ["F-obs", "SIGF-obs"]
  miller_arrays = run_and_reload(params, "tst1.mtz")
  assert (not miller_arrays[0].anomalous_flag())
  # filter by signal-to-noise ratio
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.miller_array[0].filter_by_signal_to_noise = 2.0
  miller_arrays = run_and_reload(params, "tst1.mtz")
  data = miller_arrays[0].data()
  sigmas = miller_arrays[0].sigmas()
  assert (data.size() == 321) and ((data / sigmas).all_ge(2.0))
  # data scaling
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.miller_array[0].scale_factor = 2.0
  miller_arrays = run_and_reload(params, "tst1.mtz")
  data2 = miller_arrays[0].data()
  assert approx_equal(flex.max(data2), 2.*flex.max(data))
  # remove negatives
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.miller_array[0].remove_negatives = True
  miller_arrays = run_and_reload(params, "tst1.mtz")
  assert (miller_arrays[0].data().size() == 331)
  # scale to maximum value
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.miller_array[0].scale_max = 2000.
  miller_arrays = run_and_reload(params, "tst1.mtz")
  data3 = miller_arrays[0].data()
  assert (flex.max(data3) == 2000.)
  # improper operations on R-free flags
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.miller_array[0].scale_factor = None
  params.mtz_file.miller_array[1].output_as = "amplitudes"
  # this one won't actually crash (it will be ignored)
  miller_arrays = run_and_reload(params, "tst1.mtz")
  params.mtz_file.miller_array[1].output_as = "auto"
  params.mtz_file.miller_array[1].force_type = "amplitudes"
  try :
    miller_arrays = run_and_reload(params, "tst1.mtz")
  except Sorry, e :
    pass
  else :
    raise Exception_expected
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.miller_array[1].filter_by_signal_to_noise = 2.0
  try :
    miller_arrays = run_and_reload(params, "tst1.mtz")
  except Sorry, e :
    pass
  else :
    raise Exception_expected
  # improper output labels
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.miller_array[1].output_labels.append("NULL")
  try :
    miller_arrays = run_and_reload(params, "tst1.mtz")
  except Sorry, e :
    assert ("number of output labels" in str(e))
  else :
    raise Exception_expected
  params.mtz_file.miller_array[1].output_labels.pop()
  params.mtz_file.miller_array[0].output_labels.pop()
  try :
    miller_arrays = run_and_reload(params, "tst1.mtz")
  except Sorry, e :
    assert ("number of output labels" in str(e))
  else :
    raise Exception_expected
  # resolution filter
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.d_min = 2.0
  miller_arrays = run_and_reload(params, "tst1.mtz")
  assert approx_equal(miller_arrays[0].d_min(), 2.0, eps=0.01)
  assert approx_equal(miller_arrays[1].d_min(), 2.0, eps=0.01)
  # resolution filter for a specific array
  params.mtz_file.d_min = None
  params.mtz_file.miller_array[0].d_min = 2.0
  miller_arrays = run_and_reload(params, "tst1.mtz")
  assert approx_equal(miller_arrays[0].d_min(), 2.0, eps=0.01)
  assert approx_equal(miller_arrays[1].d_min(), 1.0, eps=0.01)
  # change-of-basis (reindexing)
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.crystal_symmetry.change_of_basis = "b,a,c"
  miller_arrays = run_and_reload(params, "tst1.mtz")
  assert (miller_arrays[0].unit_cell().parameters() ==
    (7.0, 6.0, 8.0, 90.0, 90.0, 90.0))
  # expand symmetry (expand_to_p1=True)
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.crystal_symmetry.expand_to_p1 = True
  miller_arrays = run_and_reload(params, "tst1.mtz")
  assert (miller_arrays[0].space_group_info().type().number() == 1)
  # expand symmetry (different output space group)
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.crystal_symmetry.output_space_group = \
    sgtbx.space_group_info("P21")
  miller_arrays = run_and_reload(params, "tst1.mtz")
  assert (miller_arrays[0].space_group_info().type().number() == 4)
  # incompatible input space_group/unit_cell
  params.mtz_file.crystal_symmetry.space_group = sgtbx.space_group_info("P4")
  try :
    miller_arrays = run_and_reload(params, "tst1.mtz")
  except Sorry, e :
    assert ("Input unit cell" in str(e))
  else :
    raise Exception_expected
  # incompatible output space_group/unit_cell
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.crystal_symmetry.output_space_group = \
    sgtbx.space_group_info("P6322")
  try :
    miller_arrays = run_and_reload(params, "tst1.mtz")
  except Sorry, e :
    assert ("incompatible with the specified" in str(e))
  else :
    raise Exception_expected
  # R-free manipulation (starting from incomplete flags)
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.miller_array[1].d_min = 1.2
  params.mtz_file.output_file = "tst_data2.mtz"
  miller_arrays = run_and_reload(params, "tst_data2.mtz")
  assert (miller_arrays[1].data().size() == 138)
  flags1 = miller_arrays[1].data()
  params = master_phil.fetch(source=new_phil).extract()
  # now extend the incomplete flags
  params.mtz_file.r_free_flags.extend = True
  for ma in params.mtz_file.miller_array :
    ma.file_name = "tst_data2.mtz"
  params.mtz_file.output_file = "tst4.mtz"
  miller_arrays = run_and_reload(params, "tst4.mtz")
  assert (miller_arrays[1].data().size() == 221)
  # export for ccp4 programs (flag=0, everything else > 0)
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.r_free_flags.export_for_ccp4 = True
  params.mtz_file.output_file = "tst_data3.mtz"
  miller_arrays = run_and_reload(params, "tst_data3.mtz")
  free_selection = (miller_arrays[1].data() == 0)
  old_selection = (orig_arrays[1].data() == 1)
  assert (free_selection.all_eq(old_selection))
  # preserve input values (now in tst_data3.mtz)
  params = master_phil.fetch(source=new_phil).extract()
  params.mtz_file.output_file = "tst4.mtz"
  for ma in params.mtz_file.miller_array :
    ma.file_name = "tst_data3.mtz"
  # actually, the flag values won't be preserved here...
  miller_arrays = run_and_reload(params, "tst4.mtz")
  new_selection = (miller_arrays[1].data() == 1)
  assert (free_selection.all_eq(new_selection))
  # ...but they will here
  params.mtz_file.r_free_flags.preserve_input_values = True
  miller_arrays = run_and_reload(params, "tst4.mtz")
  new_selection = (miller_arrays[1].data() == 0)
  assert (free_selection.all_eq(new_selection))

# this requires data in phenix_regression
# TODO replace this with equivalent using synthetic data
def exercise_command_line () :
  if (not libtbx.env.has_module("phenix_regression")) :
    print "phenix_regression not available, skipping"
    return
  file1 = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/reflection_files/enk.mtz",
    test=os.path.isfile)
  file2 = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/reflection_files/enk_r1A.mtz",
    test=os.path.isfile)
  log = null_out()
  test_file = "tst%d-1.mtz" % os.getpid()
  test_file2 = "tst%d-2.mtz" % os.getpid()
  try :
    p = reflection_file_editor.run(
      args=[file1, file2, "dry_run=True"],
      out=log)
  except Sorry, e :
    assert str(e).startswith("Duplicate column label 'R-free-flags'.")
  else :
    raise Exception_expected
  p = reflection_file_editor.run(
    args=[file1, file2, "dry_run=True", "resolve_label_conflicts=True",
          "output_file=%s" % test_file],
    out=log)
  assert ([ c.label() for c in p.mtz_object.columns() ] ==
    ['H','K','L','I-obs','SIGI-obs','F-obs','R-free-flags','R-free-flags_2'])
  p.finish()
  mtz_in = file_reader.any_file(test_file)
  miller_arrays = mtz_in.file_object.as_miller_arrays()
  flags1 = miller_arrays[-2]
  assert flags1.info().label_string() == "R-free-flags"
  (d_max, d_min) = flags1.d_max_min()
  assert (approx_equal(d_max, 11.14, eps=0.01) and
          approx_equal(d_min, 1.503, eps=0.01))
  flags2 = miller_arrays[-1]
  assert flags2.info().label_string() == "R-free-flags_2"
  (d_max, d_min) = flags2.d_max_min()
  assert (approx_equal(d_max, 11.14, eps=0.01) and
          approx_equal(d_min,1.00,eps=0.01))
  p = reflection_file_editor.run(
    args=[file1, file2, "resolve_label_conflicts=True", "extend=True",
          "output_file=%s" % test_file],
    out=log)
  mtz_in = file_reader.any_file(test_file)
  miller_arrays = mtz_in.file_object.as_miller_arrays()
  (d_max_first, d_min_first) = miller_arrays[1].d_max_min()
  (d_max_last, d_min_last) = miller_arrays[-1].d_max_min()
  assert (d_max_first <= d_max_last)
  assert (d_min_first == d_min_last)
  #os.remove(test_file)
  old_r_free_1 = miller_arrays[-2]
  old_r_free_2 = miller_arrays[-1]
  # export to CCP4 convention
  p = reflection_file_editor.run(
    args=[file1, file2, "resolve_label_conflicts=True", "extend=False",
          "export_for_ccp4=False", "output_file=%s" % test_file],
     out=log)
  mtz_in = file_reader.any_file(test_file)
  miller_arrays = mtz_in.file_object.as_miller_arrays()
  # os.remove(test_file)
  assert miller_arrays[-2].info().label_string() == "R-free-flags"
  assert miller_arrays[-1].info().label_string() == "R-free-flags_2"
  old_r_free_1 = miller_arrays[-2]
  old_r_free_2 = miller_arrays[-1]
  p = reflection_file_editor.run(
    args=[file1, file2, "resolve_label_conflicts=True", "extend=False",
          "export_for_ccp4=True", "output_file=%s" % test_file2],
    out=log)
  mtz_in = file_reader.any_file(test_file2)
  miller_arrays = mtz_in.file_object.as_miller_arrays()
  assert (len(set(miller_arrays[-2].data())) == 5)
  assert (len(set(miller_arrays[-1].data())) == 10)
  old_flags_1 = (old_r_free_1.data() == 1)
  old_flags_2 = (old_r_free_2.data() == 1)
  new_flags_1 = (miller_arrays[-2].data() == 0)
  new_flags_2 = (miller_arrays[-1].data() == 0) #.select(old_flags_2)
  assert (old_flags_1 == new_flags_1).count(False) == 0
  assert (old_flags_2 == new_flags_2).count(False) == 0

if __name__ == "__main__" :
  exercise_basic()
  exercise_command_line()
  print "OK"
