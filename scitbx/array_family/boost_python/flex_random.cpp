#include <scitbx/array_family/boost_python/flex_fwd.h>

#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/overloads.hpp>
#include <boost/random/mersenne_twister.hpp>

namespace scitbx { namespace af { namespace boost_python {

namespace {

  class mersenne_twister
  {
    public:
      mersenne_twister(unsigned seed=0)
      :
        generator_(seed+1)
      {
        init();
      }

      void
      seed(unsigned value=0) { generator_.seed(value+1); }

      shared<std::size_t>
      random_size_t(std::size_t size)
      {
        shared<std::size_t> result(size, init_functor_null<std::size_t>());
        for(std::size_t i=0;i<size;i++) {
          result[i] = static_cast<std::size_t>(generator_());
        }
        return result;
      }

      shared<double>
      random_double(std::size_t size)
      {
        shared<double> result(size, init_functor_null<double>());
        for(std::size_t i=0;i<size;i++) {
          result[i] = as_double(generator_()-generator_min_)
                    / generator_range_;
        }
        return result;
      }

      shared<std::size_t>
      random_permutation(std::size_t size)
      {
        shared<std::size_t> result(size, init_functor_null<std::size_t>());
        for(std::size_t i=0;i<size;i++) {
          result[i] = i;
        }
        for(std::size_t i=0;i<size;i++) {
          std::size_t j = static_cast<std::size_t>(generator_()) % size;
          std::swap(result[i], result[j]);
        }
        return result;
      }

    private:
      boost::mt19937 generator_;
#if defined(__INTEL_COMPILER)
      unsigned n_bits_half_word_;
      boost::mt19937::result_type half_;
#endif
      boost::mt19937::result_type generator_min_;
      double generator_range_;

      void
      init()
      {
#if defined(__INTEL_COMPILER)
        n_bits_half_word_ = sizeof(boost::mt19937::result_type) * 4;
        half_ = static_cast<boost::mt19937::result_type>(1)<<n_bits_half_word_;
#endif
        generator_min_ = generator_.min();
        generator_range_ = as_double(generator_.max()-generator_min_);
      }

      double
      as_double(boost::mt19937::result_type generated_value)
      {
#if defined(__INTEL_COMPILER)
        double result = static_cast<double>(
          generated_value >> n_bits_half_word_);
        result *= static_cast<double>(half_);
        result += static_cast<double>(generated_value % half_);
        return result;
#else
        return static_cast<double>(generated_value);
#endif
      }
  };

  struct mersenne_twister_wrappers
  {
    typedef mersenne_twister w_t;

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      seed_overloads, seed, 0, 1)

    static void
    wrap()
    {
      using namespace boost::python;
      class_<mersenne_twister>("mersenne_twister", no_init)
        .def(init<optional<unsigned> >((arg_("seed")=0)))
        .def("random_size_t", &w_t::random_size_t, (arg_("size")))
        .def("random_double", &w_t::random_double, (arg_("size")))
        .def("random_permutation", &w_t::random_permutation, (arg_("size")))
        .def("seed", &w_t::seed, seed_overloads((arg_("value")=0)))
      ;
    }
  };

} // namespace <anonymous>

  void wrap_flex_random()
  {
    mersenne_twister_wrappers::wrap();
  }

}}} // namespace scitbx::af::boost_python
