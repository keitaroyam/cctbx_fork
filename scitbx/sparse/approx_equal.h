#ifndef SCITBX_SPARSE_APPROX_EQUAL_H
#define SCITBX_SPARSE_APPROX_EQUAL_H

#include <limits>
#include <scitbx/sparse/vector.h>
#include <scitbx/sparse/matrix.h>

namespace scitbx { namespace sparse {

/// Element-wise comparison with a given absolute tolerance
template<typename T>
struct approx_equal
{
  T tolerance;

  approx_equal(T tolerance_=std::numeric_limits<T>::epsilon())
    : tolerance(tolerance_)
  {}

  bool operator()(vector<T> const &a, vector<T> const &b) const
  {
    if (a.size() != b.size()) return false;
    a.sort_indices();
    b.sort_indices();
    typename vector<T>::const_iterator p = a.begin(), q = b.begin();
    while (p != a.end() && q != b.end()) {
      if (p.index() < q.index()) {
        if (std::abs(*p) > tolerance) return false;
        ++p;
      }
      else if (p.index() > q.index()) {
        if (std::abs(*q) > tolerance) return false;
        ++q;
      }
      else {
        if (std::abs(*p - *q) > tolerance) return false;
        ++p; ++q;
      }
    }
    typename vector<T>::const_iterator r, r_end;
    if (p == a.end()) {
      r = q;
      r_end = b.end();
    }
    else {
      r = p;
      r_end = a.end();
    }
    for(; r != r_end; ++r) {
      if (std::abs(*r) > tolerance) return false;
    }
    return true;
  }

  bool operator()(matrix<T> const &a, matrix<T> const &b) const
  {
    if(a.n_cols() != b.n_cols() || a.n_rows() != b.n_rows()) return false;
    for (typename matrix<T>::column_index j=0; j < a.n_cols(); j++) {
      if (!(*this)(a.col(j), b.col(j))) return false;
    }
    return true;
  }
};


}} // scitbx::sparse

#endif // GUARD
