from cctbx.array_family import flex
import math, time, sys, os
from libtbx import adopt_init_args
from libtbx.test_utils import approx_equal
import mmtbx.model
from libtbx import introspection
import libtbx.load_env
from mmtbx import monomer_library
import mmtbx.monomer_library.server
import mmtbx.monomer_library.pdb_interpretation
from cStringIO import StringIO

def exercise():
  # initial setup
  mon_lib_srv = monomer_library.server.server()
  ener_lib = monomer_library.server.ener_lib()
  cif_file = libtbx.env.find_in_repositories(
            relative_path="phenix_regression/pdb/tyr.cif", test=os.path.isfile)
  mon_lib_srv.process_cif(file_name= cif_file)
  ener_lib.process_cif(file_name= cif_file)
  pdb_file = libtbx.env.find_in_repositories(
            relative_path="phenix_regression/pdb/ygg.pdb", test=os.path.isfile)
  processed_pdb_file = monomer_library.pdb_interpretation.process(
                                       mon_lib_srv               = mon_lib_srv,
                                       ener_lib                  = ener_lib,
                                       file_name                 = pdb_file,
                                       raw_records               = None,
                                       force_symmetry            = True)
  xray_structure = processed_pdb_file.xray_structure()
  aal = processed_pdb_file.all_chain_proxies.stage_1.atom_attributes_list
  geometry = processed_pdb_file.geometry_restraints_manager(
                                                    show_energies      = True,
                                                    plain_pairs_radius = 5.0)
  restraints_manager = mmtbx.restraints.manager(geometry      = geometry,
                                                normalization = False)
  bond_proxies_simple = geometry.pair_proxies(
                  sites_cart = xray_structure.sites_cart()).bond_proxies.simple

  mol = mmtbx.model.manager(restraints_manager     = restraints_manager,
                            restraints_manager_ini = restraints_manager,
                            xray_structure         = xray_structure,
                            atom_attributes_list   = aal)
  # get dbe manager
  mol.add_dbe(fmodel = None)
  assert mol.dbe_selection.size() == 86
  assert mol.dbe_selection.count(True) == 45
  assert mol.dbe_selection.count(False) == 41

def run():
  exercise()

if (__name__ == "__main__"):
  run()
  print "OK"
