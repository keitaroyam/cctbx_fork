from cctbx.eltbx import xray_scattering
import cctbx.eltbx.gaussian_fit
import scitbx.math.gaussian_fit
from cctbx.array_family import flex
import scitbx.math.gaussian
import sys, os

def run(args, plots_dir="wk1995_it1992_plots"):
  if ("--help" in args or len(args) not in [0,1]):
    print "usage: python wk1995_it1992.py [d_min]"
    return
  d_min = 1/4.
  if (len(args) == 1):
    d_min = float(args[0])
    assert d_min > 0
  stol_max = 1/(2*d_min)
  n_points = scitbx.math.gaussian_fit.n_less_than(
    sorted_array=cctbx.eltbx.gaussian_fit.international_tables_stols,
    cutoff=stol_max)
  labels = flex.std_string()
  max_errors = flex.double()
  for wk in xray_scattering.wk1995_iterator():
    it = xray_scattering.it1992(wk.label(), 1)
    gaussian_fit = scitbx.math.gaussian.fit(
      cctbx.eltbx.gaussian_fit.international_tables_stols[:n_points],
      wk.fetch(),
      cctbx.eltbx.gaussian_fit.international_tables_sigmas[:n_points],
      it.fetch())
    labels.append(wk.label())
    max_errors.append(flex.max(gaussian_fit.significant_relative_errors()))
    if (plots_dir is not None):
      if (not os.path.isdir(plots_dir)):
        print "No plots because the directory %s does not exist." % plots_dir
        plots_dir = None
      else:
        cctbx.eltbx.gaussian_fit.write_plots(
          plots_dir=plots_dir,
          label=wk.label(),
          gaussian_fit=gaussian_fit)
  perm = flex.sort_permutation(max_errors, 0001)
  labels = labels.select(perm)
  max_errors = max_errors.select(perm)
  for l,e in zip(labels, max_errors):
    print "%.6s %.4f" % (l,e)

if (__name__ == "__main__"):
  run(sys.argv[1:])
