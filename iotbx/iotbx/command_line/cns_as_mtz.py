import iotbx.cns.reflection_reader
from iotbx.option_parser import option_parser
import sys, os
from iotbx import mtz

def run(args):
  if (len(args) == 0): args = ["--help"]
  command_line = (option_parser(
    usage="iotbx.cns_as_mtz [options] cns_file",
    description="Example: iotbx.cns_as_mtz scale.hkl")
    .enable_symmetry_comprehensive()
    .option("-q", "--quiet",
      action="store_true",
      default=False,
      help="suppress output")
  ).process(args=args)
  if (len(command_line.args) != 1):
    command_line.parser.show_help()
    return
  cns_file_name = command_line.args[0]
  crystal_symmetry = command_line.symmetry
  if (crystal_symmetry.unit_cell() is None):
    print
    print "*" * 79
    print "Unknown unit cell parameters."
    print "Use --symmetry or --unit_cell to define unit cell:"
    print "*" * 79
    print
    command_line.parser.show_help()
    return
  if (crystal_symmetry.space_group_info() is None):
    print
    print "*" * 79
    print "Unknown space group."
    print "Use --symmetry or --space_group to define space group:"
    print "*" * 79
    print
    command_line.parser.show_help()
    return
  if (not command_line.options.quiet):
    print "CNS file name:", cns_file_name
    print "Crystal symmetry:"
    crystal_symmetry.show_summary(prefix="  ")
  reflection_file = iotbx.cns.reflection_reader.cns_reflection_file(
    file_handle=open(cns_file_name, "r"))
  if (not command_line.options.quiet):
    reflection_file.show_summary()
  miller_arrays = reflection_file.as_miller_arrays(
                                             crystal_symmetry=crystal_symmetry)
  mtz_dataset = None
  for miller_array in miller_arrays:
    if (mtz_dataset is None):
      mtz_dataset = miller_array.as_mtz_dataset(
        column_root_label=miller_array.info().labels[0])
    else:
      mtz_dataset.add_miller_array(
        miller_array=miller_array,
        column_root_label=miller_array.info().labels[0])
  mtz_object = mtz_dataset.mtz_object()
  mtz_object.show_summary()
  if(cns_file_name.count(".") == 1):
     mtz_file_name = cns_file_name[:cns_file_name.index(".")]
  mtz_file_name += ".mtz"
  print "Writing MTZ file: ",mtz_file_name
  mtz_object.write(mtz_file_name)

if (__name__ == "__main__"):
  run(sys.argv[1:])
