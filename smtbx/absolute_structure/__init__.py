from __future__ import division

import math
import sys

from cctbx.array_family import flex

from libtbx.utils import xfrange
from libtbx.utils\
     import format_float_with_standard_uncertainty as format_float_with_su
from libtbx.utils import Sorry

from scitbx.math import distributions


class hooft_analysis:
  """
  Determination of absolute structure using Bayesian statistics
  on Bijvoet differences.

  See:
    Hooft, R.W.W., Straver, L.H., Spek, A.L. (2008). J. Appl. Cryst., 41, 96-103.

    Hooft, R.W.W., Straver, L.H., Spek, A.L. (2009). Acta Crystallogr. A65, 319-321.

    Hooft, R.W.W., Straver, L.H., Spek, A.L. (2010). J. Appl. Cryst., 43, 665-668.

  and for more information:
    http://www.absolutestructure.com/bibliography.html

  """

  def __init__(self, fo2, fc,
               scale_factor=None,
               outlier_cuttoff_factor=2,
               probability_plot_slope=None):
    self.probability_plot_slope = probability_plot_slope
    assert fo2.is_xray_intensity_array()
    assert fc.is_complex_array()
    assert not fo2.space_group().is_centric()
    if scale_factor is None:
      scale_factor = fo2.scale_factor(fc)
    fc2 = fc.as_intensity_array()
    self.delta_fc2 = fc2.anomalous_differences()
    self.delta_fo2 = fo2.anomalous_differences()
    self.n_bijvoet_pairs = self.delta_fo2.size()
    cutoff_sel = flex.abs(self.delta_fo2.data()) > (
      outlier_cuttoff_factor * scale_factor) * flex.max(
        flex.abs(self.delta_fc2.data()))
    self.delta_fo2 = self.delta_fo2.select(~cutoff_sel)
    self.delta_fc2 = self.delta_fc2.select(~cutoff_sel)
    self.delta_fo2 = self.delta_fo2.customized_copy(
      data=self.delta_fo2.data()/scale_factor)
    if not self.delta_fo2.size():
      raise Sorry("Absolute structure could not be determined")
    min_gamma = -10
    max_gamma = 10

    # quick and dirty to find better min, max gammas
    max_log_p_obs = -1e100
    while True:
      # search for the maximum
      width = max_gamma - min_gamma
      if width < 0.0001:
        break
      middle = (min_gamma + max_gamma)/2
      a = middle - width/4
      b = middle + width/4
      value_a = self.log_p_obs_given_gamma(a)
      value_b = self.log_p_obs_given_gamma(b)
      if value_a > value_b:
        max_gamma = middle
      elif value_a == value_b:
        min_gamma = a
        max_gamma = b
      else:
        min_gamma = middle
      max_log_p_obs = max([max_log_p_obs, value_a, value_b])
    while True:
      # search for where the curve becomes close to zero on the left
      min_gamma = middle - width/2
      if (width > 100 or
          self.log_p_obs_given_gamma(min_gamma) - max_log_p_obs < -10):
        break
      width *= 2
    width = max_gamma - min_gamma
    while True:
      # search for where the curve becomes close to zero on the right
      max_gamma = middle + width/2
      if (width > 100 or
          self.log_p_obs_given_gamma(max_gamma) - max_log_p_obs < -10):
        break
      width *= 2

    n_steps = 500
    d_gamma = (max_gamma - min_gamma)/n_steps
    # now do it properly
    log_p_obs_given_gammas = flex.double()
    for gamma in xfrange(min_gamma, max_gamma, d_gamma):
      log_p_obs_given_gammas.append(self.log_p_obs_given_gamma(gamma))
    max_log_p_obs = flex.max(log_p_obs_given_gammas)
    G_numerator = 0
    G_denominator = 0
    p_u_gammas = flex.double()
    # Numerical integration using trapezoidal rule
    for i, gamma in enumerate(xfrange(min_gamma, max_gamma, d_gamma)):
      p_u_gamma = math.exp(log_p_obs_given_gammas[i] - max_log_p_obs)
      p_u_gammas.append(p_u_gamma)
      if i == 0: continue
      G_numerator += 0.5 * d_gamma * (
        (gamma-d_gamma) * p_u_gammas[-2] + gamma * p_u_gammas[-1])
      G_denominator += 0.5 * (p_u_gammas[-2] + p_u_gammas[-1]) * d_gamma
    self.G = G_numerator/G_denominator
    sigma_squared_G_numerator = 0
    # Numerical integration using trapezoidal rule
    next = None
    for i, gamma in enumerate(xfrange(min_gamma, max_gamma, d_gamma)):
      previous = next
      next = math.pow((gamma - self.G), 2) * p_u_gammas[i] * d_gamma
      if i == 0: continue
      sigma_squared_G_numerator += 0.5 * (previous + next)
    self.hooft_y = (1-self.G)/2
    self.sigma_G = math.sqrt(sigma_squared_G_numerator/G_denominator)
    self.sigma_y = self.sigma_G/2

    # Now calculate P2, P3 values
    log_p_obs_given_gamma_is_minus_1 = self.log_p_obs_given_gamma(-1)
    log_p_obs_given_gamma_is_0 = self.log_p_obs_given_gamma(0)
    log_p_obs_given_gamma_is_1 = self.log_p_obs_given_gamma(1)
    max_log_p_obs = max([log_p_obs_given_gamma_is_minus_1,
                         log_p_obs_given_gamma_is_0,
                         log_p_obs_given_gamma_is_1])
    # all values normalised by max_log_p_obs for numerical stability
    log_p_obs_given_gamma_is_minus_1 -= max_log_p_obs
    log_p_obs_given_gamma_is_0 -= max_log_p_obs
    log_p_obs_given_gamma_is_1 -= max_log_p_obs
    p2_denominator = math.exp(log_p_obs_given_gamma_is_1) \
                   + math.exp(log_p_obs_given_gamma_is_minus_1)
    p3_denominator = math.exp(log_p_obs_given_gamma_is_1) \
                   + math.exp(log_p_obs_given_gamma_is_minus_1) \
                   + math.exp(log_p_obs_given_gamma_is_0)
    #
    if p2_denominator == 0: self.p2 = None
    else:
      self.p2 = (math.exp(log_p_obs_given_gamma_is_1)) / p2_denominator
    self.p3_true = (
      math.exp(log_p_obs_given_gamma_is_1)) / p3_denominator
    self.p3_false = (
      math.exp(log_p_obs_given_gamma_is_minus_1)) / p3_denominator
    self.p3_racemic_twin = (
      math.exp(log_p_obs_given_gamma_is_0)) / p3_denominator

  def log_p_obs_given_gamma(self, gamma):
    x_gamma = (gamma * self.delta_fc2.data() - self.delta_fo2.data()) \
            / self.delta_fo2.sigmas()
    if self.probability_plot_slope is not None:
      x_gamma /= self.probability_plot_slope
    return -0.5 * flex.sum_sq(x_gamma)

  def show(self, out=None):
    if out is None: out=sys.stdout
    print >> out, "Bijvoet pairs (all): %i" %self.n_bijvoet_pairs
    print >> out, "Bijvoet pairs (used): %i" %self.delta_fo2.size()
    print >> out, "Bijvoet pairs coverage: %.2f" %(
      self.n_bijvoet_pairs/self.delta_fo2.customized_copy(
        anomalous_flag=True).complete_set().n_bijvoet_pairs())
    print >> out, "G: %s" %format_float_with_su(self.G, self.sigma_G)
    if self.p2 is None:
      print >> out, "P2(true): n/a"
    else:
      print >> out,  "P2(true): %.3f" %self.p2
    print >> out,  "P3(true): %.3f" %self.p3_true
    print >> out,  "P3(false): %.3f" %self.p3_false
    print >> out,  "P3(racemic twin): %.3f" %self.p3_racemic_twin
    print >> out, "Hooft y: %s" %format_float_with_su(
      self.hooft_y, self.sigma_y)


class bijvoet_differences_probability_plot:
  """
  Hooft, R.W.W., Straver, L.H., Spek, A.L. (2010). J. Appl. Cryst., 43, 665-668.
  """

  def __init__(self,
               hooft_analysis,
               use_students_t_distribution=False,
               students_t_nu=None,
               probability_plot_slope=None):
    self.delta_fo2, minus_fo2 =\
        hooft_analysis.delta_fo2.generate_bijvoet_mates().hemispheres_acentrics()
    self.delta_fc2, minus_fc2 =\
        hooft_analysis.delta_fc2.generate_bijvoet_mates().hemispheres_acentrics()
    # we want to plot both hemispheres
    self.delta_fo2.indices().extend(minus_fo2.indices())
    self.delta_fo2.data().extend(minus_fo2.data() * -1)
    self.delta_fo2.sigmas().extend(minus_fo2.sigmas())
    self.delta_fc2.indices().extend(minus_fc2.indices())
    self.delta_fc2.data().extend(minus_fc2.data() * -1)
    self.indices = self.delta_fo2.indices()
    observed_deviations = (hooft_analysis.G * self.delta_fc2.data()
                           - self.delta_fo2.data())/self.delta_fo2.sigmas()

    if probability_plot_slope is not None:
      observed_deviations /= probability_plot_slope
    selection = flex.sort_permutation(observed_deviations)
    observed_deviations = observed_deviations.select(selection)
    if use_students_t_distribution:
      if students_t_nu is None:
        students_t_nu = maximise_students_t_correlation_coefficient(
          observed_deviations, 1, 200)
      self.distribution = distributions.students_t_distribution(students_t_nu)
    else:
      self.distribution = distributions.normal_distribution()
    self.x = self.distribution.quantiles(observed_deviations.size())
    self.y = observed_deviations
    self.fit = flex.linear_regression(self.x[5:-5], self.y[5:-5])
    self.correlation = flex.linear_correlation(self.x[5:-5], self.y[5:-5])
    assert self.fit.is_well_defined()

  def show(self, out=None):
    if out is None: out=sys.stdout
    print >> out, "y_intercept: %.3f" %self.fit.y_intercept()
    print >> out, "slope: %.3f" %self.fit.slope()
    print >> out, "coefficient: %.4f" %self.correlation.coefficient()


def maximise_students_t_correlation_coefficient(observed_deviations,
                                                min_nu, max_nu):
  def compute_corr_coeff(i):
    distribution = distributions.students_t_distribution(i)
    expected_deviations = distribution.quantiles(observed_deviations.size())
    return flex.linear_correlation(
      observed_deviations[5:-5], expected_deviations[5:-5])
  assert max_nu > min_nu
  assert min_nu > 0
  while True:
    width = max_nu - min_nu
    if width < 0.01: break
    middle = (min_nu + max_nu)/2
    a = middle - width/4
    b = middle + width/4
    value_a = compute_corr_coeff(a).coefficient()
    value_b = compute_corr_coeff(b).coefficient()
    if value_a > value_b:
      max_nu = middle
    elif value_a == value_b:
      min_nu = a
      max_nu = b
    else:
      min_nu = middle
  return middle

class students_t_hooft_analysis(hooft_analysis):
  """
  Hooft, R.W.W., Straver, L.H., Spek, A.L. (2010). J. Appl. Cryst., 43, 665-668.
  """

  def __init__(self, fo2, fc,
               degrees_of_freedom,
               scale_factor=None,
               outlier_cuttoff_factor=2,
               probability_plot_slope=None):
    self.degrees_of_freedom = degrees_of_freedom
    hooft_analysis.__init__(self, fo2, fc,
                            scale_factor=scale_factor,
                            outlier_cuttoff_factor=outlier_cuttoff_factor,
                            probability_plot_slope=probability_plot_slope)

  def log_p_obs_given_gamma(self, gamma):
    dof = self.degrees_of_freedom
    x_gamma = (gamma * self.delta_fc2.data() - self.delta_fo2.data()) \
            / self.delta_fo2.sigmas()
    if self.probability_plot_slope is not None:
      x_gamma /= self.probability_plot_slope
    return -(1+dof)/2 * flex.sum(flex.log(flex.pow2(x_gamma) + dof))
