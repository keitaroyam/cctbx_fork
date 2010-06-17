#ifndef FEM_DATA_OF_TYPE_HPP
#define FEM_DATA_OF_TYPE_HPP

#include <fem/arr.hpp>
#include <fem/str_arr_ref.hpp>
#include <boost/noncopyable.hpp>

namespace fem {

  template <typename T>
  struct data_of_type : boost::noncopyable
  {
    T const* values;
    size_t values_size;
    size_t value_index;

    data_of_type(
      T const* values_,
      size_t values_size_)
    :
      values(values_),
      values_size(values_size_),
      value_index(0)
    {}

    ~data_of_type() { ASSERTBX(value_index == values_size); }

#define FEM_LOC(V) \
    data_of_type& \
    operator,( \
      V& val) \
    { \
      ASSERTBX(value_index < values_size); \
      val = values[value_index++]; \
      return *this; \
    }
    FEM_LOC(char)
    FEM_LOC(bool)
    FEM_LOC(int)
    FEM_LOC(float)
    FEM_LOC(double)
#undef FEM_LOC

    template <size_t Ndims>
    data_of_type&
    operator,(
      arr_ref<T, Ndims>& val)
    {
      size_t n = val.size_1d();
      T* val_begin = val.begin();
      for(size_t i=0;i<n;i++) (*this), val_begin[i];
      return *this;
    }
  };

  struct data_of_type_str : boost::noncopyable
  {
    char const** values;
    size_t values_size;
    size_t value_index;

    data_of_type_str(
      char const** values_,
      size_t values_size_)
    :
      values(values_),
      values_size(values_size_),
      value_index(0)
    {}

    ~data_of_type_str() { ASSERTBX(value_index == values_size); }

    data_of_type_str&
    operator,(
      str_ref val)
    {
      ASSERTBX(value_index < values_size);
      val = values[value_index++];
      return *this;
    }

    template <int StrLen, size_t Ndims>
    data_of_type_str&
    operator,(
      arr_ref<str<StrLen>, Ndims>& val)
    {
      size_t n = val.size_1d();
      str<StrLen>* val_begin = val.begin();
      for(size_t i=0;i<n;i++) (*this), val_begin[i];
      return *this;
    }

    template <size_t Ndims>
    data_of_type_str&
    operator,(
      str_arr_ref<Ndims>& val)
    {
      size_t n = val.size_1d();
      for(size_t i=0;i<n;i++) (*this), val[i];
      return *this;
    }
  };

}

#define FEM_VALUES_AND_SIZE values, sizeof(values) / sizeof(*values)

#endif // GUARD
