#include <cctbx/error.h>

int
main()
{
  double x = 1.1;
  int n = 1;
  CCTBX_ASSERT(x*x*x < n)(x)(n);
  return 0;
}
