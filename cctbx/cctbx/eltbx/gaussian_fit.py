from cctbx.eltbx import xray_scattering
from cctbx.array_family import flex
import scitbx.math.gaussian
from scitbx.math.gaussian_fit import find_max_x_multi
from scitbx.python_utils import easy_pickle
from scitbx.python_utils.misc import adopt_init_args, user_plus_sys_time
import sys, os

# d = 1/(2*stol)
# stol = 1/(2*d)
international_tables_stols = flex.double(
  [0.00, 0.01, 0.02, 0.03, 0.04, 0.05,
   0.06, 0.07, 0.08, 0.09, 0.10,
   0.11, 0.12, 0.13, 0.14, 0.15,
   0.16, 0.17, 0.18, 0.19, 0.20,
   0.22, 0.24, 0.25, 0.26, 0.28, 0.30,
   0.32, 0.34, 0.35, 0.36, 0.38, 0.40,
   0.42, 0.44, 0.45, 0.46, 0.48, 0.50,
   0.55, 0.60, 0.65, 0.70, 0.80, 0.90, 1.00,
   1.10, 1.20, 1.30, 1.40, 1.50,
   1.60, 1.70, 1.80, 1.90, 2.00,
   2.50, 3.00, 3.50, 4.00, 5.00, 6.00])

international_tables_sigmas = flex.double(
  [0.0005, 0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0005, 0.0005, 0.0005, 0.0005, 0.0005,
   0.0008, 0.0008, 0.0008, 0.0008, 0.0008, 0.0008])

def show_fit_summary(source, label, gaussian_fit, e,
                     e_other=None, n_terms_other=None):
  n_terms = str(gaussian_fit.n_terms())
  if (gaussian_fit.c() != 0): n_terms += "+c"
  n_terms += ","
  stol = gaussian_fit.table_x()[-1]
  d_min = 1/(2*stol)
  print "%24s: %s n_terms=%-4s stol=%.2f, d_min=%.2f, e=%.4f" % (
    source, label, n_terms, stol, d_min, e),
  if (e_other is not None and e_other > e and n_terms_other == n_terms):
    print "Better",
  print

def show_literature_fits(label, n_terms, null_fit, n_points,
                         e_other=None, table_rounding_error=0.0005):
  for lib in [xray_scattering.wk1995,
              xray_scattering.it1992,
              xray_scattering.two_gaussian_agarwal_isaacs,
              xray_scattering.two_gaussian_agarwal_1978,
              xray_scattering.one_gaussian_agarwal_1978]:
    if (lib == xray_scattering.wk1995):
      try:
        lib_gaussian = xray_scattering.wk1995(label, 1).fetch()
        lib_source = "WK1995"
      except:
        lib_gaussian = None
    elif (lib == xray_scattering.it1992):
      try:
        lib_gaussian = xray_scattering.it1992(label, 1).fetch()
        lib_source = "IT1992"
      except:
        lib_gaussian = None
    elif (lib.table.has_key(label)):
      lib_gaussian = lib.table[label]
      lib_source = lib.source_short
    else:
      lib_gaussian = None
    if (lib_gaussian is not None):
      gaussian_fit = scitbx.math.gaussian.fit(
        null_fit.table_x()[:n_points],
        null_fit.table_y()[:n_points],
        null_fit.table_sigmas()[:n_points],
        lib_gaussian)
      e = flex.max(gaussian_fit.significant_relative_errors(
        table_rounding_error))
      show_fit_summary(lib_source, label, gaussian_fit, e,
                       e_other, lib_gaussian.n_terms())

def write_plot(f, xs, ys):
  for x,y in zip(xs,ys):
    print >> f, x, y
  print >> f, "&"

def write_plots(plots_dir, label, gaussian_fit, table_rounding_error=0.0005):
  label = label.replace("'", "prime")
  file_name = os.path.join(plots_dir, label+".xy")
  f = open(file_name, "w")
  write_plot(f, gaussian_fit.table_x(), gaussian_fit.table_y())
  write_plot(f, gaussian_fit.table_x(), gaussian_fit.fitted_values())
  f.close()
  file_name = os.path.join(plots_dir, label+".cmp")
  f = open(file_name, "w")
  for x,y,a,e in zip(gaussian_fit.table_x(),
                     gaussian_fit.table_y(),
                     gaussian_fit.fitted_values(),
                     gaussian_fit.significant_relative_errors(
                       table_rounding_error)):
    print >> f, "%4.2f %6.3f %6.3f %8.4f %6.3f" % (x, y, a, a-y, e)
  f.close()
  return file_name

class fit_parameters:

  def __init__(self, max_n_terms=6,
                     target_powers=[2,4],
                     minimize_using_sigmas=00000,
                     n_repeats_minimization=5,
                     enforce_positive_b_mod_n=1,
                     b_min=1.e-6,
                     max_max_error=0.01,
                     n_start_fractions=5,
                     table_rounding_error=0.0005):
    adopt_init_args(self, locals())

def incremental_fits(label, null_fit, params=None, plots_dir=None,
                     verbose=0):
  if (params is None): params = fit_parameters()
  f0 = null_fit.table_y()[0]
  results = []
  previous_n_points = 0
  existing_gaussian = xray_scattering.gaussian([],[])
  while (existing_gaussian.n_terms() < params.max_n_terms):
    if (previous_n_points == null_fit.table_x().size()):
      print "%s: Full fit with %d terms. Search stopped." % (
        label, existing_gaussian.n_terms())
      print
      break
    n_terms = existing_gaussian.n_terms() + 1
    fit = find_max_x_multi(
      null_fit=null_fit,
      existing_gaussian=existing_gaussian,
      target_powers=params.target_powers,
      minimize_using_sigmas=params.minimize_using_sigmas,
      n_repeats_minimization=params.n_repeats_minimization,
      enforce_positive_b_mod_n=params.enforce_positive_b_mod_n,
      b_min=params.b_min,
      max_max_error=params.max_max_error,
      n_start_fractions=params.n_start_fractions)
    if (fit.min is None):
      print "Warning: No fit: %s n_terms=%d" % (label, n_terms)
      print
      break
    if (previous_n_points > fit.min.final_gaussian_fit.table_x().size()):
      print "Warning: previous fit included more sampling points."
    previous_n_points = fit.min.final_gaussian_fit.table_x().size()
    show_fit_summary(
      "Best fit", label, fit.min.final_gaussian_fit, fit.max_error)
    show_literature_fits(
      label=label,
      n_terms=n_terms,
      null_fit=null_fit,
      n_points=fit.min.final_gaussian_fit.table_x().size(),
      e_other=fit.max_error,
      table_rounding_error=params.table_rounding_error)
    fit.min.final_gaussian_fit.show()
    existing_gaussian = fit.min.final_gaussian_fit
    print
    sys.stdout.flush()
    if (plots_dir):
      write_plots(
        plots_dir=plots_dir,
        label=label+"_%d"%n_terms,
        gaussian_fit=fit.min.final_gaussian_fit,
        table_rounding_error=params.table_rounding_error)
    g = fit.min.final_gaussian_fit
    results.append(xray_scattering.fitted_gaussian(
      stol=g.table_x()[-1], gaussian_sum=g))
  return results

def run(args=[], params=None, verbose=0):
  timer = user_plus_sys_time()
  if (params is None): params = fit_parameters()
  chunk_n = 1
  chunk_i = 0
  if (len(args) > 0 and len(args[0].split(",")) == 2):
    chunk_n, chunk_i = [int(i) for i in args[0].split(",")]
    args = args[1:]
  plots_dir = "plots"
  if (not os.path.isdir(plots_dir)):
    print "***************************************************************"
    print "No plots because target directory does not exist (mkdir %s)." % \
      plots_dir
    print "***************************************************************"
    print
    plots_dir = None
  if (chunk_n > 1):
    assert plots_dir is not None
  results = {}
  results["fit_parameters"] = params
  i_chunk = 0
  for wk in xray_scattering.wk1995_iterator():
    flag = i_chunk % chunk_n == chunk_i
    i_chunk += 1
    if (not flag):
      continue
    if (len(args) > 0 and wk.label() not in args): continue
    null_fit = scitbx.math.gaussian.fit(
      international_tables_stols,
      wk.fetch(),
      international_tables_sigmas,
      xray_scattering.gaussian(0, 00000))
    results[wk.label()] = incremental_fits(
      label=wk.label(),
      null_fit=null_fit,
      params=params,
      plots_dir=plots_dir,
      verbose=verbose)
    sys.stdout.flush()
    easy_pickle.dump("fits_%02d.pickle" % chunk_i, results)
  print "CPU time: %.2f seconds" % timer.elapsed()

if (__name__ == "__main__"):
  from cctbx.eltbx.gaussian_fit import run
  run(sys.argv[1:])
