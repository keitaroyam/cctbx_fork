#ifndef FEM_INTRINSICS_HPP
#define FEM_INTRINSICS_HPP

#include <algorithm>
#include <cmath>

namespace fem {

  template <typename T>
  inline
  int
  if_arithmetic(
    T const& value)
  {
    if (value == 0) return 0;
    if (value > 0) return 1;
    return -1;
  }

  template <typename V, typename S>
  inline
  V
  sign(
    V const& value,
    S const& sign_source)
  {
    if (sign_source < 0) {
      if (value > 0) return -value;
    }
    else if (value < 0) {
      return -value;
    }
    return value;
  }

  template <typename T>
  inline
  float
  real(
    T const& value) { return static_cast<float>(value); }

  template <typename T>
  inline
  double
  dble(
    T const& value) { return static_cast<double>(value); }

  inline
  float
  sqrt(
    float const& x)
  {
    return std::sqrt(x);
  }

  inline
  double
  sqrt(
    double const& x)
  {
    return std::sqrt(x);
  }

  inline
  float
  cos(
    float const& angle)
  {
    return std::cos(angle);
  }

  inline
  double
  cos(
    double const& angle)
  {
    return std::cos(angle);
  }

  inline
  float
  sin(
    float const& angle)
  {
    return std::sin(angle);
  }

  inline
  double
  sin(
    double const& angle)
  {
    return std::sin(angle);
  }

  inline
  float
  exp(
    float const& x)
  {
    return std::exp(x);
  }

  inline
  double
  exp(
    double const& x)
  {
    return std::exp(x);
  }

  inline
  double
  dexp(
    double const& x)
  {
    return std::exp(x);
  }

  inline
  float
  alog10(
    float const& x)
  {
    return std::log10(x);
  }

  inline
  double
  alog10(
    double const& x)
  {
    return std::log10(x);
  }

  template <typename T>
  inline
  int
  fint(
    T const& val)
  {
    return static_cast<int>(val);
  }

  template <typename T>
  inline
  int
  aint(
    T const& val)
  {
    return static_cast<int>(val);
  }

  template <typename T>
  inline
  float
  ffloat(
    T const& val)
  {
    return static_cast<float>(val);
  }

  inline
  int
  mod(
    int const& v1,
    int const& v2) { return v1 % v2; }

  inline
  float
  amod(
    float const& v1,
    float const& v2) { return std::fmod(v1, v2); }

  inline
  float
  mod(
    float const& v1,
    float const& v2) { return std::fmod(v1, v2); }

  inline
  double
  dmod(
    double const& v1,
    double const& v2) { return std::fmod(v1, v2); }

  inline
  double
  mod(
    double const& v1,
    double const& v2) { return std::fmod(v1, v2); }

  inline
  int
  iabs(
    int const& v) { return std::abs(v); }

  inline
  double
  dabs(
    double const& v) { return std::abs(v); }

  inline
  int
  min0(
    int const& v1,
    int const& v2) { return std::min(v1, v2); }

  inline
  int
  min(
    int const& v1,
    int const& v2) { return std::min(v1, v2); }

  inline
  float
  amin1(
    float const& v1,
    float const& v2) { return std::min(v1, v2); }

  inline
  float
  min(
    float const& v1,
    float const& v2) { return std::min(v1, v2); }

  inline
  double
  dmin1(
    double const& v1,
    double const& v2) { return std::min(v1, v2); }

  inline
  double
  min(
    double const& v1,
    double const& v2) { return std::min(v1, v2); }

  inline
  float
  amin0(
    int const& v1,
    float const& v2) { return std::min(static_cast<float>(v1), v2); }

  inline
  float
  min(
    int const& v1,
    float const& v2) { return std::min(static_cast<float>(v1), v2); }

  inline
  float
  min1(
    float const& v1,
    int const& v2) { return std::min(v1, static_cast<float>(v2)); }

  inline
  float
  min(
    float const& v1,
    int const& v2) { return std::min(v1, static_cast<float>(v2)); }

  inline
  int
  max0(
    int const& v1,
    int const& v2) { return std::max(v1, v2); }

  inline
  int
  max(
    int const& v1,
    int const& v2) { return std::max(v1, v2); }

  inline
  float
  amax1(
    float const& v1,
    float const& v2) { return std::max(v1, v2); }

  inline
  float
  amax1(
    float const& v1,
    float const& v2,
    float const& v3) { return amax1(amax1(v1, v2), v3); }

  inline
  float
  amax1(
    float const& v1,
    float const& v2,
    float const& v3,
    float const& v4) { return amax1(amax1(v1, v2, v3), v4); }

  inline
  float
  max(
    float const& v1,
    float const& v2) { return std::max(v1, v2); }

  inline
  double
  dmax1(
    double const& v1,
    double const& v2) { return std::max(v1, v2); }

  inline
  double
  max(
    double const& v1,
    double const& v2) { return std::max(v1, v2); }

  inline
  float
  amax0(
    int const& v1,
    float const& v2) { return std::max(static_cast<float>(v1), v2); }

  inline
  float
  max(
    int const& v1,
    float const& v2) { return std::max(static_cast<float>(v1), v2); }

  inline
  float
  max1(
    float const& v1,
    int const& v2) { return std::max(v1, static_cast<float>(v2)); }

  inline
  float
  max(
    float const& v1,
    int const& v2) { return std::max(v1, static_cast<float>(v2)); }

  inline
  int
  pow(
    int const& base,
    int const& exponent)
  {
    if (exponent < 0) return 0;
    int result = 1;
    for(int i=0;i<exponent;i++) {
      result *= base;
    }
    return result;
  }

  inline
  float
  pow(
    int const& base,
    float const& exponent)
  {
    return std::pow(static_cast<float>(base), exponent);
  }

  using std::abs;
  using std::log;
  using std::pow;
  using std::acos;
  using std::atan2;

} // namespace fem

#endif // GUARD
