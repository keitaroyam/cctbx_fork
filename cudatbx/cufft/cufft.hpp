#ifndef GPUTBX_CUFFT_H
#define GPUTBX_CUFFT_H

#ifdef CUFFT_DOUBLE_PRECISION
#define RealType double
#define CuFFTRealType cufftDoubleReal
#define CuFFTComplexType cufftDoubleComplex
#else
#define RealType float
#define CuFFTRealType cufftReal
#define CuFFTComplexType cufftComplex
#endif

// CCTBX includes
#include <scitbx/array_family/boost_python/utils.h>
#include <scitbx/array_family/versa.h>
#include <scitbx/array_family/accessors/c_grid.h>
#include <scitbx/error.h>

// CUDA includes
#include <cufft.h>
#include <cuda.h>
#include <cuda_runtime.h>

#include <ctime>
#include <iostream>

namespace gputbx { namespace cufft {
  namespace af = scitbx::af;

  af::versa<std::complex<RealType>, af::flex_grid<> >
  real_to_complex_3d_in_place(
    af::versa<RealType, af::flex_grid<> >& data)
  {
    int mx = static_cast<int>(data.accessor().all()[0]);
    int my = static_cast<int>(data.accessor().all()[1]);
    int mz = static_cast<int>(data.accessor().all()[2]);
    int nx = static_cast<int>(data.accessor().focus()[0]);
    int ny = static_cast<int>(data.accessor().focus()[1]);
    int nz = static_cast<int>(data.accessor().focus()[2]);
    SCITBX_ASSERT(mx == nx);
    SCITBX_ASSERT(my == ny);
    SCITBX_ASSERT(mz == 2*(nz/2+1));
    RealType* in = data.begin();
    std::complex<RealType> *out=reinterpret_cast<std::complex<RealType> *>(in);
    CuFFTRealType *cuda_in;
    int memsize = nx * ny * mz;
    cudaMalloc((void **)&cuda_in, sizeof(CuFFTComplexType)*memsize/2);
    cudaMemcpy(cuda_in, in, sizeof(CuFFTRealType)*memsize,
      cudaMemcpyHostToDevice);
    cufftHandle p;
#ifdef CUFFT_DOUBLE_PRECISION
    cufftPlan3d(&p, nx, ny, nz, CUFFT_D2Z);
    cufftSetCompatibilityMode(p, CUFFT_COMPATIBILITY_FFTW_ALL);
    cufftExecD2Z(p, cuda_in, (CuFFTComplexType *) cuda_in);
#else
    cufftPlan3d(&p, nx, ny, nz, CUFFT_R2C);
    cufftSetCompatibilityMode(p, CUFFT_COMPATIBILITY_FFTW_ALL);
    cufftExecR2C(p, cuda_in, (CuFFTComplexType *) cuda_in);
#endif
    cudaMemcpy(out, cuda_in, sizeof(CuFFTComplexType)*memsize/2,
      cudaMemcpyDeviceToHost);
    cudaFree(cuda_in);
    cufftDestroy(p);
    return af::versa<std::complex<RealType>, af::flex_grid<> >(
      data.handle(),
      af::flex_grid<>((af::adapt(af::tiny<int, 3>(mx,my,mz/2)))));
  }

  af::versa<RealType, af::flex_grid<> >
  complex_to_real_3d_in_place(
    af::versa<std::complex<RealType>, af::flex_grid<> >& data,
    af::tiny<int, 3> const& n)
  {
    af::boost_python::assert_0_based_3d(data.accessor());
    SCITBX_ASSERT(!data.accessor().is_padded());
    int mx = static_cast<int>(data.accessor().all()[0]);
    int my = static_cast<int>(data.accessor().all()[1]);
    int mz = static_cast<int>(data.accessor().all()[2]) * 2;
    int nx = n[0];
    int ny = n[1];
    int nz = n[2];
    SCITBX_ASSERT(mx == nx);
    SCITBX_ASSERT(my == ny);
    SCITBX_ASSERT(mz == 2*(nz/2+1));
    int memsize = nx * ny * mz;
    CuFFTComplexType *in = reinterpret_cast<CuFFTComplexType *>(data.begin());
    RealType *out = reinterpret_cast<RealType*>(in);
    CuFFTComplexType *cuda_in;
    cudaMalloc((void **)&cuda_in, sizeof(CuFFTComplexType)*memsize/2);
    cudaMemcpy(cuda_in, in, sizeof(CuFFTComplexType)*memsize/2,
      cudaMemcpyHostToDevice);
    CuFFTRealType *cuda_out = (CuFFTRealType *) cuda_in;
    cufftHandle p;
#ifdef CUFFT_DOUBLE_PRECISION
    cufftPlan3d(&p, nx, ny, nz, CUFFT_Z2D);
    cufftSetCompatibilityMode(p, CUFFT_COMPATIBILITY_FFTW_ALL);
    cufftExecZ2D(p, cuda_in, cuda_out);
#else
    cufftPlan3d(&p, nx, ny, nz, CUFFT_C2R);
    cufftSetCompatibilityMode(p, CUFFT_COMPATIBILITY_FFTW_ALL);
    cufftExecC2R(p, cuda_in, cuda_out);
#endif
    cudaMemcpy(out, cuda_out, sizeof(CuFFTRealType)*memsize,
      cudaMemcpyDeviceToHost);
    cudaFree(cuda_in);
    cufftDestroy(p);
    return af::versa<RealType, af::flex_grid<> >(
      data.handle(),
      af::flex_grid<>((af::adapt(af::tiny<int, 3>(nx,ny,mz))))
        .set_focus(af::adapt(n)));
  }

  void
  complex_to_complex_3d_in_place(
    af::versa<std::complex<RealType>, af::flex_grid<> > & data,
    int direction)
  {
    SCITBX_ASSERT(direction == CUFFT_FORWARD || direction == CUFFT_INVERSE);
    int nx = static_cast<int>(data.accessor().all()[0]);
    int ny = static_cast<int>(data.accessor().all()[1]);
    int nz = static_cast<int>(data.accessor().all()[2]);
    int n_elems = nx * ny * nz;
    CuFFTComplexType *in = reinterpret_cast<CuFFTComplexType*>(data.begin());
    CuFFTComplexType *cuda_in;//, *cuda_out;
    cudaMalloc((void **)&cuda_in, sizeof(CuFFTComplexType)*n_elems);
    cudaMemcpy(cuda_in, in, sizeof(CuFFTComplexType)*n_elems,
      cudaMemcpyHostToDevice);
    cufftHandle p;
#ifdef CUFFT_DOUBLE_PRECISION
    cufftPlan3d(&p, nx, ny, nz, CUFFT_Z2Z);
    cufftSetCompatibilityMode(p, CUFFT_COMPATIBILITY_FFTW_ALL);
    cufftExecZ2Z(p, cuda_in, cuda_in, direction);
#else
    cufftPlan3d(&p, nx, ny, nz, CUFFT_C2C);
    cufftSetCompatibilityMode(p, CUFFT_COMPATIBILITY_FFTW_ALL);
    cufftExecC2C(p, cuda_in, cuda_in, direction);
#endif
    cufftDestroy(p);
    cudaMemcpy(in, cuda_in, sizeof(CuFFTComplexType)*n_elems,
      cudaMemcpyDeviceToHost);
    cudaFree(cuda_in);
  }

}} // namespace gputbx::cufft

#endif
