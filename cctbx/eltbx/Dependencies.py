# $Id$

import makefile_generator

class write_makefiles(makefile_generator.write_makefiles):

  def dependencies(self):

    self.lib_python_subdir = "cctbx_boost/eltbx"

    self.files = (
      "global/error.cpp",
      "eltbx/basic.cpp",
      "eltbx/tinypse.cpp",
      "eltbx/tinypsemodule.cpp",
      "eltbx/icsd_radii.cpp",
      "eltbx/icsd_radiimodule.cpp",
      "eltbx/wavelengths.cpp",
      "eltbx/wavelengthsmodule.cpp",
      "eltbx/caasf_it1992.cpp",
      "eltbx/caasf_it1992module.cpp",
      "eltbx/caasf_wk1995.cpp",
      "eltbx/caasf_wk1995module.cpp",
      "eltbx/efpfdp.cpp",
      "eltbx/fpfdpmodule.cpp",
      "eltbx/henke.cpp",
      "eltbx/henke_tables_01_12.cpp",
      "eltbx/henke_tables_13_24.cpp",
      "eltbx/henke_tables_25_36.cpp",
      "eltbx/henke_tables_37_48.cpp",
      "eltbx/henke_tables_49_60.cpp",
      "eltbx/henke_tables_61_72.cpp",
      "eltbx/henke_tables_73_84.cpp",
      "eltbx/henke_tables_85_92.cpp",
      "eltbx/henkemodule.cpp",
      "eltbx/sasaki.cpp",
      "eltbx/sasaki_tables_01_12.cpp",
      "eltbx/sasaki_tables_13_24.cpp",
      "eltbx/sasaki_tables_25_36.cpp",
      "eltbx/sasaki_tables_37_48.cpp",
      "eltbx/sasaki_tables_49_60.cpp",
      "eltbx/sasaki_tables_61_72.cpp",
      "eltbx/sasaki_tables_73_82.cpp",
      "eltbx/sasakimodule.cpp",
      "eltbx/neutron.cpp",
      "eltbx/neutronmodule.cpp",
      "eltbx/tst_tinypse.py",
      "eltbx/tst_icsd_radii.py",
      "eltbx/tst_wavelengths.py",
      "eltbx/tst_caasf_it1992.py",
      "eltbx/tst_caasf_wk1995.py",
      "eltbx/tst_henke.py",
      "eltbx/tst_sasaki.py",
      "eltbx/tst_neutron.py",
    )

    lib = [
      "error",
      "basic",
      "tinypse",
      "icsd_radii",
      "wavelengths",
      "caasf_it1992",
      "caasf_wk1995",
      "efpfdp",
      "henke",
      "henke_tables_01_12",
      "henke_tables_13_24",
      "henke_tables_25_36",
      "henke_tables_37_48",
      "henke_tables_49_60",
      "henke_tables_61_72",
      "henke_tables_73_84",
      "henke_tables_85_92",
      "sasaki",
      "sasaki_tables_01_12",
      "sasaki_tables_13_24",
      "sasaki_tables_25_36",
      "sasaki_tables_37_48",
      "sasaki_tables_49_60",
      "sasaki_tables_61_72",
      "sasaki_tables_73_82",
      "neutron",
    ]

    self.libraries = {
      "eltbx": tuple(lib),
    }

    self.boost_python_modules = {
      "tinypse":
        (("tinypsemodule", "tinypse", "basic", "error"), ()),
      "icsd_radii":
        (("icsd_radiimodule", "icsd_radii", "basic", "error"), ()),
      "wavelengths":
        (("wavelengthsmodule", "wavelengths", "basic", "error"), ()),
      "caasf_it1992":
        (("caasf_it1992module", "caasf_it1992", "basic", "error"), ()),
      "caasf_wk1995":
        (("caasf_wk1995module", "caasf_wk1995", "basic", "error"), ()),
      "fpfdp":
        (("fpfdpmodule", "efpfdp", "basic", "error"), ()),
      "henke":
        (("henkemodule",
          "henke",
          "henke_tables_01_12",
          "henke_tables_13_24",
          "henke_tables_25_36",
          "henke_tables_37_48",
          "henke_tables_49_60",
          "henke_tables_61_72",
          "henke_tables_73_84",
          "henke_tables_85_92",
          "efpfdp", "basic", "error"), ()),
      "sasaki":
        (("sasakimodule",
          "sasaki",
          "sasaki_tables_01_12",
          "sasaki_tables_13_24",
          "sasaki_tables_25_36",
          "sasaki_tables_37_48",
          "sasaki_tables_49_60",
          "sasaki_tables_61_72",
          "sasaki_tables_73_82",
          "efpfdp", "basic", "error"), ()),
      "neutron":
        (("neutronmodule", "neutron", "basic", "error"), ()),
    }

  def make_test(self):
    print "tst:"
    print "\tpython tst_tinypse.py"
    print "\tpython tst_icsd_radii.py"
    print "\tpython tst_wavelengths.py"
    print "\tpython tst_caasf_it1992.py"
    print "\tpython tst_caasf_wk1995.py"
    print "\tpython tst_neutron.py"
    print "\tpython tst_henke.py"
    print "\tpython tst_sasaki.py"
