#ifndef SCITBX_ARRAY_FAMILY_REDUCTIONS_H
#define SCITBX_ARRAY_FAMILY_REDUCTIONS_H

#include <scitbx/array_family/ref.h>
#include <scitbx/array_family/misc_functions.h>

namespace scitbx { namespace af {

  template <typename ElementType1, typename AccessorType1,
            typename ElementType2, typename AccessorType2>
  int
  order(
    const_ref<ElementType1, AccessorType1> const& a1,
    const_ref<ElementType2, AccessorType2> const& a2)
  {
    std::size_t sz_min = (a1.size() < a2.size() ? a1.size() : a2.size());
    for(std::size_t i=0;i<sz_min;i++) {
      if (a1[i] < a2[i]) return -1;
      if (a2[i] < a1[i]) return 1;
    }
    if (a1.size() < a2.size()) return -1;
    if (a2.size() < a1.size()) return 1;
    return 0;
  }

  template <typename ElementType, typename AccessorType>
  std::size_t
  max_index(const_ref<ElementType, AccessorType> const& a)
  {
    if (a.size() == 0) {
      throw std::runtime_error("max_index() argument is an empty array");
    }
    std::size_t result = 0;
    for(std::size_t i=1;i<a.size();i++) {
      if (a[result] < a[i]) result = i;
    }
    return result;
  }

  template <typename ElementType, typename AccessorType>
  std::size_t
  min_index(const_ref<ElementType, AccessorType> const& a)
  {
    if (a.size() == 0) {
      throw std::runtime_error("min_index() argument is an empty array");
    }
    std::size_t result = 0;
    for(std::size_t i=1;i<a.size();i++) {
      if (a[result] > a[i]) result = i;
    }
    return result;
  }

  template <typename ElementType, typename AccessorType>
  ElementType
  max(const_ref<ElementType, AccessorType> const& a)
  {
    if (a.size() == 0) {
      throw std::runtime_error("max() argument is an empty array");
    }
    ElementType result = a[0];
    for(std::size_t i=1;i<a.size();i++) {
      if (result < a[i]) result = a[i];
    }
    return result;
  }

  template <typename ElementType, typename AccessorType>
  ElementType
  min(const_ref<ElementType, AccessorType> const& a)
  {
    if (a.size() == 0) {
      throw std::runtime_error("min() argument is an empty array");
    }
    ElementType result = a[0];
    for(std::size_t i=1;i<a.size();i++) {
      if (result > a[i]) result = a[i];
    }
    return result;
  }

  template <typename ElementType, typename AccessorType>
  ElementType
  max_absolute(const_ref<ElementType, AccessorType> const& a)
  {
    if (a.size() == 0) {
      throw std::runtime_error("max_absolute() argument is an empty array");
    }
    ElementType result = fn::absolute(a[0]);
    for(std::size_t i=1;i<a.size();i++) {
      ElementType aai = fn::absolute(a[i]);
      if (result < aai) result = aai;
    }
    return result;
  }

  template <typename ElementType, typename AccessorType>
  ElementType
  sum(const_ref<ElementType, AccessorType> const& a)
  {
    ElementType result = 0;
    for(std::size_t i=0;i<a.size();i++) result += a[i];
    return result;
  }

  template <typename ElementType, typename AccessorType>
  ElementType
  sum_sq(const_ref<ElementType, AccessorType> const& a)
  {
    ElementType result = 0;
    for(std::size_t i=0;i<a.size();i++) result += a[i] * a[i];
    return result;
  }

  template <typename ElementType, typename AccessorType>
  ElementType
  product(const_ref<ElementType, AccessorType> const& a)
  {
    std::size_t sz = a.size();
    if (sz == 0) return 0;
    ElementType result = 1;
    for(std::size_t i=0;i<sz;i++) result *= a[i];
    return result;
  }

  template <typename ElementType, typename AccessorType>
  ElementType
  mean(const_ref<ElementType, AccessorType> const& a)
  {
    if (a.size() == 0) {
      throw std::runtime_error("mean() argument is an empty array");
    }
    ElementType result = a[0];
    for(std::size_t i=1;i<a.size();i++) result += a[i];
    return result / a.size();
  }

  template <typename ElementType, typename AccessorType>
  ElementType
  mean_sq(const_ref<ElementType, AccessorType> const& a)
  {
    if (a.size() == 0) {
      throw std::runtime_error("mean_sq() argument is an empty array");
    }
    ElementType result = a[0] * a[0];
    for(std::size_t i=1;i<a.size();i++) result += a[i] * a[i];
    return result / a.size();
  }

  template <typename ElementTypeValues, typename AccessorTypeValues,
            typename ElementTypeWeights, typename AccessorTypeWeights>
  ElementTypeValues
  mean_weighted(
    const_ref<ElementTypeValues, AccessorTypeValues> const& values,
    const_ref<ElementTypeWeights, AccessorTypeWeights> const& weights)
  {
    if (values.size() != weights.size()) throw_range_error();
    if (values.size() == 0) {
      throw std::runtime_error("mean_weighted() argument is an empty array");
    }
    ElementTypeValues sum_vw = values[0] * weights[0];
    ElementTypeWeights sum_w = weights[0];
    for(std::size_t i=1;i<values.size();i++) {
      sum_vw += values[i] * weights[i];
      sum_w += weights[i];
    }
    return sum_vw / sum_w;
  }

  template <typename ElementTypeValues, typename AccessorTypeValues,
            typename ElementTypeWeights, typename AccessorTypeWeights>
  ElementTypeValues
  mean_sq_weighted(
    const_ref<ElementTypeValues, AccessorTypeValues> const& values,
    const_ref<ElementTypeWeights, AccessorTypeWeights> const& weights)
  {
    if (values.size() != weights.size()) throw_range_error();
    if (values.size() == 0) {
      throw std::runtime_error(
        "mean_sq_weighted() argument is an empty array");
    }
    ElementTypeValues sum_vvw = values[0] * values[0] * weights[0];
    ElementTypeWeights sum_w = weights[0];
    for(std::size_t i=1;i<values.size();i++) {
      sum_vvw += values[i] * values[i] * weights[i];
      sum_w += weights[i];
    }
    return sum_vvw / sum_w;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_eq(const_ref const& other) const
  {
    const ElementType* o = other.begin();
    const ElementType* t = begin();
    const ElementType* e = end();
    if (e-t != other.end()-o) return false;
    while (t != e) {
      if (!(*t++ == *o++)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_eq(ElementType const& other) const
  {
    const ElementType* t = begin();
    const ElementType* e = end();
    while (t != e) {
      if (!(*t++ == other)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_ne(const_ref const& other) const
  {
    const ElementType* o = other.begin();
    const ElementType* t = begin();
    const ElementType* e = end();
    if (e-t != other.end()-o) return false;
    while (t != e) {
      if (!(*t++ != *o++)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_ne(ElementType const& other) const
  {
    const ElementType* t = begin();
    const ElementType* e = end();
    while (t != e) {
      if (!(*t++ != other)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_lt(const_ref const& other) const
  {
    const ElementType* o = other.begin();
    const ElementType* t = begin();
    const ElementType* e = end();
    if (e-t != other.end()-o) throw_range_error();
    while (t != e) {
      if (!(*t++ < *o++)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_lt(ElementType const& other) const
  {
    const ElementType* t = begin();
    const ElementType* e = end();
    while (t != e) {
      if (!(*t++ < other)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_gt(const_ref const& other) const
  {
    const ElementType* o = other.begin();
    const ElementType* t = begin();
    const ElementType* e = end();
    if (e-t != other.end()-o) throw_range_error();
    while (t != e) {
      if (!(*t++ > *o++)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_gt(ElementType const& other) const
  {
    const ElementType* t = begin();
    const ElementType* e = end();
    while (t != e) {
      if (!(*t++ > other)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_le(const_ref const& other) const
  {
    const ElementType* o = other.begin();
    const ElementType* t = begin();
    const ElementType* e = end();
    if (e-t != other.end()-o) throw_range_error();
    while (t != e) {
      if (!(*t++ <= *o++)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_le(ElementType const& other) const
  {
    const ElementType* t = begin();
    const ElementType* e = end();
    while (t != e) {
      if (!(*t++ <= other)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_ge(const_ref const& other) const
  {
    const ElementType* o = other.begin();
    const ElementType* t = begin();
    const ElementType* e = end();
    if (e-t != other.end()-o) throw_range_error();
    while (t != e) {
      if (!(*t++ >= *o++)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_ge(ElementType const& other) const
  {
    const ElementType* t = begin();
    const ElementType* e = end();
    while (t != e) {
      if (!(*t++ >= other)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_approx_equal(
    const_ref const& other,
    ElementType const& tolerance) const
  {
    const ElementType* o = other.begin();
    const ElementType* t = begin();
    const ElementType* e = end();
    if (e-t != other.end()-o) return false;
    while (t != e) {
      if (!fn::approx_equal(*t++, *o++, tolerance)) return false;
    }
    return true;
  }

  template <typename ElementType, typename AccessorType>
  bool
  const_ref<ElementType, AccessorType>
  ::all_approx_equal(
    ElementType const& other,
    ElementType const& tolerance) const
  {
    const ElementType* t = begin();
    const ElementType* e = end();
    while (t != e) {
      if (!fn::approx_equal(*t++, other, tolerance)) return false;
    }
    return true;
  }

}} // namespace scitbx::af

#endif // SCITBX_ARRAY_FAMILY_REDUCTIONS_H
