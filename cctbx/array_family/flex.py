from __future__ import division
import scitbx.array_family.flex

import boost.python
ext_ = boost.python.import_ext("cctbx_array_family_flex_ext")
from scitbx_array_family_flex_ext import *
from cctbx_array_family_flex_ext import *
ext = ext_
del ext_

scitbx.array_family.flex.export_to("cctbx.array_family.flex")
