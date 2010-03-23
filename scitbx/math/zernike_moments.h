#ifndef SCITBX_MATH_ZERNIKE_MOM_H_
#define SCITBX_MATH_ZERNIKE_MOM_H

#include <scitbx/constants.h>
#include <cmath>
#include <cstdio>
#include <iostream>
#include <iomanip>

#include <scitbx/array_family/shared.h>

#include <scitbx/vec3.h>
#include <scitbx/math/zernike.h>
#include <complex>
#include <string>

using namespace scitbx::math::zernike;
using scitbx::constants::pi;

namespace af=scitbx::af;

namespace scitbx { namespace math {
namespace zernike {

  template <typename FloatType>
  class voxel
  {
    public:
      voxel() {}
      voxel( int const& n_point,   // will be optimized later: rmax/fraction/np<=bond_length
             int const& splat_range, // number of grid points that an atom spans in 1d
             bool const& uniform,
             bool const& fixed_dx,
             FloatType const& dx,
             FloatType const& fraction, // will be optimized later: splat_range*dx< (1-fraction)*rmax
             scitbx::af::const_ref< scitbx::vec3<FloatType> > xyz
           ):
           NP_(n_point), dx_(1.0/static_cast<FloatType>(NP_) ), uniform_(uniform),fixed_dx_(fixed_dx),
           splat_range_(splat_range), natom_(xyz.size()), center_(0,0,0), fract_(fraction)
      {
        FloatType tmp_r2;
        for(int i=0;i<natom_;i++) {
          xyz_.push_back( xyz[i] );
          center_ += xyz_[i];
        }
        center_ /= static_cast<FloatType> (natom_);
        rmax_=0.0;
        for(int i=0;i<natom_;i++) {
          xyz_[i] -= center_;
          tmp_r2 = xyz_[i].length_sq();
          if(rmax_< tmp_r2) rmax_= tmp_r2;
        }
        rmax_ = std::sqrt( rmax_ );

        if(fixed_dx_) {
          NP_ = int(rmax_/dx)+1;
          dx_ = 1.0/static_cast<FloatType>(NP_);
        }

        scale_ = 1.0/rmax_*fract_;
        for(int i=0;i<natom_;i++)
          scaled_xyz_.push_back( scale_*xyz_[i] );

        initialize_voxel();
        xyz2voxel();
  //      std::string info( print_status() );

      }

      FloatType rmax() { return rmax_; }
      FloatType fraction() { return fract_; }

      int occupied_sites() {

        int count=0, n_tot_=2*NP_+1;
        for(int i=0;i<n_tot_;i++)
          for(int j=0;j<n_tot_;j++)
            for(int k=0;k<n_tot_;k++)
              if(value_[i][j][k] > 0)
                count++;
        return count;
      }

      std::string print_status()
      {
        int tot_point= std::pow(2*NP_+1,3);
        int occupied_points = occupied_sites();
        std::string info("");
        char *tmp_info;

        info += "number of grid point is: ";
        std::sprintf(tmp_info, "%d\n", tot_point);
        info += tmp_info;

        info += "rmax is                : ";
        std::sprintf(tmp_info, "%f\n", rmax_);
        info += tmp_info;

        info += "max fraction one 1-d is: ";
        std::sprintf(tmp_info, "%f\n", fract_);
        info += tmp_info;

        info += "non-empty grid point is: ";
        std::sprintf(tmp_info, "%d\n", occupied_points);
        info += tmp_info;

        info += "non-empty grid fract is: ";
        std::sprintf(tmp_info,"%f\n", occupied_points/FloatType(tot_point));
        info += tmp_info;

        return info;
      }

      int np() { return NP_;}

      scitbx::af::shared< scitbx::vec3< FloatType> > xyz() {return xyz_;}

      bool xyz2voxel() {
        // build voxel map based on xyz coord
        int xi,yi,zi;
        int two_NP = NP_*2;
        for(int i=0;i<natom_;i++) {
          if(scaled_xyz_[i][0] <0 )
            xi=int(scaled_xyz_[i][0]/dx_-0.5)+NP_;
          else
            xi=int(scaled_xyz_[i][0]/dx_+0.5)+NP_;

          if(scaled_xyz_[i][1] <0 )
            yi=int(scaled_xyz_[i][1]/dx_-0.5)+NP_;
          else
            yi=int(scaled_xyz_[i][1]/dx_+0.5)+NP_;

          if(scaled_xyz_[i][2] <0 )
            zi=int(scaled_xyz_[i][2]/dx_-0.5)+NP_;
          else
            zi=int(scaled_xyz_[i][2]/dx_+0.5)+NP_;

          if(uniform_)
            mark_region_uniform(xi,yi,zi);
          else
            mark_region_non_uniform(xi,yi,zi);
        }
      }

      void mark_region_uniform(int xi, int yi, int zi) {
        for(int i=xi-splat_range_;i<=xi+splat_range_;i++)
          for(int j=yi-splat_range_;j<=yi+splat_range_;j++)
            for(int k=zi-splat_range_;k<=zi+splat_range_;k++)
              value_[i][j][k] = 1.0;  //uniform

        return;
      }

      void mark_region_non_uniform(int xi, int yi, int zi) {
        for(int i=xi-splat_range_;i<=xi+splat_range_;i++)
          for(int j=yi-splat_range_;j<=yi+splat_range_;j++)
            for(int k=zi-splat_range_;k<=zi+splat_range_;k++)
              value_[i][j][k] += 1.0;  //non-uniform
          return;
        }

      bool initialize_voxel() {
        int n_tot=2*NP_+1;
        int i,j,k;
        for(i=0;i<n_tot;i++){
          af::shared< af::shared<FloatType> > voxel_i;
          for(j=0;j<n_tot;j++) {
            af::shared< FloatType > voxel_ij(n_tot,0.0);
            voxel_i.push_back( voxel_ij );
          }
          value_.push_back( voxel_i );
        }
        return true;
      }

      FloatType value(scitbx::vec3<int> xyz) {
        return get_value(xyz[0],xyz[1],xyz[2]);
      }

      FloatType get_value(int xi, int yi, int zi) {
        return value_[xi][yi][zi];
      }

      af::shared< FloatType > map()
      { af::shared<FloatType> map;
        int i,j,k, n_tot = 2*NP_+1;
        for(i=0;i<n_tot;i++)
          for(j=0;j<n_tot;j++)
            for(k=0;k<n_tot;k++)
              map.push_back(value_[i][j][k]);
        return map;
      }


    private:
      scitbx::af::shared< scitbx::vec3<FloatType> > xyz_;
      scitbx::af::shared< scitbx::vec3<FloatType> > scaled_xyz_;
      int natom_, NP_;
      bool uniform_, fixed_dx_;
      FloatType dx_, splat_range_, rmax_, scale_, fract_;
      scitbx::vec3<FloatType> center_;
      af::shared< af::shared< af::shared<FloatType> > > value_;
  };


  template <typename FloatType>
  class grid
  { //the 3D grid that encloses unit sphere with resolution 1/(2*N)
    public:
      grid() {}
      grid(
             int const& N_point,
             int const& n_max
             ):
             N_point_(N_point),
             n_max_(n_max)
      {
        delta_ = 1.0/static_cast<FloatType>(N_point_);
        build_grid();
        compute_gm();
      }

      bool build_grid()
      {
        for(int i=-N_point_;i<=N_point_;i++)
          one_d_.push_back( i*delta_ );

        for(int i=0;i<=2*N_point_;i++) {
          for(int j=0;j<=2*N_point_;j++) {
            for(int k=0;k<=2*N_point_;k++) {
               scitbx::vec3<FloatType>point( one_d_[i],one_d_[j],one_d_[k] );
               if(point.length_sq() <=1.0){  //in/on the unit sphere
                 xyz_indx_.push_back( scitbx::vec3<int>(i,j,k) );
                 xyz_.push_back( point );
               }  //end if
            }  //end k
          }  //end j
        } //end i
        return true;
      }

     af::shared< scitbx::vec3<FloatType> > unit_sphere() {return xyz_;}
     af::shared< scitbx::vec3<int> > unit_sphere_index() {return xyz_indx_;}

// Clean the grid point based on voxel value:
// i.e. if (voxel(x,y,z) == 0), there is no need to keep the grid point

      bool clean_space(voxel<FloatType> v, bool pdb_out) {
        int total_point=xyz_indx_.size();
        FloatType value;
        FloatType scale_factor = v.rmax()/v.fraction();
        for(int i=0;i<total_point;i++) {
          value=v.value( xyz_indx_[i] );
          if(value > 0 ) {
            voxel_value_.push_back( value );
            voxel_indx_.push_back( xyz_indx_[i] );
            if(pdb_out) {
              std::cout<<"ATOM      1  CA  GLY A   1    ";
              for(int jj=0;jj<3;jj++)
                std::cout<<std::setw(8)<<std::setprecision(3)<<one_d_[xyz_indx_[i][jj]]*scale_factor;
              std::cout<<std::endl;
            } //end of if output
          }
        }
        return true;
      }

      int occupied_sites() { return voxel_indx_.size(); }

      bool compute_gm()
      {
//      Starts with order (1)
        gm_.push_back(one_d_);
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
          result.push_back(a[i]*b[i]/d*(d-1.0));
        }
        return result;
      }

      FloatType space_sum(int r, int s, int t)
      {
        int total_point=voxel_indx_.size(), x,y,z;
        FloatType tot(0.0), temp;

        for(int i=0;i<total_point;i++) {
          x=voxel_indx_[i][0];
          y=voxel_indx_[i][1];
          z=voxel_indx_[i][2];

          temp=gm_[r][x+1]-gm_[r][x];
           //first index is the x_position
           //the second index is the power of (r+1);
           //The value is aleady divided by (r+1)
           //see the function: compute_gm()
          temp *= (gm_[s][y+1]-gm_[s][y]);
          temp *= (gm_[t][z+1]-gm_[t][z]);
          temp *= voxel_value_[i];
          tot += temp;
        }
        return tot;
      }

      bool construct_space_sum() {

        for(int r=0;r<=n_max_;r++) {
          af::shared< af::shared<FloatType> > ss_r;
          for(int s=0;s<=n_max_;s++) {
            af::shared<FloatType> ss_rs;
            for(int t=0;t<=n_max_;t++) {
              if( r+s+t <= n_max_)
                ss_rs.push_back( space_sum(r,s,t) );
              else
                ss_rs.push_back( 0.0 );
            }  //end of t
          ss_r.push_back( ss_rs );
          } //end of s
        ss_.push_back( ss_r );
        } //end of r

        return true;
      }

      FloatType get_ss(int r, int s, int t) {
        return ss_[r][s][t];
      }

    private:
      scitbx::math::zernike::nlm_array<FloatType> C_nlm_;
      scitbx::af::shared< scitbx::vec3<int> > xyz_indx_;
      scitbx::af::shared< scitbx::vec3<FloatType> > xyz_;
      scitbx::af::shared<FloatType>one_d_;
      scitbx::af::shared< scitbx::af::shared<FloatType> >gm_;
        //Geometric moments up to order n_max_
      af::shared< af::shared< af::shared< FloatType > > > ss_;
      af::shared< FloatType > voxel_value_;
      scitbx::af::shared< scitbx::vec3<int> > voxel_indx_;
      int n_max_, N_point_;
      FloatType delta_;
  };

  template <typename FloatType>
  class moments
  {
    public:
      moments(){}
      moments(
             grid<FloatType> grid,
             int const& n_max
             ):
             grid_(grid),
             C_nlm_(n_max),
             C_nl_(n_max),
             n_max_(n_max),
             complex_i_(0,1.0)
      {
        initialize();
        calc_Chi();
        calc_invariance();
      }

      scitbx::math::zernike::nlm_array<FloatType>
      all_moments()
      {
        return C_nlm_;
      }

      scitbx::math::zernike::nl_array<FloatType>
      invariance()
      { return C_nl_; }

      void calc_invariance()
      {
        int start_l;
        FloatType norm2;
        af::shared<FloatType> norm_array;
        for(int n=0;n<=n_max_;n++) {
          start_l = (n-n/2*2);
          for(int l=0;l<=n;l+=2) {
            norm2 = norm(C_nlm_.get_coef(n,l,0) );
            for(int m=1;m<=l;m++) {
              norm2 += 2* norm(C_nlm_.get_coef(n,l,m) );
            }
            norm_array.push_back( norm2 );
          }
        }
        C_nl_.load_coefs( C_nl_.nl(), norm_array.const_ref() );
        return;
      }



      std::complex<FloatType> get_moment(int n,int l,int m)
      {
         return C_nlm_.get_coef(n,l,m);
      }

      void set_moment(int n,int l,int m,std::complex<FloatType> value)
      {
         C_nlm_.set_coef(n,l,m,value);
         return;
      }

      void calc_Chi()
      {
        int start_l;
        std::complex<FloatType> value;
        for(int n=0;n<=n_max_;n++) {
          start_l = (n-n/2*2); //ensure (n-l) is even
          for(int l=start_l;l<=n;l+=2){
            for(int m=0;m<=l;m++)
            {
            // std::cout<<value<<std::endl;
             value=calc_Chi_nlm(n,l,m);
             set_moment(n,l,m,value);
             if(m>0) {
               value = std::conj(value);
               value *= is_even(m);
               set_moment(n,l,-m,value);
             } //endif
            }
          }
        }
        return;
      }

      std::complex<FloatType> calc_Chi_nlm(int n, int l, int m)
      {
        std::complex<FloatType> value;
        int k=(n-l)/2;
        value = clm_[l][m]*std::pow(2.0,-m)*0.75/pi;
        value *= sum1(n,l,m,k);
        return value;
      }



// Utility functions

      void initialize()
      {
        build_fac();
        build_bino();
        build_Clm_array();
        build_Qlkv();
//      test();
      }

      bool test()
      {
        std::cout<<"factorial(10): "<<fac_[10]<<" compared to "<<3628800<<std::endl;
        std::cout<<"binomial(10,6): "<<bino_[10][6]<<" compared to "<<210<<std::endl;
        std::cout<<"c(l,m) (5,3): "<<clm_[5][3]<<" compared to "<<sqrt(11*fac_[8]*fac_[2])/fac_[5]<<std::endl;
        std::cout<<"q_lkv (3,2,1): "<<Q_lkv_[3][2][1]<<" compared to "<<(-85.1)<<std::endl;
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

      void build_Clm_array()
      {
        for(int l=0;l<=n_max_;l++){
          scitbx::af::shared<FloatType> cl(l+1,scitbx::af::init_functor_null<FloatType>() );
          for(int m=0;m<=l;m++){
            cl[m] = (2*l+1.0)*fac_[l+m]*fac_[l-m];
            cl[m]=std::sqrt( cl[m] );
            cl[m] /= fac_[l];
          }
          clm_.push_back( cl );
        }
        return;
      }

      void build_Qlkv()
      {
        for(int l=0;l<=n_max_;l++){
          scitbx::af::shared< scitbx::af::shared<FloatType> > q_kv;
          for(int k=0;k<=(n_max_-l)/2;k++){
            scitbx::af::shared<FloatType> q_v(k+1,scitbx::af::init_functor_null<FloatType>());
            for(int v=0;v<=k;v++){
              q_v[v] = is_even(k+v)/FloatType(pow(2,(2*k)))*sqrt((2*l+4*k+3)/3.0);
              q_v[v] *= bino_[2*k][k]*bino_[k][v]*bino_[2*(k+l+v)+1][2*k];
              q_v[v] /= bino_[k+l+v][k];
            }
            q_kv.push_back( q_v );
          }
          Q_lkv_.push_back( q_kv );
        }
        return;
      }

      FloatType sum6(int n,int l,int m, int nu, int alpha, int beta, int u, int mu)
      {
        int r, s, t;
        FloatType temp(0.0);
        for(int v=0;v<=mu;v++) {
          r = 2*(v+alpha)+u;
          s = 2*(mu-v+beta)+m-u;
          t = 2*(nu-alpha-beta-mu)+l-m;
          temp += bino_[mu][v] * grid_.get_ss(r,s,t);
        }
        return temp;
      }

      FloatType sum5(int n,int l,int m, int nu, int alpha, int beta, int u)
      {
        FloatType temp(0.0);
        for(int mu=0;mu<=(l-m)/2;mu++) {
          temp += is_even(mu)*pow(2,-2.0*mu)*bino_[l][mu]*bino_[l-mu][m+mu]*sum6(n,l,m,nu,alpha,beta,u,mu);
        }
        return temp;
      }

      std::complex<FloatType> sum4(int n,int l,int m, int k, int nu, int alpha, int beta)
      {
        std::complex<FloatType> temp(0,0);
        for(int u=0;u<=m;u++){
          temp += is_even(m-u)*bino_[m][u]*std::pow( complex_i_, u)*sum5(n,l,m,nu,alpha,beta,u);
        }
        return temp;
      }

      std::complex<FloatType> sum3(int n,int l,int m, int k, int nu, int alpha)
      {
        std::complex<FloatType> temp(0,0);
        int max_beta = nu-alpha;
        for(int beta=0;beta<=max_beta;beta++){
          temp += bino_[nu-alpha][beta]* sum4(n,l,m,k,nu,alpha,beta);
        }
        return temp;
      }

      std::complex<FloatType> sum2(int n,int l,int m, int k, int nu)
      {
        std::complex<FloatType> temp(0,0);
        for(int alpha=0;alpha<=nu;alpha++) {
          temp += bino_[nu][alpha]*sum3(n,l,m,k,nu,alpha);
        }
        return temp;
      }

      std::complex<FloatType> sum1(int n,int l,int m, int k)
      {
        std::complex<FloatType> temp(0,0);
        for(int nu=0;nu<=k;nu++) {
          temp += Q_lkv_[l][k][nu]*sum2(n,l,m,k,nu);
        }
        temp = conj(temp);
        return temp;
      }

      int is_even(int n)
      {
        if(n == n/2*2) return 1;
        else return (-1);
      }

    private:
      scitbx::math::zernike::nlm_array<FloatType> C_nlm_;
      scitbx::math::zernike::nl_array<FloatType> C_nl_;
      scitbx::af::shared<FloatType> fac_;
      scitbx::af::shared< scitbx::af::shared<FloatType> > bino_;
      scitbx::af::shared< scitbx::af::shared<FloatType> > clm_;
      scitbx::af::shared< scitbx::af::shared< scitbx::af::shared<FloatType> > > Q_lkv_;
      int n_max_;
      std::complex<FloatType> complex_i_;
      grid<FloatType> grid_;
  };


}
}} //namespace scitbx::math::zernike
#endif //SCITBX_MATH_ZERNIKE_MOM_H
