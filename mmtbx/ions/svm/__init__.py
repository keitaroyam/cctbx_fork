# -*- coding: utf-8; py-indent-offset: 2 -*-
"""
A set of functions to act upon ChemicalEnvironment and ScatteringEnvironment and
produce a single class and vector of features for use with a classifier.

This module relies on a SVM classifier generated by the module within
phenix_dev.ion_identification.nader_ml. See that module's description for more
details.

See Also
--------
mmtbx.ions.environment
mmtbx.ions.geometry
phenix_dev.ion_identification.nader_ml
"""

from __future__ import division, absolute_import
from mmtbx.ions.environment import N_SUPPORTED_ENVIRONMENTS
from mmtbx.ions.geometry import SUPPORTED_GEOMETRY_NAMES
import mmtbx.ions.identify
from iotbx.pdb import common_residue_names_water as WATER_RES_NAMES
from cctbx.eltbx import sasaki
from libtbx import Auto, slots_getstate_setstate_default_initializer
from libtbx.str_utils import make_sub_header
from libtbx.utils import Sorry
import libtbx.load_env

from collections import Iterable
from cStringIO import StringIO
from ctypes import c_double
from cPickle import load
import errno
import os
import sys

try : # XXX required third-party dependencies
  import numpy as np
  import svm
  import svmutil
except ImportError :
  svm = None
  svmutil = None
  np = None

CLASSIFIERS_PATH = libtbx.env.find_in_repositories(
  relative_path = "chem_data/classifiers",
  test = os.path.isdir,
  )

_CLASSIFIER = {}
_CLASSIFIER_OPTIONS = {}

ALLOWED_IONS = ["HOH", "MN", "ZN", "FE", "NI", "CA"]
ALLOWED_IONS += ["NA", "MG"]

def _get_classifier(svm_name=None):
  """
  If need be, initializes, and then returns a classifier trained to
  differentiate between different ions and water. Also returns of options for
  gathering features.

  To use the classifier, you will need to pass it to
  svm.libsvm.svm_predict_probability. Ion prediction is already encapsulated by
  predict_ion, so most users should just call that.

  Parameters
  ----------
  svm_name : str, optional
      The SVM to use for prediction. By default, the SVM trained on heavy atoms
      and calcium in the presence of anomalous data is used. See
      chem_data/classifiers for a full list of SVMs available.

  Returns
  -------
  svm.svm_model
      The libsvm classifier used to predict the identities of ion sites.
  dict of str, bool
      Options to pass to ion_vector when collecting features about these sites.
  tuple of (tuple of numpy.array of float, numpy.array of float), tuple of
  float)
      The scaling parameters passed to scale_to.
  numpy.array of bool
      The features of the vector that were selected as important for
      classification. Useful for both asserting that ion_vector is returning
      something of the correct size as well as only selection features that
      actually affect classification.

  See Also
  --------
  svm.libsvm.svm_predict_probability
  mmtbx.ions.svm.predict_ion
  phenix_dev.ion_identification.nader_ml.ions_test_ml_combos.train_svm
  """
  assert (svmutil is not None)
  global _CLASSIFIER, _CLASSIFIER_OPTIONS

  if svm_name is None:
    svm_name = "heavy"

  if svm_name not in _CLASSIFIER:
    svm_path = os.path.join(CLASSIFIERS_PATH, "{}.model".format(svm_name))
    options_path = os.path.join(CLASSIFIERS_PATH,
                                "{}_options.pkl".format(svm_name))
    try:
      _CLASSIFIER[svm_name] = svmutil.svm_load_model(svm_path)
    except IOError as err:
      if err.errno != errno.ENOENT:
        raise err
      else:
        _CLASSIFIER[svm_name] = None
        _CLASSIFIER_OPTIONS[svm_name] = None
    with open(options_path) as f:
      _CLASSIFIER_OPTIONS[svm_name] = load(f)

  return _CLASSIFIER[svm_name], _CLASSIFIER_OPTIONS[svm_name]

def ion_class(chem_env):
  """
  Returns the class name associated with the ion, analogous to the chemical
  ID.

  Parameters
  ----------
  chem_env : mmtbx.ions.environment.ChemicalEnvironment
      The object to extract the class from.
  Returns
  -------
  str
      The class associated with the ion.
  """
  if hasattr(chem_env.atom, "segid") and chem_env.atom.segid.strip():
    return chem_env.atom.segid.strip().upper()
  return chem_env.atom.resname.strip().upper()

def ion_vector(chem_env, scatter_env, anom=True, use_scatter=True,
               geometry=True, valence=True, b_iso=True, occ=True,
               diff_peak=True, elements=None, use_chem=True, ratios=True):
  """
  Creates a vector containing all of the useful properties contained
  within ion. Merges together the vectors from ion_*_vector().

  Parameters
  ----------
  chem_env : mmtbx.ions.environment.ChemicalEnvironment
      A object containing information about the chemical environment at a site.
  scatter_env : mmtbx.ions.environment.ScatteringEnvironment, optional
      An object containing information about the scattering environment at a
      site.

  Returns
  -------
  numpy.array of float
      A vector containing quantitative properties for classification.

  See Also
  --------
  ion_model_vector()
  ion_electron_density_vector()
  ion_geometry_vector()
  ion_nearby_atoms_vector()
  ion_valence_vector()
  ion_anomalous_vector()
  """
  assert (np is not None)
  return np.concatenate((
    ion_model_vector(scatter_env),
    ion_electron_density_vector(
      scatter_env, b_iso=b_iso, occ=occ, diff_peak=diff_peak)
    if use_scatter else [],
    ion_geometry_vector(chem_env)
    if use_chem and geometry else [],
    ion_nearby_atoms_vector(chem_env)
    if use_chem else [],
    ion_valence_vector(chem_env, elements=elements)
    if use_chem and valence else [],
    ion_anomalous_vector(scatter_env, elements=elements, ratios=ratios)
    if use_scatter and anom else [],
    ))

def ion_model_vector(scatter_env, nearest_res=0.5):
  """
  Creates a vector containing information about the general properties of the
  model in which the site is found. Currently this only includes the minimum
  resolution of the data set.

  Parameters
  ----------
  scatter_env : mmtbx.ions.environment.ScatteringEnvironment
      An object containing information about the scattering environment at a
      site.
  nearest_res : float, optional
      If not None, the nearest value to round d_min to. Default value is 0.5
      angstroms.

  Returns
  -------
  numpy.array of float
      A vector containing quantitative properties for classification.
  """
  d_min = scatter_env.d_min
  if nearest_res is not None:
    # Rounds d_min to the nearest value divisible by nearest_res
    factor = 1 / nearest_res
    d_min = round(d_min * factor) / factor
  return np.array([ d_min, ], dtype=float)

def ion_electron_density_vector(scatter_env, b_iso=False, occ=False,
                                diff_peak=False):
  """
  Creates a vector containing information about the electron density around
  the site. Currently this only includes the site's peak in the 2FoFc map. May
  be expanded in the future to include information about the volume of density
  around the site.

  Parameters
  ----------
  scatter_env : mmtbx.ions.environment.ScatteringEnvironment
      An object containing information about the scattering environment at a
      site.

  Returns
  -------
  numpy.array of float
      A vector containing quantitative properties for classification.
  """
  props = [
    scatter_env.fo_density[0],
    scatter_env.fo_density[1],
    # scatter_env.pai,
  ]
  if diff_peak:
    props.append(scatter_env.fofc_density[0])
  if b_iso:
    props.append(
      scatter_env.b_iso /
      (scatter_env.b_mean_hoh if scatter_env.b_mean_hoh != 0 else 15))
  if occ:
    props.append(scatter_env.occ)
  return np.array(props, dtype=float)

def ion_geometry_vector(chem_env, geometry_names=None):
  """
  Creates a vector for a site's geometry. For each geometry in geometry_names
  the vector contains a 1 if that geometry is present at the site and 0
  otherwise.

  A single boolean was chosen after some trial and error with an SVM as
  differences in deviations < 15 degrees were not found to be significant in
  helping to diffentiate ions.

  Parameters
  ----------
  chem_env : mmtbx.ions.environment.ChemicalEnvironment
      A object containing information about the chemical environment at a site.
  geometry_names : list of str, optional
      A list of geometry names to check for. If unset, take names from
      mmtbx.ions.SUPPORTED_GEOMETRY_NAMES.

  Returns
  -------
  numpy.array of float
      A vector containing quantitative properties for classification.
  """
  if geometry_names is None:
    geometry_names = SUPPORTED_GEOMETRY_NAMES

  present_geometry_names = [i[0] for i in chem_env.geometry]
  return np.fromiter((i in present_geometry_names for i in geometry_names),
                     dtype=float)

def ion_nearby_atoms_vector(chem_env, environments=None):
  """
  Creates a vector for the identities of the ions surrounding a site. Returns
  a vector with a count of coordinating nitrogens, oxygens, sulfurs, and
  chlorines.

  Parameters
  ----------
  chem_env : mmtbx.ions.environment.ChemicalEnvironment
      A object containing information about the chemical environment at a site.
  environments : list of int, optional
      A list of environments to check for. If unset, takes values from
      mmtbx.ions.environment.N_SUPPORTED_ENVIRONMENTS.

  Returns
  -------
  numpy.array of float
      A vector containing quantitative properties for classification.
  """

  if environments is None:
    environments = range(N_SUPPORTED_ENVIRONMENTS)

  return np.fromiter((chem_env.chemistry[i] for i in environments),
                     dtype=float)

def ion_valence_vector(chem_env, elements=None):
  """
  Calculate the BVS and VECSUM values for a variety of ion identities.

  Parameters
  ----------
  chem_env : mmtbx.ions.environment.ChemicalEnvironment
      A object containing information about the chemical environment at a site.
  elements : list of str, optional
      A list of elements to compare the experimental BVS and VECSUM
      against. If unset, takes the list from mmtbx.ions.ALLOWED_IONS.

  Returns
  -------
  numpy.array of float
      A vector containing quantitative properties for classification.
  """

  if elements is None:
    elements = [i for i in ALLOWED_IONS if i not in WATER_RES_NAMES]
  ret = []

  for element in elements:
    ret.append(chem_env.get_valence(
      element=element,
      charge=mmtbx.ions.server.get_charge(element)))

  # Flatten the list
  return _flatten_list(ret)

def ion_anomalous_vector(scatter_env, elements=None, ratios=True):
  """
  Calculate the f'' / f''_expected for a variety of ion identities.

  Parameters
  ----------
  scatter_env : mmtbx.ions.environment.ScatteringEnvironment
      An object containing information about the scattering environment at a
      site.
  elements : list of str, optional
      A list of elements to compare the experimental f'' against. If unset,
      takes the list from mmtbx.ions.ALLOWED_IONS.
  ratios : bool, optional
      If False, instead of calculating ratios, just return a vector of the
      wavelength, f', and f''.

  Returns
  -------
  numpy.array of float
      A vector containing quantitative properties for classification.
  """

  if elements is None:
    elements = [i for i in ALLOWED_IONS if i not in WATER_RES_NAMES]

  if scatter_env.fpp is None or scatter_env.wavelength is None:
    if ratios:
      return np.zeros(len(elements))
    else:
      return np.zeros(2)

  if ratios:
    ret = np.fromiter(
      (scatter_env.fpp /
       sasaki.table(element).at_angstrom(scatter_env.wavelength).fdp()
       for element in elements),
       float)
  else:
    ret = _flatten_list([
      scatter_env.fpp, scatter_env.fp
      ])
  return ret

def scale_to(matrix, source, target):
  """
  Given an upper and lower bound for each row of matrix, scales the values to be
  within the range specified by target.

  Parameters
  ----------
  matrix : numpy.array of float
      The matrix to be scaled.
  source : tuple of numpy.array of float
      The upper and lower bound on the values of each row in the original
      matrix.
  target : tuple of float
      The target range to scale to.

  Returns
  -------
  matrix : numpy.array of float
      The matrix with scaled values.

  Examples
  --------
  >>> import numpy as np
  >>> matrix = np.array([[0, 1, 2],
                         [2, 3, 4],
                         [1, 2, 3]])
  >>> source = (np.array([2, 3, 4]),
                np.array([0, 1, 2]))
  >>> target = (0, 1)
  >>> _scale_to(matrix, source, target)
  array([[ 1. ,  1. ,  1. ],
         [ 0. ,  0. ,  0. ],
         [ 0.5,  0.5,  0.5]])
  """
  matrix = np.array(matrix)
  keep_rows = source[0] != source[1]
  matrix = matrix[:, keep_rows]
  source = (source[0][keep_rows], source[1][keep_rows])
  return (matrix - source[0]) * (target[1] - target[0]) / \
    (source[1] - source[0]) + target[0]

def predict_ion(chem_env, scatter_env, elements=None, svm_name=None):
  """
  Uses the trained classifier to predict the ions that most likely fit a given
  list of features about the site.

  Parameters
  ----------
  chem_env : mmtbx.ions.environment.ChemicalEnvironment
      A object containing information about the chemical environment at a site.
  scatter_env : mmtbx.ions.environment.ScatteringEnvironment, optional
      An object containing information about the scattering environment at a
      site.
  elements : list of str, optional
      A list of elements to include within the prediction. Must be a subset of
      mmtbx.ions.svm.ALLOWED_IONS. Note: Water is not added to elements by
      default.
  svm_name : str, optional
      The SVM to use for prediction. By default, the SVM trained on heavy atoms
      and calcium in the presence of anomalous data is used

  Returns
  -------
  list of tuple of str, float or None
      Returns a list of classes and the probability associated with each or None
      if the trained classifier cannot be loaded.
  """

  # Load the classifier and the parameters used to interact with it
  classifier, classifier_options = _get_classifier(svm_name)

  if classifier is None or classifier_options is None:
    return None

  vector_options, scaling, features = classifier_options

  # Convert our data into a format that libsvm will accept
  vector = ion_vector(chem_env, scatter_env, **vector_options)
  vector = scale_to(vector, scaling[0], scaling[1])

  assert len(vector) == len(features)

  vector = vector[features]

  xi = svm.gen_svm_nodearray(
    list(vector), isKernel=classifier.param.kernel_type == svm.PRECOMPUTED,
    )[0]

  nr_class = classifier.get_nr_class()
  # prob_estimates isn't actually read by svm_predict_probability, it is only
  # written to with the final estimates. We just need to allocate space for it.
  prob_estimates = (c_double * nr_class)()
  svm.libsvm.svm_predict_probability(classifier, xi, prob_estimates)
  probs = prob_estimates[:nr_class]
  labels = [ALLOWED_IONS[i] for i in classifier.get_labels()]

  # print "__predict_ion__:", dict(zip(labels, probs))

  lst = zip(labels, probs)
  lst.sort(key=lambda x: -x[-1])

  if elements is not None:
    for element in elements:
      if element not in ALLOWED_IONS:
        raise Sorry("Unsupported element '{}'".format(element))

    # Filter out elements the caller does not care about
    classes, probs = [], []
    for element, prob in lst:
      if element in elements:
        classes.append(element)
        probs.append(prob)

    # Re-normalize the probabilities
    total = sum(probs)
    probs = [i / total for i in probs]
    lst = zip(classes, probs)

  return lst

def _flatten_list(lst):
  """
  Turn a tree main out of lists into one flat numpy array. Converts all Nones
  into zeros and integers into floats in the process.

  Parameters
  ----------
  lst : list or list of list or list of list of list or ...
      A list to be flattened

  Returns
  -------
  numpy.array of float
      A flat list of values.
  """

  def _flatten(lst):
    """
    Returns a generator for each element in the flattened version of lst.
    """

    for item in lst:
      if isinstance(item, Iterable) and not isinstance(item, basestring):
        for sub in _flatten(item):
          yield sub
      else:
        yield item

  return np.fromiter(
    (float(i) if i is not None else 0. for i in _flatten(lst)),
    dtype=float
    )

# Adapters for main identification/building routines
svm_phil_str = """
svm
  .expert_level = 3
{
  min_score = 0.2
    .type = float
  min_score_above = 0.1
    .type = float
  min_fraction_of_next = 2.0
    .type = float
}
"""

class svm_prediction (slots_getstate_setstate_default_initializer) :
  __slots__ = ["i_seq", "pdb_id_str", "atom_info_str", "map_stats",
               "atom_types", "scores", "final_choice"]

  def show (self, out=sys.stdout, prefix="") :
    for line in self.atom_info_str.splitlines() :
      print >> out, prefix+line.rstrip()
    print >> out, prefix+"SVM scores:"
    for elem, score in zip(self.atom_types, self.scores) :
      print >> out, prefix+"  %4s : %.3f" % (elem, score)
    if (self.final_choice is not None) :
      print >> out, prefix+"Final choice: %s" % self.final_choice

  def show_brief (self, out=sys.stdout, prefix="") :
    final_choice = self.final_choice
    if (final_choice is None) :
      final_choice = "----"
      best_score = "----"
    else :
      for atom_type, score in zip(self.atom_types, self.scores) :
        if (atom_type == final_choice.element) :
          best_score = "%5.3f" % score
          break
    print >> out, prefix+"%s   %4s  %5s  %5.2f  %5.2f" % \
      (self.pdb_id_str, final_choice.element, best_score,
       self.map_stats.two_fofc, self.map_stats.fofc)

class manager (mmtbx.ions.identify.manager) :
  def analyze_water (self, i_seq, debug=True, candidates=Auto) :
    atom_props = mmtbx.ions.identify.AtomProperties(i_seq, self)
    expected_atom_type = atom_props.get_atom_type(
      params=self.params.water)
    if (expected_atom_type == mmtbx.ions.identify.WATER_POOR) :
      return None
    auto_candidates = candidates is Auto
    if auto_candidates:
      candidates = mmtbx.ions.DEFAULT_IONS
    elif isinstance(candidates, str) or isinstance(candidates, unicode) :
      candidates = candidates.replace(",", " ").split()
    candidates = [i.strip().upper() for i in candidates]
    if (candidates == ['X']) : # XXX hack for testing - X is "dummy" element
      candidates = []
    from mmtbx.ions.environment import ScatteringEnvironment, \
      ChemicalEnvironment
    chem_env = ChemicalEnvironment(
      i_seq,
      atom_props.nearby_atoms,
      self)
    scatter_env = ScatteringEnvironment(
      i_seq=i_seq,
      manager=self,
      fo_density=self.get_map_gaussian_fit("mFo", i_seq),
      fofc_density=self.get_map_gaussian_fit("mFo-DFc", i_seq),
      anom_density=self.get_map_gaussian_fit("anom", i_seq))
    if auto_candidates:
      candidates = None
    else:
      candidates.append("HOH")
    predictions = predict_ion(chem_env, scatter_env, elements = candidates)
    if predictions is not None:
      # XXX: filtered candidates == probability > threshold?
      final_choice = None
      predictions.sort(lambda a,b: cmp(b[1], a[1]))
      best_guess, best_score = predictions[0]
      if (best_guess != "HOH") :
        next_guess, next_score = predictions[1]
        if ((best_score >= self.params.svm.min_score) and
            (best_score>=(next_score*self.params.svm.min_fraction_of_next))) :
          final_choice = mmtbx.ions.server.get_metal_parameters(best_guess)
      atom_info_out = StringIO()
      atom_props.show_properties(identity="HOH", out=atom_info_out)
      result = svm_prediction(
        i_seq=i_seq,
        pdb_id_str=self.pdb_atoms[i_seq].id_str(),
        atom_info_str=atom_info_out.getvalue(),
        map_stats=self.map_stats(i_seq),
        atom_types=[ pred[0] for pred in predictions ],
        scores=[ pred[1] for pred in predictions ],
        final_choice=final_choice)
      return result
    return None

  def analyze_waters (self, out=sys.stdout, debug=True, candidates=Auto) :
    waters = self.extract_waters()
    print >> out, "  %d waters to analyze" % len(waters)
    print >> out, ""
    if (len(waters) == 0) : return
    #nproc = easy_mp.get_processes(self.nproc)
    predictions = []
    for i_seq in waters :
      prediction = self.analyze_water(
        i_seq=i_seq,
        debug=debug,
        candidates=candidates)
      if (prediction is not None) :
        predictions.append(prediction)
    filtered = []
    for result in predictions :
      if (debug) :
        result.show(out=out, prefix="  ")
        print >> out, ""
      if (result.final_choice is not None) :
        filtered.append(result)
    if (len(filtered) == 0) :
      print >> out, ""
      print >> out, "  No waters could be classified as possible ions."
    else :
      make_sub_header("Predicted ions", out=out)
      for result in filtered :
        result.show_brief(out=out, prefix="  ")
    return filtered
