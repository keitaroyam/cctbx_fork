
from libtbx import easy_pickle
from libtbx.utils import Sorry
import re
import os

class result (object) :
  def __init__ (self, dir_name) :
    self.dir_name = dir_name
    self._distl = None
    self._labelit = None
    self._groups = None
    distl_file = os.path.join(dir_name, "DISTL_pickle"))
    labelit_file = os.path.join(dir_name, "LABELIT_pickle")
    groups_file = os.path.join(dir_name, "LABELIT_possible")
    if (os.path.exists(distl_file)) :
      self._distl = easy_pickle.load(distl_file)
    if (os.path.exists(labelit_file)) :
      self._labelit = easy_pickle.load(labelit_file)
    if (os.path.exists(groups_file)) :
      self._groups = easy_pickle.load(groups_file)

  def get_integration_result (self, sol_id, image_id) :
    file_name = os.path.join(self.dir_name, "integration_%d_%d" % (sol_id,
      image_id))
    if (not os.path.exists(file_name)) :
      raise Sorry("Can't find the file %s!" % file_name)
    integ_result = easy_pickle.load(file_name)
    summary = get_integration_summary(integ_result, image_id)
    return integ_result, summary

def find_integration_files (dir_name, base_name) :
  files = []
  for file_name in os.listdir(dir_name) :
    if (file_name.startswith(base_name)) :
      files.append(os.path.join(dir_name, file_name))
  return files

def get_integration_summary (integ_result, sol_id) :
  summary = dict(
    solution=sol_id,
    point_group=integ_result['pointgroup'],
    beam_center=(integ_result['xbeam'], integ_result['ybeam']),
    distance=integ_result['distance'],
    d_min=integ_result['resolution'],
    mosaicity=integ_result['mosaicity'],
    rms=integ_result['residual'],
    bins=integ_result['table_raw'])
  return summary

def load_integration_results (dir_name, base_name, image_id=1) :
  files = find_integration_files(dir_name, base_name)
  results = []
  summaries = []
  for file_path in files :
    result = easy_pickle.load(file_path)
    results.append(result)
    file_name = os.path.basename(file_path)
    suffix = re.sub(base_name + "_", "", file_name)
    sol_id_, img_id_ = suffix.split("_")
    if (int(img_id_) != image_id) :
      continue
    summary = get_integration_summary(result, int(sol_id_))
    summaries.append(summary)
  r_s = list(zip(results, summaries))
  r_s_sorted = sorted(r_s, lambda x,y: cmp(y[1]['solution'], x[1]['solution']))
  return [ r for r,s in r_s_sorted ], [ s for r, s in r_s_sorted ]

class TableData (object) :
  """Base class for wx.ListCtrl data source objects in this module."""
  def __init__ (self, table) :
    assert isinstance(table, list)
    self.table = table

  def GetItemCount (self) :
    return len(self.table)

  def GetItemImage (self, item) :
    return 0

class ResultData (TableData) :
  def GetItemText (self, item, col) :
    n_items = self.GetItemCount()
    assert (item < n_items) and (0 <= col <= 6)
    result = self.table[item]
    if (col == 0) :
      return "%d" % result['solution']
    elif (col == 1) :
      return result['point_group']
    elif (col == 2) :
      return "%.2f %.2f" % result['beam_center']
    elif (col == 3) :
      return "%.2f" % result['distance']
    elif (col == 4) :
      return "%.2f" % result['d_min']
    elif (col == 5) :
      return "%.2f" % result['mosaicity']
    else :
      return "%.3f" % result['rms']

class BinData (TableData) :
  def GetItemText (self, item, col) :
    n_items = self.GetItemCount()
    assert (item < n_items) and (0 <= col <= 4)
    bin = self.table[item]
    if (col == 0) :
      return "%d" % bin.i_bin
    elif (col == 1) :
      return "%g - %g" % bin.d_max_min
    elif (col == 2) :
      return "%d / %d" % bin.completeness
    elif (col == 3) :
      return "%8.1f" % bin.mean_I
    else :
      return "%8.1f" % bin.mean_I_sigI
