
from __future__ import division
from libtbx.utils import null_out
import os.path
import sys

extend_master_phil = """
include scope mmtbx.building.extend_sidechains.master_params
output_model = None
  .type = path
output_map_coeffs = None
  .type = path
"""

def get_master_phil () :
  from mmtbx.command_line import generate_master_phil_with_inputs
  return generate_master_phil_with_inputs(phil_string=extend_master_phil,
    enable_automatic_twin_detection=True)

def run (args, out=sys.stdout, verbose=True) :
  import mmtbx.building.extend_sidechains
  import mmtbx.command_line
  input_out = out
  if (not verbose) :
    input_out = null_out()
  cmdline = mmtbx.command_line.load_model_and_data(
    args=args,
    master_phil=get_master_phil(),
    process_pdb_file=False,
    out=input_out,
    usage_string="""\
mmtbx.extend_sidechains model.pdb data.mtz [restraints.cif] [options]

Rebuild sidechains with missing non-hydrogen atoms.  Includes real-space
refinement (but needs work).""")
  params = cmdline.params
  prefix = os.path.splitext(os.path.basename(params.input.pdb.file_name[0]))[0]
  return mmtbx.building.extend_sidechains.extend_and_refine(
    pdb_hierarchy=cmdline.pdb_hierarchy,
    xray_structure=cmdline.xray_structure,
    fmodel=cmdline.fmodel,
    params=params,
    prefix=prefix,
    cif_objects=[ co for fn, co in cmdline.cif_objects ],
    out=out,
    verbose=verbose,
    output_model=params.output_model,
    output_map_coeffs=params.output_map_coeffs)

if (__name__ == "__main__") :
  run(sys.argv[1:])
