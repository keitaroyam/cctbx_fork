
from __future__ import division
from libtbx import easy_run

def exercise () :
  from mmtbx.regression import make_fake_anomalous_data
  mtz_file, pdb_file = make_fake_anomalous_data.generate_calcium_inputs()
  args = ["ca_frag_hoh.pdb", "ca_frag.mtz", "wavelength=1.12", "nproc=1"]
  result = easy_run.fully_buffered("mmtbx.water_screen %s" % " ".join(args)
    ).raise_if_errors()
  assert ("  Probable element: CA+2" in result.stdout_lines)
  print "OK"

if (__name__ == "__main__") :
  exercise()
