
from __future__ import division
import os
from mmtbx.command_line import geometry_minimization
from libtbx.utils import Usage
from cStringIO import StringIO

def parse_user_mods(filename):
  flipped_residues = []
  f = file(filename, 'rb')
  for line in f.readlines():
    if line.startswith("USER  MOD"):
      if "FLIP" in line:
        temp = line.strip().split(':')
        flipped_residues.append(temp[1].rstrip())
  f.close()
  return flipped_residues

def finalize_coords(filename, outfile, updated_coords):
  f = file(filename, 'rb')
  out_f = file(outfile, 'w')
  for line in f.readlines():
    if line.startswith("ATOM  "):
      key = line[12:26]
      if key in updated_coords:
        new_line = line[:30]+updated_coords[key]+line[54:]
        print >> out_f, new_line.strip()
      else:
        print >> out_f, line.strip()

    else:
      print >> out_f, line.strip()
  f.close()
  out_f.close()

def run(args):
  #log = StringIO()
  if len(args) != 3:
    raise Usage(
      "mmtbx.nqh_minimize input.pdb output.pdb temp_dir_path")
  filename = args[0]
  outfile = args[1]
  temp_dir = args[2]
  basename = os.path.basename(filename)
  flipped_residues = parse_user_mods(filename=filename)
  selection = "selection = (not (name ' CA ' or name ' N  ' or name ' C  ' " +\
              "or name ' O  ' or name ' HA ' or name ' H  ' " +\
              "or name ' OXT')) and ("
  restrain = "reference_restraints.restrain_starting_coord_selection = " +\
             "(not (name ' CA ' or name ' N  ' or name ' C  ' " +\
             "or name ' O  ' or name ' HA ' or name ' H  ' " +\
             "or name ' OXT')) and ("
  is_first = True
  for flip in flipped_residues:
    if not is_first:
      selection += " or"
      restrain += " or"
    else:
      is_first = False
    selection += " (chain '%s' and resseq %s and resname %s)" % \
                  (flip[0:2], flip[2:6].strip(), flip[7:])
    restrain += " (chain '%s' and resseq %s and resname %s)" % \
                  (flip[0:2], flip[2:6].strip(), flip[7:])
  selection += " )"
  restrain += " )"
  sigma = "reference_restraints.coordinate_sigma=0.05"
  directory = "directory="+temp_dir
  params = os.path.join(temp_dir, "nqh.params")
  p = file(params, 'w')
  print >> p, selection
  print >> p, restrain
  print >> p, sigma
  print >> p, directory
  print >> p, "stop_for_unknowns=False"
  p.close()
  temp_pdb = os.path.join(temp_dir, "nqh_flips.pdb")
  out = file(temp_pdb, 'w')
  f = file(filename, 'rb')
  for line in f.readlines():
    if line.startswith("ATOM  "):
      id_str = line[17:26]
      key = id_str[3:5]+id_str[5:]+' '+id_str[0:3]
      if key in flipped_residues:
        print >> out, line.strip()
  out.close()
  f.close()
  min_args = []
  min_args.append(filename)
  min_args.append(params)

  log_file = os.path.join(temp_dir, "nqh.log")
  log = file(log_file, 'w')

  o = geometry_minimization.run(min_args, log=log)

  updated_coords = {}
  ind = max(0,basename.rfind("."))
  ofn = \
    basename+"_minimized.pdb" if ind==0 else basename[:ind]+"_minimized.pdb"
  min_file = file(os.path.join(temp_dir, ofn), 'rb')
  for line in min_file.readlines():
    if line.startswith("ATOM  "):
      id_str = line[17:26]
      check_key = id_str[3:5]+id_str[5:]+' '+id_str[0:3]
      if check_key in flipped_residues:
        key = line[12:26]
        coords = line[30:54]
        updated_coords[key] = coords
  min_file.close()
  finalize_coords(
    filename=filename,
    outfile=outfile,
    updated_coords=updated_coords)
