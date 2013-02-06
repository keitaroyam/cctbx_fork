#ifndef MMTBX_GEOMETRY_CONTAINMENT_H
#define MMTBX_GEOMETRY_CONTAINMENT_H

#include <scitbx/math/cartesian_product_fixed_size.hpp>
#include <boost/iterator/filter_iterator.hpp>

#include <cmath>
#include <vector>

namespace mmtbx
{

namespace geometry
{

namespace containment
{

struct PointInOriginSphere
{
  template< typename Vector >
  inline bool operator ()(
    const Vector& point,
    const typename Vector::value_type& radius_sq
    ) const;
};

struct PointInOriginDiamond
{
  template< typename Vector >
  inline bool operator ()(
    const Vector& point,
    const typename Vector::value_type& radius
    ) const;
};

struct PointInOriginCube
{
  template< typename Vector >
  inline bool operator ()(
    const Vector& point,
    const typename Vector::value_type& radius
    ) const;
};

struct PointInCube
{

  template< typename FloatType >
  inline bool one_dimensional(
    const FloatType& point,
    const FloatType& low,
    const FloatType& high
    ) const;

  template< typename Vector >
  inline bool operator ()(
    const Vector& point,
    const Vector& low,
    const Vector& high
    ) const;
};

// Check with multiple neighbours
template< bool select_overlapped = true >
struct PurePythagorean : private PointInOriginSphere
{
  BOOST_STATIC_CONSTANT( bool, return_value_overlapped = select_overlapped );
  BOOST_STATIC_CONSTANT( bool, return_value_accessible = !select_overlapped );
  template< typename Container >
  inline bool operator ()(
    const typename Container::value_type::vector_type& point,
    const Container& neighbours
    ) const;
};

template< bool select_overlapped = true >
struct DiamondPrefilter
  : private PointInOriginSphere, private PointInOriginDiamond
{
  BOOST_STATIC_CONSTANT( bool, return_value_overlapped = select_overlapped );
  BOOST_STATIC_CONSTANT( bool, return_value_accessible = !select_overlapped );
  template< typename Container >
  inline bool operator ()(
    const typename Container::value_type::vector_type& point,
    const Container& neighbours
    ) const;
};

template< bool select_overlapped = true >
struct CubePrefilter
  : private PointInOriginSphere, private PointInCube
{
  BOOST_STATIC_CONSTANT( bool, return_value_overlapped = select_overlapped );
  BOOST_STATIC_CONSTANT( bool, return_value_accessible = !select_overlapped );
  template< typename Container >
  inline bool operator ()(
    const typename Container::value_type::vector_type& point,
    const Container& neighbours
    ) const;
};

// Containment within specified object
template< typename Range, typename Functor >
struct FilterResult
{
public:
  typedef Range input_range_type;
  typedef typename input_range_type::iterator_type iterator_type;
  typedef Functor functor_type;
  typedef boost::filter_iterator< functor_type, iterator_type > filter_iterator;
  typedef scitbx::math::cartesian_product::iterated_range< filter_iterator >
    result_range_type;
};

template< typename Neighbour, typename Algorithm >
class Checker : private Algorithm
{
public:
  typedef Neighbour neighbour_type;
  typedef typename Neighbour::value_type value_type;
  typedef typename Neighbour::vector_type vector_type;
  typedef std::vector< neighbour_type > storage_type;

  typedef bool result_type;
  typedef const vector_type& argument_type;

  typedef Checker< Neighbour, Algorithm > functor_type;

private:
  storage_type neighbours_;

public:
  Checker();
  ~Checker();

  template< typename InputIterator >
  void add(InputIterator begin, InputIterator end);
  const storage_type& neighbours() const;

  inline bool operator ()(const vector_type& point) const;

  template< typename Range >
  inline typename FilterResult< Range, functor_type >::result_range_type
    filter(
      const typename
      FilterResult< Range, functor_type >::input_range_type& points
      ) const;
};


#include "containment.hxx"

} // namespace containment
} // namespace geometry
} // namespace mmtbx

#endif // MMTBX_GEOMETRY_CONTAINMENT_H

