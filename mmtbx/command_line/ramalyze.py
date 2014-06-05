# LIBTBX_SET_DISPATCHER_NAME phenix.ramalyze
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export PHENIX_GUI_ENVIRONMENT=1

from __future__ import division
import mmtbx.validation.ramalyze
import iotbx.phil
from libtbx.utils import Usage, Sorry
import os.path
import sys

def get_master_phil():
  return iotbx.phil.parse(input_string="""
    include scope mmtbx.validation.molprobity_cmdline_phil_str
    plot = False
      .type = bool
      .help = Create graphics of plots (if Matplotlib is installed)
    wxplot = False
      .type = bool
      .help = Display interactive plots (requires wxPython and Matplotlib)
""", process_includes=True)

usage_string = """
phenix.ramalyze file.pdb [params.eff] [options ...]

Options:

  model=input_file      input PDB file
  outliers_only=False   only print outliers
  verbose=False         verbose text output
  plot=False            Create graphics of plots (if Matplotlib is installed)

Example:

  phenix.ramalyze model=1ubq.pdb outliers_only=True
"""

def run (args, out=sys.stdout, quiet=False) :
  cmdline = iotbx.phil.process_command_line_with_files(
    args=args,
    master_phil=get_master_phil(),
    pdb_file_def="model",
    usage_string=usage_string)
  params = cmdline.work.extract()
  if (params.model is None) :
    raise Usage(usage_string)
  pdb_in = cmdline.get_file(params.model, force_type="pdb")
  hierarchy = pdb_in.file_object.construct_hierarchy()
  hierarchy.atoms().reset_i_seq()
  result = mmtbx.validation.ramalyze.ramalyze(
    pdb_hierarchy=hierarchy,
    show_errors=None,
    outliers_only=params.outliers_only,
    out=out,
    quiet=quiet)
  if params.verbose:
    result.show_old_output(out=out, verbose=True)
  if params.plot :
    plot_file_base = os.path.splitext(os.path.basename(params.model))[0]
    result.write_plots(plot_file_base=plot_file_base, out=out)
  if params.wxplot :
    try :
      import wxtbx.app
    except ImportError, e :
      raise Sorry("wxPython not available.")
    else :
      app = wxtbx.app.CCTBXApp(0)
      result.display_wx_plots()
      app.MainLoop()

if (__name__ == "__main__") :
  run(sys.argv[1:])
