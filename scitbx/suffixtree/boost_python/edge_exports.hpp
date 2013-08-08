#ifndef SUFFIXTREE_PYTHON_EDGE_EXPORTS_HPP_
#define SUFFIXTREE_PYTHON_EDGE_EXPORTS_HPP_

#include <boost/python/class.hpp>
#include <boost/python/object.hpp>
#include <boost/python/operators.hpp>
#include <boost/python/list.hpp>
#include <boost/python/errors.hpp>
#include <boost/python/def.hpp>
#include <boost/python/iterator.hpp>

#include <boost/shared_ptr.hpp>
#include <boost/functional.hpp>

#include <scitbx/suffixtree/edge.hpp>
#include <scitbx/suffixtree/iterator.hpp>

namespace scitbx
{
namespace suffixtree
{
namespace python
{

template< typename Iterator >
class PythonIterator
{
public:
  typedef Iterator iterator_type;
  typedef typename iterator_type::value_type value_type;

private:
  iterator_type current_;
  iterator_type end_;

public:
  PythonIterator(iterator_type const& begin, iterator_type const& end)
    : current_( begin ), end_( end )
  {};
  ~PythonIterator()
  {};

  value_type next()
  {
    if ( current_ == end_ )
    {
      PyErr_SetString(PyExc_StopIteration, "No more data.");
      boost::python::throw_error_already_set();
    }

    return *( current_++ );
  }

  static boost::python::object pass_through(boost::python::object const& o)
  {
    return o;
  }

  static void wrap(const char* python_name)
  {
    using namespace boost::python;

    class_< PythonIterator >(python_name, no_init)
      .def( "next", &PythonIterator::next)
      .def("__iter__", PythonIterator::pass_through )
      ;
  }
};

template<
  typename Glyph,
  typename Index,
  typename WordLength,
  typename SuffixLabel,
  template< typename, typename > class NodeAdapter
  >
struct edge_exports
{
  typedef edge::Edge< Glyph, Index, WordLength, SuffixLabel, NodeAdapter > edge_type;
  typedef typename edge_type::ptr_type ptr_type;
  typedef typename edge_type::const_ptr_type const_ptr_type;
  typedef typename edge_type::weak_ptr_type weak_ptr_type;
  typedef typename edge_type::const_weak_ptr_type const_weak_ptr_type;
  typedef typename edge_type::index_type index_type;
  typedef typename edge_type::suffix_label_type suffix_label_type;
  typedef typename edge_type::node_type node_type;
  typedef typename edge_type::word_length_type word_length_type;
  typedef typename edge_type::glyph_type glyph_type;

  static void throw_python_key_error()
  {
    PyErr_SetString(PyExc_KeyError, "Key not found");
    boost::python::throw_error_already_set();
  }

  static const_ptr_type to_const_ptr(ptr_type const& edge_ptr)
  {
    return boost::const_pointer_cast< edge_type const >( edge_ptr );
  }

  static index_type get_start_const(const_ptr_type const& edge_ptr)
  {
    return edge_ptr->start();
  }

  static index_type get_start(ptr_type const& edge_ptr)
  {
    return get_start_const( to_const_ptr( edge_ptr ) );
  }

  static void set_start(ptr_type const& edge_ptr, index_type const& start)
  {
    edge_ptr->start() = start;
  }

  static index_type get_stop_const(const_ptr_type const& edge_ptr)
  {
    return edge_ptr->stop();
  }

  static index_type get_stop(ptr_type const& edge_ptr)
  {
    return get_stop_const( to_const_ptr( edge_ptr ) );
  }

  static suffix_label_type get_suffix_label_const(const_ptr_type const& edge_ptr)
  {
    return edge_ptr->label();
  }

  static suffix_label_type get_suffix_label(ptr_type const& edge_ptr)
  {
    return get_suffix_label_const( to_const_ptr( edge_ptr ) );
  }

  static bool node_contains_const(const_ptr_type const& edge_ptr, glyph_type const& key)
  {
    return edge_ptr->find( key ) != edge_ptr->end();
  }

  static bool node_contains(ptr_type const& edge_ptr, glyph_type const& key)
  {
    return node_contains_const( to_const_ptr( edge_ptr ), key );
  }

  static bool node_empty_const(const_ptr_type const& edge_ptr)
  {
    return edge_ptr->empty();
  }

  static bool node_empty(ptr_type const& edge_ptr)
  {
    return edge_ptr->empty();
  }

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wreturn-type"

  static const_ptr_type node_get_item_const(const_ptr_type const& edge_ptr, glyph_type const& key)
  {
    typename edge_type::const_iterator it = edge_ptr->find( key );

    if ( it != edge_ptr->end() )
    {
      return it->second;
    }
    else
    {
      throw_python_key_error();
    }
  }

  static ptr_type node_get_item(ptr_type const& edge_ptr, glyph_type const& key)
  {
    typename edge_type::iterator it = edge_ptr->find( key );

    if ( it != edge_ptr->end() )
    {
      return it->second;
    }
    else
    {
      throw_python_key_error();
    }
  }

#pragma clang diagnostic pop

  static void node_set_item(
    ptr_type const& edge_ptr,
    glyph_type const& key,
    ptr_type const& value
    )
  {
    std::pair< typename edge_type::iterator, bool > res = edge_ptr->insert(
      typename edge_type::value_type( key, value )
      );

    if ( not res.second )
    {
      ( res.first )->second = value;
    }
  }

  static boost::python::list node_keys_const(const_ptr_type const& edge_ptr)
  {
    boost::python::list result;

    for(
      typename edge_type::const_iterator it = edge_ptr->begin();
      it != edge_ptr->end();
      ++it
      )
    {
      const glyph_type& k = it->first;
      result.append( k );
    }

    return result;
  }

  static boost::python::list node_keys(ptr_type const& edge_ptr)
  {
    return node_keys_const( to_const_ptr( edge_ptr ) );
  }

  static const_weak_ptr_type const get_parent_const(const_ptr_type const& edge_ptr)
  {
    return edge_ptr->parent();
  }

  static weak_ptr_type const get_parent(ptr_type const& edge_ptr)
  {
    return edge_ptr->parent();
  }

  static void set_parent(ptr_type const& edge_ptr, weak_ptr_type const& parent)
  {
    edge_ptr->parent() = parent;
  }

  static const_weak_ptr_type const get_suffix_const(const_ptr_type const& edge_ptr)
  {
    return edge_ptr->suffix();
  }

  static weak_ptr_type const get_suffix(ptr_type const& edge_ptr)
  {
    return edge_ptr->suffix();
  }

  static void set_suffix(ptr_type const& edge_ptr, weak_ptr_type const& suffix)
  {
    edge_ptr->suffix() = suffix;
  }

  static bool is_root(ptr_type const& edge_ptr)
  {
    return edge_ptr->is_root();
  }

  static bool is_root_const(const_ptr_type const& edge_ptr)
  {
    return edge_ptr->is_root();
  }

  static bool is_leaf(ptr_type const& edge_ptr)
  {
    return edge_ptr->is_leaf();
  }

  static bool is_leaf_const(const_ptr_type const& edge_ptr)
  {
    return edge_ptr->is_leaf();
  }

  static boost::python::object const_weak_ptr_upgrade(const_weak_ptr_type const& weak_edge)
  {
    const_ptr_type edge_ptr = weak_edge.lock();

    if ( edge_ptr )
    {
        return boost::python::object( edge_ptr );
    }
    else
    {
      return boost::python::object();
    }
  }

  static boost::python::object weak_ptr_upgrade(weak_ptr_type const& weak_edge)
  {
    ptr_type edge_ptr = weak_edge.lock();

    if ( edge_ptr )
    {
      return boost::python::object( edge_ptr );
    }
    else
    {
      return boost::python::object();
    }
  }

  static const_weak_ptr_type const_ptr_downgrade(const_ptr_type const& edge_ptr)
  {
    return edge_ptr;
  }

  static weak_ptr_type ptr_downgrade(ptr_type const& edge_ptr)
  {
    return edge_ptr;
  }

  static std::size_t calculate_hash_const(const_ptr_type const& edge_ptr)
  {
    return boost::hash_value( edge_ptr );
  }

  static std::size_t calculate_hash(ptr_type const& edge_ptr)
  {
    return boost::hash_value( edge_ptr );
  }

  template< typename IteratorType >
  static PythonIterator< IteratorType > get_iterator(
    typename IteratorType::ptr_type const& root
    )
  {
    return PythonIterator< IteratorType >(
      IteratorType::begin( root ),
      IteratorType::end( root )
      )
      ;
  }

  static void wrap()
  {
    using namespace boost::python;

    class_< ptr_type >( "edge", no_init )
      .def( "root", edge_type::root )
      .staticmethod( "root" )
      .def( "branch", edge_type::branch, ( arg( "start" ), arg( "stop" ) ) )
      .staticmethod( "branch" )
      .def( "leaf", edge_type::leaf, ( arg( "start" ), arg( "length" ), arg( "label" ) ) )
      .staticmethod( "leaf" )
      .add_property( "start",get_start, set_start )
      .add_property( "stop", get_stop )
      .add_property( "label", get_suffix_label )
      .add_property( "parent", get_parent, set_parent )
      .add_property( "suffix", get_suffix, set_suffix )
      .def( "is_root", is_root )
      .def( "is_leaf", is_leaf )
      .def( "weakref", ptr_downgrade )
      .def( "is_empty", node_empty )
      .def( "__contains__", node_contains, arg( "key" ) )
      .def( "__getitem__", node_get_item, arg( "key" ) )
      .def( "__setitem__", node_set_item, ( arg( "key" ), arg( "value" ) ) )
      .def( "keys", node_keys )
      .def( self == self )
      .def( self != self )
      .def( self == other< const_ptr_type >() )
      .def( self != other< const_ptr_type >() )
      .def( "__hash__", calculate_hash )
      ;

    class_< weak_ptr_type >( "weak_edge", no_init )
      .def( "__call__", weak_ptr_upgrade )
      ;

    class_< const_ptr_type >( "const_edge", no_init )
      .def( "from_edge", to_const_ptr )
      .staticmethod( "from_edge" )
      .add_property( "start",get_start_const )
      .add_property( "stop", get_stop_const )
      .add_property( "label", get_suffix_label_const )
      .add_property( "parent", get_parent_const )
      .add_property( "suffix", get_suffix_const )
      .def( "is_leaf", is_leaf_const )
      .def( "is_root", is_root_const )
      .def( "weakref", const_ptr_downgrade )
      .def( "is_empty", node_empty_const )
      .def( "__contains__", node_contains_const, arg( "key" ) )
      .def( "__getitem__", node_get_item_const, arg( "key" ) )
      .def( "keys", node_keys_const )
      .def( self == self )
      .def( self != self )
      .def( self == other< ptr_type >() )
      .def( self != other< ptr_type >() )
      .def( "__hash__", calculate_hash_const )
      ;

    class_< const_weak_ptr_type >( "const_weak_edge", no_init )
      .def( "__call__", const_weak_ptr_upgrade )
      ;

    PythonIterator< iterator::PreOrder< edge_type > >::wrap( "preorder_iterator" );
    def(
      "preorder_iteration",
      get_iterator< iterator::PreOrder< edge_type > >,
      arg( "root" )
      );

    PythonIterator< iterator::PreOrder< edge_type const > >::wrap( "const_preorder_iterator" );
    def(
      "preorder_iteration",
      get_iterator< iterator::PreOrder< edge_type const > >,
      arg( "root" )
      );

    PythonIterator< iterator::PostOrder< edge_type > >::wrap( "postorder_iterator" );
    def(
      "postorder_iteration",
      get_iterator< iterator::PostOrder< edge_type > >,
      arg( "root" )
      );
    PythonIterator< iterator::PostOrder< edge_type const > >::wrap( "const_postorder_iterator" );
    def(
      "postorder_iteration",
      get_iterator< iterator::PostOrder< edge_type const > >,
      arg( "root" )
      );
  }
};

} // namespace python
} // namespace suffixtree
} // namespace scitbx

#endif // SUFFIXTREE_PYTHON_EDGE_EXPORTS_HPP_
