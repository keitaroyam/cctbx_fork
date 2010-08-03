#include <scitbx/array_family/boost_python/flex_fwd.h>

#include <boost/python.hpp>

#include <scitbx/sym_mat3.h>
#include <scitbx/array_family/versa.h>
#include <scitbx/array_family/shared.h>
#include <scitbx/array_family/accessors/c_grid.h>
#include <boost/scoped_array.hpp>

namespace boost_python_meta_ext { struct holder {}; }

// simlar to time_eigensystem_real_symmetric()
#define SCITBX_LOC(fxx) \
  scitbx::vec3<double> \
  time_dsyev_##fxx( \
    scitbx::sym_mat3<double> const& m, std::size_t n_repetitions) \
  { \
    SCITBX_ASSERT(n_repetitions % 2 == 0); \
    scitbx::vec3<double> result(0,0,0); \
    for(std::size_t i=0;i<n_repetitions/2;i++) { \
      for(std::size_t j=0;j<2;j++) { \
        scitbx::vec3<double> w; \
        scitbx::mat3<double> a(m); \
        dsyev_##fxx##_wrapper("V", "U", \
          af::ref<double, af::c_grid<2> >(a.begin(), af::c_grid<2>(3,3)), \
          w.ref()); \
        if (j == 0) result += w; \
        else        result -= w; \
      } \
    } \
    return result / static_cast<double>(n_repetitions); \
  }

#if defined(SCITBX_LAPACK_FEM)

#include <lapack_fem/dgesvd.hpp>
#include <lapack_fem/dsyev.hpp>

namespace scitbx { namespace lapack { namespace boost_python {

  lapack_dgesvd_fem::common dgesvd_cmn;
  lapack_dsyev_fem::common dsyev_cmn;

  boost::python::object
  dgesvd_fem_wrapper(
    af::ref<double, af::c_grid<2> > const& a)
  {
    int m = a.accessor()[1];
    int n = a.accessor()[0];
    SCITBX_ASSERT(m > 0);
    SCITBX_ASSERT(n > 0);
    int lda = fem::max(1,m);
    af::shared<double> s(fem::min(m,n), 0.);
    af::versa<double, af::c_grid<2> > u(af::c_grid<2>(m, m), 0.);
    af::versa<double, af::c_grid<2> > vt(af::c_grid<2>(n, n), 0.);
    int lwork = fem::max(1,3*fem::min(m,n)+fem::max(m,n),5*fem::min(m,n));
    boost::scoped_array<double> work(new double[lwork]);
    int info;
    lapack_dgesvd_fem::dgesvd(
      dgesvd_cmn,
      /*jobu*/ "A",
      /*jobvt*/ "A",
      m,
      n,
      a[0],
      lda,
      s[0],
      u[0],
      /*ldu*/ m,
      vt[0],
      /*ldvt*/ n,
      work[0],
      lwork,
      info);
    boost::python::object result((boost_python_meta_ext::holder()));
    result.attr("s") = s;
    result.attr("u") = u;
    result.attr("vt") = vt;
    result.attr("info") = info;
    return result;
  }

  int
  dsyev_fem_wrapper(
    std::string const& jobz,
    std::string const& uplo,
    af::ref<double, af::c_grid<2> > const& a,
    af::ref<double> const& w)
  {
    SCITBX_ASSERT(a.accessor().is_square());
    int n = a.accessor()[0];
    SCITBX_ASSERT(w.size() == n);
    int lwork = std::max(1, 3*n-1);
    boost::scoped_array<double> work(new double[lwork]);
    int info;
    lapack_dsyev_fem::dsyev(
      dsyev_cmn,
      fem::str_cref(jobz.data(), jobz.size()),
      fem::str_cref(uplo.data(), uplo.size()),
      n,
      a[0],
      /*lda*/ n,
      w[0],
      work[0],
      lwork,
      info);
    return info;
  }

  SCITBX_LOC(fem)

}}} // namespace scitbx::lapack::boost_python

#endif // SCITBX_LAPACK_FEM

#if defined(SCITBX_LAPACK_FOR)

extern "C" {
  void
  dsyev_(
    char const* jobz,
    char const* uplo,
    int const* n,
    double* a,
    int const* lda,
    double* w,
    double* work,
    int const* lwork,
    int* info,
    int jobz_len,
    int uplo_len);
}

namespace scitbx { namespace lapack { namespace boost_python {

  int
  dsyev_for_wrapper(
    std::string const& jobz,
    std::string const& uplo,
    af::ref<double, af::c_grid<2> > const& a,
    af::ref<double> const& w)
  {
    SCITBX_ASSERT(a.accessor().is_square());
    int n = a.accessor()[0];
    SCITBX_ASSERT(w.size() == n);
    int lwork = std::max(1, 3*n-1);
    boost::scoped_array<double> work(new double[lwork]);
    int info;
    dsyev_(
      jobz.data(),
      uplo.data(),
      &n,
      &a[0],
      /*lda*/ &n,
      &w[0],
      &work[0],
      &lwork,
      &info,
      jobz.size(),
      uplo.size());
    return info;
  }

  SCITBX_LOC(for)

}}} // namespace scitbx::lapack::boost_python

#endif // SCITBX_LAPACK_FOR

#undef SCITBX_LOC

namespace scitbx { namespace lapack { namespace boost_python {

  void
  wrap()
  {
    using namespace boost::python;
#if defined(SCITBX_LAPACK_FEM)
    def("lapack_dgesvd_fem", dgesvd_fem_wrapper, (
      arg("a")));
    def("lapack_dsyev_fem", dsyev_fem_wrapper, (
      arg("jobz"), arg("uplo"), arg("a"), arg("w")));
    def("time_lapack_dsyev_fem", time_dsyev_fem);
#endif
#if defined(SCITBX_LAPACK_FOR)
    def("lapack_dsyev_for", dsyev_for_wrapper, (
      arg("jobz"), arg("uplo"), arg("a"), arg("w")));
    def("time_lapack_dsyev_for", time_dsyev_for);
#endif
  }

}}} // namespace scitbx::lapack::boost_python
