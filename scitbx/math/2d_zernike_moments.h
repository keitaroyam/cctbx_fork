#ifndef SCITBX_MATH_2D_ZERNIKE_MOM_H
#define SCITBX_MATH_2D_ZERNIKE_MOM_H

#include <scitbx/constants.h>
#include <cmath>
#include <cstdio>
#include <iostream>
#include <iomanip>

#include <scitbx/array_family/shared.h>
#include<scitbx/array_family/versa.h>
#include <scitbx/array_family/accessors/c_grid.h>

#include <scitbx/vec2.h>
#include <scitbx/vec3.h>
#include <scitbx/mat3.h>
#include <scitbx/math/zernike.h>
#include <complex>
#include <string>

using namespace scitbx::math::zernike;
using scitbx::constants::pi;

namespace af=scitbx::af;

namespace scitbx { namespace math {
namespace zernike {

  template <typename FloatType>
  class grid_2d
  { //the 2D grid that encloses unit disk with resolution 1/(2*N)
    public:
      grid_2d() {}
      grid_2d(
             int const& N_point,
             int const& n_max
             ):
             N_point_(N_point),
             n_max_(n_max),
             ss_r_(n_max, 0.0),
             ss_s_(n_max, 0.0),
             grid_(n_max+1, n_max+1),
             ss_(grid_, 0.0)
      {
        delta_ = 1.0/static_cast<FloatType>(N_point_);
        build_grid();
        compute_gm();
      }


      int np() { return N_point_; }

      af::versa< FloatType, af::c_grid<2> > ss() {
        return ss_;
      }

      bool build_grid()
      {
        for(int i=1;i<=2*N_point_+1;i++)
          one_d_.push_back( i );

        for(int i=0;i<=2*N_point_;i++) {
          for(int j=0;j<=2*N_point_;j++) {
               scitbx::vec2<FloatType>point( one_d_[i],one_d_[j]);
               scitbx::vec2< int > p_indx( i, j );
               all_indx_.push_back( p_indx );
               if(point.length_sq() <=1.0){  //in/on the unit sphere
                 xy_indx_.push_back( p_indx  );
      //           xy_.push_back( point );
               }  //end if
          }  //end j
        } //end i
        return true;
      }

     af::versa< FloatType, af::c_grid<2> > get_all_ss() { return ss_; }

// Clean the grid point based on voxel value:
// i.e. if (voxel(x,y,z) == 0), there is no need to keep the grid point

      bool clean_space( af::const_ref< scitbx::vec3<FloatType> > image) {
        int total_point=image.size();
        FloatType x,y, bound, r2;
        bound = N_point_*N_point_;
        for(int i=0;i<total_point;i++) {
          x=image[i][0]-N_point_;
          y=image[i][1]-N_point_;
          r2 = x*x+y*y;
          if(image[i][2] != 0  && r2 <= bound) {
            voxel_.push_back( image[i] );
          }
        }
//        std::cout<<"occupied pixel "<<voxel_.size()<<std::endl;
        return true;
      }

      bool compute_gm()
      {
//      Starts with order (0)
        gm_.push_back( af::shared< FloatType > (2*N_point_+1, 1.0)  );
        for(int n=1;n<=n_max_+2;n++)
          gm_.push_back( array_product(gm_[n-1],one_d_, n+1) );
        return true;
      }

      af::shared<FloatType> array_product( af::shared<FloatType> a, af::shared<FloatType> b, int n)
      {
        int size = a.size();
        FloatType d(n);
        af::shared<FloatType> result;
        result.reserve( size );
        for(int i=0;i<size;i++) {
          result.push_back(a[i]*b[i]);
        }
        return result;
      }

      FloatType space_sum(int r, int s)
      {
        int total_point=voxel_.size(), x,y;
        FloatType tot(0.0), temp,z;

        for(int i=0;i<total_point;i++) {
          x=voxel_[i][0];
          y=voxel_[i][1];
          z=voxel_[i][2];

          temp=gm_[r][x]*gm_[s][y]*z;
          tot += temp;
        }
        return tot;
      }


      bool construct_space_sum() {
        for(int r=0;r<=n_max_;r++) {
          for(int s=0;s<=n_max_;s++) {
        //      if( r+s <= n_max_)
                ss_(r, s) =  space_sum(r,s);
          } //end of s
        } //end of r

        return true;
      }

      FloatType get_ss(int r, int s) {
        return ss_(r,s);
      }

    private:
      scitbx::af::shared< scitbx::vec2<int> > all_indx_;
      scitbx::af::shared< scitbx::vec2<int> > xy_indx_;
      scitbx::af::shared< scitbx::vec3<FloatType> > voxel_;
      scitbx::af::shared<FloatType>one_d_;
      scitbx::af::shared<FloatType>ss_r_;
      scitbx::af::shared<FloatType>ss_s_;
      scitbx::af::shared< scitbx::af::shared<FloatType> >gm_;
        //Geometric moments up to order n_max_
      af::c_grid<2> grid_;
      af::versa< FloatType, af::c_grid<2> > ss_;
      int n_max_, N_point_;
      FloatType delta_;
  };

  template <typename FloatType>
  class zernike_2d_moments
  {
    public:
      zernike_2d_moments(){}
      zernike_2d_moments(
             grid_2d<FloatType> grid,
             int const& n_max
             ):
             grid_(grid),
             C_nm_(n_max),
             C_nn_(n_max),
             n_max_(n_max)
      {
        N_point_=grid.np();
        initialize();
        calc_Chi();
      }


      void calc_moments( af::const_ref< FloatType> new_ss ) {
        update_ss( new_ss );
        calc_Chi();
        return;
      }

      void update_ss( af::const_ref< FloatType> new_ss ) {
        int size = new_ss.size();
        for(int i=0;i<size;i++)
          ss_[i] = new_ss[i];
        return;
      }

      //scitbx::math::zernike::nl_array<std::complex< FloatType > >
      scitbx::af::shared< std::complex<FloatType > >
      all_moments()
      {
        return C_nm_.coefs();
      }

      scitbx::math::zernike::nl_array<FloatType>
      fnn()
      { return C_nn_; }



      std::complex<FloatType> get_moment(int n,int m)
      {
         return C_nm_.get_coef(n,m);
      }

      void set_moment(int n,int m,std::complex<FloatType> value)
      {
         C_nm_.set_coef(n,m,value);
         return;
      }

      void calc_Chi()
      {
        int in,im;
        std::complex<FloatType> value;
        in = 0;
        for(int n=n_max_;n>=0;n--) {
          im = 0;
          for(int m=n;m>=0;m-=2){
             value=calc_Chi_nm(n,m,in,im);
             set_moment(n,m,value);
             if(m>0) {
               value = std::conj(value);
             //  value *= is_even(m);
               set_moment(n,-m,value);
             } //endif
            im++;
          }
          in++;
        }
        return;
      }

      std::complex<FloatType> calc_Chi_nm(int n, int m, int in, int im)
      {
        std::complex<FloatType> value(0,0);
        int ik=0;
        for(int k=n;k>=m;k-=2)
        {
          value += Bnmk_[in][im][ik]*sum1(n,m,k);
          ik++;
        }
        value *= (n+1.0)/norm_factor_;
        return value;
      }



// Utility functions

      void initialize()
      {
        ss_ = grid_.ss().deep_copy();
        norm_factor_ = pi*N_point_*N_point_;
      //  for(int i=0;i<=n_max_;i++)
       //   for(int j=0;j<=n_max_;j++)
        //    std::cout<<i<<" "<<j<<" "<<ss_(i,j)<<std::endl;
        build_fac();
        build_bino();
        build_Bnmk_array();
        build_H_array(N_point_+1);
        //print_Bnmk();

        std::complex<FloatType>complex_i(0,-1.0);
        for(int i=0;i<=n_max_;i++)
          i_pow_n_.push_back( ( std::pow(complex_i, i)) );
      //test();
      }

      bool test()
      {
        std::cout<<"factorial(10): "<<fac_[10]<<" compared to "<<3628800<<std::endl;
        std::cout<<"binomial(10,6): "<<bino_[10][6]<<" compared to "<<210<<std::endl;
      }

      void build_fac()
      {
        fac_.reserve(2*(n_max_+2));
        fac_.push_back(1.0);
        for(int i=1;i<=2*n_max_+3;i++)  //maximum factorial is (2*n+1)!
        {
          fac_.push_back( fac_[i-1]*i );
        }
        return;
      }

      void build_bino()
      {
        for(int i=0;i<=n_max_*2+2;i++){
          scitbx::af::shared<FloatType> bino_i(i+1,scitbx::af::init_functor_null<FloatType>() );
          for(int j=0;j<=(i/2);j++){
            bino_i[j] = fac_[i]/(fac_[j]*fac_[i-j]);
            bino_i[i-j]= bino_i[j];
          }
          bino_.push_back( bino_i );
        }
        return;
      }

      void build_Bnmk_array()
      {
        int n,m,k;
        int in,im,ik;
        for( n=n_max_;n>=0;n--){
          af::shared< af::shared< FloatType > > Bmk;
          for( m=n;m>=0;m-=2) {
            af::shared< FloatType > Bk;
            for( k=n;k>=m;k-=2) {
              Bk.push_back(0);
              }
            Bmk.push_back( Bk );
          }
          Bnmk_.push_back( Bmk );
        }

        in=0;
        for( n=n_max_;n>=0;n--){
          im=1;
          Bnmk_[in][0][0] = 1.0;
          for( m=n-2;m>=0;m-=2) {
            Bnmk_[in][im][0]=Bnmk_[in][im-1][0]*(n+m+2.0)/(n-m);
            ik=1;
            for( k=n-2;k>=m;k-=2) {
              Bnmk_[in][im][ik]=-Bnmk_[in][im][ik-1]*(k+m+2.0)*(k+2.0-m)/(k+2.0+n)/(n-k);
              ik++;
              }
            im++;
          }
          in++;
        }

      }

      void print_Bnmk()
      {
        int in,im,ik;
        in = 0;
        for(int n=n_max_;n>=0;n--) {
          im = 0;
          for(int m=n;m>=0;m-=2) {
            ik=0;
            for(int k=n;k>=m;k-=2) {
              std::cout<<n<<" "<<m<<" "<<k<<" "<<Bnmk_[in][im][ik]<<std::endl;
              ik++;
            }
            im++;
          }
          in++;
        }
        return;
      }

      void build_H_array(int D)
      {
        FloatType log_D=std::log(D);
        FloatType log_D_1=std::log(D-1);

        for(int alpha=0;alpha<=n_max_;alpha++) {
          af::shared< FloatType > ha;
          for(int p=0;p<=alpha;p++) {
            ha.push_back( is_even(alpha-p)*bino_[alpha][p]*std::exp( (alpha-p)*log_D-alpha*log_D_1) );
          }
          H_array_.push_back( ha );
        }
      }

      std::complex<FloatType> sum3(int n,int m, int k, int nu, int d)
      {
        std::complex<FloatType> temp(0,0), tempb(0,0);
        int beta = 2*nu+d;
        int alpha = k-beta;
        for(int p=0;p<=alpha;p++){
          tempb = 0.0;
          for( int q=0;q<=beta; q++) {
        //    std::cout<<"in sum3 "<<nu<<" "<<temp<<std::endl;
            tempb += H_array_[beta][q]*ss_(p,q);
          }
          temp += H_array_[alpha][p]*tempb;
        }
        return temp;
      }

      std::complex<FloatType> sum2(int n,int m, int k, int nu)
      {
        std::complex<FloatType> temp(0,0);
        for(int d=0;d<=m;d++) {
          temp += i_pow_n_[d]*bino_[m][d]*sum3(n,m,k,nu,d);
//          std::cout<<"in sum2 "<<nu<<" "<<temp<<std::endl;
        }
        return temp;
      }

      std::complex<FloatType> sum1(int n,int m, int k)
      {
        std::complex<FloatType> temp(0,0);
        int max_nu = (k-m)/2;
        for(int nu=0;nu<=max_nu;nu++) {
          temp += bino_[max_nu][nu]*sum2(n,m,k,nu);
//          std::cout<<"in sum1 "<<n<<" "<<m<<" "<<nu<<" "<<temp<<std::endl;
        }
        //temp = conj(temp);
        return temp;
      }

      int is_even(int n)
      {
        if(n == n/2*2) return 1;
        else return (-1);
      }

    private:
      scitbx::math::zernike::nl_array<std::complex<FloatType> > C_nm_;
      scitbx::math::zernike::nl_array<FloatType> C_nn_;
      scitbx::af::shared<FloatType> fac_;
      scitbx::af::shared< scitbx::af::shared<FloatType> > bino_;
      scitbx::af::shared< scitbx::af::shared<FloatType> > H_array_;
      scitbx::af::shared< scitbx::af::shared< scitbx::af::shared<FloatType> > > Bnmk_;
      int n_max_, N_point_;
      FloatType norm_factor_;
      scitbx::af::shared< std::complex<FloatType> > i_pow_n_;
      af::versa< FloatType, af::c_grid<2> > ss_;
      grid_2d<FloatType> grid_;
  };


}
}} //namespace scitbx::math::2dzernike
#endif //SCITBX_MATH_2D_ZERNIKE_MOM_H
