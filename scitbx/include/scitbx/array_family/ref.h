/* Copyright (c) 2001-2002 The Regents of the University of California
   through E.O. Lawrence Berkeley National Laboratory, subject to
   approval by the U.S. Department of Energy.
   See files COPYRIGHT.txt and LICENSE.txt for further details.

   Revision history:
     2002 Aug: Copied from cctbx/array_family (R.W. Grosse-Kunstleve)
     2002 Jan: Created (R.W. Grosse-Kunstleve)
 */

#ifndef SCITBX_ARRAY_FAMILY_REF_H
#define SCITBX_ARRAY_FAMILY_REF_H

#include <scitbx/array_family/error.h>
#include <scitbx/array_family/grid_accessor.h>
#include <scitbx/array_family/detail/ref_helpers.h>

namespace scitbx { namespace af {

  template <typename ElementType,
            typename AccessorType = grid<1> >
  class const_ref
  {
    public:
      SCITBX_ARRAY_FAMILY_TYPEDEFS

      typedef AccessorType accessor_type;
      typedef typename accessor_type::index_type index_type;

      const_ref()
        : m_begin(0)
      {}
      const_ref(const ElementType* begin, accessor_type ac)
        : m_begin(begin), m_accessor(ac)
      {}
      // convenience constructors
      const_ref(
        const ElementType* begin, long n0)
        : m_begin(begin), m_accessor(n0)
      {}
      const_ref(
        const ElementType* begin, long n0, long n1)
        : m_begin(begin), m_accessor(n0, n1)
      {}
      const_ref(
        const ElementType* begin, long n0, long n1, long n2)
        : m_begin(begin), m_accessor(n0, n1, n2)
      {}

      accessor_type const& accessor() const { return m_accessor; }
      size_type size() const { return m_accessor.size_1d(); }

      const ElementType* begin() const { return m_begin; }
      const ElementType* end() const { return m_begin + size(); }
      ElementType const& front() const { return m_begin[0]; }
      ElementType const& back() const { return m_begin[size()-1]; }

      ElementType const& operator[](size_type i) const { return m_begin[i]; }

      ElementType const& at(size_type i) const {
        if (i >= size()) throw_range_error();
        return m_begin[i];
      }

      const_ref<ElementType> as_1d() const {
        return const_ref<ElementType>(m_begin, size());
      }

      value_type const& operator()(index_type const& i) const {
        return this->begin()[m_accessor(i)];
      }

      // Convenience operator()

      value_type const& operator()(long i0) const {
        return operator()(index_type(i0));
      }
      value_type const& operator()(long i0,
                                   long i1) const {
        return operator()(index_type(i0, i1));
      }
      value_type const& operator()(long i0,
                                   long i1,
                                   long i2) const {
        return operator()(index_type(i0, i1, i2));
      }

      bool all_eq(const_ref const& other) const;

      bool all_eq(ElementType const& other) const;

      bool all_ne(const_ref const& other) const;

      bool all_ne(ElementType const& other) const;

      bool all_lt(const_ref const& other) const;

      bool all_lt(ElementType const& other) const;

      bool all_gt(const_ref const& other) const;

      bool all_gt(ElementType const& other) const;

      bool all_le(const_ref const& other) const;

      bool all_le(ElementType const& other) const;

      bool all_ge(const_ref const& other) const;

      bool all_ge(ElementType const& other) const;

      bool
      all_approx_equal(
        const_ref const& other,
        ElementType const& tolerance) const;

      bool
      all_approx_equal(
        ElementType const& other,
        ElementType const& tolerance) const;

    protected:
      const ElementType* m_begin;
      accessor_type m_accessor;
  };

  template <typename ElementType,
            typename AccessorType = grid<1> >
  class ref : public const_ref<ElementType, AccessorType>
  {
    public:
      SCITBX_ARRAY_FAMILY_TYPEDEFS

      typedef const_ref<ElementType, AccessorType> base_class;
      typedef AccessorType accessor_type;
      typedef typename accessor_type::index_type index_type;

      ref()
      {}

      ref(ElementType* begin, accessor_type ac)
        : base_class(begin, ac)
      {}

      // convenience constructors
      ref(ElementType* begin, long n0)
      : base_class(begin, n0)
      {}

      ref(ElementType* begin, long n0, long n1)
      : base_class(begin, n0, n1)
      {}

      ref(ElementType* begin, long n0, long n1, long n2)
      : base_class(begin, n0, n1, n2)
      {}

      ElementType*
      begin() const { return const_cast<ElementType*>(this->m_begin); }

      ElementType*
      end() const { return begin() + this->size(); }

      ElementType&
      front() const { return begin()[0]; }

      ElementType&
      back() const { return end()[-1]; }

      ElementType&
      operator[](size_type i) const { return begin()[i]; }

      ElementType&
      at(size_type i) const
      {
        if (i >= this->size()) throw_range_error();
        return begin()[i];
      }

      ref const&
      fill(ElementType const& x) const
      {
        std::fill(begin(), end(), x);
        return *this;
      }

      ref<ElementType>
      as_1d() const
      {
        return ref<ElementType>(this->begin(), this->size());
      }

      value_type&
      operator()(index_type const& i) const
      {
        return begin()[this->m_accessor(i)];
      }

      // Convenience operator()

      value_type&
      operator()(long i0) const
      {
        return operator()(index_type(i0));
      }

      value_type&
      operator()(long i0, long i1) const
      {
        return operator()(index_type(i0, i1));
      }

      value_type&
      operator()(long i0, long i1, long i2) const
      {
        return operator()(index_type(i0, i1, i2));
      }
  };

}} // namespace scitbx::af

#endif // SCITBX_ARRAY_FAMILY_REF_H
