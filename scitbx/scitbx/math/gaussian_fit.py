import scitbx.math.gaussian
from scitbx.math import golay_24_12_generator
from scitbx import lbfgs
from cctbx.array_family import flex
from scitbx.python_utils.math_utils import ifloor
from scitbx.python_utils.misc import adopt_init_args
import math
import sys

def n_less_than(sorted_array, cutoff, eps=1.e-6):
  selection = sorted_array < cutoff + eps
  result = selection.count(0001)
  assert selection[:result].all_eq(0001)
  return result

class minimize:

  def __init__(self, gaussian_fit, target_power,
                     use_sigmas=00000,
                     enforce_positive_b=0001,
                     lbfgs_termination_params=None,
                     lbfgs_core_params=lbfgs.core_parameters(m=7)):
    adopt_init_args(self, locals())
    assert target_power in [2,4]
    self.n = gaussian_fit.n_terms() * 2
    self.x = flex.double(self.n, 0)
    self.first_target_value = None
    self.minimizer = lbfgs.run(
      target_evaluator=self,
      termination_params=lbfgs_termination_params,
      core_params=lbfgs_core_params)
    self.apply_shifts()
    self.compute_target(compute_gradients=00000)
    self.final_target_value = self.f
    self.final_gaussian_fit = self.gaussian_fit_shifted
    self.max_error = flex.max(
      self.final_gaussian_fit.significant_relative_errors())

  def apply_shifts(self):
    self.gaussian_fit_shifted = self.gaussian_fit.apply_shifts(
      self.x, self.enforce_positive_b)

  def compute_target(self, compute_gradients):
    differences = self.gaussian_fit_shifted.differences()
    self.f = self.gaussian_fit_shifted.target_function(
      self.target_power, self.use_sigmas, differences)
    if (compute_gradients):
      self.g = self.gaussian_fit_shifted.gradients_d_abc(
        self.target_power, self.use_sigmas, differences)
      if (self.enforce_positive_b):
        self.g = self.gaussian_fit.gradients_d_shifts(self.x, self.g)
    else:
      self.g = None

  def __call__(self):
    if (self.first_target_value is None):
      assert self.x.all_eq(0)
      self.gaussian_fit_shifted = self.gaussian_fit
    else:
      self.apply_shifts()
    self.compute_target(compute_gradients=0001)
    if (self.first_target_value is None):
      self.first_target_value = self.f
    return self.x, self.f, self.g

def minimize_multi(start_fit,
                   target_powers,
                   minimize_using_sigmas,
                   enforce_positive_b_mod_n,
                   b_min,
                   n_repeats_minimization):
  best_min = None
  for target_power in target_powers:
    min_gaussian_fit = start_fit
    for i in xrange(n_repeats_minimization):
      enforce_positive_b_this_time = (i % enforce_positive_b_mod_n == 0)
      try:
        minimized = minimize(
          gaussian_fit=min_gaussian_fit,
          target_power=target_power,
          use_sigmas=minimize_using_sigmas,
          enforce_positive_b=enforce_positive_b_this_time)
      except RuntimeError, e:
        if (str(e).find("lbfgs error: ") < 0): raise
        print e
        print "Aborting this minimization."
        print
        sys.stdout.flush()
        minimized = None
        break
      if (min(minimized.final_gaussian_fit.array_of_b()) < b_min):
        minimized = None
        break
      min_gaussian_fit = minimized.final_gaussian_fit
      if (best_min is None or best_min.max_error > minimized.max_error):
        best_min = minimized
  return best_min

def find_max_x(gaussian_fit,
               target_powers,
               minimize_using_sigmas,
               n_repeats_minimization,
               enforce_positive_b_mod_n,
               b_min,
               max_max_error):
  table_x = gaussian_fit.table_x()
  table_y = gaussian_fit.table_y()
  sigmas = gaussian_fit.table_sigmas()
  prev_n_points = 0
  good_n_points = 0
  i_x_high = table_x.size() - 1
  while 1:
    if (good_n_points == 0):
      x = (table_x[0] + table_x[i_x_high]) / 2
      n_points = n_less_than(sorted_array=table_x, cutoff=x)
      if (n_points == prev_n_points):
        n_points -= 1
        if (n_points < gaussian_fit.n_terms()*2):
          break
      prev_n_points = n_points
    else:
      n_points = good_n_points + 1
    start_fit = scitbx.math.gaussian.fit(
      table_x[:n_points],
      table_y[:n_points],
      sigmas[:n_points],
      gaussian_fit)
    best_min = minimize_multi(
      start_fit=start_fit,
      target_powers=target_powers,
      minimize_using_sigmas=minimize_using_sigmas,
      enforce_positive_b_mod_n=enforce_positive_b_mod_n,
      b_min=b_min,
      n_repeats_minimization=n_repeats_minimization)
    if (best_min is None or best_min.max_error > max_max_error):
      if (good_n_points != 0):
        break
      i_x_high = n_points - 1
    else:
      good_n_points = n_points
      good_min = best_min
      gaussian_fit = best_min.final_gaussian_fit
      if (good_n_points == table_x.size()):
        break
  if (good_n_points != 0):
    return good_min
  return None

def make_start_gaussian(null_fit,
                        existing_gaussian,
                        i_split,
                        i_x,
                        start_fraction,
                        b_range=1.e-3):
  x_sq = null_fit.table_x()[i_x]**2
  y0_table = null_fit.table_y()[0]
  yx_table = null_fit.table_y()[i_x]
  y0_existing = existing_gaussian.at_x_sq(0)
  yx_existing = existing_gaussian.at_x_sq(x_sq)
  n_terms = existing_gaussian.n_terms() + 1
  if (n_terms == 1):
    a = flex.double([y0_table])
    b = flex.double()
    yx_part = yx_table
  else:
    scale_old = 1 - start_fraction
    b = flex.double(existing_gaussian.array_of_b())
    b_max = flex.max(flex.abs(b))
    b_min = b_max * b_range
    sel = b < b_min
    b.set_selected(sel, flex.double(sel.count(0001), b_min))
    if (i_split < 0):
      a = flex.double(existing_gaussian.array_of_a()) * scale_old
      a.append(y0_table - flex.sum(a))
      yx_part = yx_table - yx_existing * scale_old
    else:
      t_split = scitbx.math.gaussian.term(
        existing_gaussian.array_of_a()[i_split],
        existing_gaussian.array_of_b()[i_split])
      a = flex.double(existing_gaussian.array_of_a())
      a.append(a[i_split] * start_fraction)
      a[i_split] *= scale_old
      yx_part = t_split.at_x_sq(x_sq) * start_fraction
  addl_b = 0
  if (a[-1] != 0):
    r = yx_part / a[-1]
    if (0 < r <= 1):
      addl_b = -math.log(r) / x_sq
  b.append(addl_b)
  if (addl_b != 0):
    assert abs(a[-1] * math.exp(-b[-1] * x_sq) - yx_part) < 1.e-6
  result = scitbx.math.gaussian.fit(
    null_fit.table_x(),
    null_fit.table_y(),
    null_fit.table_sigmas(),
    scitbx.math.gaussian.sum(iter(a), iter(b)))
  if (addl_b != 0 and i_split < 0):
    assert abs(result.at_x_sq(0) - y0_table) < 1.e-4
  if (n_terms == 1):
    assert abs(result.at_x_sq(x_sq) - yx_table) < 1.e-4
  return result

def find_max_x_multi(null_fit,
                     existing_gaussian,
                     target_powers,
                     minimize_using_sigmas,
                     enforce_positive_b_mod_n,
                     b_min,
                     max_max_error,
                     n_start_fractions,
                     n_repeats_minimization,
                     factor_y_x_begin=0.9,
                     factor_y_x_end=0.1,
                     factor_x_step=2.):
  i_x_begin = None
  i_x_end = None
  y0 = null_fit.table_y()[0]
  for i,target_value in null_fit.table_y().items():
    if (i_x_begin is None and target_value < y0 * factor_y_x_begin):
      i_x_begin = i
    if (i_x_end is None and target_value < y0 * factor_y_x_end):
      i_x_end = i
      break
  assert i_x_begin is not None
  assert i_x_end is not None
  n_terms = existing_gaussian.n_terms() + 1
  i_x_step = max(1, ifloor((i_x_end-i_x_begin) / (factor_x_step*n_terms)))
  if (n_terms == 1): n_start_fractions = 2
  best_min = None
  for i_x in xrange(i_x_begin, i_x_end, i_x_step):
    for i_split in xrange(-1, existing_gaussian.n_terms()):
      for i_start_fraction in xrange(0,n_start_fractions):
        gaussian_fit = make_start_gaussian(
          null_fit=null_fit,
          existing_gaussian=existing_gaussian,
          i_split=i_split,
          i_x=i_x,
          start_fraction=i_start_fraction/float(n_start_fractions))
        for target_power in target_powers:
          good_min = find_max_x(
            gaussian_fit=gaussian_fit,
            target_powers=[target_power],
            minimize_using_sigmas=minimize_using_sigmas,
            n_repeats_minimization=n_repeats_minimization,
            enforce_positive_b_mod_n=enforce_positive_b_mod_n,
            b_min=b_min,
            max_max_error=max_max_error)
          if (good_min is not None):
            if (best_min is None
                or best_min.final_gaussian_fit.table_x().size()
                 < good_min.final_gaussian_fit.table_x().size()
                or best_min.final_gaussian_fit.table_x().size()
                == good_min.final_gaussian_fit.table_x().size()
                  and best_min.max_error > good_min.max_error):
              best_min = good_min
  return best_min

def make_golay_based_start_gaussian(null_fit, code):
  assert len(code) == 24
  a_starts = [1,4,16,32]
  b_starts = [1,4,16,32]
  a = flex.double()
  b = flex.double()
  for i_term in xrange(6):
    i_bits = i_term * 2
    bits_a = code[i_bits], code[i_bits+12]
    bits_b = code[i_bits+1], code[i_bits+12+1]
    a.append(a_starts[bits_a[0]*2+bits_a[1]])
    b.append(b_starts[bits_b[0]*2+bits_b[1]])
  a = a * null_fit.table_y()[0] / flex.sum(a)
  return scitbx.math.gaussian.fit(
    null_fit.table_x(),
    null_fit.table_y(),
    null_fit.table_sigmas(),
    scitbx.math.gaussian.sum(iter(a), iter(b)))

def fit_with_golay_starts(label,
                          null_fit,
                          null_fit_more,
                          n_terms,
                          target_powers,
                          minimize_using_sigmas,
                          enforce_positive_b_mod_n,
                          b_min,
                          n_repeats_minimization,
                          negligible_max_error=0.001,
                          print_to=None):
  assert n_terms == 6
  if (label is not None and print_to is None):
    print_to = sys.stdout
  good_min = None
  for golay_code in golay_24_12_generator():
    start_fit = make_golay_based_start_gaussian(
      null_fit=null_fit,
      code=golay_code)
    best_min = minimize_multi(
      start_fit=start_fit,
      target_powers=target_powers,
      minimize_using_sigmas=minimize_using_sigmas,
      enforce_positive_b_mod_n=enforce_positive_b_mod_n,
      b_min=b_min,
      n_repeats_minimization=n_repeats_minimization)
    if (best_min is not None):
      if (good_min is None or good_min.max_error > best_min.max_error):
        good_min = best_min
        fit_more = scitbx.math.gaussian.fit(
          null_fit_more.table_x(),
          null_fit_more.table_y(),
          null_fit_more.table_sigmas(),
          good_min.final_gaussian_fit)
        if (print_to is not None):
          print >> print_to, label, "max_error fitted=%.4f, more=%.4f" % (
            good_min.max_error,
            flex.max(fit_more.significant_relative_errors()))
          fit_more.show(f=print_to)
          fit_more.show_table(f=print_to)
          print >> print_to
          print_to.flush()
        if (good_min.max_error <= negligible_max_error):
          break
  if (print_to is not None):
    if (good_min is None):
      print >> print_to, "Final: %s: No successful minimization." % label
    else:
      print >> print_to, "Final:", label, "max_error fitted=%.4f, more=%.4f" % (
        good_min.max_error,
        flex.max(fit_more.significant_relative_errors()))
    print >> print_to
  return good_min
