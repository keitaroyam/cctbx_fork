# $Id$

import makefile_generator

class write_makefiles(makefile_generator.write_makefiles):

  def dependencies(self):

    self.files = (
      "global/error.cpp",
      "global/bpl_utils.cpp",
      "global/tiny_bpl.cpp",
      "sftbx/sftbxmodule.cpp",
      "sftbx/tst.py",
    )

    self.boost_python_modules = {
      "sftbx": (("sftbxmodule",
                 "error",
                 "bpl_utils", "tiny_bpl"), ("sgtbx", "uctbx")),
    }
