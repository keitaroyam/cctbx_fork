/* -*- mode: c++; c-basic-offset: 2; indent-tabs-mode: nil; tab-width: 8 -*-
 *
 * $Id: ext.cpp 21225 2014-11-28 21:06:02Z phyy-nx $
 */
#include <cctbx/boost_python/flex_fwd.h>
#include <boost/python.hpp>
#include <boost/python/class.hpp>
#include <scitbx/array_family/flex_types.h>
#include <scitbx/array_family/shared.h>
#include <scitbx/math/basic_statistics.h>
#include <cctbx/miller.h>
#include <cctbx/uctbx.h>

/*

This file contains an implmentation of calc_avg_I from
postrefine/mod_util.py, which averages observed intensities,
does outlier rejection and computes various statistics.

*/

using namespace boost::python;

namespace prime {
  enum Average_Mode {
    Average,  ///< normal avearaging
    Weighted, ///< weighted averaging
    Final     ///< averaging done when the postrefinement is finishing
  };

  typedef
    scitbx::af::shared<cctbx::miller::index<int> > shared_miller;

  struct average_result_store {
    // class for returning results
    shared_miller miller_index;
    scitbx::af::shared<double> I_avg;
    scitbx::af::shared<double> sigI_avg;
    scitbx::af::shared<double> r_meas_w_top;
    scitbx::af::shared<double> r_meas_w_btm;
    scitbx::af::shared<double> r_meas_top;
    scitbx::af::shared<double> r_meas_btm;
    scitbx::af::shared<int> multiplicity;
    scitbx::af::shared<double> I_avg_even;
    scitbx::af::shared<double> I_avg_odd;
    std::string txt_obs_out;
    std::string txt_reject_out;
  };

  class averaging_engine {
    // interface for computing averages
    const int group_no_;
    const scitbx::af::shared<int> group_id_list_;
    const shared_miller miller_index_;
    const shared_miller miller_index_ori_;
    const scitbx::af::shared<double> I_;
    const scitbx::af::shared<double> sigI_;
    const scitbx::af::shared<double> G_;
    const scitbx::af::shared<double> B_;
    const scitbx::af::shared<double> p_set_;
    const scitbx::af::shared<double> rs_set_;
    const scitbx::af::shared<double> wavelength_set_;
    const scitbx::af::shared<double> sin_theta_over_lambda_sq_;
    const scitbx::af::shared<double> SE_;
    public:
    Average_Mode avg_mode_;
    double sigma_max_;
    bool flag_volume_correction_;
    int n_rejection_cycle_;
    bool flag_output_verbose_;

    public: averaging_engine(
      // main constructor, used for passing in arrays. other parmaters exposed
      // as properties to python
      int group_no,
      scitbx::af::shared<int> group_id_list,
      const shared_miller& miller_index,
      const shared_miller& miller_index_ori,
      const scitbx::af::shared<double>& I,
      const scitbx::af::shared<double>& sigI,
      const scitbx::af::shared<double>& G,
      const scitbx::af::shared<double>& B,
      const scitbx::af::shared<double>& p_set,
      const scitbx::af::shared<double>& rs_set,
      const scitbx::af::shared<double>& wavelength_set,
      const scitbx::af::shared<double>& sin_theta_over_lambda_sq,
      const scitbx::af::shared<double>& SE
      ):
        group_no_(group_no),
        group_id_list_(group_id_list),
        miller_index_(miller_index),
        miller_index_ori_(miller_index_ori),
        I_(I),sigI_(sigI),G_(G),B_(B),p_set_(p_set),
        rs_set_(rs_set),
        wavelength_set_(wavelength_set),
        sin_theta_over_lambda_sq_(sin_theta_over_lambda_sq),
        SE_(SE)
    {
      avg_mode_ = Average;
      sigma_max_ = 99.0;
      flag_volume_correction_ = true;
      n_rejection_cycle_ = 1;
      flag_output_verbose_ = false;
    }

    static const double CONST_SE_MIN_WEIGHT;
    static const double CONST_SE_MAX_WEIGHT;
    static const double CONST_SIG_I_FACTOR;

    public: average_result_store
    calc_avg_I() {
      /*
      Average the intensites.

      I_ is an array with N observations.  miller_indices is an array with M indices.
      M should always be <= N. Observations are arranged into groups where the members
      of the same group have the same miller index.  group_id_list is N long and indexes
      each observation to a group and its miller index. group_id_list should be sorted
      (ascending) and that sort order applied to G, B, etc.
      */

      average_result_store results;
      std::ostringstream txt_obs_out;
      std::ostringstream txt_reject_out;

      // convert to the full intensity and calculate mosaic spread FIXTHIS mosaic spread unused? maybe just logged?
      scitbx::af::shared<double> I_full;
      scitbx::af::shared<double> mosaic_radian_set;
      for(int x = 0; x < G_.size(); x++) {
        I_full.push_back(((G_[x] * std::exp(-2*B_[x]*sin_theta_over_lambda_sq_[x]) * I_[x])/p_set_[x]));
        mosaic_radian_set.push_back(2 * rs_set_[x] * wavelength_set_[x]);
      }

      if (flag_volume_correction_)
        for (int x = 0; x < I_full.size(); x++)
          I_full[x] *= (4.0/3.0) * (rs_set_[x]);


      // Iterate over each group of intensites. They will match a single miller_index each
      int obs_ptr = 0; // this will track along the intensites array as each group is processed
      for (int g = 0; g < group_no_; g++) {
        SCITBX_ASSERT(group_id_list_[obs_ptr] == g); // this verifies that group_id_list is sorted

        int obs_ptr_start = obs_ptr;

        // gather intensites and errors for this group
        double max_w = CONST_SE_MAX_WEIGHT;
        double min_w = std::sqrt(CONST_SE_MIN_WEIGHT);
        scitbx::af::shared<double> I_group;
        scitbx::af::shared<double> sigI_group;
        scitbx::af::shared<double> I_full_group;
        scitbx::af::shared<double> SE_group;
        scitbx::af::shared<double> SE_norm;
        scitbx::af::shared<double> SE_std_norm;
        cctbx::miller::index<int> current_index;
        shared_miller current_index_ori;
        std::ostringstream txt_reject_out_group;

        bool found_one = false;
        while (obs_ptr < I_.size()) {
          if (group_id_list_[obs_ptr] != g) {
            break; // found them all
          }

          if (found_one) {
            SCITBX_ASSERT(current_index == miller_index_[obs_ptr]);
          }
          else {
            found_one = true;
            current_index = miller_index_[obs_ptr];
          }
          I_group.push_back(I_[obs_ptr]);
          sigI_group.push_back(sigI_[obs_ptr]);
          I_full_group.push_back(I_full[obs_ptr]);
          SE_group.push_back(SE_[obs_ptr]);
          current_index_ori.push_back(miller_index_ori_[obs_ptr]);
          obs_ptr++;
        }
        SCITBX_ASSERT(found_one);


        // log
        char buf[512];
        sprintf(buf, "Reflection: %d,%d,%d\nmeanI    medI  sigI_est sigI_true delta_sigI   n_refl\n",current_index[0],current_index[1],current_index[2]);
        txt_obs_out << buf;
        scitbx::af::shared<double> I_full_group_copy;
        for (int i = 0; i < I_full_group.size(); i++)
          I_full_group_copy.push_back(I_full_group[i]);
        scitbx::math::basic_statistics<double> basic_stat(I_full_group_copy.const_ref());
        scitbx::math::median_functor mf;

        double median_I = mf(I_full_group_copy.ref());
        double mean_I = basic_stat.mean;
        double std_I = basic_stat.mean_absolute_deviation_from_mean; // based on what I think numpy is doing compared to basic_statistics

        sprintf(buf, "%6.2f %6.2f %8.2f %8.0f\n", mean_I, median_I, std_I, double(I_full_group.size()));
        txt_obs_out << buf;

        //reject outliers
        if (I_full_group.size() > 2) {
          for (int i_rejection = 0; i_rejection < n_rejection_cycle_; i_rejection++) {
            scitbx::af::shared<double> I_full_group_copy;
            scitbx::af::shared<double> I_full_group_filtered;
            scitbx::af::shared<double> SE_group_filtered;
            for (int i = 0; i < I_full_group.size(); i++)
              I_full_group_copy.push_back(I_full_group[i]);
            scitbx::math::basic_statistics<double> basic_stat(I_full_group_copy.const_ref());
            scitbx::math::median_functor mf;

            double median_I = mf(I_full_group_copy.ref());
            double mean_I = basic_stat.mean;
            double std_I = basic_stat.mean_absolute_deviation_from_mean; // based on what I think numpy is doing compared to basic_statistics

            for (int i = 0; i < I_full_group.size(); i++) {
              double I_full_as_sigma = (I_full_group[i] - median_I) / std_I;
              if (I_full_as_sigma > sigma_max_) {
                SCITBX_ASSERT(false);

                char buf[512];
                sprintf(buf, "filename %3.0f %3.0f %3.0f %10.2f %10.2f\n", // note, not using pickle_filename_set
                  double(current_index_ori[i][0]), double(current_index_ori[i][1]), double(current_index_ori[i][2]), I_group[i], sigI_group[i]);
                txt_reject_out_group << buf;
              }
              else {
                I_full_group_filtered.push_back(I_full_group[i]);
                SE_group_filtered.push_back(SE_group[i]);
              }
            }
            I_full_group = I_full_group_filtered;
            SE_group = SE_group_filtered;

            char buf[512];
            sprintf(buf, "%6.2f %6.2f %8.2f %8.0f\n", mean_I, median_I, std_I, double(I_full_group.size()));
            txt_obs_out << buf;

            if (I_full_group.size() <= 3)
              break;
          }
          if (I_full_group.size() == 0) {
            printf("miller_index (%d, %d, %d) rejected at calc_avg", current_index[0], current_index[1], current_index[2]);
            continue;
          }
        }
        // normalize the SE
        double se_max = scitbx::af::max(SE_group.ref());
        double se_min = scitbx::af::min(SE_group.ref());
        double SE_norm_val, SE_std_norm_val;
        if (SE_group.size() == 1 or ((se_max-se_min) < 0.1) or avg_mode_ == Average) {
          SE_norm_val = min_w+((max_w - min_w)/2);
          SE_std_norm_val = (1.0+((CONST_SIG_I_FACTOR - 1.0)/2));
          for (int i = 0; i < SE_group.size(); i++) {
            SE_norm.push_back(SE_norm_val);
            SE_std_norm.push_back(SE_std_norm_val);
          }
        }
        else {
          double m = (max_w - min_w)/(se_min-se_max);
          double b = max_w - (m*se_min);
          double m_std = (CONST_SIG_I_FACTOR - 1.0)/(se_min-se_max);
          double b_std = CONST_SIG_I_FACTOR - (m_std*se_min);

          for (int i = 0; i < SE_group.size(); i++) {
            SE_norm.push_back( (m*SE_group[i]) + b);
            SE_std_norm.push_back( ( (m_std*SE_group[i])) + b_std);
          }
        }

        double SE_norm_sum = scitbx::af::sum(SE_norm.const_ref());
        SCITBX_ASSERT(SE_norm_sum != 0);
        scitbx::af::shared<double> avg_tmp;
        scitbx::af::shared<double> sigI_full;
        for (int i = 0; i < SE_norm.size(); i++) {
          avg_tmp.push_back(SE_norm[i] * I_full_group[i]);

          //test calculation of sigI
          sigI_full.push_back(std::sqrt(I_full_group[i]) * SE_std_norm[i]);
        }

        double I_avg = scitbx::af::sum(avg_tmp.const_ref())/SE_norm_sum;
        double sigI_avg = scitbx::af::mean(sigI_full.const_ref());

        //Rmeas, Rmeas_w, multiplicity
        int multiplicity = I_full_group.size();
        double r_meas_w_top = 0;
        double r_meas_w_btm = 0;
        double r_meas_top = 0;
        double r_meas_btm = 0;
        double r_meas = 0;
        double r_meas_w = 0;
        if (multiplicity > 1) {
          int n_obs = multiplicity;
          double w_top_sum = 0;
          double w_btm_sum = 0;
          double top_sum = 0;

          for (int i = 0; i < n_obs; i++) {
            w_top_sum += std::pow(((I_full_group[i] - I_avg)*SE_norm[i]),2);
            r_meas_w_btm += std::pow(I_full_group[i]*SE_norm[i],2);
            top_sum += std::abs(((I_full_group[i] - I_avg)*SE_norm[i]));
            r_meas_btm += std::abs(I_full_group[i]*SE_norm[i]);

          }

          r_meas_w_top = w_top_sum*std::sqrt(n_obs/(n_obs-1));
          r_meas_top = top_sum*std::sqrt(n_obs/(n_obs-1));
          r_meas = r_meas_top/r_meas_btm;
          r_meas_w = r_meas_w_top/r_meas_w_btm;
        }

        //for calculation of cc1/2
        //separate the observations into two groups
        double I_avg_even = 0;
        double I_avg_odd = 0;
        double I_even_sum = 0;
        double I_odd_sum = 0;
        double I_even_weighted_sum = 0;
        double I_odd_weighted_sum = 0;
        double SE_norm_even_sum = 0;
        double SE_norm_odd_sum = 0;

        if (multiplicity > 1) {
          for (int i = 0; i < I_full_group.size(); i++) {
            if (i % 2 == 0) {
              I_even_sum += I_full_group[i];
              I_even_weighted_sum += I_full_group[i] * SE_norm[i];
              SE_norm_even_sum += SE_norm[i];
            }
            else {
              I_odd_sum += I_full_group[i];
              I_odd_weighted_sum += I_full_group[i] * SE_norm[i];
              SE_norm_odd_sum += SE_norm[i];
            }
          }

          if (I_full_group.size() % 2 == 1) {
            I_odd_sum += I_full_group[I_full_group.size()-1];
            I_odd_weighted_sum += I_full_group[I_full_group.size()-1] * SE_norm[SE_norm.size()-1];
            SE_norm_odd_sum += SE_norm[SE_norm.size()-1];
          }

          if (avg_mode_ == Weighted || avg_mode_ == Final) {
            I_avg_even = I_even_weighted_sum/SE_norm_even_sum;
            I_avg_odd = I_odd_weighted_sum/SE_norm_odd_sum;
          }
          else {
            SCITBX_ASSERT(avg_mode_ == Average);
            int size;
            if(I_full_group.size() % 2 == 1)
              size = (I_full_group.size()+1)/2;
            else
              size = I_full_group.size()/2;
            I_avg_even = I_even_sum/size;
            I_avg_odd = I_odd_sum/size;
          }
        }

        // save the results for this group
        results.miller_index.push_back(current_index);
        results.I_avg.push_back(I_avg);
        results.sigI_avg.push_back(sigI_avg);
        results.r_meas_w_top.push_back(r_meas_w_top);
        results.r_meas_w_btm.push_back(r_meas_w_btm);
        results.r_meas_top.push_back(r_meas_top);
        results.r_meas_btm.push_back(r_meas_btm);
        results.multiplicity.push_back(multiplicity);
        results.I_avg_even.push_back(I_avg_even);
        results.I_avg_odd.push_back(I_avg_odd);

        if (flag_output_verbose_) {
          txt_obs_out << "    I_o        sigI_o    G      B     Eoc      rs    lambda rocking(deg) W     Wsig     I_full     sigI_full\n";
          for (int i = 0; i < I_full_group.size(); i++) {
            char buf[512];
            sprintf(buf, "%10.2f %10.2f %6.2f %6.2f %6.2f %8.5f %8.5f %8.5f %6.2f %6.2f %10.2f %10.2f\n",
              I_group[i],sigI_group[i],1/G_[obs_ptr_start+i],B_[obs_ptr_start+i],p_set_[obs_ptr_start+i],rs_set_[obs_ptr_start+i],
              wavelength_set_[obs_ptr_start+i],mosaic_radian_set[obs_ptr_start+i]*180/scitbx::constants::pi,SE_norm[i],SE_std_norm[i],
              I_full_group[i],sigI_full[i]);
            txt_obs_out << buf;
          }
          char buf[512];
          sprintf(buf, "Merged I, sigI: %6.2f, %6.2f\n",I_avg,sigI_avg);
          txt_obs_out << buf;
          sprintf(buf, "Rmeas: %6.2f Qw: %6.2f\n",r_meas,r_meas_w);
          txt_obs_out << buf;
          sprintf(buf, "No. total observed: %4.0f No. after rejection: %4.0f\n", double(obs_ptr-obs_ptr_start), double(I_full_group.size()));
          txt_obs_out << buf;
          txt_obs_out << "List of rejected observations:\n";
          txt_obs_out << txt_reject_out_group.str();
        }
        txt_reject_out << txt_reject_out_group.str();
      }
      results.txt_obs_out = txt_obs_out.str();
      results.txt_reject_out = txt_reject_out.str();

      return results;
    }
  };


const double averaging_engine::CONST_SE_MIN_WEIGHT = 0.17;
const double averaging_engine::CONST_SE_MAX_WEIGHT = 1.0;
const double averaging_engine::CONST_SIG_I_FACTOR = 5.0;

namespace boost_python { namespace {
  void
  init_module() {
    using namespace boost::python;
    typedef return_value_policy<return_by_value> rbv;
    typedef default_call_policies dcp;
    typedef averaging_engine w_t;

    class_<w_t>("averaging_engine", no_init)
      .def(init<int,scitbx::af::shared<int>,
        const shared_miller&,const shared_miller&,
        const scitbx::af::shared<double>&,
        const scitbx::af::shared<double>&,
        const scitbx::af::shared<double>&,
        const scitbx::af::shared<double>&,
        const scitbx::af::shared<double>&,
        const scitbx::af::shared<double>&,
        const scitbx::af::shared<double>&,
        const scitbx::af::shared<double>&,
        const scitbx::af::shared<double>&
        >(
        (arg("group_no"),arg("group_id_list"),
        arg("miller_list"),arg("miller_list_ori"),arg("I"),arg("sigI"),
        arg("G"),arg("B"),arg("p_set"),arg("rs_set"),
        arg("wavelength_set"),arg("sin_theta_over_lambda_sq"),arg("SE")
        )))
      .def("calc_avg_I", &averaging_engine::calc_avg_I)
      .add_property("avg_mode",
        make_getter(&averaging_engine::avg_mode_, rbv()),
        make_setter(&averaging_engine::avg_mode_, dcp()))
      .add_property("sigma_max",
        make_getter(&averaging_engine::sigma_max_, rbv()),
        make_setter(&averaging_engine::sigma_max_, dcp()))
      .add_property("flag_volume_correction",
        make_getter(&averaging_engine::flag_volume_correction_, rbv()),
        make_setter(&averaging_engine::flag_volume_correction_, dcp()))
      .add_property("n_rejection_cycle",
        make_getter(&averaging_engine::n_rejection_cycle_, rbv()),
        make_setter(&averaging_engine::n_rejection_cycle_, dcp()))
      .add_property("flag_output_verbose",
        make_getter(&averaging_engine::flag_output_verbose_, rbv()),
        make_setter(&averaging_engine::flag_output_verbose_, dcp()))
      ;

    class_<average_result_store>("average_result_store",init<>())
      .add_property("miller_index",
        make_getter(&average_result_store::miller_index, rbv()),
        make_setter(&average_result_store::miller_index, dcp()))
      .add_property("I_avg",
        make_getter(&average_result_store::I_avg, rbv()),
        make_setter(&average_result_store::I_avg, dcp()))
      .add_property("sigI_avg",
        make_getter(&average_result_store::sigI_avg, rbv()),
        make_setter(&average_result_store::sigI_avg, dcp()))
      .add_property("r_meas_w_top",
        make_getter(&average_result_store::r_meas_w_top, rbv()),
        make_setter(&average_result_store::r_meas_w_top, dcp()))
      .add_property("r_meas_w_btm",
        make_getter(&average_result_store::r_meas_w_btm, rbv()),
        make_setter(&average_result_store::r_meas_w_btm, dcp()))
      .add_property("r_meas_top",
        make_getter(&average_result_store::r_meas_top, rbv()),
        make_setter(&average_result_store::r_meas_top, dcp()))
      .add_property("r_meas_btm",
        make_getter(&average_result_store::r_meas_btm, rbv()),
        make_setter(&average_result_store::r_meas_btm, dcp()))
      .add_property("multiplicity",
        make_getter(&average_result_store::multiplicity, rbv()),
        make_setter(&average_result_store::multiplicity, dcp()))
      .add_property("I_avg_even",
        make_getter(&average_result_store::I_avg_even, rbv()),
        make_setter(&average_result_store::I_avg_even, dcp()))
      .add_property("I_avg_odd",
        make_getter(&average_result_store::I_avg_odd, rbv()),
        make_setter(&average_result_store::I_avg_odd, dcp()))
      .add_property("txt_obs_out",
        make_getter(&average_result_store::txt_obs_out, rbv()),
        make_setter(&average_result_store::txt_obs_out, dcp()))
      .add_property("txt_reject_out",
        make_getter(&average_result_store::txt_reject_out, rbv()),
        make_setter(&average_result_store::txt_reject_out, dcp()))
    ;
  };

  using namespace boost::python;

  void export_average_mode()
  {
    enum_<Average_Mode>("Average_Mode")
      .value("Average", Average)
      .value("Weighted", Weighted)
      .value("Final", Final);
  }

}}} // namespace prime::boost_python::<anonymous>

BOOST_PYTHON_MODULE(prime_ext)
{
  prime::boost_python::init_module();
  prime::boost_python::export_average_mode();

}
