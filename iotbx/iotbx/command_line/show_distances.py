from cctbx.crystal import coordination_sequences
from cctbx.crystal import distance_ls
import cctbx.crystal.pair_asu_table
from iotbx.kriber import strudat
from iotbx.option_parser import iotbx_option_parser
import sys

def run():
  command_line = (iotbx_option_parser(
    usage="iotbx.show_distances [options] studat_file [...]",
    description="Example: iotbx.show_distances strudat --tag=SOD")
    .option(None, "--tag",
      action="store",
      type="string",
      dest="tag",
      help="tag as it appears in the strudat file")
    .option(None, "--distance_cutoff",
      action="store",
      type="float",
      default=5,
      dest="distance_cutoff",
      help="Maximum distance to be considered",
      metavar="FLOAT")
    .option(None, "--cs",
      action="store",
      type="int",
      dest="cs",
      help="Compute N terms of the coordination sequences",
      metavar="N")
    .option(None, "--coseq",
      action="store",
      type="string",
      dest="coseq",
      help="name of file with known coordination sequences",
      metavar="FILE")
  ).process()
  if (len(command_line.args) == 0):
    command_line.parser.show_help()
    return
  n_shells = command_line.options.cs
  if (command_line.options.coseq is not None):
    coseq_dict = coordination_sequences.get_kriber_coseq_file(
      file_name=command_line.options.coseq)
    if (n_shells is None): n_shells = 10
  else:
    coseq_dict = None
  for file_name in command_line.args:
    strudat_entries = strudat.read_all_entries(open(file_name))
    for entry in strudat_entries.entries:
      if (    command_line.options.tag is not None
          and command_line.options.tag != entry.tag):
        continue
      print "strudat tag:", entry.tag
      print
      structure = entry.as_xray_structure()
      structure.show_summary().show_scatterers()
      print
      asu_mappings = structure.asu_mappings(
        buffer_thickness=command_line.options.distance_cutoff)
      pair_asu_table = cctbx.crystal.pair_asu_table.pair_asu_table(
        asu_mappings=asu_mappings)
      pair_asu_table.add_all_pairs(
        distance_cutoff=command_line.options.distance_cutoff)
      pairs = distance_ls.show_pairs(
        structure=structure,
        pair_asu_table=pair_asu_table)
      print
      print "Pair counts:", list(pairs.pair_counts)
      print
      if (n_shells is not None):
        term_table = coordination_sequences.simple_and_slow(
          pair_asu_table=pair_asu_table,
          n_shells=n_shells)
        coordination_sequences.show_terms(
          structure=structure,
          term_table=term_table,
          coseq_dict=coseq_dict)
        print

if (__name__ == "__main__"):
  run()
