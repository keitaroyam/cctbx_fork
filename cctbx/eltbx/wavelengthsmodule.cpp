// $Id$

#include <boost/python/class_builder.hpp>
#include <cctbx/eltbx/basic.h>
#include <cctbx/eltbx/wavelengths.h>

using namespace eltbx;

namespace {

  double keV(double Length) {
    return cctbx::constants::factor_keV_Angstrom / Length;
  }
  double Angstrom(double Energy) {
    return cctbx::constants::factor_keV_Angstrom / Energy;
  }
}

BOOST_PYTHON_MODULE_INIT(wavelengths)
{
  try
  {
#   include <cctbx/basic/from_bpl_import.h>

    python::module_builder this_module("wavelengths");

    const std::string Revision = "$Revision$";
    this_module.add(ref(to_python(
        Revision.substr(11, Revision.size() - 11 - 2))), "__version__");

    class_builder<WaveLength>
    py_WaveLength(this_module, "WaveLength");

    this_module.def(keV, "keV");
    this_module.def(Angstrom, "Angstrom");

    py_WaveLength.def(constructor<int>());
    py_WaveLength.def(constructor<const std::string&>());
    py_WaveLength.def(&WaveLength::Label, "Label");
    py_WaveLength.def(&WaveLength::operator(), "__call__");
    py_WaveLength.def(&WaveLength::Energy, "Energy");
  }
  catch(...)
  {
    boost::python::handle_exception(); // Deal with the exception for Python
  }
}
