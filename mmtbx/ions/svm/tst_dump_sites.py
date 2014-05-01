 # -*- coding: utf-8; py-indent-offset: 2 -*-

from __future__ import division

import os
import sys
from pickle import load

import libtbx
from mmtbx.regression.make_fake_anomalous_data import generate_zinc_inputs
from mmtbx.ions.svm.dump_sites import main
from mmtbx.ions.svm import ion_class

def exercise():
  wavelength = 1.025
  mtz_file, pdb_file = generate_zinc_inputs(anonymize=True)
  null_out = libtbx.utils.null_out()
  main(["skip_twin_detection=True",
        "input.pdb.file_name=" + pdb_file,
        "input.xray_data.file_name=" + mtz_file,
        "wavelength={}".format(wavelength)], out=null_out)

  sites_path = os.path.splitext(pdb_file)[0] + "_sites.pkl"
  sites = load(open(sites_path))

  assert len(sites) == 7
  for chem_env, scatter_env in sites:
    assert chem_env is not None
    assert scatter_env is not None
    for name in chem_env.__slots__:
      if getattr(chem_env, name) is None:
        print "Error: chem_env.{} is not set".format(name)
        sys.exit()
    for name in scatter_env.__slots__:
      # f' is not set by phaser
      if name in ["fp"]:
        continue
      # Only check f'' for heavy metals
      if name != "fpp" or ion_class(chem_env) != "HOH":
        if getattr(scatter_env, name) is None:
          print "Error: scatter_env.{} is not set".format(name)
          sys.exit()

  os.remove(pdb_file)
  os.remove(mtz_file)
  os.remove(sites_path)
  # "zn_frag_hoh.pdb" => "zn_frag_fmodel.eff"
  os.remove(os.path.splitext(pdb_file)[0][:-4] + "_fmodel.eff")

  print "OK"

if __name__ == "__main__":
  exercise()
