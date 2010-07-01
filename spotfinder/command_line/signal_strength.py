# LIBTBX_SET_DISPATCHER_NAME distl.signal_strength
import libtbx.phil
import libtbx.phil.command_line
from libtbx.utils import Sorry
import sys, os
additional_spotfinder_phil_defs ="""
distl {
  minimum_spot_area = None
    .type = int
    .help = "Override default application; set minimum spot area (in pixels) within spotfinder."
  minimum_signal_height = None
    .type = float
    .help = "Override default application; set minimum signal height (in units of background noise sigma) within spotfinder."
  pdf_output = None
    .type = str
    .help="File name for optional PDF graphical output for distl.signal_strength (*.pdf)"
}
"""

master_params = libtbx.phil.parse("""\
distl {
  image = None
    .type = str
    .help="Image file name"
  res {
    outer=None
      .type=float
      .help="High resolution limit in angstroms"
    inner=None
      .type=float
      .help="Low resolution limit in angstroms"
  }
  verbose = False
    .type = bool
    .help="Lengthy spot printout"
}
"""+additional_spotfinder_phil_defs)

def run(args, command_name="distl.signal_strength"):
  help_str="""explanation:
Local background and background standard deviation are determined.
Pixel maxima are chosen if > 3 sigmas above background.
Spots are grown around the maxima, and retained if they fit minimal area criteria.
Total number of candidates at this stage is reported as "Spot Total"
Ice rings are eliminated by at least two different algorithms (rings of high pixel
  values and rings of high spot count).
Resolution filters are applied if given on the command line.
Total number of candidates at this stage is reported as "In-Resolution Total"
Other spot-quality filters are applied to give the number of "Good Bragg Candidates".
Method 1 Resolution is a published legacy algorithm (Zhang et al, 2006) no longer used.
Method 2 Resolution reflects drop off of spot count as a function of resolution shell,
  but is overridden by command line input of distl.res.outer
Signal strength of the Good Bragg Candidates is then presented as integrated area of
  the spot above local background, expressed in pixel-analog/digital units.
Very verbose output is available by setting distl.verbose=True
"""

  if (len(args) == 0 or args[0] in ["H","h","-H","-h","help","--help","-help"]):
    print "usage:   %s image_filename [parameter=value ...]" % command_name
    print "example: %s lysozyme_001.img distl.res.outer=2.0 distl.res.inner=6.0 distl.minimum_spot_area=8"%command_name
    master_params.show(attributes_level=1,expert_level=1)
    print help_str
    return

  print "%s: characterization of candidate Bragg spots"%command_name

  phil_objects = []
  argument_interpreter = libtbx.phil.command_line.argument_interpreter(
    master_phil=master_params, home_scope="distl")
  image_file_name = None
  moving_pdb_file_name = None
  for arg in args:
    if (os.path.isfile(arg)):
      if (image_file_name is None): image_file_name = arg
      else: raise Sorry("Too many file names.")
    else:
      try: command_line_params = argument_interpreter.process(arg=arg)
      except KeyboardInterrupt: raise
      except: raise Sorry("Unknown file or keyword: %s" % arg)
      else: phil_objects.append(command_line_params)

  working_params = master_params.fetch(sources=phil_objects)
  params = working_params.extract()

  def raise_missing(what):
      raise Sorry("""\
Missing file name for %(what)s structure:
  Please add
    %(what)s=file_name
  to the command line to specify the %(what)s structure.""" % vars())

  if (image_file_name is None):
    if (params.distl.image is None): raise_missing("file name")
  else:
    params.distl.image = image_file_name

  print "#Parameters used:"
  print "#phil __ON__"
  print
  working_params = master_params.format(python_object=params)
  working_params.show()
  print
  print "#phil __OFF__"
  print

  #Now actually run the program logic
  from spotfinder.applications import signal_strength
  signal_strength.run_signal_strength(working_params.extract())

if (__name__ == "__main__"):
  run(args=sys.argv[1:])
