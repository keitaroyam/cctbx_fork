from iotbx import xplor
import iotbx.xplor.map
from cctbx import crystal

def extract_from(file_name):
  xplor_map = xplor.map.reader(file_name=file_name, header_only=0001)
  return crystal.symmetry(
    unit_cell=xplor_map.unit_cell,
    space_group_info=None)
