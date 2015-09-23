from __future__ import division
import cctbx.array_family.flex # import dependency
import boost.python
ext = boost.python.import_ext("mmtbx_ncs_ext")
import iotbx.pdb
from scitbx.array_family import flex
from mmtbx.ncs import tncs
from libtbx.test_utils import approx_equal

pdb_str="""
CRYST1   55.000   55.000   55.000  90.00  90.00  90.00 P 1
SCALE1      0.018182  0.000000  0.000000        0.00000
SCALE2      0.000000  0.018182  0.000000        0.00000
SCALE3      0.000000  0.000000  0.018182        0.00000
ATOM      1 C7   ALA A   1      13.701  17.636  20.433  1.00 10.00           C
ATOM      2 C116 ALA A   2      12.366   6.187  17.949  1.00 10.00           C
ATOM      3 C135 ALA A   3      12.358  18.443  20.392  1.00 10.00           C
ATOM      4 C318 ALA A   4      16.723   9.456  15.994  1.00 10.00           C
ATOM      5 C325 ALA A   5      13.023  10.841  10.069  1.00 10.00           C
ATOM      6 C375 ALA A   6      12.752  15.083   6.413  1.00 10.00           C
ATOM      7 C393 ALA A   7      10.852  10.986   7.235  1.00 10.00           C
ATOM      8 C423 ALA A   8       6.856  17.368  17.973  1.00 10.00           C
ATOM      9 C529 ALA A   9       8.289  18.565  18.488  1.00 10.00           C
ATOM     10 C582 ALA A  10      18.055  19.070   8.401  1.00 10.00           C
ATOM     11 C668 ALA A  11       9.912  22.046  11.754  1.00 10.00           C
ATOM     12 C723 ALA A  12      12.430  16.010  19.850  1.00 10.00           C
ATOM     13 C768 ALA A  13      11.102  15.960  19.526  1.00 10.00           C
ATOM     14 C769 ALA A  14       8.437  12.573  12.854  1.00 10.00           C
ATOM     15 C801 ALA A  15      17.327  17.934  17.256  1.00 10.00           C
ATOM     16 C829 ALA A  16       8.276  18.775  10.775  1.00 10.00           C
ATOM     17 C845 ALA A  17      12.801  22.237   9.595  1.00 10.00           C
ATOM     18 C900 ALA A  18      14.712  14.808  14.485  1.00 10.00           C
ATOM     19 C959 ALA A  19       7.926  15.643   9.501  1.00 10.00           C
ATOM     20 C978 ALA A  20      13.077  16.727  22.622  1.00 10.00           C
ATOM     21 C104 ALA A  21      11.201   9.953  17.040  1.00 10.00           C
ATOM     22 C107 ALA A  22       9.132   7.449  13.843  1.00 10.00           C
ATOM     23 C109 ALA A  23      17.073  16.541  15.076  1.00 10.00           C
ATOM     24 C113 ALA A  24      18.273  10.890  19.158  1.00 10.00           C
ATOM     25 C114 ALA A  25       9.020  12.518  15.904  1.00 10.00           C
ATOM     26 C129 ALA A  26      19.727   9.098  21.104  1.00 10.00           C
ATOM     27 C129 ALA A  27      23.544  17.469  18.536  1.00 10.00           C
ATOM     28 C130 ALA A  28      17.361  17.842  13.001  1.00 10.00           C
ATOM     29 C134 ALA A  29      17.419  12.979  14.542  1.00 10.00           C
ATOM     30 C152 ALA A  30      19.464  11.727  19.346  1.00 10.00           C
ATOM     31 C153 ALA A  31      22.842  12.077  10.237  1.00 10.00           C
ATOM     32 C154 ALA A  32      16.451  13.085  16.752  1.00 10.00           C
ATOM     33 C164 ALA A  33      10.038  20.697  14.559  1.00 10.00           C
ATOM     34 C167 ALA A  34      14.185  20.324   7.437  1.00 10.00           C
ATOM     35 C168 ALA A  35       6.300  17.761  11.873  1.00 10.00           C
ATOM     36 C169 ALA A  36      22.681  12.748  10.334  1.00 10.00           C
ATOM     37 C174 ALA A  37      14.879  15.242  21.473  1.00 10.00           C
ATOM     38 C177 ALA A  38      12.619  10.245  17.743  1.00 10.00           C
ATOM     39 C178 ALA A  39      20.810  12.695  12.135  1.00 10.00           C
ATOM     40 C183 ALA A  40      19.126  18.354  21.302  1.00 10.00           C
ATOM     41 C186 ALA A  41      22.171   9.795  15.535  1.00 10.00           C
ATOM     42 C187 ALA A  42      10.123  20.228  15.505  1.00 10.00           C
ATOM     43 C189 ALA A  43      14.218  20.351  20.400  1.00 10.00           C
ATOM     44 C190 ALA A  44      17.990  14.381   8.065  1.00 10.00           C
ATOM     45 C192 ALA A  45      22.487  11.050   9.852  1.00 10.00           C
ATOM     46 C195 ALA A  46      13.513   9.358  17.902  1.00 10.00           C
ATOM     47 C216 ALA A  47      19.547  19.669  18.906  1.00 10.00           C
ATOM     48 C221 ALA A  48      16.348  19.661  14.511  1.00 10.00           C
ATOM     49 C226 ALA A  49      14.910  11.972  18.502  1.00 10.00           C
ATOM     50 C229 ALA A  50      18.475  23.509  15.945  1.00 10.00           C
ATOM     51 C234 ALA A  51      11.102  10.570  17.360  1.00 10.00           C
ATOM     52 C237 ALA A  52      14.353  22.477  18.648  1.00 10.00           C
ATOM     53 C247 ALA A  53       9.150  19.933  10.445  1.00 10.00           C
ATOM     54 C250 ALA A  54      18.684   6.783  11.555  1.00 10.00           C
ATOM     55 C253 ALA A  55      22.260  15.618  18.081  1.00 10.00           C
ATOM     56 C254 ALA A  56       8.434  20.022  15.818  1.00 10.00           C
ATOM     57 C259 ALA A  57      16.042  14.366   5.312  1.00 10.00           C
ATOM     58 C262 ALA A  58      21.392  21.650  14.481  1.00 10.00           C
ATOM     59 C264 ALA A  59       6.678  17.698  12.625  1.00 10.00           C
ATOM     60 C269 ALA A  60       8.327  12.879  17.470  1.00 10.00           C
ATOM     61 C271 ALA A  61       7.510   9.079  17.557  1.00 10.00           C
ATOM     62 C273 ALA A  62      11.103  16.026  20.771  1.00 10.00           C
ATOM     63 C279 ALA A  63      19.453   8.063  20.118  1.00 10.00           C
ATOM     64 C285 ALA A  64      18.893   7.710  10.625  1.00 10.00           C
ATOM     65 C295 ALA A  65      20.485  20.440  11.734  1.00 10.00           C
ATOM     66 C304 ALA A  66      13.310  10.067  10.497  1.00 10.00           C
ATOM     67 C304 ALA A  67      13.522  10.034  22.514  1.00 10.00           C
ATOM     68 C307 ALA A  68      13.752   5.717  11.896  1.00 10.00           C
ATOM     69 C309 ALA A  69       9.873  10.448  12.931  1.00 10.00           C
ATOM     70 C316 ALA A  70      17.329  16.937  17.428  1.00 10.00           C
ATOM     71 C316 ALA A  71      12.746  11.817  20.837  1.00 10.00           C
ATOM     72 C336 ALA A  72      17.247  10.742  17.405  1.00 10.00           C
ATOM     73 C337 ALA A  73      21.636  11.562  20.613  1.00 10.00           C
ATOM     74 C344 ALA A  74      20.145  20.995  20.309  1.00 10.00           C
ATOM     75 C345 ALA A  75       9.873  12.910  10.483  1.00 10.00           C
ATOM     76 C348 ALA A  76      14.952  20.215  12.301  1.00 10.00           C
ATOM     77 C357 ALA A  77       9.415  11.208   8.319  1.00 10.00           C
ATOM     78 C358 ALA A  78      14.853  16.782  11.204  1.00 10.00           C
ATOM     79 C364 ALA A  79      13.852  15.132  24.685  1.00 10.00           C
ATOM     80 C366 ALA A  80      18.626  10.327  17.281  1.00 10.00           C
ATOM     81 C376 ALA A  81      13.940  16.792  11.870  1.00 10.00           C
ATOM     82 C392 ALA A  82      10.279  17.606  21.633  1.00 10.00           C
ATOM     83 C395 ALA A  83       5.395  16.876  15.353  1.00 10.00           C
ATOM     84 C399 ALA A  84      12.370  14.354  19.736  1.00 10.00           C
TER
ATOM      1 C7   ALA B   1      34.105  37.076  40.618  1.00 10.00           C
ATOM      2 C116 ALA B   2      32.437  26.057  37.264  1.00 10.00           C
ATOM      3 C135 ALA B   3      32.392  37.996  40.951  1.00 10.00           C
ATOM      4 C318 ALA B   4      37.193  29.639  35.870  1.00 10.00           C
ATOM      5 C325 ALA B   5      32.591  30.896  30.164  1.00 10.00           C
ATOM      6 C375 ALA B   6      32.307  35.048  26.823  1.00 10.00           C
ATOM      7 C393 ALA B   7      31.037  31.201  27.096  1.00 10.00           C
ATOM      8 C423 ALA B   8      26.841  36.978  38.074  1.00 10.00           C
ATOM      9 C529 ALA B   9      28.627  37.883  38.522  1.00 10.00           C
ATOM     10 C582 ALA B  10      37.454  39.526  28.120  1.00 10.00           C
ATOM     11 C668 ALA B  11      29.348  41.781  32.056  1.00 10.00           C
ATOM     12 C723 ALA B  12      32.618  35.604  40.023  1.00 10.00           C
ATOM     13 C768 ALA B  13      31.549  35.805  39.410  1.00 10.00           C
ATOM     14 C769 ALA B  14      28.625  32.682  33.048  1.00 10.00           C
ATOM     15 C801 ALA B  15      37.381  38.195  37.187  1.00 10.00           C
ATOM     16 C829 ALA B  16      27.919  39.046  30.886  1.00 10.00           C
ATOM     17 C845 ALA B  17      32.342  42.790  30.078  1.00 10.00           C
ATOM     18 C900 ALA B  18      34.932  35.084  34.457  1.00 10.00           C
ATOM     19 C959 ALA B  19      27.513  35.402  29.410  1.00 10.00           C
ATOM     20 C978 ALA B  20      33.383  36.333  42.869  1.00 10.00           C
ATOM     21 C104 ALA B  21      31.282  29.487  36.620  1.00 10.00           C
ATOM     22 C107 ALA B  22      29.377  27.072  33.374  1.00 10.00           C
ATOM     23 C109 ALA B  23      37.334  36.283  34.901  1.00 10.00           C
ATOM     24 C113 ALA B  24      38.395  30.716  38.571  1.00 10.00           C
ATOM     25 C114 ALA B  25      29.406  32.512  36.213  1.00 10.00           C
ATOM     26 C129 ALA B  26      39.845  28.668  40.941  1.00 10.00           C
ATOM     27 C129 ALA B  27      43.677  37.204  38.244  1.00 10.00           C
ATOM     28 C130 ALA B  28      37.076  37.669  32.668  1.00 10.00           C
ATOM     29 C134 ALA B  29      37.422  33.309  34.243  1.00 10.00           C
ATOM     30 C152 ALA B  30      39.978  31.548  39.306  1.00 10.00           C
ATOM     31 C153 ALA B  31      43.046  32.626  30.113  1.00 10.00           C
ATOM     32 C154 ALA B  32      36.394  32.860  36.616  1.00 10.00           C
ATOM     33 C164 ALA B  33      30.103  40.815  35.011  1.00 10.00           C
ATOM     34 C167 ALA B  34      33.842  40.676  27.604  1.00 10.00           C
ATOM     35 C168 ALA B  35      25.835  37.554  32.202  1.00 10.00           C
ATOM     36 C169 ALA B  36      42.835  33.471  29.848  1.00 10.00           C
ATOM     37 C174 ALA B  37      35.210  35.215  41.213  1.00 10.00           C
ATOM     38 C177 ALA B  38      32.497  29.896  37.900  1.00 10.00           C
ATOM     39 C178 ALA B  39      40.735  32.729  31.555  1.00 10.00           C
ATOM     40 C183 ALA B  40      39.498  38.264  41.586  1.00 10.00           C
ATOM     41 C186 ALA B  41      42.030  29.676  34.848  1.00 10.00           C
ATOM     42 C187 ALA B  42      29.710  40.046  35.599  1.00 10.00           C
ATOM     43 C189 ALA B  43      34.280  40.116  40.500  1.00 10.00           C
ATOM     44 C190 ALA B  44      38.075  34.623  27.639  1.00 10.00           C
ATOM     45 C192 ALA B  45      42.072  31.696  29.134  1.00 10.00           C
ATOM     46 C195 ALA B  46      34.111  29.249  37.354  1.00 10.00           C
ATOM     47 C216 ALA B  47      39.769  39.718  38.871  1.00 10.00           C
ATOM     48 C221 ALA B  48      36.001  40.029  34.774  1.00 10.00           C
ATOM     49 C226 ALA B  49      34.730  31.636  38.736  1.00 10.00           C
ATOM     50 C229 ALA B  50      38.003  43.407  35.891  1.00 10.00           C
ATOM     51 C234 ALA B  51      31.308  30.214  36.950  1.00 10.00           C
ATOM     52 C237 ALA B  52      34.148  42.169  38.714  1.00 10.00           C
ATOM     53 C247 ALA B  53      29.120  39.727  30.704  1.00 10.00           C
ATOM     54 C250 ALA B  54      38.379  27.051  31.007  1.00 10.00           C
ATOM     55 C253 ALA B  55      42.124  35.709  37.741  1.00 10.00           C
ATOM     56 C254 ALA B  56      27.991  40.000  36.357  1.00 10.00           C
ATOM     57 C259 ALA B  57      35.558  34.654  24.899  1.00 10.00           C
ATOM     58 C262 ALA B  58      41.492  41.787  34.694  1.00 10.00           C
ATOM     59 C264 ALA B  59      26.421  37.256  33.036  1.00 10.00           C
ATOM     60 C269 ALA B  60      28.363  32.288  37.755  1.00 10.00           C
ATOM     61 C271 ALA B  61      27.845  29.111  37.600  1.00 10.00           C
ATOM     62 C273 ALA B  62      30.879  35.542  41.065  1.00 10.00           C
ATOM     63 C279 ALA B  63      40.101  28.033  39.328  1.00 10.00           C
ATOM     64 C285 ALA B  64      38.919  27.919  30.479  1.00 10.00           C
ATOM     65 C295 ALA B  65      40.586  40.919  32.140  1.00 10.00           C
ATOM     66 C304 ALA B  66      33.396  30.329  30.243  1.00 10.00           C
ATOM     67 C304 ALA B  67      34.240  29.637  42.184  1.00 10.00           C
ATOM     68 C307 ALA B  68      34.005  25.591  31.545  1.00 10.00           C
ATOM     69 C309 ALA B  69      30.053  30.085  32.739  1.00 10.00           C
ATOM     70 C316 ALA B  70      37.143  36.817  37.056  1.00 10.00           C
ATOM     71 C316 ALA B  71      32.894  31.825  40.769  1.00 10.00           C
ATOM     72 C336 ALA B  72      37.257  30.466  37.187  1.00 10.00           C
ATOM     73 C337 ALA B  73      42.177  31.914  40.533  1.00 10.00           C
ATOM     74 C344 ALA B  74      40.142  40.553  40.036  1.00 10.00           C
ATOM     75 C345 ALA B  75      29.931  32.680  30.434  1.00 10.00           C
ATOM     76 C348 ALA B  76      34.401  40.448  32.452  1.00 10.00           C
ATOM     77 C357 ALA B  77      29.597  31.036  28.440  1.00 10.00           C
ATOM     78 C358 ALA B  78      34.705  36.748  31.303  1.00 10.00           C
ATOM     79 C364 ALA B  79      34.499  34.741  44.806  1.00 10.00           C
ATOM     80 C366 ALA B  80      39.142  30.459  37.147  1.00 10.00           C
ATOM     81 C376 ALA B  81      33.832  37.046  31.738  1.00 10.00           C
ATOM     82 C392 ALA B  82      30.121  37.122  42.189  1.00 10.00           C
ATOM     83 C395 ALA B  83      25.486  36.337  36.112  1.00 10.00           C
ATOM     84 C399 ALA B  84      32.248  34.298  40.158  1.00 10.00           C
TER
END
"""

def e_sm(f_obs, reflections_per_bin, eps_fac = None):
  # compute E and E**2
  eps = f_obs.epsilons().data().as_double()
  if(eps_fac is not None):
    eps = eps * eps_fac
  f_obs.setup_binner(reflections_per_bin = reflections_per_bin)
  E = flex.double(f_obs.data().size(), 0)
  for i_bin in f_obs.binner().range_used():
    bin_sel = f_obs.binner().selection(i_bin)
    fo = f_obs.data().select(bin_sel)
    if(fo.size()==0): continue
    e = eps.select(bin_sel)
    fo_eps = fo/flex.sqrt(e)
    E_bin = fo_eps/(flex.sum(fo_eps**2)/fo_eps.size())**0.5
    E = E.set_selected(bin_sel, E_bin)
  E_sq = E**2
  # compute <E**4>/<E**2>**2
  centrics_selection  = f_obs.centric_flags().data()
  result = []
  for prefix, sel in [("centric:",  centrics_selection),
                      ("acentric:",~centrics_selection)]:
    if(sel.count(True)==0): continue
    E_ = E.select(sel)
    E_sq_ = E_sq.select(sel)
    result.append(flex.mean(E_sq_*E_sq_)/flex.mean(E_sq_)**2)
  return result

def exercise_00(reflections_per_bin=150):
  """
  Finite differences test for radii
  """
  pdb_inp = iotbx.pdb.input(source_info=None, lines=pdb_str)
  pdb_inp.write_pdb_file(file_name="model.pdb")
  xray_structure = pdb_inp.xray_structure_simple()
  xray_structure = xray_structure.set_b_iso(value=10)
  f_obs = abs(xray_structure.structure_factors(d_min=2.0).f_calc())
  f_obs.set_sigmas(sigmas = flex.double(f_obs.data().size(), 0.0))
  reflections_per_bin = min(f_obs.data().size(), reflections_per_bin)
  f_obs.setup_binner(reflections_per_bin = reflections_per_bin)
  binner = f_obs.binner()
  n_bins = binner.n_bins_used()
  #
  ncs_pairs = tncs.groups(
    pdb_hierarchy    = pdb_inp.construct_hierarchy(),
    crystal_symmetry = f_obs.crystal_symmetry(),
    n_bins           = n_bins).ncs_pairs
  ncs_pairs[0].set_radius(5)
  pot = tncs.potential(f_obs = f_obs, ncs_pairs = ncs_pairs,
      reflections_per_bin = reflections_per_bin)
  pot = pot.set_refine_radius()
  t = pot.target()
  g_exact = pot.gradient()
  #
  eps = 1.e-3
  #
  pot.update(x = flex.double([5+eps]))
  t1 = pot.target()
  #
  pot.update(x = flex.double([5-eps]))
  t2 = pot.target()
  #
  g_fd = (t1-t2)/(2*eps)
  #
  assert approx_equal(g_fd, g_exact[0], 1.e-6)

def exercise_01(reflections_per_bin=150):
  """
  Finite differences test for rho_mn.
  """
  pdb_inp = iotbx.pdb.input(source_info=None, lines=pdb_str)
  pdb_inp.write_pdb_file(file_name="model.pdb")
  xray_structure = pdb_inp.xray_structure_simple()
  xray_structure = xray_structure.set_b_iso(value=10)
  f_obs = abs(xray_structure.structure_factors(d_min=2.0).f_calc())
  f_obs.set_sigmas(sigmas = flex.double(f_obs.data().size(), 0.0))
  reflections_per_bin = min(f_obs.data().size(), reflections_per_bin)
  f_obs.setup_binner(reflections_per_bin = reflections_per_bin)
  binner = f_obs.binner()
  n_bins = binner.n_bins_used()
  #
  ncs_pairs = tncs.groups(
    pdb_hierarchy    = pdb_inp.construct_hierarchy(),
    crystal_symmetry = f_obs.crystal_symmetry(),
    n_bins           = n_bins).ncs_pairs
  #
  pot = tncs.potential(f_obs = f_obs, ncs_pairs = ncs_pairs,
      reflections_per_bin = reflections_per_bin)
  pot = pot.set_refine_rhoMN()
  t = pot.target()
  g_exact = pot.gradient()
  #print "Exact:", list(g_exact)
  #
  rho_mn = flex.double()
  for p in ncs_pairs:
    rho_mn.extend(p.rho_mn)
  #
  eps = 1.e-6
  #
  g_fd = []
  for i, rho_mn_i in enumerate(rho_mn):
    rho_mn_p = rho_mn.deep_copy()
    rho_mn_p[i] = rho_mn_i + eps
    rho_mn_m = rho_mn.deep_copy()
    rho_mn_m[i] = rho_mn_i - eps
    #
    pot.update(x = rho_mn_p)
    t1 = pot.target()
    #
    pot.update(x = rho_mn_m)
    t2 = pot.target()
    #
    g_fd_ = (t1-t2)/(2*eps)
    g_fd.append(g_fd_)
  #print "Finite diff.:",g_fd
  assert approx_equal(g_fd, g_exact, 1.e-3)

def exercise_02(reflections_per_bin=150):
  """
  tncs_epsfac calculation with radius refinement
  """
  pdb_inp = iotbx.pdb.input(source_info=None, lines=pdb_str)
  pdb_inp.write_pdb_file(file_name="model.pdb")
  xray_structure = pdb_inp.xray_structure_simple()
  for b in [0, 50, 100, 200, 400, 800]:
    xray_structure = xray_structure.set_b_iso(value=b)
    print "B: %5.1f"%b
    for d_min in [2,3,4,6,8]:
      f_obs = abs(xray_structure.structure_factors(d_min=d_min).f_calc())
      result = tncs.compute_eps_factor(
        f_obs               = f_obs,
        pdb_hierarchy       = pdb_inp.construct_hierarchy(),
        reflections_per_bin = reflections_per_bin)
      M2      = e_sm(f_obs, reflections_per_bin)[0]
      M2_corr = e_sm(f_obs, reflections_per_bin, result.epsfac)[0]
      fmt="  d_min: %5.1f R: refined %4.1f estimate %4.1f 2nd Mom.: orig %4.2f corr %4.2f"
      print fmt%(d_min, result.ncs_pairs[0].radius,
        result.ncs_pairs[0].radius_estimate, M2, M2_corr)
  # this shows summary for the result corresponding to last trial B and d_min
  result.show_summary()

if (__name__ == "__main__"):
  exercise_00()
  exercise_01()
  exercise_02()
