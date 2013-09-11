#ifndef DIRECT_SUMMATION_CUH
#define DIRECT_SUMMATION_CUH

#include <cudatbx/cuda_utilities.cuh>
#include <cudatbx/math/reduction.cuh>
#include <cudatbx/scattering/direct_summation.h>
#include <cudatbx/scattering/form_factors.cuh>

/* ============================================================================
   Changing fType will affect the number of values that can be stored in shared
   and constant memory. It will also affect the sincos and exp functions used
   in the kernel since there are only hardware intrinsic functions for
   single-precision.
 */
const int threads_per_block = 1024;        // threads/block for GPU
const int padding = 128 / sizeof(fType);   // padding for data arrays
/* ============================================================================
 */

namespace cudatbx {
namespace scattering {

  // constants
  __device__ __constant__ fType two_pi = fType(2.0)*CUDART_PI_F;
  const int padded_size = 16;
  __device__ __constant__ int d_padded_size = padded_size;

  /* ==========================================================================

     Memory properties for C2070, compute capability 2.0
     (CUDA C Programming Guide v 4.0, Appendix F)
     ---------------------------------------------------
     registers - register, r/w, "fast", per-multiprocessor   32K 4B registers
     local memory - r/w, "slow", per-thread                  512 KB
     __shared__ - shared memory, r/w, "fast", block-wide     48 KB
     __device__ - global memory, r/w, "slow", grid-wide,     6 GB
     __constant__ - constant memory, r, "fast", grid-wide    64 KB

     Shared memory is broken up into 32 banks and is interleaved into 32-bit
     words (4 bytes).  For example, an array of length 64 containing single
     precision values will have elements 0 and 32 in the same bank, 1 and 33
     in the same bank, etc.  To access shared memory with no conflicts (all
     threads get data with one read), each thread should read from a different
     bank, or have multiple threads read the same value in the same bank.  In
     the previous example, having all threads access element 0 or having each
     thread read a different element between 0 and 31, inclusive, will only
     require one read.  Accessing elements 0 and 32 will require two reads.

     Appendix F.4 describes the memory properties for compute capability 2.0
     devices in more detail and has figures for efficient memory access
     patterns.

     Basic approach
     --------------
     Each thread calculates the sum for one h, so each thread will
     independently loop over all atoms and put the sum into global memory

     All coordinates are loaded into global memory and then each thread copies
     sections into shared memory.  The kernel loops over all sections to sum
     over all atoms.  Rotation matrix/translation vectors pairs are also loaded
     and looped in the same manner.  Form factors are stored in constant memory

     The thread index is checked against the length of the array multiple times
     because all threads are used for reading atom data from global, but only
     threads whose index is less than the array length are needed for
     summation.  Additionaly, two __syncthreads() calls are required.  The
     first is to make sure all the atom data is copied into shared memory
     before any summation is started, and the second is to make sure all the
     summation is finished before the atom data in shared memory is replaced
     with new data.

     Data format for kernel
     ----------------------
     xyz = x_0 ... x_n y_0 ... y_n z_0 ... z_n
     solvent_weights = s_0 s_1 ... s_n
     h = h_0 ... h_n k_0 ... k_n l_0 ... l_n
     rt = r_00 ... r_08 t_00 ... t_02 ... r_10 ... t_n2
     a = a_00 a_01 a_02 ... a_n3 a_n4 a_n5
     b = ""
     c = c_0 c_1 ... c_n

     To facilitate coalesced reads from global memory, the data is grouped
     into sections.  For example, for xyz, all the x's come first, then all
     the y's, and lastly, all the z's.  When read from global memory, three
     coalesced reads will read in all the xyz's for a set of 32 atoms, one
     read from each section.  The size of the shared arrays is equal to the
     number of threads so that all threads will attempt to read from global
     memory.  There are checks against the actual length of available data.

     For the structue_factor_kernel, the general format of the loops is,

     -----------------------------
     | x_0 | x_1 | x_2 | x_3 | ...          xyz array in global memory
     -----------------------------
        |     |     |     |                 each thread stores one value into
        |     |     |     |                 shared memory
        V     V     V     V                 x[threadIdx.x] = xyz[current_atom];
     -----------------------------
     | x_0 | x_1 | x_2 | x_3 | ...          x array in shared memory
     -----------------------------
        |
        |-----|-----|-----|                 each thread reads one value
        V     V     V     V                 x_a = x[a];
     --------------------------------------------------------
     |each thread calculates its own sum with its registers |
     --------------------------------------------------------
        |     |     |     |
        |     |     |     |                 loop over all atoms
        V     V     V     V
     -----------------------------
     | r_0 | r_1 | r_2 | r_3 | ...          each thread copies its sums into
     -----------------------------          the structure factor arrays in
     -----------------------------          global memory
     | i_0 | i_1 | i_2 | i_3 | ...
     -----------------------------

     --------------------------------------------------------------------------
  */

  // kernel
  template <typename floatType>
  __global__ void structure_factor_kernel
  (const int* scattering_type, const floatType* xyz,
   const floatType* solvent_weights, const int n_xyz, const int padded_n_xyz,
   const floatType* h, const int n_h, const int padded_n_h,
   const floatType* rt, const int n_rt,
   floatType* sf_real, floatType* sf_imag) {

    int i = blockDim.x * blockIdx.x + threadIdx.x;

    floatType h_i, k_i, l_i, stol_sq;
    floatType f[max_types];
    if (i < n_h) {
      // read h from global memory (stored in registers)
      h_i = h[               i];
      k_i = h[  padded_n_h + i];
      l_i = h[2*padded_n_h + i];

      // calculate form factors (stored in local memory)
      // last form factor is always for boundary solvent layer
      stol_sq = floatType(0.25) * (h_i*h_i + k_i*k_i + l_i*l_i);
      for (int type=0; type<dc_n_types; type++) {
        f[type] = form_factor(type,stol_sq);
      }
    }

    // copy atoms into shared memory one chunk at a time and sum
    // all threads are used for reading data
    // shared arrays can be allocated at kernel invocation, but it requires
    // partitioning a big array (implement later)
    __shared__ floatType x[threads_per_block];
    __shared__ floatType y[threads_per_block];
    __shared__ floatType z[threads_per_block];
    __shared__ floatType solvent[threads_per_block];
    __shared__ int s_type[threads_per_block];
    __shared__ floatType rot_trans[threads_per_block];
    floatType real_sum = 0.0;
    floatType imag_sum = 0.0;
    floatType s,c,f1,f2,xx,yy,zz,x_a,y_a,z_a;
    int current_atom, current_rt, rt_offset;

    for (int atom=0; atom<n_xyz; atom += blockDim.x) {
      current_atom = atom + threadIdx.x;
      // coalesce reads using threads, but don't read past n_xyz
      // one read for each variable should fill chunk of 32 atoms
      // total length = # of threads/block
      if (current_atom < n_xyz) {
        x[threadIdx.x] = xyz[                 current_atom];
        y[threadIdx.x] = xyz[  padded_n_xyz + current_atom];
        z[threadIdx.x] = xyz[2*padded_n_xyz + current_atom];
        solvent[threadIdx.x] = solvent_weights[current_atom];
        s_type[threadIdx.x] = scattering_type[current_atom];
      }

      // loop over all rotation/translation operators
      // one coalesced read will copy (# of threads)/(padded_size) rot/trans
      // since the number of threads is a multiple of 32, it will also always
      // be evenly divisible by padded_size
      for (int rt_i=0; rt_i<n_rt; rt_i += blockDim.x/d_padded_size) {
        current_rt = rt_i*d_padded_size + threadIdx.x;
        if (current_rt < n_rt*d_padded_size) {
          rot_trans[threadIdx.x] = rt[current_rt];
        }

        // wait for all data to be copied into shared memory
        __syncthreads();

        // then sum over all the atoms that are now available to all threads
        if (i < n_h) {
          for (int r=0; r<blockDim.x/d_padded_size; r++) {
            current_rt = rt_i + r;  // overall counter for rot/trans pairs
            if (current_rt < n_rt) {
              for (int a=0; a<blockDim.x; a++) {
                current_atom = atom + a;  // overall counter for atom number
                if (current_atom < n_xyz) {
                  x_a = x[a];  // transfer from shared memory to registers
                  y_a = y[a];  // might not be necessary due to cache
                  z_a = z[a];
                  rt_offset = r*d_padded_size;
                  // apply rotation and translation by expanding Rx + t
                  xx = (x_a*rot_trans[rt_offset    ] +
                        y_a*rot_trans[rt_offset + 1] +
                        z_a*rot_trans[rt_offset + 2] +
                        rot_trans[rt_offset + 9]);
                  yy = (x_a*rot_trans[rt_offset + 3] +
                        y_a*rot_trans[rt_offset + 4] +
                        z_a*rot_trans[rt_offset + 5] +
                        rot_trans[r*padded_size + 10]);
                  zz = (x_a*rot_trans[rt_offset + 6] +
                        y_a*rot_trans[rt_offset + 7] +
                        z_a*rot_trans[rt_offset + 8] +
                        rot_trans[rt_offset + 11]);
                  __sincosf(two_pi*(xx * h_i + yy * k_i + zz * l_i),&s,&c);
                  // bulk solvent correction in f
                  // boundary layer solvent scale in solvent
                  // structure factor = sum{(form factor)[exp(2pi h*x)]}
                  if (dc_complex_form_factor) {
                    // form factor = f1 + i f2
                    f1 = dc_a[s_type[a]*dc_n_terms] +
                      solvent[a]*dc_a[(dc_n_types-1)*dc_n_terms];
                    f2 = dc_b[s_type[a]*dc_n_terms] +
                      solvent[a]*dc_b[(dc_n_types-1)*dc_n_terms];
                    real_sum += f1*c - f2*s;
                    imag_sum += f1*s + f2*c;
                  } else {
                    f1 = f[s_type[a]] + solvent[a]*f[dc_n_types-1];
                    real_sum += f1 * c;
                    imag_sum += f1 * s;
                  }
                }
              }
            }
          }
        }

        // wait before starting next chunk so data isn't changed for lagging threads
        __syncthreads();
      }
    }

    // transfer result to global memory
    if (i < n_h) {
      sf_real[i] += real_sum;
      sf_imag[i] += imag_sum;
    }
  }

  /* ==========================================================================
     "Rapid and accurate calculation of small-angle scattering profiles using
      the golden ratio"
     Watson, MC, Curtis, JE. J. Appl. Cryst. (2013). 46, 1171-1177

     Quadrature approach for calculating SAXS intensities
     --------------------------------------------------------------------------
   */
  template <typename floatType>
  __global__ void expand_q_lattice_kernel
  (const floatType* q, const int n_q,
   const floatType* lattice, const int n_lattice, const int padded_n_lattice,
   floatType* workspace, const int padded_n_workspace) {

    int i = blockDim.x * blockIdx.x + threadIdx.x;

    __shared__ floatType lx[threads_per_block];
    __shared__ floatType ly[threads_per_block];
    __shared__ floatType lz[threads_per_block];

    int current_l;
    floatType q_j;
    if (i < n_lattice) {
      // copy lattice points into shared memory
      lx[threadIdx.x] = lattice[                     i];
      ly[threadIdx.x] = lattice[  padded_n_lattice + i];
      lz[threadIdx.x] = lattice[2*padded_n_lattice + i];
      __syncthreads();

      // and expand for all q
      for (int j=0; j<n_q; j++) {
        current_l = j*n_lattice + i;
        q_j = q[j];
        workspace[                       current_l] = q_j * lx[threadIdx.x];
        workspace[  padded_n_workspace + current_l] = q_j * ly[threadIdx.x];
        workspace[2*padded_n_workspace + current_l] = q_j * lz[threadIdx.x];
      }
      __syncthreads();
    }
  }

  // --------------------------------------------------------------------------

  template <typename floatType>
  __global__ void saxs_kernel
  (const int* scattering_type, const floatType* xyz,
   const floatType* solvent_weights, const int n_xyz, const int padded_n_xyz,
   const int n_q, const int n_lattice,
   floatType* workspace, const int padded_n_workspace) {

    int i = blockDim.x * blockIdx.x + threadIdx.x;

    // loop over all q and lattice points (more parallel than loop over q)
    floatType q_x,q_y,q_z,stol_sq;
    floatType f[max_types];
    int n_total = n_q * n_lattice;
    floatType c = 0.0625/(CUDART_PI_F*CUDART_PI_F);
    if (i < n_total) {
      // read q from global memory (stored in registers)
      q_x = workspace[                       i];
      q_y = workspace[  padded_n_workspace + i];
      q_z = workspace[2*padded_n_workspace + i];

      // calculate form factors (stored in local memory)
      stol_sq = c * (q_x*q_x + q_y*q_y + q_z*q_z);
      for (int type=0; type<dc_n_types; type++) {
        f[type] = form_factor(type,stol_sq);
      }
    }

    // copy atoms into shared memory one chunk at a time and sum
    // all threads are used for reading data
    __shared__ floatType x[threads_per_block];
    __shared__ floatType y[threads_per_block];
    __shared__ floatType z[threads_per_block];
    __shared__ floatType solvent[threads_per_block];
    __shared__ int s_type[threads_per_block];
    floatType real_sum = 0.0;
    floatType imag_sum = 0.0;
    floatType s,f1,f2;
    int current_atom;

    for (int atom=0; atom<n_xyz; atom += blockDim.x) {
      current_atom = atom + threadIdx.x;
      // coalesce reads using threads, but don't read past n_xyz
      // one read for each variable should fill chunk of 32 atoms
      // total length = # of threads/block
      if (current_atom < n_xyz) {
        x[threadIdx.x] = xyz[                 current_atom];
        y[threadIdx.x] = xyz[  padded_n_xyz + current_atom];
        z[threadIdx.x] = xyz[2*padded_n_xyz + current_atom];
        solvent[threadIdx.x] = solvent_weights[current_atom];
        s_type[threadIdx.x] = scattering_type[current_atom];
      }

      // wait for all data to be copied into shared memory
      __syncthreads();

      // then sum over all the atoms that are now available to all threads
      if (i < n_total) {
        for (int a=0; a<blockDim.x; a++) {
          current_atom = atom + a;  // overall counter for atom number
          if (current_atom < n_xyz) {
            __sincosf((x[a] * q_x + y[a] * q_y + z[a] * q_z),&s,&c);

            // structure factor = sum{(form factor)[exp(2pi h*x)]}
            if (dc_complex_form_factor) {
              // form factor = f1 + i f2
              f1 = dc_a[s_type[a]*dc_n_terms] +
                solvent[a]*dc_a[(dc_n_types-1)*dc_n_terms];
              f2 = dc_b[s_type[a]*dc_n_terms] +
                solvent[a]*dc_b[(dc_n_types-1)*dc_n_terms];
              real_sum += f1*c - f2*s;
              imag_sum += f1*s + f2*c;
            } else {
              f1 = f[s_type[a]] + solvent[a]*f[dc_n_types-1];
              real_sum += f1 * c;
              imag_sum += f1 * s;
            }
          }
        }
      }
      // wait before starting next chunk so data isn't changed for lagging threads
      __syncthreads();
    }

    // transfer result to global memory
    if (i < n_total) {
      workspace[i] = real_sum * real_sum + imag_sum * imag_sum;
    }
  }

  // --------------------------------------------------------------------------

  template <typename floatType>
  __global__ void solvent_saxs_kernel
  (const int* scattering_type, const floatType* xyz,
   const floatType* solvent_weights, const int n_xyz, const int padded_n_xyz,
   const int n_q, const int n_lattice,
   floatType* workspace, const int padded_n_workspace) {

    int i = blockDim.x * blockIdx.x + threadIdx.x;

    // loop over all q and lattice points (more parallel than loop over q)
    floatType q_x,q_y,q_z,stol_sq;
    floatType f[max_types];
    int n_total = n_q * n_lattice;
    floatType c = 0.0625/(CUDART_PI_F*CUDART_PI_F);
    if (i < n_total) {
      // read q from global memory (stored in registers)
      q_x = workspace[                       i];
      q_y = workspace[  padded_n_workspace + i];
      q_z = workspace[2*padded_n_workspace + i];

      // calculate form factors (stored in local memory)
      stol_sq = c * (q_x*q_x + q_y*q_y + q_z*q_z);
      for (int type=0; type<dc_n_types; type++) {
        f[             type] = p_form_factor(type,stol_sq);
        f[dc_n_types + type] = x_form_factor(type,stol_sq);
      }
    }

    // copy atoms into shared memory one chunk at a time and sum
    // all threads are used for reading data
    __shared__ floatType x[threads_per_block];
    __shared__ floatType y[threads_per_block];
    __shared__ floatType z[threads_per_block];
    __shared__ floatType solvent[threads_per_block];
    __shared__ int s_type[threads_per_block];
    floatType p_real = 0.0;
    floatType p_imag = 0.0;
    floatType x_real = 0.0;
    floatType x_imag = 0.0;
    floatType bl_real = 0.0;
    floatType bl_imag = 0.0;
    floatType s,f1,f2;
    int current_atom;

    for (int atom=0; atom<n_xyz; atom += blockDim.x) {
      current_atom = atom + threadIdx.x;
      // coalesce reads using threads, but don't read past n_xyz
      // one read for each variable should fill chunk of 32 atoms
      // total length = # of threads/block
      if (current_atom < n_xyz) {
        x[threadIdx.x] = xyz[                 current_atom];
        y[threadIdx.x] = xyz[  padded_n_xyz + current_atom];
        z[threadIdx.x] = xyz[2*padded_n_xyz + current_atom];
        solvent[threadIdx.x] = solvent_weights[current_atom];
        s_type[threadIdx.x] = scattering_type[current_atom];
      }

      // wait for all data to be copied into shared memory
      __syncthreads();

      // then sum over all the atoms that are now available to all threads
      if (i < n_total) {
        for (int a=0; a<blockDim.x; a++) {
          current_atom = atom + a;  // overall counter for atom number
          if (current_atom < n_xyz) {
            __sincosf((x[a] * q_x + y[a] * q_y + z[a] * q_z),&s,&c);

            // structure factor = sum{(form factor)[exp(2pi h*x)]}
            f1 = f[s_type[a]];
            p_real += f1 * c;
            p_imag += f1 * s;
            f2 = f[dc_n_types + s_type[a]];
            x_real += f2 * c;
            x_imag += f2 * s;
            f1 = solvent[a]*f[dc_n_types-1];
            bl_real += f1 * c;
            bl_imag += f1 * s;
          }
        }
      }
      // wait before starting next chunk so data isn't changed for lagging threads
      __syncthreads();
    }

    // transfer result to global memory
    if (i < n_total) {
      workspace[  padded_n_workspace + i] = p_real;
      workspace[2*padded_n_workspace + i] = p_imag;
      workspace[3*padded_n_workspace + i] = x_real;
      workspace[4*padded_n_workspace + i] = x_imag;
      workspace[5*padded_n_workspace + i] = bl_real;
      workspace[6*padded_n_workspace + i] = bl_imag;
    }
  }

  // --------------------------------------------------------------------------

  template <typename floatType>
  __global__ void collect_solvent_saxs_kernel
  (const int n_q, const int n_lattice, const floatType c1, const floatType c2,
   floatType* workspace, const int padded_n_workspace) {
    int i = blockDim.x * blockIdx.x + threadIdx.x;
    floatType real_sum, imag_sum;
    if (i < n_q*n_lattice) {
      real_sum = workspace[ padded_n_workspace + i] +
        c1 * workspace[3*padded_n_workspace + i] +
        c2 * workspace[5*padded_n_workspace + i];
      imag_sum = workspace[2*padded_n_workspace + i] +
        c1 * workspace[4*padded_n_workspace + i] +
        c2 * workspace[6*padded_n_workspace + i];
      workspace[i] = real_sum * real_sum + imag_sum * imag_sum;
    }
  }
  
  /* ==========================================================================
   */

}
}
#endif // DIRECT_SUMMATION_CUH
