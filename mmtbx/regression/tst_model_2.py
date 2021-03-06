from __future__ import division
import libtbx.load_env
import mmtbx.model
from mmtbx import monomer_library
import mmtbx.monomer_library.server
import mmtbx.monomer_library.pdb_interpretation
import sys
import time

pdb_str_1 = """
CRYST1   79.110   79.110   37.465  90.00  90.00  90.00 P 43 21 2
ATOM      1  N   GLY A  67      11.351   9.426  29.699  1.00 16.57      A    N
ATOM      2  CA  GLY A  67      12.344   8.654  30.419  1.00 16.65      A    C
ATOM      3  C   GLY A  67      13.703   9.318  30.525  1.00 17.27      A    C
ATOM      4  O   GLY A  67      14.613   8.754  31.138  1.00 18.12      A    O
ATOM      5  HA2 GLY A  67      12.423   8.145  31.069  1.00 19.98      A    H
ATOM      6  HA3 GLY A  67      12.500   7.679  29.465  1.00 19.98      A    H
ATOM      7  H  AGLY A  67      11.059  10.035  30.076  0.23 19.88      A    H
ATOM      8  D  BGLY A  67      10.213   9.620  30.015  0.77 19.88      A    D
ATOM      9  N   ARG A  68      13.850  10.509  29.946  1.00 17.04      A    N
ATOM     10  CA  ARG A  68      15.122  11.232  30.010  1.00 18.21      A    C
ATOM     11  C   ARG A  68      14.955  12.712  30.337  1.00 19.28      A    C
ATOM     12  O   ARG A  68      15.856  13.506  30.060  1.00 18.39      A    O
ATOM     13  CB  ARG A  68      15.888  11.102  28.683  1.00 17.72      A    C
ATOM     14  CG  ARG A  68      15.297  11.878  27.495  1.00 17.98      A    C
ATOM     15  CD  ARG A  68      16.259  11.919  26.349  1.00 18.60      A    C
ATOM     16  NE  ARG A  68      15.794  12.838  25.306  1.00 17.24      A    N
ATOM     17  CZ  ARG A  68      16.143  12.775  24.023  1.00 19.10      A    C
ATOM     18  NH1 ARG A  68      16.951  11.815  23.586  1.00 18.15      A    N
ATOM     19  NH2 ARG A  68      15.667  13.670  23.169  1.00 19.17      A    N
ATOM     20  HA  ARG A  68      15.830  11.010  30.791  1.00 21.85      A    H
ATOM     21  HB2 ARG A  68      17.337  11.333  28.919  1.00 21.26      A    H
ATOM     22  HB3 ARG A  68      15.561   9.834  28.355  1.00 21.26      A    H
ATOM     23  HG2 ARG A  68      14.659  11.228  27.304  1.00 21.57      A    H
ATOM     24  HG3 ARG A  68      15.210  12.439  27.504  1.00 21.57      A    H
ATOM     25  HD2 ARG A  68      17.528  12.809  26.638  1.00 22.31      A    H
ATOM     26  HD3 ARG A  68      16.578  11.260  25.838  1.00 22.31      A    H
ATOM     28  HE AARG A  68      14.669  13.645  25.770  0.36 20.68      A    H
ATOM     29 HH11AARG A  68      16.967  11.381  22.649  0.47 21.78      A    H
ATOM     30 HH12AARG A  68      17.341  12.024  22.866  0.63 21.78      A    H
ATOM     31 HH21AARG A  68      15.024  14.090  23.756  0.17 23.00      A    H
ATOM     32 HH22AARG A  68      16.091  13.841  22.354  0.05 23.00      A    H
ATOM     34  DE BARG A  68      15.088  13.911  25.471  0.64 20.68      A    D
ATOM     35 DH11BARG A  68      17.608  11.777  22.724  0.53 21.78      A    D
ATOM     36 DH12BARG A  68      17.213  11.872  23.102  0.37 21.78      A    D
ATOM     37 DH21BARG A  68      15.418  14.257  23.927  0.83 23.00      A    D
ATOM     38 DH22BARG A  68      16.100  13.112  22.705  0.95 23.00      A    D
ATOM     39  N   THR A  69      13.811  13.085  30.907  1.00 18.60      A    N
ATOM     40  CA  THR A  69      13.578  14.468  31.314  1.00 21.27      A    C
ATOM     41  C   THR A  69      13.418  14.522  32.825  1.00 23.37      A    C
ATOM     42  O   THR A  69      12.315  14.330  33.336  1.00 22.36      A    O
ATOM     43  CB  THR A  69      12.332  15.076  30.647  1.00 18.85      A    C
ATOM     44  OG1 THR A  69      12.366  14.826  29.239  1.00 16.82      A    O
ATOM     45  CG2 THR A  69      12.281  16.578  30.889  1.00 22.56      A    C
ATOM     46  HA  THR A  69      14.629  15.325  31.109  1.00 25.52      A    H
ATOM     47  HB  THR A  69      10.945  14.324  30.978  1.00 22.62      A    H
ATOM     48 HG21 THR A  69      11.903  16.728  32.276  1.00 27.08      A    H
ATOM     49 HG22 THR A  69      12.881  17.251  30.508  1.00 27.08      A    H
ATOM     50 HG23 THR A  69      11.505  17.383  30.947  1.00 27.08      A    H
ATOM     51  H  ATHR A  69      12.567  12.975  31.042  0.05 22.32      A    H
ATOM     52  HG1ATHR A  69      12.071  14.204  28.953  0.10 20.18      A    H
ATOM     53  D  BTHR A  69      13.365  12.836  31.566  0.95 22.32      A    D
ATOM     54  DG1BTHR A  69      12.219  13.577  29.249  0.90 20.18      A    D
TER
END
"""

pdb_str_2 = """
CRYST1   34.238   35.096   43.858  90.00  90.00  90.00 P 21 21 21    0
ATOM      1  N   LYS A  45       6.154   2.754   1.212  1.00 12.39           N
ATOM      2  C   LYS A  45       7.533   2.537  -0.815  1.00  8.18           C
ATOM      3  O   LYS A  45       8.546   2.217  -1.437  1.00  8.18           O
ATOM      4  CA ALYS A  45       7.469   2.388   0.702  0.18  8.95           C
ATOM      5  CB ALYS A  45       7.820   0.954   1.105  0.18 15.56           C
ATOM      6  CG ALYS A  45       7.880   0.729   2.607  0.18  7.12           C
ATOM      7  CD ALYS A  45       8.227  -0.714   2.935  0.18 22.74           C
ATOM      8  CE ALYS A  45       8.402  -0.914   4.432  0.18 43.83           C
ATOM      9  NZ ALYS A  45       7.134  -0.676   5.175  0.18 58.88           N
ATOM     23  CA BLYS A  45       7.396   2.217   0.670  0.82  9.42           C
ATOM     24  CB BLYS A  45       7.467   0.704   0.891  0.82 15.14           C
ATOM     25  CG BLYS A  45       7.428   0.288   2.352  0.82  9.76           C
ATOM     26  CD BLYS A  45       7.539  -1.221   2.500  0.82 22.13           C
ATOM     27  CE BLYS A  45       6.396  -1.931   1.793  0.82 22.20           C
ATOM     28  NZ BLYS A  45       6.495  -3.411   1.927  0.82 22.09           N
ATOM      0  HA ALYS A  45       8.198   3.068   1.142  0.18  9.42           H   new
ATOM      0  HA BLYS A  45       8.223   2.691   1.198  0.82  9.42           H   new
ATOM      0  HB2ALYS A  45       7.082   0.276   0.676  0.18 15.14           H   new
ATOM      0  HB2BLYS A  45       6.636   0.232   0.368  0.82 15.14           H   new
ATOM      0  HB3ALYS A  45       8.784   0.691   0.670  0.18 15.14           H   new
ATOM      0  HB3BLYS A  45       8.384   0.324   0.441  0.82 15.14           H   new
ATOM      0  HG2ALYS A  45       8.624   1.393   3.047  0.18  9.76           H   new
ATOM      0  HG2BLYS A  45       8.244   0.769   2.891  0.82  9.76           H   new
ATOM      0  HG3ALYS A  45       6.919   0.985   3.054  0.18  9.76           H   new
ATOM      0  HG3BLYS A  45       6.499   0.633   2.806  0.82  9.76           H   new
ATOM      0  HD2ALYS A  45       7.439  -1.372   2.568  0.18 22.13           H   new
ATOM      0  HD2BLYS A  45       8.490  -1.560   2.089  0.82 22.13           H   new
ATOM      0  HD3ALYS A  45       9.145  -0.996   2.419  0.18 22.13           H   new
ATOM      0  HD3BLYS A  45       7.536  -1.486   3.557  0.82 22.13           H   new
ATOM      0  HE2ALYS A  45       8.751  -1.929   4.625  0.18 22.20           H   new
ATOM      0  HE2BLYS A  45       5.446  -1.592   2.207  0.82 22.20           H   new
ATOM      0  HE3ALYS A  45       9.172  -0.237   4.801  0.18 22.20           H   new
ATOM      0  HE3BLYS A  45       6.398  -1.661   0.737  0.82 22.20           H   new
ATOM      0  HZ1ALYS A  45       7.263  -0.936   6.174  0.18 22.09           H   new
ATOM      0  HZ1BLYS A  45       5.698  -3.859   1.432  0.82 22.09           H   new
ATOM      0  HZ2ALYS A  45       6.877   0.330   5.110  0.18 22.09           H   new
ATOM      0  HZ2BLYS A  45       7.390  -3.738   1.510  0.82 22.09           H   new
ATOM      0  HZ3ALYS A  45       6.375  -1.255   4.761  0.18 22.09           H   new
ATOM      0  HZ3BLYS A  45       6.467  -3.671   2.934  0.82 22.09           H   new
TER
END
"""

def run(args):
  if (not libtbx.env.has_module("reduce")) :
    print "Reduce not installed, needed for model.idealize_h(). skipping"
    return
  for pdb_str in [pdb_str_1, pdb_str_2]:
    for use_neutron_distances in [True, False]:
      print "use_neutron_distances:", use_neutron_distances, "*"*30
      params = monomer_library.pdb_interpretation.master_params.extract()
      params.use_neutron_distances = use_neutron_distances
      processed_pdb_file = monomer_library.pdb_interpretation.process(
        mon_lib_srv    = monomer_library.server.server(),
        ener_lib       = monomer_library.server.ener_lib(
          use_neutron_distances=use_neutron_distances),
        raw_records    = pdb_str,
        params         = params,
        force_symmetry = True)
      xray_structure = processed_pdb_file.xray_structure()
      sctr_keys = \
        xray_structure.scattering_type_registry().type_count_dict().keys()
      has_hd = "H" in sctr_keys or "D" in sctr_keys
      geometry = processed_pdb_file.geometry_restraints_manager(
        show_energies      = False,
        assume_hydrogens_all_missing = not has_hd,
        plain_pairs_radius = 5.0)
      restraints_manager = mmtbx.restraints.manager(
        geometry = geometry, normalization = False)
      xrs = xray_structure.deep_copy_scatterers()
      m = mmtbx.model.manager(
        restraints_manager = restraints_manager,
        xray_structure     = xrs,
        pdb_hierarchy      = processed_pdb_file.all_chain_proxies.pdb_hierarchy)
      #
      r1 = m.geometry_statistics(ignore_hd = False)
      m.idealize_h(show=False)
      r2 = m.geometry_statistics(ignore_hd = False)
      print "%6.3f %6.3f %6.3f %6.3f"%(r1.a_mean,r1.b_mean, r2.a_mean,r2.b_mean)
      assert r2.a_mean < 1.0, "assertion %f < 1.0" % r2.a_mean
      assert r2.b_mean < 0.01, "assertion %f < 0.01" % r2.b_mean

if (__name__ == "__main__"):
  t0 = time.time()
  run(sys.argv[1:])
  print "Time: %6.3f"%(time.time()-t0)
