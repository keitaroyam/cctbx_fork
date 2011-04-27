
from libtbx.utils import Sorry, Usage
import cStringIO
import os
import sys

class summary (object) :
  def __init__ (self, pdb_hierarchy=None, pdb_file=None, sites_cart=None,
      keep_hydrogens=False) :
    if (pdb_hierarchy is None) :
      assert (pdb_file is not None)
      from iotbx import file_reader
      pdb_in = file_reader.any_file(pdb_file, force_type="pdb")
      pdb_in.assert_file_type("pdb")
      pdb_hierarchy = pdb_in.file_object.construct_hierarchy()
      pdb_hierarchy.atoms().reset_i_seq()
    if (sites_cart is not None) :
      pdb_hierarchy.atoms().set_xyz(sites_cart)
    from mmtbx.validation import ramalyze, rotalyze, cbetadev, clashscore
    log = cStringIO.StringIO()
    rama = ramalyze.ramalyze()
    rama.analyze_pdb(hierarchy=pdb_hierarchy)
    rama_out_count, rama_out_percent = rama.get_outliers_count_and_fraction()
    rama_fav_count, rama_fav_percent = rama.get_favored_count_and_fraction()
    self.rama_fav = rama_fav_percent * 100.0
    self.rama_out = rama_out_percent * 100.0
    rota = rotalyze.rotalyze()
    rota.analyze_pdb(hierarchy=pdb_hierarchy)
    rota_count, rota_perc = rota.get_outliers_count_and_fraction()
    self.rota_out = rota_perc * 100.0
    cs = clashscore.clashscore()
    clash_dict, clash_list = cs.analyze_clashes(hierarchy=pdb_hierarchy,
      keep_hydrogens=keep_hydrogens)
    self.clash_score = clash_dict['']
    cbeta = cbetadev.cbetadev()
    cbeta_txt, cbeta_summ, cbeta_list = cbeta.analyze_pdb(
      hierarchy=pdb_hierarchy,
      outliers_only=True)
    self.cbeta_out = len(cbeta_list)

  def show (self, out=sys.stdout, prefix="  ") :
    print >> out, "%sRamachandran outliers = %6.2f %%" % (prefix,self.rama_out)
    print >> out, "%s             favored  = %6.2f %%" % (prefix,self.rama_fav)
    print >> out, "%sRotamer outliers      = %6.2f %%" % (prefix,self.rota_out)
    print >> out, "%sC-beta deviations     = %6d" % (prefix,self.cbeta_out)
    print >> out, "%sClashscore            = %6.2f" % (prefix,self.clash_score)

def run (args, out=sys.stdout) :
  if (len(args) == 0) :
    raise Usage("""
mmtbx.validation_summary model.pdb

Prints a brief summary of validation criteria, including Ramachandran
statistics, rotamer outliers, clashscore, C-beta deviations, plus R-factors
and RMS(bonds)/RMS(angles) if found in PDB header.  (This is primarily used
for evaluating the output of refinement tests; general users are advised to
run phenix.model_vs_data or the validation GUI.)
""")
  pdb_file = args[0]
  if (not os.path.isfile(pdb_file)) :
    raise Sorry("Not a file: %s" % pdb_file)
  s = summary(pdb_file=pdb_file)
  pdb_lines = open(pdb_file, "r").readlines()
  r_work = None
  r_free = None
  rms_bonds = None
  rms_angles = None
  for line in pdb_lines :
    if (line.startswith("REMARK   3")) :
      if ("Final:" in line) :
        fields = line.split()
        for i, field in enumerate(fields) :
          if (field == "r_work") :
            r_work = float(fields[i+2])
          elif (field == "r_free") :
            r_free = float(fields[i+2])
          elif (field == "bonds") :
            rms_bonds = float(fields[i+2])
          elif (field == "angles") :
            rms_angles = float(fields[i+2])
        break
      elif ("3   R VALUE            (WORKING SET)" in line) :
        r_work = float(line.split(":")[1].strip())
      elif ("3   FREE R VALUE                    " in line) :
        r_free = float(line.split(":")[1].strip())
    elif (line.startswith("REMARK 200")) :
      break
  print >> out, ""
  print >> out, "Validation summary for %s:" % pdb_file
  s.show(out=out)
  if (r_work is not None) :
    print >> out, "  R-work                = %8.4f" % r_work
  if (r_free is not None) :
    print >> out, "  R-free                = %8.4f" % r_free
  if (rms_bonds is not None) :
    print >> out, "  RMS(bonds)            = %8.4f" % rms_bonds
  if (rms_angles is not None) :
    print >> out, "  RMS(angles)           = %6.2f" % rms_angles
  print >> out, ""

if (__name__ == "__main__") :
  run(sys.argv[1:])
