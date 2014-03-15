/* -*- mode: c++; c-basic-offset: 2; indent-tabs-mode: nil; tab-width: 8 -*-
 *
 * $Id$
 */
#include <cctbx/boost_python/flex_fwd.h>
#include <boost/tokenizer.hpp>

#include <boost/python/module.hpp>
#include <boost/python/class.hpp>
#include <boost/python/def.hpp>
#include <boost/python/dict.hpp>
#include <boost/python/list.hpp>
#include <scitbx/array_family/flex_types.h>
#include <scitbx/array_family/shared.h>
#include <scitbx/vec3.h>
#include <scitbx/vec2.h>
#include <scitbx/constants.h>
#include <scitbx/math/mean_and_variance.h>
#include <cctbx/miller.h>
#include <cctbx/uctbx.h>
#include <vector>
#include <map>
#include <set>

using namespace boost::python;

namespace xfel {

struct correction_vector_store {
  typedef scitbx::vec2<double> vec2;
  typedef scitbx::vec3<double> vec3;
  scitbx::af::flex_int tiles;
  scitbx::af::shared<int> tilecounts;
  scitbx::af::shared<vec3> tilecenters;

  scitbx::af::shared<double> radii;
  scitbx::af::shared<vec2> mean_cv;
  scitbx::af::shared<vec2> master_coords;
  scitbx::af::shared<vec2> master_cv;
  scitbx::af::shared<int> master_tiles;
  scitbx::af::shared<vec2> all_tile_obs_spo;
  vec2 overall_cv;
  double sum_sq_cv;

  void initialize_per_tile_sums(){
    tilecounts = scitbx::af::shared<int>(tiles.size()/4,0);
    radii = scitbx::af::shared<double>(tiles.size()/4,0.);
    mean_cv = scitbx::af::shared<vec2>(tiles.size()/4,vec2(0.,0.));
    master_tiles = scitbx::af::shared<int>();
    master_coords = scitbx::af::shared<vec2>();
    master_cv = scitbx::af::shared<vec2>();
    all_tile_obs_spo = scitbx::af::shared<vec2>();
    overall_cv = vec2();
    sum_sq_cv = 0.;
    tilecenters = scitbx::af::shared<vec3>();
    for (int x = 0; x < tiles.size()/4; ++x){
      tilecenters.push_back( vec3(
        (tiles[4*x+0] + tiles[4*x+2])/2.,
        (tiles[4*x+1] + tiles[4*x+3])/2.,
         0.) );
    }
  }

  int
  register_line(double const&a,double const&b,double const&c,double const&d,
                double const&e,double const&f,double const&g,double const&h){
    vec2 observed_center(a,b);
    vec2 refined_center(c,d);
    vec2 observed_spot(e,f);
    vec2 predicted_spot(g,h);
    vec2 prediction = predicted_spot - refined_center;

    vec2 correction_vector = predicted_spot - observed_spot;

    int itile = 0;
    for (int x = 0; x < tiles.size()/4; ++x){
      if (tiles[4*x+0]<predicted_spot[0] && predicted_spot[0]<tiles[4*x+2] &&
          tiles[4*x+1]<predicted_spot[1] && predicted_spot[1]<tiles[4*x+3]){
         itile = x;
         break;
      }
    }
    SCITBX_ASSERT(correction_vector.length() <= 10);
    tilecounts[itile]+=1;
    radii[itile]+=prediction.length();
    mean_cv[itile] = mean_cv[itile] + correction_vector;
    master_tiles.push_back(itile);
    master_cv.push_back(correction_vector);
    master_coords.push_back(prediction);
    all_tile_obs_spo.push_back(observed_spot -
                               vec2(tilecenters[itile][0],tilecenters[itile][1]));
    overall_cv += correction_vector;
    sum_sq_cv += correction_vector.length_sq();
    return itile;
  }

  double
  weighted_average_angle_deg_from_tile(int const& itile) const {

    scitbx::af::shared<vec2> selected_cv;
    scitbx::af::shared<vec2> selected_tile_obs_spo;
    scitbx::af::shared<vec2> translated_correction_vectors;
    scitbx::af::shared<vec2> all_tile_pred_spo;

    for (int x = 0; x < master_tiles.size(); ++x){
      if (master_tiles[x]==itile){
        selected_cv.push_back( master_cv[x] );
        selected_tile_obs_spo.push_back( all_tile_obs_spo[x] );
        translated_correction_vectors.push_back( master_cv[x] - mean_cv[itile] );
        all_tile_pred_spo.push_back( all_tile_obs_spo[x] + master_cv[x] );
      }
    }

    double numerator = 0.;
    double denominator = 0.;

    for (int x = 0; x < selected_cv.size(); ++x){
      vec2 co = selected_tile_obs_spo[x];
      vec2 cp = all_tile_pred_spo[x];
      double co_cp_norm = co.length()*cp.length();
      if (co_cp_norm==0) {continue;}
      double co_dot_cp = co*cp;
      double co_cross_cp_coeff = (co[0]*cp[1]-cp[0]*co[1]);
      double sin_theta = co_cross_cp_coeff / co_cp_norm;
      double cos_theta = co_dot_cp / co_cp_norm;
      double angle_deg = std::atan2(sin_theta,cos_theta)/scitbx::constants::pi_180;
      double weight = std::sqrt(co_cp_norm);
      numerator += weight*angle_deg;
      denominator += weight;
    }
    return numerator/denominator;
  }

  double
  weighted_average_angle_deg_from_tile(int const& itile, vec2 const& post_mean_cv_itile,
    scitbx::af::shared<double> correction_vector_x,
    scitbx::af::shared<double> correction_vector_y ) const {

    scitbx::af::shared<vec2> selected_cv;
    scitbx::af::shared<vec2> selected_tile_obs_spo;
    scitbx::af::shared<vec2> translated_correction_vectors;
    scitbx::af::shared<vec2> all_tile_pred_spo;

    for (int x = 0; x < master_tiles.size(); ++x){
      if (master_tiles[x]==itile){
        vec2 correction_vector (correction_vector_x[x],correction_vector_y[x]);
        selected_cv.push_back( correction_vector );
        selected_tile_obs_spo.push_back( all_tile_obs_spo[x] );
        translated_correction_vectors.push_back( correction_vector - post_mean_cv_itile );
        all_tile_pred_spo.push_back( all_tile_obs_spo[x] + correction_vector );
      }
    }

    double numerator = 0.;
    double denominator = 0.;

    for (int x = 0; x < selected_cv.size(); ++x){
      vec2 co = selected_tile_obs_spo[x];
      vec2 cp = all_tile_pred_spo[x];
      double co_cp_norm = co.length()*cp.length();
      double co_dot_cp = co*cp;
      double co_cross_cp_coeff = (co[0]*cp[1]-cp[0]*co[1]);
      double sin_theta = co_cross_cp_coeff / co_cp_norm;
      double cos_theta = co_dot_cp / co_cp_norm;
      double angle_deg = std::atan2(sin_theta,cos_theta)/scitbx::constants::pi_180;
      double weight = std::sqrt(co_cp_norm);
      numerator += weight*angle_deg;
      denominator += weight;
    }
    return numerator/denominator;
  }


};

static boost::python::tuple
get_radial_tangential_vectors(correction_vector_store const& L, int const& itile){

    scitbx::vec2<double> radial(0,0);
    scitbx::vec2<double> tangential;
    for (int x = 0; x < L.master_tiles.size(); ++x){
      if (L.master_tiles[x]==itile){
        radial += L.master_coords[x];
      }
    }
    radial = radial.normalize();
    tangential = scitbx::vec2<double>( -radial[1], radial[0] );

    // Now consider 2D Gaussian distribution of all the observations
    scitbx::af::shared<double> radi_projection;
    scitbx::af::shared<double> tang_projection;
    for (int x = 0; x < L.master_tiles.size(); ++x){
      if (L.master_tiles[x]==itile){
        scitbx::vec2<double> recentered_cv = L.master_cv[x] - L.mean_cv[itile];
        radi_projection.push_back( recentered_cv*radial );
        tang_projection.push_back( recentered_cv*tangential );
      }
    }
    scitbx::math::mean_and_variance<double> radistats(radi_projection.const_ref());
    scitbx::math::mean_and_variance<double> tangstats(tang_projection.const_ref());

    return make_tuple(radial,tangential,radistats.mean(),tangstats.mean(),
                      radistats.unweighted_sample_standard_deviation(),
                      tangstats.unweighted_sample_standard_deviation());
}

static boost::python::tuple
get_radial_tangential_vectors(correction_vector_store const& L, int const& itile,
    scitbx::vec2<double> const& post_mean_cv_itile,
    scitbx::af::shared<double> correction_vector_x,
    scitbx::af::shared<double> correction_vector_y,
    scitbx::af::shared<double> model_calc_minus_center_x,
    scitbx::af::shared<double> model_calc_minus_center_y
    ){

    scitbx::vec2<double> radial(0,0);
    scitbx::vec2<double> tangential;
    for (int x = 0; x < L.master_tiles.size(); ++x){
      if (L.master_tiles[x]==itile){
        radial += scitbx::vec2<double>(model_calc_minus_center_x[x],model_calc_minus_center_y[x]);
      }
    }
    radial = radial.normalize();
    tangential = scitbx::vec2<double>( -radial[1], radial[0] );

    // Now consider 2D Gaussian distribution of all the observations
    scitbx::af::shared<double> radi_projection;
    scitbx::af::shared<double> tang_projection;
    for (int x = 0; x < L.master_tiles.size(); ++x){
      if (L.master_tiles[x]==itile){
        scitbx::vec2<double> correction_vector (correction_vector_x[x],correction_vector_y[x]);
        scitbx::vec2<double> recentered_cv = correction_vector - post_mean_cv_itile;
        radi_projection.push_back( recentered_cv*radial );
        tang_projection.push_back( recentered_cv*tangential );
      }
    }
    scitbx::math::mean_and_variance<double> radistats(radi_projection.const_ref());
    scitbx::math::mean_and_variance<double> tangstats(tang_projection.const_ref());

    return make_tuple(radial,tangential,radistats.mean(),tangstats.mean(),
                      radistats.unweighted_sample_standard_deviation(),
                      tangstats.unweighted_sample_standard_deviation());
}

static boost::python::tuple
get_correction_vector_xy(correction_vector_store const& L, int const& itile){

    scitbx::af::shared<double> xcv;
    scitbx::af::shared<double> ycv;
    for (int x = 0; x < L.master_tiles.size(); ++x){
      if (L.master_tiles[x]==itile){
        xcv.push_back( L.master_cv[x][0] );
        ycv.push_back( L.master_cv[x][1] );
      }
    }
    return make_tuple(xcv,ycv);
}

struct column_parser {
  std::vector<scitbx::af::shared<int> > int_columns;
  std::vector<scitbx::af::shared<double> > double_columns;
  std::map<std::string,int> int_column_lookup;
  std::map<std::string,int> double_column_lookup;
  std::vector<int> int_token_addresses;
  std::vector<int> double_token_addresses;
  column_parser(){}

  void set_int(std::string const& key, int const& optional_column){
    int_columns.push_back(scitbx::af::shared<int>());
    int_token_addresses.push_back(optional_column);
    int_column_lookup[key]=int_columns.size()-1;
  }
  void set_int(std::string const& key, scitbx::af::shared<int> values){
    int_columns.push_back(values);
    int_column_lookup[key]=int_columns.size()-1;
  }
  void set_double(std::string const& key, int const& optional_column){
    double_columns.push_back(scitbx::af::shared<double>());
    double_token_addresses.push_back(optional_column);
    double_column_lookup[key]=double_columns.size()-1;
  }
  void set_double(std::string const& key, scitbx::af::shared<double> values){
    double_columns.push_back(values);
    double_column_lookup[key]=double_columns.size()-1;
  }
  scitbx::af::shared<int> get_int(std::string const& key) {
    return int_columns[int_column_lookup[key]];
  }
  scitbx::af::shared<double> get_double(std::string const& key) {
    return double_columns[double_column_lookup[key]];
  }
  void parse_from_line(std::string const& line){
    typedef boost::tokenizer<boost::char_separator<char> > tokenizer;
    boost::char_separator<char> sep(" ");
    tokenizer tok(line,sep);
    tokenizer::iterator tok_iter = tok.begin();
    std::vector<std::string> tokens;
    for (; tok_iter!=tok.end(); ++tok_iter){
      tokens.push_back( (*tok_iter) );
    }

    //parse the integers
    for (int i = 0; i<int_columns.size(); ++i){
      int_columns[i].push_back( atoi( tokens[int_token_addresses[i]].c_str()) );
    }
    //parse the doubles
    for (int i = 0; i<double_columns.size(); ++i){
      double_columns[i].push_back( atof(tokens[double_token_addresses[i]].c_str()) );
    }
  }
};

struct scaling_results {
private:
  /*
   * For each unique reflection, the set of accepted frame ID:s on
   * which it was observed.
   */
  std::vector<std::set<int> > reflection_frame;

  /*
   * Lower limit on correlation coefficient.
   */
  double reflection_frame_min_corr;

  /*
   * Populate each element of reflection_frame with the union of
   * frames with correlation coefficient greater than
   * reflection_frame_min_corr.  This function is intended for lazy
   * evaluation.
   */
  void
  update_frame_count()
  {
    shared_double cc = frames.get_double("cc");
    shared_int frame_id = observations.get_int("frame_id");
    shared_int hkl_id = observations.get_int("hkl_id");

    reflection_frame.resize(merged_asu_hkl.size());
    for (std::size_t i = 0; i < hkl_id.size(); i++) {
      const int this_frame_id = frame_id[i];
      if (cc[this_frame_id] > reflection_frame_min_corr)
        reflection_frame[hkl_id[i]].insert(this_frame_id);
    }
  }

public:
  int frame_id_dwell;
  typedef scitbx::af::shared<int> shared_int;
  typedef scitbx::af::shared<double> shared_double;
  typedef scitbx::af::versa<bool, scitbx::af::flex_grid<> > shared_bool;
  typedef
   scitbx::af::versa<cctbx::miller::index<>, scitbx::af::flex_grid<> > shared_miller;
  typedef scitbx::vec3<double> vec3;
  typedef scitbx::af::shared<vec3> shared_vec3;
  column_parser& observations, frames;
  shared_miller& merged_asu_hkl;
  shared_bool& selected_frames;

  shared_double sum_I,sum_I_SIGI,summed_wt_I,summed_weight;
  shared_double n_rejected, n_obs, d_min_values;
  shared_int completeness, summed_N;
  shared_vec3 i_isig_list;
  int Nhkl;

  scaling_results (column_parser &observations, column_parser &frames,
                   shared_miller& hkls, shared_bool& data_subset):
    observations(observations),frames(frames),merged_asu_hkl(hkls),
    selected_frames(data_subset){}
  void mark0 (double const& params_min_corr,
              cctbx::uctbx::unit_cell const& params_unit_cell) {
    shared_int hkl_id = observations.get_int("hkl_id");
    shared_int frame_id = observations.get_int("frame_id");
    shared_double intensity = observations.get_double("i");
    shared_double sigi = observations.get_double("sigi");
    shared_double cc = frames.get_double("cc");
    shared_double slope = frames.get_double("slope");
    int Nframes = frame_id.size();
    int Nhkl = merged_asu_hkl.accessor().focus()[0];
    initialize_results(Nframes, Nhkl);

    for (int iobs = 0; iobs < hkl_id.size(); ++iobs){
      int this_frame_id = frame_id[iobs];
      if (!selected_frames[this_frame_id]) {continue;}
      int this_hkl_id = hkl_id[iobs];
      double this_cc, this_slope;
      if (this_frame_id != frame_id_dwell){
        frame_id_dwell = this_frame_id;
        this_cc = cc[this_frame_id];
        this_slope = slope[this_frame_id];
      }
      if (this_cc <= params_min_corr){
        continue;
      }
      completeness[this_hkl_id] += 1;
      double this_i = intensity[iobs];
      double this_sig = sigi[iobs];
      n_obs[this_frame_id] += 1;
      if (this_i <=0.){
        n_rejected[this_frame_id] += 1;
        continue;
      }
      summed_N[this_hkl_id] += 1;
      double Intensity = this_i / this_slope;
      double isigi = this_i/this_sig;
      sum_I[this_hkl_id] += Intensity;
      sum_I_SIGI[this_hkl_id] += isigi;
      cctbx::miller::index<> this_index( merged_asu_hkl[this_hkl_id] );
      i_isig_list.push_back( vec3(
        this_hkl_id, Intensity, isigi));
      double this_d_spacing = params_unit_cell.d(this_index);
      double this_frame_d_min = d_min_values[this_frame_id];
      if (this_frame_d_min==0.){
        d_min_values[this_frame_id] = this_d_spacing;
      } else if (this_d_spacing < this_frame_d_min) {
        d_min_values[this_frame_id] = this_d_spacing;
      }

      double sigma = this_sig / this_slope;
      double variance = sigma * sigma;
      summed_wt_I[this_hkl_id] += Intensity / variance;
      summed_weight[this_hkl_id] += 1. / variance;

    }
  }

  /*
   * For each resolution bin, find the union of accepted frames
   * contributing at least one observation of a reflection.
   */
  std::size_t
  count_frames(
    double params_min_corr, const shared_bool& reflection_selection)
  {
    std::set<int> s;

    if (reflection_frame.size() != merged_asu_hkl.size() ||
        reflection_frame_min_corr != params_min_corr) {
      reflection_frame_min_corr = params_min_corr;
      update_frame_count();
    }

    SCITBX_ASSERT(reflection_frame.size() == reflection_selection.size());
    for (std::size_t i = 0; i < reflection_frame.size(); i++) {
      if (reflection_selection[i])
        s.insert(reflection_frame[i].begin(), reflection_frame[i].end());
    }

    return s.size();
  }

  void mark1 (double const& params_min_corr,
              cctbx::uctbx::unit_cell const& params_unit_cell) {
    // this eliminates the filter based on correlation with isomorphous structure
    // so more reflections are included than in mark0
    shared_int hkl_id = observations.get_int("hkl_id");
    shared_int frame_id = observations.get_int("frame_id");
    shared_double intensity = observations.get_double("i");
    shared_double sigi = observations.get_double("sigi");
    int Nframes = frame_id.size();
    int Nhkl = merged_asu_hkl.accessor().focus()[0];
    initialize_results(Nframes, Nhkl);

    for (int iobs = 0; iobs < hkl_id.size(); ++iobs){
      int this_frame_id = frame_id[iobs];
      if (!selected_frames[this_frame_id]) {continue;}
      int this_hkl_id = hkl_id[iobs];
      if (this_frame_id != frame_id_dwell){
        frame_id_dwell = this_frame_id;
      }
      completeness[this_hkl_id] += 1;
      double this_i = intensity[iobs];
      double this_sig = sigi[iobs];
      n_obs[this_frame_id] += 1;
      if (this_i <=0.){
        n_rejected[this_frame_id] += 1;
        continue;
      }
      summed_N[this_hkl_id] += 1;
      double Intensity = this_i;
      double isigi = this_i/this_sig;
      sum_I[this_hkl_id] += Intensity;
      sum_I_SIGI[this_hkl_id] += isigi;
      cctbx::miller::index<> this_index( merged_asu_hkl[this_hkl_id] );
      i_isig_list.push_back( vec3(
        this_hkl_id, Intensity, isigi));
      double this_d_spacing = params_unit_cell.d(this_index);
      double this_frame_d_min = d_min_values[this_frame_id];
      if (this_frame_d_min==0.){
        d_min_values[this_frame_id] = this_d_spacing;
      } else if (this_d_spacing < this_frame_d_min) {
        d_min_values[this_frame_id] = this_d_spacing;
      }

      double sigma = this_sig;
      double variance = sigma * sigma;
      summed_wt_I[this_hkl_id] += Intensity / variance;
      summed_weight[this_hkl_id] += 1. / variance;
    }
  }

  private:
  void initialize_results(const int& Nframes, const int& Nhkl){
    frame_id_dwell=-1;
    sum_I = shared_double(Nhkl, 0.);
    sum_I_SIGI = shared_double(Nhkl, 0.);
    completeness = shared_int(Nhkl, 0.);
    summed_N = shared_int(Nhkl, 0.);
    summed_wt_I = shared_double(Nhkl, 0.);
    summed_weight = shared_double(Nhkl, 0.);
    n_rejected = shared_double(Nframes, 0.);
    n_obs = shared_double(Nframes, 0.);
    d_min_values = shared_double(Nframes, 0.);
    i_isig_list = shared_vec3();
  }
};


typedef scitbx::af::shared<int> shared_int;
typedef scitbx::af::shared<double> shared_double;
typedef scitbx::af::versa<bool, scitbx::af::flex_grid<> > shared_bool;


/* column_parser cannot be const
 *
 * @param w Per-observation weigths.  All elements of @p w must be
 *          <code>&ge; 0</code>.
 */
static boost::python::tuple
compute_functional_and_gradients(const shared_double& x,
                                 const shared_double& w,
                                 std::size_t n_frames,
                                 column_parser& observations)
{
  const shared_double data = observations.get_double("i");
  const shared_double sigmas = observations.get_double("sigi");
  const shared_int frames = observations.get_int("frame_id");
  const shared_int hkl = observations.get_int("hkl_id");

  const std::size_t n_obs = w.size();

  SCITBX_ASSERT(data.size() == n_obs);
  SCITBX_ASSERT(sigmas.size() == n_obs);
  SCITBX_ASSERT(frames.size() == n_obs);
  SCITBX_ASSERT(hkl.size() == n_obs);

  shared_double g(x.size());
  double f = 0;
  double w_tot = 0;

  for (std::size_t i = 0; i < n_obs; i++) {
    if (w[i] <= 0)
      continue;

    const int h = hkl[i];
    const double I_m = x[n_frames + h];
    if (I_m <= 0) // XXX This warrants a comment
      continue;

    const int m = frames[i];
    const double G = x[m];
    const double t = data[i] - G * I_m;

    f += w[i] * t * t;
    g[m] += -2.0 * w[i] * I_m * t;
    g[n_frames + h] += -2.0 * w[i] * G * t;
    w_tot += w[i];
  }

  /* If w_tot == 0, then f and g should be identically zero.  w_tot <
   * 0 should not happen.
   */
  if (w_tot > 0) {
    f /= w_tot;
    for (std::size_t i = 0; i < g.size(); i++)
      g[i] /= w_tot;
  }

  return (boost::python::make_tuple(f, g));
}


/*
 * The curvatures() function returns the diagonal elements of the
 * Hessian matrix.
 *
 * If we knew that compute_functional_and_gradients() was always
 * called before curvatures(), we could calculate the curvatures there
 * and just return them here.
 */
shared_double
curvatures(const shared_double& x,
           const shared_double& w,
           std::size_t n_frames,
           column_parser& observations)
{
  const shared_double data = observations.get_double("i");
  const shared_double sigmas = observations.get_double("sigi");
  const shared_int frames = observations.get_int("frame_id");
  const shared_int hkl = observations.get_int("hkl_id");

  const std::size_t n_obs = w.size();

  SCITBX_ASSERT(data.size() == n_obs);
  SCITBX_ASSERT(sigmas.size() == n_obs);
  SCITBX_ASSERT(frames.size() == n_obs);
  SCITBX_ASSERT(hkl.size() == n_obs);

  shared_double c(x.size());
  double w_tot = 0;

  printf("CURVATURES CALLED\n");

  for (std::size_t i = 0; i < n_obs; i++) {
    if (w[i] <= 0)
      continue;

    if (data[i] <= 0)
      continue;

    const int h = hkl[i];
    const double I_m = x[n_frames + h];
    if (I_m <= 0) // XXX See compute_functional_and_gradients()
      continue;

    const int m = frames[i];
    const double G = x[m];

    c[m] += 2.0 * w[i] * I_m * I_m;
    c[n_frames + h] += 2.0 * w[i] * G * G;
    w_tot += w[i];
  }

  for (std::size_t i = 0; i < c.size(); i++)
    c[i] /= w_tot;

  /*
  for (std::size_t i = 0; i < c.size(); i++)
    if (c[i] <= 0)
      printf("CURVATURES index %d is %f\n", i, c[i]);
  */

  return (c);
}


/* The intensity column in the MTZ file written by
 * finalize_and_save_data() in cxi_merge.scaling_manager is calculated
 * as
 *
 *   summed_wt_I / summed_weight.
 *
 * The corresponding standard deviations are
 *
 *   sqrt(1 / summed_weight).
 *
 * In order to ensure that the refined model intensities are
 * reproduced in the final intensity column, this function populates
 * summed_wt_I with the model intensities multiplied by their
 * corresponding weight.
 *
 * XXX Duplicates code w.r.t. other stuff defined in this file.  It
 * should ideally be possible to reuse get_scaling_results() below!
 *
 * XXX Needs to be cleaned up!
 */
static boost::python::tuple
get_scaling_results_mark2(const shared_double& x,
                          const shared_double& w,
                          scaling_results& L,
                          const cctbx::uctbx::unit_cell& params_unit_cell)
{
  const shared_double data = L.observations.get_double("i");
  const shared_double sigmas = L.observations.get_double("sigi");

  // slope is only needed for mark0 comparison.
  const shared_double slope = L.frames.get_double("slope");

  const shared_int frames = L.observations.get_int("frame_id");
  const shared_int hkl = L.observations.get_int("hkl_id");

  const std::size_t n_frames = L.selected_frames.size();
  const std::size_t n_hkl = x.size() - n_frames;
  const std::size_t n_obs = w.size();

  SCITBX_ASSERT(data.size() == n_obs);
  SCITBX_ASSERT(sigmas.size() == n_obs);
  SCITBX_ASSERT(frames.size() == n_obs);
  SCITBX_ASSERT(hkl.size() == n_obs);

  /* Weighted sum of squared deviations between scaled, observed
   * intensities and refined intensities.
   */
  shared_double wssq_dev(n_hkl);
  shared_double w_tot(n_hkl);

  for (std::size_t m = 0; m < n_frames; m++) {
    L.n_rejected[m] = 0;
    L.n_obs[m] = 0;
    L.d_min_values[m] = 0;
  }

  for (std::size_t i = 0; i < n_hkl; i++) {
    L.sum_I[i] = 0;
    L.sum_I_SIGI[i] = 0;
    L.completeness[i] = 0;
    L.summed_N[i] = 0;
    L.summed_wt_I[i] = 0;
    L.summed_weight[i] = 0;
  }

  L.i_isig_list.clear();

  for (std::size_t i = 0; i < n_obs; i++) {
    const int m = frames[i];

    /* Filtering the observations based on weight early in the loop
     * alters the statistics.  Previously, a reflection was counted as
     * observed and would contribute to the completeness as long as
     * the frame was not rejected, even if its integrated intensity or
     * standard deviation was non-positive.  Now, any observations
     * with non-positive weight are not counted as observed and do not
     * contribute to the completeness.
     */
    if (w[i] <= 0) {
      L.n_rejected[m] += 1;
      continue;
    }

    const int h = hkl[i];
    L.completeness[h] += 1;
    L.n_obs[m] += 1;

    // Mind negative scaling factors!
    const double G = x[m];
    //const double G = slope[m]; // To reproduce mark0 scaling
    //const double G = 1; // To reproduce mark1 scaling

    /* The integrated, observed intensity, I, and its standard
     * deviation, s, scaled by the per-frame scale factor, G.
     */
    const double I = data[i] / G;
    const double s = sigmas[i] / G;
    const double w_this = G * G * w[i]; // XXX ugly!
    const double IsigI = I / s;

    L.summed_N[h] += 1;
    L.sum_I[h] += I;
    L.sum_I_SIGI[h] += IsigI;

    L.i_isig_list.push_back(scitbx::vec3<double>(h, I, IsigI));

    const double d =
      params_unit_cell.d(cctbx::miller::index<>(L.merged_asu_hkl[h]));
    if (L.d_min_values[m] <= 0 || L.d_min_values[m] > d)
      L.d_min_values[m] = d;

    /* Running, weighted, and squared sum of deviations between
     * scaled, observed intensities and refined dittos.  Note that
     * neither L.summed_weight nor L.summed_wt_I are written in this
     * loop.
     *
     * Leave ESTIMATE_REFINED_UNCERTAINTY undefined to propagate the
     * shot noise in quadrature to the merged sig(I).  The
     * alternative, i.e. estimating the refined uncertainity, is
     * currently broken.
     *
     * XXX Must ensure w_tot > 0 in order to preserve logic in the
     * looped branch below.
     */
//#define ESTIMATE_REFINED_UNCERTAINTY 1
    const double t = I - x[n_frames + h];
#ifdef ESTIMATE_REFINED_UNCERTAINTY
    wssq_dev[h] += w_this * t * t;
    w_tot[h] += w_this;
#else
    wssq_dev[h] += 1.0 / (s * s);
    w_tot[h] += 1;
#endif
  }

  /* Multiply model intensities by the summed weight, such that the
   * intensities written to the final MTZ-file will be correct.
   */
  for (std::size_t h = 0; h < n_hkl; h++) {
    if (w_tot[h] > 0 && x[n_frames + h] > 0) {
#ifdef ESTIMATE_REFINED_UNCERTAINTY
      L.summed_weight[h] = wssq_dev[h] / w_tot[h];
#else
      L.summed_weight[h] = wssq_dev[h];
#endif
      L.summed_wt_I[h] =
        L.summed_weight[h] > 0 ? x[n_frames + h] * L.summed_weight[h] : 0;

    } else {
      L.summed_weight[h] = 0;
      L.summed_wt_I[h] = 0;
    }
  }

  return (make_tuple(L.sum_I,
                     L.sum_I_SIGI,
                     L.completeness,
                     L.summed_N,
                     L.summed_wt_I,
                     L.summed_weight,
                     L.n_rejected,
                     L.n_obs,
                     L.d_min_values,
                     L.i_isig_list));
}


static boost::python::tuple
get_scaling_results(scaling_results const& L){
  return make_tuple(    L.sum_I, L.sum_I_SIGI,
    L.completeness, L.summed_N,
    L.summed_wt_I, L.summed_weight,
    L.n_rejected, L.n_obs,
    L.d_min_values, L.i_isig_list );
}

static boost::python::dict
get_isigi_dict(scaling_results const& L){
  boost::python::dict ISIGI;
  std::map<int, boost::python::list> cpp_mapping;
  for (int ditem=0; ditem<L.i_isig_list.size(); ++ditem){
    scaling_results::vec3 dataitem = L.i_isig_list[ditem];
    if (cpp_mapping.find(dataitem[0]) == cpp_mapping.end()) {
      cpp_mapping[dataitem[0]]=boost::python::list();
    }
    boost::python::tuple i_isigi = make_tuple( dataitem[1], dataitem[2] );
    cpp_mapping[dataitem[0]].append( i_isigi );
  }
  for (std::map<int, boost::python::list>::const_iterator item = cpp_mapping.begin();
       item != cpp_mapping.end(); ++item) {
    cctbx::miller::index<> this_index( L.merged_asu_hkl[item->first] );
    boost::python::tuple miller_index = make_tuple( this_index[0],this_index[1],this_index[2] );
    ISIGI[miller_index] = item->second;
  }
  return ISIGI;
}

double distance_between_points(scitbx::vec2<int> const& a, scitbx::vec2<int> const& b) {
  return std::sqrt((std::pow(double(b[0]-a[0]),2)+std::pow(double(b[1]-a[1]),2)));
}

void radial_average(scitbx::af::versa<double, scitbx::af::flex_grid<> > & data,
scitbx::vec2<int> const& beam_center,
scitbx::af::shared<double> sums,
scitbx::af::shared<double> sums_sq,
scitbx::af::shared<int> counts,
double pixel_size, double distance,
scitbx::vec2<int> const& upper_left,
scitbx::vec2<int> const& lower_right) {
  std::size_t extent = sums.size();
  double extent_in_mm = extent * pixel_size;
  double extent_two_theta = std::atan(extent_in_mm/distance)*180/scitbx::constants::pi;

  std::size_t size_x = data.accessor().focus()[0];
  std::size_t size_y = data.accessor().focus()[1];

  for(std::size_t y = upper_left[1]; y < lower_right[1]; y++) {
    for(std::size_t x = upper_left[0]; x < lower_right[0]; x++) {
      double val = data(x,y);
      if(val > 0) {
        scitbx::vec2<int> point((int)x,(int)y);
        double d_in_mm = distance_between_points(point,beam_center) * pixel_size;
        double twotheta = std::atan(d_in_mm/distance)*180/scitbx::constants::pi;
        std::size_t bin = (std::size_t)std::floor(twotheta*extent/extent_two_theta);
        sums[bin] += val;
        sums_sq[bin] += val*val;
        counts[bin]++;
      }
    }
  }
}

namespace boost_python { namespace {

  boost::python::tuple
  foo2()
  {
    return boost::python::make_tuple(1,2,3,4);
  }

  void
  init_module() {
    using namespace boost::python;

    typedef return_value_policy<return_by_value> rbv;
    typedef default_call_policies dcp;

    def("get_correction_vector_xy", &get_correction_vector_xy);
    def("get_radial_tangential_vectors",
        (boost::python::tuple(*)(correction_vector_store const&, int const&))
        &get_radial_tangential_vectors);
    def("get_radial_tangential_vectors",
        (boost::python::tuple(*)(correction_vector_store const&, int const&,
         scitbx::vec2<double> const&,
         scitbx::af::shared<double>,
         scitbx::af::shared<double>,
         scitbx::af::shared<double>,
         scitbx::af::shared<double>))
        &get_radial_tangential_vectors);

    class_<scaling_results>("scaling_results",no_init)
      .def(init<column_parser&, column_parser&, scaling_results::shared_miller&,
                scaling_results::shared_bool&>())
      .def("count_frames",&scaling_results::count_frames)
      .def("mark0",&scaling_results::mark0)
      .def("mark1",&scaling_results::mark1)
    ;
    def("compute_functional_and_gradients", &compute_functional_and_gradients);
    def("curvatures", &curvatures);
    def("get_scaling_results_mark2", &get_scaling_results_mark2);
    def("get_scaling_results", &get_scaling_results);
    def("get_isigi_dict", &get_isigi_dict);

    class_<correction_vector_store>("correction_vector_store",init<>())
      .add_property("tiles",
        make_getter(&correction_vector_store::tiles, rbv()),
        make_setter(&correction_vector_store::tiles, dcp()))
      .def("register_line",&correction_vector_store::register_line)
      .def("initialize_per_tile_sums",&correction_vector_store::initialize_per_tile_sums)
      .add_property("tilecounts",
        make_getter(&correction_vector_store::tilecounts, rbv()))
      .add_property("radii",
        make_getter(&correction_vector_store::radii, rbv()),
        make_setter(&correction_vector_store::radii, dcp()))
      .add_property("mean_cv",
        make_getter(&correction_vector_store::mean_cv, rbv()),
        make_setter(&correction_vector_store::mean_cv, dcp()))
      .add_property("master_tiles",
        make_getter(&correction_vector_store::master_tiles, rbv()))
      .add_property("master_cv",
        make_getter(&correction_vector_store::master_cv, rbv()))
      .add_property("overall_cv",
        make_getter(&correction_vector_store::overall_cv, rbv()),
        make_setter(&correction_vector_store::overall_cv, dcp()))
      .add_property("sum_sq_cv",
        make_getter(&correction_vector_store::sum_sq_cv, rbv()))
      .add_property("master_coords",
        make_getter(&correction_vector_store::master_coords, rbv()))
      .add_property("all_tile_obs_spo",
        make_getter(&correction_vector_store::all_tile_obs_spo, rbv()))
      .def("weighted_average_angle_deg_from_tile",
           (double(correction_vector_store::*)(int const&)const)
           &correction_vector_store::weighted_average_angle_deg_from_tile)
      .def("weighted_average_angle_deg_from_tile",
           (double(correction_vector_store::*)(int const&,correction_vector_store::vec2 const&,
           scitbx::af::shared<double>,
           scitbx::af::shared<double>)const)
           &correction_vector_store::weighted_average_angle_deg_from_tile)
    ;

    class_<column_parser>("column_parser",init<>())
      .def("set_int",(void(column_parser::*)(std::string const&, int const&))&column_parser::set_int)
      .def("set_int",(void(column_parser::*)(std::string const&, scitbx::af::shared<int>))&column_parser::set_int)
      .def("set_double",(void(column_parser::*)(std::string const&, int const&))&column_parser::set_double)
      .def("set_double",(void(column_parser::*)(std::string const&, scitbx::af::shared<double>))&column_parser::set_double)
      .def("get_int",&column_parser::get_int)
      .def("get_double",&column_parser::get_double)
      .def("parse_from_line",&column_parser::parse_from_line)
    ;

    def("radial_average", &radial_average,
      (arg("data"), arg("beam_center"), arg("sums"), arg("sums_sq"), arg("counts"),
       arg("pixel_size"), arg("distance"),
       arg("upper_left"), arg("lower_right")))
    ;
}
}}} // namespace xfel::boost_python::<anonymous>

BOOST_PYTHON_MODULE(xfel_ext)
{
  xfel::boost_python::init_module();

}
