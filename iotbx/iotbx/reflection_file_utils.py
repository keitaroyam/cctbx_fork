from iotbx import reflection_file_reader
from cctbx import miller
from cctbx.array_family import flex
import libtbx.path
from libtbx.itertbx import count
from libtbx.utils import UserError
import sys, os

class UserError_No_array_of_the_required_type(UserError): pass

def find_labels(search_labels, info_string):
  for search_label in search_labels:
    if (info_string.find(search_label) < 0):
      return False
  return True

class label_table:

  def __init__(self, miller_arrays, err=None):
    self.miller_arrays = miller_arrays
    if (err is None): self.err = sys.stderr
    else: self.err = err
    self.info_strings = []
    self.info_labels = []
    for p_array,miller_array in zip(count(1), miller_arrays):
      info = miller_array.info()
      if (info is not None):
        self.info_strings.append(str(info))
      else:
        self.info_strings.append(str(p_array))
      self.info_labels.append(getattr(info, "labels", None))

  def scores(self, label=None, labels=None):
    assert [label, labels].count(None) == 1
    if (labels is None):
      labels = [label]
    else:
      assert len(labels) > 0
      label = labels[0]
    if (len(labels) == 1):
      try: i = int(label)-1
      except (TypeError, ValueError): pass
      else:
        if (0 <= i < len(self.miller_arrays)):
          result = [0]*len(self.miller_arrays)
          result[i] = 2
          return result
    result = []
    labels_lower = [lbl.lower() for lbl in labels]
    for info_string,info_labels in zip(self.info_strings, self.info_labels):
      if (not find_labels(
               search_labels=labels_lower,
               info_string=info_string.lower())):
        result.append(0)
      elif (not find_labels(
                  search_labels=labels,
                  info_string=info_string)):
        result.append(1)
      else:
        n_exact_matches = 0
        if (info_labels is not None):
          for info_label in info_labels:
            if (info_label in labels):
              n_exact_matches += 1
        result.append(2 + n_exact_matches)
    return result

  def show_possible_choices(self,
        f=None,
        scores=None,
        minimum_score=None,
        parameter_name=None):
    if (f is None): f = self.err
    print >> f, "Possible choices:"
    if (scores is None):
      for info_string in self.info_strings:
        print >> f, " ", info_string
    else:
      for info_string,score in zip(self.info_strings, scores):
        if (score >= minimum_score):
          print >> f, " ", info_string
    print >> f
    if (parameter_name is None): hint = ""
    else: hint = "use %s\nto " % parameter_name
    print >> f, \
      "Please %sspecify an unambiguous substring of the target label." % hint
    print >> f

  def match_data_label(self, label, command_line_switch, f=None):
    if (f is None): f = self.err
    scores = self.scores(label=label)
    selected_array = None
    for high_score in [2,1]:
      if (scores.count(high_score) > 0):
        if (scores.count(high_score) > 1):
          print >> f
          print >> f, "Ambiguous %s=%s" % (command_line_switch, label)
          print >> f
          self.show_possible_choices(
            f=f, scores=scores, minimum_score=high_score)
          return None
        return self.miller_arrays[scores.index(high_score)]
    print >> f
    print >> f, "Unknown %s=%s" % (command_line_switch, label)
    print >> f
    self.show_possible_choices(f=f)
    return None

def get_xray_data_scores(miller_arrays):
  result = []
  for miller_array in miller_arrays:
    if (not miller_array.is_real_array()):
      result.append(0)
    else:
      if (miller_array.is_xray_intensity_array()):
        result.append(4)
      elif (miller_array.is_xray_amplitude_array()):
        if (miller_array.is_xray_reconstructed_amplitude_array()):
          result.append(2)
        else:
          result.append(3)
      elif (    isinstance(miller_array.data(), flex.double)
            and isinstance(miller_array.sigmas(), flex.double)):
        result.append(1)
      else:
        result.append(0)
  return result

def looks_like_r_free_flags_info(array_info):
  if (not isinstance(array_info, miller.array_info)): return False
  if (len(array_info.labels) != 1): return False
  label = array_info.labels[0].lower()
  for word in ["free", "test", "cross"]:
    if (label.find(word) >= 0): return True
  return False

class get_r_free_flags_score:

  def __init__(self, test_flag_value, n, n_free, miller_array_info):
    if (test_flag_value is not None or n_free < n*0.50):
      self.reversed = False
    else:
      self.reversed = True
      n_free = n - n_free
    self.flag_score = 0
    if (min(2000,n*0.01) < n_free < n*0.35):
      if (   looks_like_r_free_flags_info(miller_array_info)
          or min(2000,n*0.04) < n_free < n*0.20):
        self.flag_score = 2
      else:
        self.flag_score = 1

class get_r_free_flags_scores:

  def __init__(self, miller_arrays, test_flag_value):
    self.scores = []
    self.test_flag_values = []
    for i_array,miller_array in enumerate(miller_arrays):
      flag_score = 0
      effective_test_flag_value = None
      data = miller_array.data()
      if (miller_array.is_bool_array()):
        trial_test_flag_value = (
          test_flag_value is None or bool(test_flag_value))
        n_free = data.count(trial_test_flag_value)
        scoring = get_r_free_flags_score(
          test_flag_value=test_flag_value,
          n=data.size(),
          n_free=n_free,
          miller_array_info=miller_array.info())
        if (scoring.flag_score != 0):
          flag_score = scoring.flag_score
          if (scoring.reversed):
            trial_test_flag_value = not trial_test_flag_value
          effective_test_flag_value = trial_test_flag_value
      elif (miller_array.is_integer_array()):
        try: counts = data.counts(max_keys=200)
        except RuntimeError: pass
        else:
          c_keys = counts.keys()
          c_values = counts.values()
          if (   test_flag_value is None
              or test_flag_value in c_keys):
            if (counts.size() == 2):
              if (test_flag_value is None):
                if (c_values[1] < c_values[0]):
                  i_free = 1
                else:
                  i_free = 0
              elif (test_flag_value == c_keys[0]):
                i_free = 0
              else:
                i_free = 1
              scoring = get_r_free_flags_score(
                test_flag_value=test_flag_value,
                n=data.size(),
                n_free=c_values[i_free],
                miller_array_info=miller_array.info())
              if (scoring.flag_score != 0):
                flag_score = scoring.flag_score
                if (scoring.reversed): i_free = 1-i_free
                effective_test_flag_value = c_keys[i_free]
            elif (counts.size() > 3):
              if (c_keys == range(min(c_keys), max(c_keys)+1)):
                if (min(c_values) > max(c_values)*0.55):
                  if (looks_like_r_free_flags_info(miller_array.info())):
                    flag_score = 2
                  else:
                    flag_score = 1
                  if (test_flag_value is None):
                    effective_test_flag_value = min(c_keys)
                  else:
                    effective_test_flag_value = test_flag_value
      self.scores.append(flag_score)
      self.test_flag_values.append(effective_test_flag_value)
    assert len(self.scores) == len(miller_arrays)
    assert len(self.test_flag_values) == len(miller_arrays)

def get_experimental_phases_scores(miller_arrays):
  result = []
  for miller_array in miller_arrays:
    if (miller_array.is_hendrickson_lattman_array()):
      result.append(1)
    else:
      result.append(0)
  return result

def select_array(
      parameter_name,
      labels,
      miller_arrays,
      data_scores,
      err,
      error_message_no_array,
      error_message_not_a_suitable_array,
      error_message_multiple_equally_suitable):
  if (labels is not None): assert parameter_name is not None
  if (len(miller_arrays) == 0):
    raise UserError_No_array_of_the_required_type(
      "No reflection arrays available.")
  if (data_scores is not None):
    assert max(data_scores) >= 0
  else:
    data_scores = [1]*len(miller_arrays)
  lbl_tab = label_table(miller_arrays=miller_arrays, err=err)
  if (labels is None):
    label_scores = None
  else:
    label_scores = lbl_tab.scores(labels=labels)
  if (label_scores is not None and max(label_scores) == 0):
    error = "No matching array: %s=%s" % (parameter_name, " ".join(labels))
    print >> err, "\n" + error + "\n"
    if (max(data_scores) > 0):
      lbl_tab.show_possible_choices(
        scores=data_scores,
        minimum_score=1,
        parameter_name=parameter_name)
    raise UserError(error)
  if (max(data_scores) == 0):
    if (label_scores is None):
      print >> err, "\n" + error_message_no_array + "\n"
      raise UserError_No_array_of_the_required_type(error_message_no_array)
    error = "%s%s=%s" % (
      error_message_not_a_suitable_array, parameter_name, " ".join(labels))
    print >> err, "\n" + error + "\n"
    raise UserError(error)
  if (label_scores is None):
    combined_scores = data_scores
  else:
    n = max(data_scores) + 1
    combined_scores = []
    for label_score,data_score in zip(label_scores, data_scores):
      combined_scores.append(label_score*n+data_score)
  i = combined_scores.index(max(combined_scores))
  if (combined_scores.count(combined_scores[i]) > 1):
    error = error_message_multiple_equally_suitable
    print >> err, "\n" + error + "\n"
    lbl_tab.show_possible_choices(
      scores=combined_scores,
      minimum_score=max(combined_scores),
      parameter_name=parameter_name)
    raise UserError(error)
  return i

class reflection_file_server:

  def __init__(self,
        crystal_symmetry=None,
        force_symmetry=None,
        reflection_files=None,
        err=None):
    self.crystal_symmetry = crystal_symmetry
    self.force_symmetry = force_symmetry
    if (err is None): self.err = sys.stderr
    else: self.err = err
    self.miller_arrays = []
    for reflection_file in reflection_files:
      self.miller_arrays.extend(reflection_file.as_miller_arrays(
        crystal_symmetry=self.crystal_symmetry,
        force_symmetry=self.force_symmetry))
    self.file_name_miller_arrays = {}
    for miller_array in self.miller_arrays:
      self.file_name_miller_arrays.setdefault(
        libtbx.path.canonical_path(
          miller_array.info().source), []).append(miller_array)

  def get_miller_arrays(self, file_name):
    if (file_name is None): return self.miller_arrays
    canonical_file_name = libtbx.path.canonical_path(file_name)
    result = self.file_name_miller_arrays.get(canonical_file_name, None)
    if (result is None and hasattr(os.path, "samefile")):
      for tabulated_file_name in self.file_name_miller_arrays.keys():
        if (os.path.samefile(canonical_file_name, tabulated_file_name)):
          result = self.file_name_miller_arrays[canonical_file_name] \
                 = self.file_name_miller_arrays[tabulated_file_name]
          break
    if (result is None):
      reflection_file = reflection_file_reader.any_reflection_file(
        file_name=file_name)
      if (reflection_file.file_type() is None):
        self.file_name_miller_arrays[canonical_file_name] = None
      else:
        result = self.file_name_miller_arrays[canonical_file_name] \
               = reflection_file.as_miller_arrays(
                   crystal_symmetry=self.crystal_symmetry,
                   force_symmetry=self.force_symmetry)
    if (result is None):
      raise UserError("No reflection data in file: %s" % file_name)
    return result

  def get_xray_data(self, file_name, labels, parameter_scope):
    miller_arrays = self.get_miller_arrays(file_name=file_name)
    data_scores = get_xray_data_scores(miller_arrays=miller_arrays)
    i = select_array(
      parameter_name=parameter_scope+".labels",
      labels=labels,
      miller_arrays=miller_arrays,
      data_scores=data_scores,
      err=self.err,
      error_message_no_array
        ="No array of observed xray data found.",
      error_message_not_a_suitable_array
        ="Not a suitable array of observed xray data: ",
      error_message_multiple_equally_suitable
        ="Multiple equally suitable arrays of observed xray data found.")
    return miller_arrays[i]

  def get_r_free_flags(self,
        file_name,
        label,
        test_flag_value,
        parameter_scope):
    miller_arrays = self.get_miller_arrays(file_name=file_name)
    flag_scores = get_r_free_flags_scores(
      miller_arrays=miller_arrays,
      test_flag_value=test_flag_value)
    if (label is None): labels = None
    else: labels=[label]
    i = select_array(
      parameter_name=parameter_scope+".label",
      labels=labels,
      miller_arrays=miller_arrays,
      data_scores=flag_scores.scores,
      err=self.err,
      error_message_no_array
        ="No array of R-free flags found.",
      error_message_not_a_suitable_array
        ="Not a suitable array of R-free flags: ",
      error_message_multiple_equally_suitable
        ="Multiple equally suitable arrays of R-free flags found.")
    return miller_arrays[i], flag_scores.test_flag_values[i]

  def get_experimental_phases(self, file_name, labels, parameter_scope):
    miller_arrays = self.get_miller_arrays(file_name=file_name)
    data_scores = get_experimental_phases_scores(miller_arrays=miller_arrays)
    i = select_array(
      parameter_name=parameter_scope+".labels",
      labels=labels,
      miller_arrays=miller_arrays,
      data_scores=data_scores,
      err=self.err,
      error_message_no_array
        ="No array of experimental phases found.",
      error_message_not_a_suitable_array
        ="Not a suitable array of experimental phases: ",
      error_message_multiple_equally_suitable
        ="Multiple equally suitable arrays of experimental phases found.")
    return miller_arrays[i]

def construct_output_file_name(input_file_names,
                               user_file_name,
                               file_type_label,
                               file_extension,
                               extension_seperator="."):
  if (user_file_name == "."):
    if (len(input_file_names) > 1):
      raise UserError(
        "Ambiguous name for output %s file (more than one input file)."
          % file_type_label)
    user_file_name = os.path.basename(input_file_names[0])
  if (not user_file_name.lower().endswith(file_extension)):
    user_file_name += extension_seperator + file_extension
  if (    os.path.isfile(user_file_name)
      and os.path.samefile(user_file_name, input_file_names[0])):
    user_file_name += extension_seperator + file_extension
  return user_file_name
