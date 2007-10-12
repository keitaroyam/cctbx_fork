from libtbx import easy_run
import libtbx.load_env
import sys, os, math, time
from cctbx.array_family import flex
from mmtbx import monomer_library
import mmtbx.monomer_library.pdb_interpretation
from libtbx.utils import remove_files
from mmtbx import utils
from libtbx.test_utils import approx_equal, not_approx_equal, run_command
from libtbx.utils import show_times_at_exit

class xray_structure_plus(object):
  def __init__(self, file_name):
    mon_lib_srv = monomer_library.server.server()
    ener_lib = monomer_library.server.ener_lib()
    processed_pdb_file = monomer_library.pdb_interpretation.process(
                                                   mon_lib_srv = mon_lib_srv,
                                                   ener_lib    = ener_lib,
                                                   file_name   = file_name)
    self.xray_structure = processed_pdb_file.xray_structure(show_summary=False)
    self.all_chain_proxies = processed_pdb_file.all_chain_proxies
    uc = self.xray_structure.unit_cell()
    self.occ           = self.xray_structure.scatterers().extract_occupancies()
    self.u_iso            = self.xray_structure.scatterers().extract_u_iso()
    self.u_cart           = self.xray_structure.scatterers().extract_u_cart(uc)
    self.sites_cart       = self.xray_structure.sites_cart()
    self.use_u_iso        = self.xray_structure.use_u_iso()
    self.use_u_aniso      = self.xray_structure.use_u_aniso()
    self.u_iso_used       = self.u_iso.select(self.use_u_iso)
    self.u_cart_used      = self.u_cart.select(self.use_u_aniso)
    self.u_iso_not_used   = self.u_iso.select(~self.use_u_iso)
    self.u_cart_not_used  = self.u_cart.select(~self.use_u_aniso)

  def selection(self, selection_strings):
    return utils.get_atom_selections(iselection       = False,
                                     all_chain_proxies= self.all_chain_proxies,
                                     selection_strings= selection_strings,
                                     xray_structure   = self.xray_structure)[0]

def exercise_basic(pdb_dir, verbose):
  file_name = os.path.join(pdb_dir, "phe_e.pdb")
  output = "modified.pdb"
  xrsp_init = xray_structure_plus(file_name = file_name)
  base = \
      "phenix.pdbtools %s output.pdb.file_name=%s "%(file_name, output)
  for selection_str in [None, "chain A or chain C"]:
    selection = xrsp_init.selection(selection_strings = selection_str)
    if(selection_str is None):
      assert selection.size() == selection.count(True)
    else:
      assert selection.size() == 36 and selection.count(True) == 24
    #
    cmd = base + 'adp.randomize=true selection="%s"'%str(selection_str)
    check_adp_rand(
      cmd, xrsp_init, output, selection, selection_str, verbose)
    #
    cmd = base + 'adp.set_b_iso=10.0 selection="%s"'%str(selection_str)
    check_adp_set_b_iso(
      cmd, xrsp_init, output, selection, selection_str, verbose)
    #
    cmd = base + 'adp.shift_b_iso=20.0 selection="%s"'%str(selection_str)
    check_adp_rand(
      cmd, xrsp_init, output, selection, selection_str, verbose)
    #
    cmd = base + 'adp.scale_adp=2.0 selection="%s"'%str(selection_str)
    check_adp_rand(
      cmd, xrsp_init, output, selection, selection_str, verbose)
    #
    cmd = base + 'adp.convert_to_iso=true selection="%s"'%str(selection_str)
    check_adp_to_iso(
      cmd, xrsp_init, output, selection, selection_str, verbose)
    #
    cmd = base + 'adp.convert_to_aniso=true selection="%s"'%str(selection_str)
    check_adp_to_aniso(
      cmd, xrsp_init, output, selection, selection_str, verbose)
    #
    shake = 1.5
    cmd = base+'sites.shake=%s selection="%s"'%(str(shake), str(selection_str))
    check_sites_shake(
      cmd, xrsp_init, output, selection, selection_str, shake, verbose)
    #
    cmd = base+'sites.rotate="1 2 3" sites.translate="4 5 6" selection="%s"'%(
                                                            str(selection_str))
    check_sites_rt(
      cmd, xrsp_init, output, selection, selection_str, verbose)
    #
    cmd = base+'occupancies.randomize=true selection="%s"'%(str(selection_str))
    check_occ_randomize(
      cmd, xrsp_init, output, selection, selection_str, verbose)
    #
    remove_selection_str = "element C"
    cmd = base+'remove.selection="%s" selection="%s"'%(
      str(remove_selection_str), str(selection_str))
    check_remove_selection(
      cmd, xrsp_init, output, selection, selection_str,
      remove_selection_str, verbose)
    #
    test_quiet(file_name, verbose)
  #
  cmd = base
  check_all_none(cmd, xrsp_init, output, verbose)

def test_quiet(file_name, verbose):
  output_file_name = "shifted.pdb"
  remove_files("log")
  remove_files(output_file_name)
  cmd= "phenix.pdbtools %s output.pdb.file_name=%s shake=0.1 --quiet > log"%(
                                        file_name, output_file_name)
  run_command(command=cmd, verbose=verbose)
  lines = open("log","r").readlines()
  assert len(lines) == 0

def check_adp_rand(
      cmd, xrsp_init, output, selection, selection_str, verbose,
      tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  assert approx_equal(xrsp.occ,        xrsp_init.occ,tolerance)
  assert approx_equal(xrsp.sites_cart, xrsp_init.sites_cart,tolerance)
  assert approx_equal(xrsp.use_u_iso,  xrsp_init.use_u_iso,tolerance)
  assert approx_equal(xrsp.use_u_aniso,xrsp_init.use_u_aniso,tolerance)
  assert approx_equal(xrsp.u_iso_not_used,  xrsp_init.u_iso_not_used,tolerance)
  assert approx_equal(xrsp.u_cart_not_used,xrsp_init.u_cart_not_used,tolerance)
  if(selection_str is None):
    assert not_approx_equal(xrsp.u_iso_used,  xrsp_init.u_iso_used,tolerance)
    assert not_approx_equal(xrsp.u_cart_used, xrsp_init.u_cart_used,tolerance)
  else:
    arg1 = xrsp.u_iso_used.select(selection.select(xrsp.use_u_iso))
    arg2 = xrsp_init.u_iso_used.select(selection.select(xrsp_init.use_u_iso))
    if(arg1.size() > 0): assert not_approx_equal(arg1, arg2,tolerance)
    arg1 =xrsp.u_cart_used.select(selection.select(xrsp.use_u_aniso))
    arg2 =xrsp_init.u_cart_used.select(selection.select(xrsp_init.use_u_aniso))
    if(arg1.size() > 0): assert not_approx_equal(arg1, arg2,tolerance)

def check_adp_set_b_iso(
      cmd, xrsp_init, output, selection, selection_str, verbose,
      tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  assert approx_equal(xrsp.occ,        xrsp_init.occ,tolerance)
  assert approx_equal(xrsp.sites_cart, xrsp_init.sites_cart,tolerance)
  assert approx_equal(xrsp.use_u_iso,  xrsp_init.use_u_iso,tolerance)
  assert approx_equal(xrsp.use_u_aniso,xrsp_init.use_u_aniso,tolerance)
  assert approx_equal(xrsp.u_iso_not_used,  xrsp_init.u_iso_not_used,tolerance)
  assert approx_equal(xrsp.u_cart_not_used,xrsp_init.u_cart_not_used,tolerance)
  if(selection_str is None):
    assert not_approx_equal(xrsp.u_iso_used,  xrsp_init.u_iso_used,tolerance)
    assert approx_equal(xrsp.u_cart, xrsp_init.u_cart,tolerance)
  else:
    arg1 = xrsp.u_iso_used.select(selection.select(xrsp.use_u_iso))
    arg2 = xrsp_init.u_iso_used.select(selection.select(xrsp_init.use_u_iso))
    if(arg1.size() > 0): assert not_approx_equal(arg1, arg2,tolerance)
    assert approx_equal(xrsp.u_cart, xrsp_init.u_cart,tolerance)

def check_adp_to_iso(
      cmd, xrsp_init, output, selection, selection_str, verbose,
      tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  assert approx_equal(xrsp.occ,        xrsp_init.occ,tolerance)
  assert approx_equal(xrsp.sites_cart, xrsp_init.sites_cart,tolerance)
  assert not_approx_equal(xrsp.use_u_iso,  xrsp_init.use_u_iso,tolerance)
  assert not_approx_equal(xrsp.use_u_aniso,xrsp_init.use_u_aniso,tolerance)
  assert xrsp.u_iso_not_used.size() == 0
  assert xrsp_init.u_iso_not_used.size() > 0
  assert xrsp.u_cart_used.size() == 0
  assert xrsp_init.u_cart_used.size() > 0

def check_adp_to_aniso(
      cmd, xrsp_init, output, selection, selection_str, verbose,
      tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  assert approx_equal(xrsp.occ,        xrsp_init.occ,tolerance)
  assert approx_equal(xrsp.sites_cart, xrsp_init.sites_cart,tolerance)
  if(selection_str is None):
    assert not_approx_equal(xrsp.use_u_iso,  xrsp_init.use_u_iso,tolerance)
    assert not_approx_equal(xrsp.use_u_aniso,xrsp_init.use_u_aniso,tolerance)
    assert xrsp.u_iso_used.size() == 0
    assert xrsp_init.u_iso_used.size() > 0
    assert xrsp.u_cart_not_used.size() == 0
    assert xrsp_init.u_cart_not_used.size() > 0
  else:
    assert approx_equal(xrsp.use_u_iso,  xrsp_init.use_u_iso,tolerance)
    assert approx_equal(xrsp.use_u_aniso,xrsp_init.use_u_aniso,tolerance)

def check_sites_shake(
      cmd, xrsp_init, output, selection, selection_str, shake, verbose,
      tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  assert approx_equal(xrsp.occ,    xrsp_init.occ,tolerance)
  assert approx_equal(xrsp.u_iso,  xrsp_init.u_iso,tolerance)
  assert approx_equal(xrsp.u_cart, xrsp_init.u_cart,tolerance)
  if(selection_str is None):
    diff = xrsp.sites_cart - xrsp_init.sites_cart
    assert approx_equal(
                      math.sqrt(flex.mean(diff.dot())), shake, 1.e-3,tolerance)
  else:
    diff = xrsp.sites_cart - xrsp_init.sites_cart
    assert approx_equal(
              math.sqrt(flex.mean(diff.select(selection).dot())), shake, 1.e-3)
    assert approx_equal(
              math.sqrt(flex.mean(diff.select(~selection).dot())),0.,tolerance)

def check_sites_rt(
      cmd, xrsp_init, output, selection, selection_str, verbose,
      tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  assert approx_equal(xrsp.occ,    xrsp_init.occ,tolerance)
  assert approx_equal(xrsp.u_iso,  xrsp_init.u_iso,tolerance)
  assert approx_equal(xrsp.u_cart, xrsp_init.u_cart,tolerance)
  if(selection_str is None):
    diff = xrsp.sites_cart - xrsp_init.sites_cart
    assert math.sqrt(flex.mean(diff.dot())) > 1.0
  else:
    diff = xrsp.sites_cart - xrsp_init.sites_cart
    assert math.sqrt(flex.mean(diff.select(selection).dot())) > 1.0
    assert approx_equal(
              math.sqrt(flex.mean(diff.select(~selection).dot())),0.,tolerance)

def check_occ_randomize(
      cmd, xrsp_init, output, selection,selection_str, verbose,
      tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  assert approx_equal(xrsp.sites_cart,xrsp_init.sites_cart,tolerance)
  assert approx_equal(xrsp.u_iso,     xrsp_init.u_iso,tolerance)
  assert approx_equal(xrsp.u_cart,    xrsp_init.u_cart,tolerance)
  if(selection_str is None):
    diff = flex.abs(xrsp.occ - xrsp_init.occ)
    assert flex.mean(diff) > 0.0
    assert flex.max(diff) > 0.0
  else:
    diff = flex.abs(xrsp.occ - xrsp_init.occ)
    assert flex.mean(diff) > 0.0
    assert flex.max(diff) > 0.0
    assert approx_equal(flex.mean(diff.select(~selection)),0.,tolerance)

def check_remove_selection(
      cmd, xrsp_init, output, selection, selection_str,
      remove_selection_str, verbose, tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  remove_selection = ~xrsp_init.selection(
                                      selection_strings = remove_selection_str)
  assert remove_selection.size() > remove_selection.count(True)
  assert approx_equal(xrsp.sites_cart,
                      xrsp_init.sites_cart.select(remove_selection),tolerance)
  assert approx_equal(
                    xrsp.occ, xrsp_init.occ.select(remove_selection),tolerance)
  assert approx_equal(
                xrsp.u_iso, xrsp_init.u_iso.select(remove_selection),tolerance)
  assert approx_equal(
              xrsp.u_cart, xrsp_init.u_cart.select(remove_selection),tolerance)
  sct1 = xrsp_init.xray_structure.scatterers().extract_scattering_types()
  assert sct1.count("C") > 0
  sct2 = xrsp.xray_structure.scatterers().extract_scattering_types()
  assert sct2.count("C") == 0
  assert sct2.size() == remove_selection.count(True)
  assert sct1.size() > sct2.size()

def check_all_none(cmd, xrsp_init, output, verbose, tolerance=1.e-3):
  remove_files(output)
  run_command(command=cmd, verbose=verbose)
  xrsp = xray_structure_plus(file_name = output)
  assert approx_equal(xrsp.occ,         xrsp_init.occ,tolerance)
  assert approx_equal(xrsp.sites_cart,  xrsp_init.sites_cart,tolerance)
  assert approx_equal(xrsp.use_u_iso,   xrsp_init.use_u_iso,tolerance)
  assert approx_equal(xrsp.use_u_aniso, xrsp_init.use_u_aniso,tolerance)
  assert approx_equal(xrsp.u_iso,       xrsp_init.u_iso,tolerance)
  assert approx_equal(xrsp.u_cart,      xrsp_init.u_cart,tolerance)

def exercise_multiple(pdb_dir, verbose):
  params = """\
adp {
  selection = chain A
  randomize = True
}
adp {
  selection = chain B
  shift_b_iso = 10
}
sites {
  selection = chain B
  shake = 1.5
}
sites {
  selection = chain A or chain C
  translate = 1 2 3
  rotate = 4 5 6
}
"""
  open("params", "w").write(params)
  file_name = os.path.join(pdb_dir, "phe_e.pdb")
  cmd = "phenix.pdbtools %s output.pdb.file_name=modified.pdb params" % (
    file_name)
  result = run_command(command=cmd, verbose=verbose)
  # XXX inspect results

def exercise_no_cryst1(pdb_dir, verbose):
  file_name = os.path.join(pdb_dir, "t.pdb")
  output = "modified.pdb"
  base = "phenix.pdbtools %s output.pdb.file_name=%s "%(file_name, output)
  cmd = base+'sites.rotate="0 0 0" sites.translate="0 0 0"'
  run_command(command=cmd, verbose=verbose)
  lines1 = []
  for line in open(file_name,"r").readlines():
    line = line.strip()
    assert line.count("CRYST1") == 0
    if(line.startswith("ATOM") or line.startswith("HETATM")):
      lines1.append(line)
  lines2 = []
  for line in open(output,"r").readlines():
    line = line.strip()
    assert line.count("CRYST1") == 0
    if(line.startswith("ATOM") or line.startswith("HETATM")):
      lines2.append(line)
  assert len(lines1) == len(lines2)
  for l1,l2 in zip(lines1, lines2):
    assert l1[11:70].strip() == l2[11:70].strip()

def exercise_show_adp_statistics(pdb_dir, verbose):
  file_name = os.path.join(pdb_dir, "t.pdb")
  cmd = "phenix.pdbtools %s --show-adp-statistics"%file_name
  run_command(command=cmd, verbose=verbose)

def exercise_show_geometry_statistics(pdb_dir, verbose):
  file_name = os.path.join(pdb_dir, "phe_e.pdb")
  cmd = "phenix.pdbtools %s --show-geometry-statistics"%file_name
  run_command(command=cmd, verbose=verbose)

def exercise(args):
  verbose = "--verbose" in args
  pdb_dir = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/pdb", test=os.path.isdir)
  if (pdb_dir is None):
    print "Skipping exercise(): input files not available"
    return
  eargs = {"pdb_dir": pdb_dir, "verbose": verbose}
  exercise_basic(**eargs)
  exercise_multiple(**eargs)
  exercise_no_cryst1(**eargs)
  exercise_show_adp_statistics(**eargs)
  exercise_show_geometry_statistics(**eargs)
  print "OK"

if (__name__ == "__main__"):
  show_times_at_exit()
  exercise(sys.argv[1:])
