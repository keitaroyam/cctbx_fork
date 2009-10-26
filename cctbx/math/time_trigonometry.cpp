#include <cctbx/math/cos_sin_table.h>
#include <iostream>
#include <boost/timer.hpp>

int main() {
  unsigned const n = 1024, p = 1024;
  cctbx::math::cos_sin_table<double> table(n);
  cctbx::math::cos_sin_exact<double> exact;
  std::complex<double> sum = 0;
  boost::timer t;
  for (unsigned i=0; i<p*n; ++i) {
    sum += table(i);
  }
  std::cout << t.elapsed() << "\t" << sum << std::endl;
  sum = 0;
  t.restart();
  for (unsigned i=0; i<p*n; ++i) {
    sum += exact(i);
  }
  std::cout << t.elapsed() << "\t" << sum << std::endl;
  std::cout << "OK\n" << std::endl;
  return 0;
}
