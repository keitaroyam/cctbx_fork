# $Id$

import makefile_generator

class write_makefiles(makefile_generator.write_makefiles):

  def dependencies(self):

    self.files = (
      "global/bpl_utils.cpp",
      "global/array_bpl.cpp",
      "fftbx/fftbxmodule.cpp",
      "fftbx/tst.py",
    )

    self.boost_python_modules = {
      "fftbx": (("fftbxmodule", "bpl_utils", "array_bpl"), ()),
    }
