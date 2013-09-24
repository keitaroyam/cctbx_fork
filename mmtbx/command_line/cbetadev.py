
from __future__ import division
import phenix_dev.validation.cbetadev
import iotbx.phil
from libtbx.utils import Usage
import os.path
import sys

def get_master_phil():
  return iotbx.phil.parse(input_string="""
    include scope mmtbx.validation.molprobity_cmdline_phil_str
""", process_includes=True)

def run (args, out=sys.stdout, quiet=False) :
  cmdline = iotbx.phil.process_command_line_with_files(
    args=args,
    master_phil=get_master_phil(),
    pdb_file_def="model",
    usage_string="phenix.cbetadev file.pdb [params.eff] [options ...]")
  params = cmdline.work.extract()
  if (params.model is None) :
    raise Usage(usage_string)
  pdb_in = cmdline.get_file(params.model, force_type="pdb")
  hierarchy = pdb_in.file_object.construct_hierarchy()
  result = phenix_dev.validation.cbetadev.cbetadev(
    pdb_hierarchy=hierarchy,
    outliers_only=params.outliers_only,
    out=out,
    quiet=quiet)
  if params.verbose:
    pdb_file_str = os.path.basename(params.model)[:-4]
    result.show_old_output(out=out, prefix=pdb_file_str, verbose=True)

if (__name__ == "__main__") :
  run(sys.argv[1:])
