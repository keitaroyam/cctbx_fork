"Transfer of scalepack merge reflection files to flex arrays."

# Sample scalepack OUTPUT FILE
#    1
# -987
#    34.698    71.491    54.740    90.000   106.549    90.000 p21
#   0   0   4  3617.6   287.2
#   0   1   6 12951.7  1583.6 12039.2  1665.8
#
# Format: (3I4, 4F8.1)

from cctbx import uctbx
from cctbx import sgtbx
from cctbx import crystal
from cctbx import miller
from cctbx.array_family import flex
from scitbx.python_utils import easy_pickle
import exceptions
import os
import sys

class FormatError(exceptions.Exception): pass

class reader:

  def __init__(self, file_handle, header_only=00000):
    line = file_handle.readline()
    if (line.rstrip() != "    1"):
      raise FormatError, "line 1: expecting '    1'"
    line = file_handle.readline()
    if (line.rstrip()[:2] != " -"):
      raise FormatError, "line 2: expecting ' -###'"
    line_error = "line 3: expecting unit cell parameters and space group label"
    line = file_handle.readline()
    if (len(line) < 63 or line[60] != ' '):
      raise FormatError, line_error
    try:
      uc_params = [float(line[i * 10 : (i + 1) * 10]) for i in xrange(6)]
    except:
      raise FormatError, line_error
    self.unit_cell = uctbx.unit_cell(uc_params)
    self.space_group_symbol = line[61:].strip()
    if (len(self.space_group_symbol) == 0):
      raise FormatError, line_error
    try:
      self.space_group_info = sgtbx.space_group_info(self.space_group_symbol)
    except:
      self.space_group_info = None
    if (header_only): return
    self.miller_indices = flex.miller_index()
    self.i_obs = flex.double()
    self.sigmas = flex.double()
    self.anomalous = 0
    line_count = 3
    while 1:
      line = file_handle.readline()
      line_count += 1
      line_error = "line %d: expecting (3I4, 4F8.1)" % line_count
      if (line == ""): break
      line = line.rstrip() + (" " * 44)
      flds = []
      used = 0
      for width in (4,4,4,8,8,8,8):
        next_used = used + width
        flds.append(line[used:next_used].strip())
        used = next_used
      try:
        h = [int(flds[i]) for i in xrange(3)]
      except:
        raise FormatError, line_error
      for i in (0,1):
        j = 3+2*i
        if (len(flds[j])):
          try:
            i_obs, sigma = (float(flds[j]), float(flds[j+1]))
          except:
            raise FormatError, line_error
          if (i):
            h = [-e for e in h]
            self.anomalous = 1
          self.miller_indices.append(h)
          self.i_obs.append(i_obs)
          self.sigmas.append(sigma)

  def info(self):
    return "i_obs,sigma"

  def as_miller_array(self, crystal_symmetry=None, force_symmetry=00000,
                            info_prefix=""):
    return (miller.array(
      miller_set=miller.set(
        crystal_symmetry=crystal.symmetry(
          unit_cell=self.unit_cell,
          space_group_info=self.space_group_info).join_symmetry(
            other_symmetry=crystal_symmetry,
            force=force_symmetry),
        indices=self.miller_indices,
        anomalous_flag=self.anomalous),
      data=self.i_obs,
      sigmas=self.sigmas)
      .set_info(info_prefix+self.info()).set_observation_type_xray_intensity())

  def as_miller_arrays(self, crystal_symmetry=None, force_symmetry=00000,
                             info_prefix=""):
    return [self.as_miller_array(crystal_symmetry,force_symmetry,info_prefix)]

def run(args):
  to_pickle = "--pickle" in args
  for file_name in args:
    if (file_name.startswith("--")): continue
    s = reader(open(file_name, "r"))
    miller_array = s.as_miller_array(info="From file: "+file_name)
    miller_array.show_summary()
    if (to_pickle):
      pickle_file_name = os.path.split(file_name)[1] + ".pickle"
      print "Writing:", pickle_file_name
      easy_pickle.dump(pickle_file_name, miller_array)
    print
