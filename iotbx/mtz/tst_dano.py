import sys

def recycle_dano_miller_array(miller_array):
  assert miller_array.is_xray_reconstructed_amplitude_array()
  from cctbx.array_family import flex
  mt = flex.mersenne_twister(seed=0)
  miller_array = miller_array.select(
    mt.random_permutation(size=miller_array.indices().size()))
  mtz_obj = miller_array.as_mtz_dataset(column_root_label="X").mtz_object()
  _ = mtz_obj.as_miller_arrays()
  assert len(_) == 1
  miller_array_2 = _[0]
  assert str(miller_array_2.info()) == "ccp4_mtz:X,SIGX,DANOX,SIGDANOX,ISYMX"
  a, b = miller_array.map_to_asu().common_sets(miller_array_2.map_to_asu())
  assert a.indices().all_eq(b.indices())
  from libtbx.test_utils import approx_equal
  assert approx_equal(a.data(), b.data())
  assert approx_equal(a.sigmas(), b.sigmas())

def recycle_dano_mtz(mtz_file_name):
  import iotbx.mtz
  mtz_obj = iotbx.mtz.object(file_name=mtz_file_name)
  for miller_array in mtz_obj.as_miller_arrays():
    if (miller_array.is_xray_reconstructed_amplitude_array()):
      recycle_dano_miller_array(miller_array)

def recycle_one_dano(missing, verbose):
  assert missing in [None, "+", "-"]
  from cctbx import crystal
  cs = crystal.symmetry(
    unit_cell=(13,17,19,85,95,105),
    space_group_symbol="P1")
  from cctbx.array_family import flex
  mi = flex.miller_index([(1,2,3), (-1,-2,-3)])
  fpm = flex.double([2.5, 5.5])
  spm = flex.double([0.1, 0.3])
  from cctbx import miller
  ms = miller.set(crystal_symmetry=cs, indices=mi, anomalous_flag=True)
  ma = ms.array(data=fpm, sigmas=spm)
  mtz_dataset = ma.as_mtz_dataset(column_root_label="X")
  if (missing is not None):
    for col in mtz_dataset.columns():
      if (col.label() in ["X(%s)" % missing, "SIGX(%s)" % missing]):
        col.set_values(
          values=flex.float([0]),
          selection_valid=flex.bool([False]))
    if (missing == "+"): i = 1
    else:                i = 0
    ma = ma.select(flex.size_t([i]))
  mtz_obj = mtz_dataset.mtz_object()
  from cctbx.xray import observation_types
  ma.set_observation_type(observation_types.reconstructed_amplitude())
  mtz_obj_reco = ma.as_mtz_dataset(column_root_label="R").mtz_object()
  from cStringIO import StringIO
  sio = StringIO()
  print >> sio, "Resulting mtz from .as_mtz_dataset():"
  mtz_obj_reco.show_column_data_human_readable(out=sio)
  print >> sio
  ma_reco = mtz_obj_reco.as_miller_arrays()[0]
  print >> sio, "mtz_obj_reco.as_miller_arrays result:"
  ma_reco.show_array(f=sio)
  print >> sio
  if (verbose):
    sys.stdout.write(sio.getvalue())
  if (missing is None):
    expected = """\
Resulting mtz from .as_mtz_dataset():
Column data:
-------------------------------------------------------------------------------
                       R            SIGR           DANOR        SIGDANOR
                   ISYMR

 1  2  3               4        0.158114              -3        0.316228
                       0
-------------------------------------------------------------------------------

mtz_obj_reco.as_miller_arrays result:
(1, 2, 3) 2.5 0.223606796247
(-1, -2, -3) 5.5 0.223606796247

"""
  elif (missing == "+"):
    expected = """\
Resulting mtz from .as_mtz_dataset():
Column data:
-------------------------------------------------------------------------------
                       R            SIGR           DANOR        SIGDANOR
                   ISYMR

 1  2  3             5.5             0.3            None            None
                       2
-------------------------------------------------------------------------------

mtz_obj_reco.as_miller_arrays result:
(-1, -2, -3) 5.5 0.300000011921

"""
  elif (missing == "-"):
    expected = """\
Resulting mtz from .as_mtz_dataset():
Column data:
-------------------------------------------------------------------------------
                       R            SIGR           DANOR        SIGDANOR
                   ISYMR

 1  2  3             2.5             0.1            None            None
                       1
-------------------------------------------------------------------------------

mtz_obj_reco.as_miller_arrays result:
(1, 2, 3) 2.5 0.10000000149

"""
  else:
    raise RuntimeError("Unreachable.")
  from libtbx.test_utils import show_diff
  assert not show_diff(sio.getvalue(), expected)

def run(args):
  verbose = False
  mtz_file_names = []
  for arg in args:
    if (arg == "--help"):
      from libtbx.utils import Usage
      raise Usage("iotbx.python tst_dano.py [your_dano.mtz] [--verbose]")
    elif (arg == "--verbose"):
      verbose = True
    else:
      mtz_file_names.append(arg)
  if (len(mtz_file_names) == 0):
    import libtbx.load_env
    import os
    op = os.path
    mtz_file_names.append(libtbx.env.find_in_repositories(
      relative_path="phenix_regression/reflection_files/dano.mtz",
      test=op.isfile,
      optional=False))
  for mtz_file_name in mtz_file_names:
    recycle_dano_mtz(mtz_file_name)
  for missing in [None, "+", "-"]:
    recycle_one_dano(missing, verbose)
  print "OK"

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
