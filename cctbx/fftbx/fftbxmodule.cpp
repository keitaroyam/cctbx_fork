// $Id$
/* Copyright (c) 2001 The Regents of the University of California through
   E.O. Lawrence Berkeley National Laboratory, subject to approval by the
   U.S. Department of Energy. See files COPYRIGHT.txt and
   cctbx/LICENSE.txt for further details.

   Revision history:
     2001 Dec 21: Using iterator-based fftbx interface (rwgk)
     2001 Nov 03: Created (R.W. Grosse-Kunstleve)
 */

#include <boost/python/class_builder.hpp>
#include <cctbx/fftbx/complex_to_complex_3d.h>
#include <cctbx/fftbx/real_to_complex_3d.h>
#include <cctbx/std_vector_bpl.h>
#include <cctbx/basic/boost_array_bpl.h>

using namespace cctbx;

namespace {

  void throw_size_error() {
    PyErr_SetString(PyExc_IndexError, "Vector is too small.");
    throw boost::python::error_already_set();
  }

  void throw_index_error() {
    PyErr_SetString(PyExc_IndexError, "Index is out of range.");
    throw boost::python::error_already_set();
  }

  struct vd3d_accessor
    : public ndim_vector_accessor<dimension_end<3>,
                                  std::vector<double> > {
    vd3d_accessor() {}
    vd3d_accessor(const boost::array<std::size_t, 3>& dim,
                  std::vector<double>& vec,
                  bool resize_vector = true)
      : ndim_vector_accessor<
          dimension_end<3>,
          std::vector<double> >(dim, vec, resize_vector)
    {}
    double
    getitem(const boost::array<std::size_t, 3>& I) const {
      if (!is_valid_index(I)) throw_index_error();
      return operator[](I);
    }
    void setitem(const boost::array<std::size_t, 3>& I,
                 double value) {
      if (!is_valid_index(I)) throw_index_error();
      operator[](I) = value;
    }
  };

  struct vc3d_accessor
    : public ndim_vector_accessor<dimension_end<3>,
                                  std::vector<std::complex<double> > > {
    vc3d_accessor() {}
    vc3d_accessor(const boost::array<std::size_t, 3>& dim,
                  std::vector<std::complex<double> >& vec,
                  bool resize_vector = true)
      : ndim_vector_accessor<
          dimension_end<3>,
          std::vector<std::complex<double> > >(dim, vec, resize_vector)
    {}
    std::complex<double>
    getitem(const boost::array<std::size_t, 3>& I) const {
      if (!is_valid_index(I)) throw_index_error();
      return operator[](I);
    }
    void setitem(const boost::array<std::size_t, 3>& I,
                 std::complex<double> value) {
      if (!is_valid_index(I)) throw_index_error();
      operator[](I) = value;
    }
  };

  void cc_forward_complex(fftbx::complex_to_complex<double>& fft,
                          std::vector<std::complex<double> >& vec) {
    if (vec.size() < fft.N()) throw_size_error();
    fft.forward(vec.begin());
  }
  void cc_backward_complex(fftbx::complex_to_complex<double>& fft,
                           std::vector<std::complex<double> >& vec) {
    if (vec.size() < fft.N()) throw_size_error();
    fft.backward(vec.begin());
  }
  void cc_forward_real(fftbx::complex_to_complex<double>& fft,
                       std::vector<double>& vec) {
    if (vec.size() < 2 * fft.N()) throw_size_error();
    fft.forward(vec.begin());
  }
  void cc_backward_real(fftbx::complex_to_complex<double>& fft,
                        std::vector<double>& vec) {
    if (vec.size() < 2 * fft.N()) throw_size_error();
    fft.backward(vec.begin());
  }

  void rc_forward_complex(fftbx::real_to_complex<double>& fft,
                          std::vector<std::complex<double> >& vec) {
    if (vec.size() < fft.Ncomplex()) throw_size_error();
    fft.forward(vec.begin());
  }
  void rc_backward_complex(fftbx::real_to_complex<double>& fft,
                           std::vector<std::complex<double> >& vec) {
    if (vec.size() < fft.Ncomplex()) throw_size_error();
    fft.backward(vec.begin());
  }
  void rc_forward_real(fftbx::real_to_complex<double>& fft,
                       std::vector<double>& vec) {
    if (vec.size() < fft.Mreal()) throw_size_error();
    fft.forward(vec.begin());
  }
  void rc_backward_real(fftbx::real_to_complex<double>& fft,
                        std::vector<double>& vec) {
    if (vec.size() < fft.Mreal()) throw_size_error();
    fft.backward(vec.begin());
  }

  void cc_3d_forward_complex(fftbx::complex_to_complex_3d<double>& fft,
                     vc3d_accessor map) {
    fft.forward(map);
  }
  void cc_3d_backward_complex(fftbx::complex_to_complex_3d<double>& fft,
                      vc3d_accessor map) {
    fft.backward(map);
  }
  void cc_3d_forward_real(fftbx::complex_to_complex_3d<double>& fft,
                          vd3d_accessor map) {
    fft.forward(map);
  }
  void cc_3d_backward_real(fftbx::complex_to_complex_3d<double>& fft,
                          vd3d_accessor map) {
    fft.backward(map);
  }

  void rc_3d_forward(fftbx::real_to_complex_3d<double>& fft,
                     vd3d_accessor map) {
    fft.forward(map);
  }
  void rc_3d_backward(fftbx::real_to_complex_3d<double>& fft,
                      vd3d_accessor map) {
    fft.backward(map);
  }

#   include <cctbx/basic/from_bpl_import.h>

  void init_module(python::module_builder& this_module)
  {
    const std::string Revision = "$Revision$";
    this_module.add(ref(to_python(
        Revision.substr(11, Revision.size() - 11 - 2))), "__version__");

    (void) python::wrap_std_vector(this_module,
      "vector_of_std_size_t", std::size_t());
    (void) python::wrap_std_vector(this_module,
      "vector_of_double", double());
    (void) python::wrap_std_vector(this_module,
      "vector_of_complex", std::complex<double>());

    class_builder<vd3d_accessor>
    py_vd3d_accessor(this_module, "vd3d_accessor");
    class_builder<vc3d_accessor>
    py_vc3d_accessor(this_module, "vc3d_accessor");

    class_builder<fftbx::factorization>
    py_factorization(this_module, "factorization");
    class_builder<fftbx::complex_to_complex<double> >
    py_complex_to_complex(this_module, "complex_to_complex");
    class_builder<fftbx::real_to_complex<double> >
    py_real_to_complex(this_module, "real_to_complex");
    class_builder<fftbx::complex_to_complex_3d<double> >
    py_complex_to_complex_3d(this_module, "complex_to_complex_3d");
    class_builder<fftbx::real_to_complex_3d<double> >
    py_real_to_complex_3d(this_module, "real_to_complex_3d");

    py_complex_to_complex.declare_base(
      py_factorization, boost::python::without_downcast);
    py_real_to_complex.declare_base(
      py_factorization, boost::python::without_downcast);

    py_vd3d_accessor.def(constructor<>());
    py_vd3d_accessor.def(constructor<
      const boost::array<std::size_t, 3>&,
      std::vector<double>&>());
    py_vd3d_accessor.def(constructor<
      const boost::array<std::size_t, 3>&,
      std::vector<double>&,
      bool>());
    py_vd3d_accessor.def(&vd3d_accessor::getitem, "__getitem__");
    py_vd3d_accessor.def(&vd3d_accessor::setitem, "__setitem__");

    py_vc3d_accessor.def(constructor<>());
    py_vc3d_accessor.def(constructor<
      const boost::array<std::size_t, 3>&,
      std::vector<std::complex<double> >&>());
    py_vc3d_accessor.def(constructor<
      const boost::array<std::size_t, 3>&,
      std::vector<std::complex<double> >&,
      bool>());
    py_vc3d_accessor.def(&vc3d_accessor::getitem, "__getitem__");
    py_vc3d_accessor.def(&vc3d_accessor::setitem, "__setitem__");

    py_factorization.def(constructor<>());
    py_factorization.def(constructor<std::size_t, bool>());
    py_factorization.def(&fftbx::factorization::N, "N");
    py_factorization.def(&fftbx::factorization::Factors, "Factors");

    py_complex_to_complex.def(constructor<>());
    py_complex_to_complex.def(constructor<std::size_t>());
    py_complex_to_complex.def(
      &fftbx::complex_to_complex<double>::WA, "WA");
    py_complex_to_complex.def(cc_forward_complex, "forward");
    py_complex_to_complex.def(cc_backward_complex, "backward");
    py_complex_to_complex.def(cc_forward_real, "forward");
    py_complex_to_complex.def(cc_backward_real, "backward");

    py_real_to_complex.def(constructor<>());
    py_real_to_complex.def(constructor<std::size_t>());
    py_real_to_complex.def(&fftbx::real_to_complex<double>::Nreal, "Nreal");
    py_real_to_complex.def(&fftbx::real_to_complex<double>::Mreal, "Mreal");
    py_real_to_complex.def(
      &fftbx::real_to_complex<double>::Ncomplex, "Ncomplex");
    py_real_to_complex.def(&fftbx::real_to_complex<double>::WA, "WA");
    py_real_to_complex.def(rc_forward_complex, "forward");
    py_real_to_complex.def(rc_backward_complex, "backward");
    py_real_to_complex.def(rc_forward_real, "forward");
    py_real_to_complex.def(rc_backward_real, "backward");

    py_complex_to_complex_3d.def(constructor<>());
    py_complex_to_complex_3d.def(
      constructor<std::size_t, std::size_t, std::size_t>());
    py_complex_to_complex_3d.def(
      constructor<const boost::array<std::size_t, 3>&>());
    py_complex_to_complex_3d.def(
      &fftbx::complex_to_complex_3d<double>::N, "N");
    py_complex_to_complex_3d.def(cc_3d_forward_complex, "forward");
    py_complex_to_complex_3d.def(cc_3d_backward_complex, "backward");
    py_complex_to_complex_3d.def(cc_3d_forward_real, "forward");
    py_complex_to_complex_3d.def(cc_3d_backward_real, "backward");

    py_real_to_complex_3d.def(constructor<>());
    py_real_to_complex_3d.def(
      constructor<std::size_t, std::size_t, std::size_t>());
    py_real_to_complex_3d.def(
      constructor<const boost::array<std::size_t, 3>&>());
    py_real_to_complex_3d.def(
      &fftbx::real_to_complex_3d<double>::Nreal, "Nreal");
    py_real_to_complex_3d.def(
      &fftbx::real_to_complex_3d<double>::Mreal, "Mreal");
    py_real_to_complex_3d.def(
      &fftbx::real_to_complex_3d<double>::Ncomplex, "Ncomplex");
    py_real_to_complex_3d.def(rc_3d_forward, "forward");
    py_real_to_complex_3d.def(rc_3d_backward, "backward");
  }

}

BOOST_PYTHON_MODULE_INIT(fftbx)
{
  boost::python::module_builder this_module("fftbx");
  init_module(this_module);
}
