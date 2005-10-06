#ifndef SCITBX_MATH_MEAN_AND_VARIANCE_H
#define SCITBX_MATH_MEAN_AND_VARIANCE_H

#include <scitbx/array_family/ref_reductions.h>

namespace scitbx { namespace math {

  template <typename FloatType = double>
  class mean_and_variance
  {
    public:
      typedef FloatType float_type;
      typedef std::size_t size_type;

      mean_and_variance() {}

      mean_and_variance(
        af::const_ref<FloatType> values)
      :
        sum_weights_(values.size()),
        sum_weights_sq_(values.size()),
        sum_weights_values_(af::sum(values)),
        sum_weights_delta_sq_(0)
      {
        FloatType m = mean();
        for(std::size_t i=0;i<values.size();i++) {
          sum_weights_delta_sq_ += fn::pow2(values[i] - m);
        }
      }

      mean_and_variance(
        af::const_ref<FloatType> values,
        af::const_ref<FloatType> weights)
      :
        sum_weights_(af::sum(weights)),
        sum_weights_sq_(af::sum_sq(weights)),
        sum_weights_values_(0),
        sum_weights_delta_sq_(0)
      {
        SCITBX_ASSERT(values.size() == weights.size());
        for(std::size_t i=0;i<values.size();i++) {
          sum_weights_values_ += values[i] * weights[i];
        }
        FloatType m = mean();
        for(std::size_t i=0;i<values.size();i++) {
          sum_weights_delta_sq_ += fn::pow2(values[i] - m) * weights[i];
        }
      }

      FloatType
      mean() const
      {
        SCITBX_ASSERT(sum_weights_ > 0);
        return sum_weights_values_ / sum_weights_ ;
      }

      //! Emulation of gsl_stats_wvariance of the GNU Scientific Library.
      /*! http://www.gnu.org/software/gsl/manual/gsl-ref_20.html#SEC339
       */
      FloatType
      gsl_variance() const
      {
        SCITBX_ASSERT(fn::pow2(sum_weights_) > sum_weights_sq_);
        return sum_weights_ / (fn::pow2(sum_weights_) - sum_weights_sq_)
             * sum_weights_delta_sq_;
      }

      FloatType
      gsl_standard_deviation() const { return std::sqrt(gsl_variance()); }

      FloatType
      cumulative_variance() const
      {
        SCITBX_ASSERT(sum_weights_ > 0);
        return 1 / sum_weights_;
      }

      FloatType
      cumulative_standard_deviation() const
      {
        return std::sqrt(cumulative_variance());
      }

      FloatType
      conservative_variance() const
      {
        return std::max(gsl_variance(), cumulative_variance());
      }

      FloatType
      conservative_standard_deviation() const
      {
        return std::sqrt(conservative_variance());
      }

      FloatType
      sum_weights() const { return sum_weights_; }

      FloatType
      sum_weights_sq() const { return sum_weights_sq_; }

      FloatType
      sum_weights_values() const { return sum_weights_values_; }

      FloatType
      sum_weights_delta_sq() const { return sum_weights_delta_sq_; }

    protected:
      FloatType sum_weights_;
      FloatType sum_weights_sq_;
      FloatType sum_weights_values_;
      FloatType sum_weights_delta_sq_;
  };

}} // namespace scitbx::math

#endif // SCITBX_MATH_MEAN_AND_VARIANCE_H
