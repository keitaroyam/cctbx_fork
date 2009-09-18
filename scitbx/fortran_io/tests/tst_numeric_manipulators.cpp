#include <scitbx/fortran_io/numeric_manipulators.h>
#include <scitbx/error.h>
#include <iostream>

void exercise_int() {
  using namespace scitbx::fortran_io::manipulators;
  fortran_int i3(3);
  int val, val1, val2;
  std::string s("  1  2333  4");
  {
    std::stringstream input(s);
    input >> i3 >> val;
    SCITBX_ASSERT(val == 1)(val);
    input >> i3 >> val;
    SCITBX_ASSERT(val == 2)(val);
    input >> i3 >> val;
    SCITBX_ASSERT(val == 333)(val);
    input >> i3 >> val;
    SCITBX_ASSERT(val == 4)(val);
    SCITBX_ASSERT(input.eof());
  }
  {
    std::stringstream input(s);
    input >> i3 >> val1 >> val2;
    SCITBX_ASSERT(val1 == 1)(val1);
    SCITBX_ASSERT(val2 == 2333)(val1);
  }
  {
    std::stringstream input(s);
    input >> sticky(i3) >> val1 >> val2;
    SCITBX_ASSERT(val1 == 1)(val1);
    SCITBX_ASSERT(val2 == 2)(val1);
  }
}

void exercise_real() {
  using namespace scitbx::fortran_io::manipulators;
  fortran_real f4_2(4,2);
  double val, val1, val2;
  std::string s("1.169.48");
  {
    std::stringstream input(s);
    input >> sticky(f4_2) >> val1 >> val2;
    SCITBX_ASSERT(val1 == 1.16)(val1);
    SCITBX_ASSERT(val2 == 9.48)(val2);
  }
}

int main() {
  exercise_int();
  exercise_real();
  std::cout << "OK" << std::endl;
}
