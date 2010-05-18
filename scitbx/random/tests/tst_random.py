from __future__ import division
import libtbx.utils
from libtbx.test_utils import approx_equal
import scitbx.random
from scitbx.math import basic_statistics
from scitbx.array_family import flex
import itertools

def exercise_distributions():
  from scitbx.random import normal_distribution
  n = normal_distribution()
  assert (n.mean, n.sigma) == (0, 1)
  n = normal_distribution(mean=5, sigma=10)
  assert (n.mean, n.sigma) == (5, 10)

def exercise_variate_generators():
  from scitbx.random \
       import variate, normal_distribution, bernoulli_distribution
  for i in xrange(10):
    scitbx.random.set_random_seed(0)
    g = variate(normal_distribution())
    assert approx_equal(g(), -1.2780081289048213)
    assert approx_equal(g(10),
      (-0.40474189234755492, -0.41845505596083288,
       -1.8825790263067721, -1.5779112018107659,
       -1.1888174422378859, -1.8619619179878537,
       -0.53946818661388318, -1.2400941724410812,
       0.64511959841907285, -0.59934120033270688))

  stat = basic_statistics(flex.double(itertools.islice(g, 1000000)))
  assert approx_equal(stat.mean,            0, eps=0.005)
  assert approx_equal(stat.biased_variance, 1, eps=0.005)
  assert approx_equal(stat.skew,            0, eps=0.005)
  assert approx_equal(stat.kurtosis,        3, eps=0.005)

  bernoulli_seq = variate(bernoulli_distribution(0.1))
  for b in itertools.islice(bernoulli_seq, 10):
    assert b in (True, False)
  bernoulli_sample = flex.bool(itertools.islice(bernoulli_seq, 10000))
  assert approx_equal(
    bernoulli_sample.count(True)/len(bernoulli_sample),
    0.1,
    eps = 0.01)

def run():
  libtbx.utils.show_times_at_exit()
  exercise_distributions()
  exercise_variate_generators()

if __name__ == '__main__':
  run()
