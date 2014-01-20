#include <boost_adaptbx/graph/graph_type.hpp>
#include <boost_adaptbx/graph/graph_export_adaptor.hpp>

#include <boost_adaptbx/exporting.hpp>

#include <boost/python/module.hpp>
#include <boost/python/def.hpp>

#include <boost/graph/graph_traits.hpp>
#include <boost/property_map/property_map.hpp>
#include <boost/graph/breadth_first_search.hpp>

#include <boost/ref.hpp>

#include <map>
#include <vector>

namespace boost_adaptbx
{
namespace
{

template< typename Graph >
class bfs_visitor_adaptor
{
public:
  typedef Graph graph_type;
  typedef boost::graph_traits< graph_type > graph_traits;
  typedef typename graph_traits::vertex_descriptor vertex_descriptor;
  typedef typename graph_traits::edge_descriptor edge_descriptor;
  typedef graph_export_adaptor::vertex_descriptor_converter< vertex_descriptor > converter;

private:
  boost::python::object m_visitor;

public:
  explicit bfs_visitor_adaptor(boost::python::object visitor) : m_visitor( visitor ) {};
  ~bfs_visitor_adaptor() {};

  void call_python_method(const char* name, edge_descriptor e, Graph const& g)
  {
    boost::python::object attr = m_visitor.attr( name );
    attr(e, boost::cref( g ) );
  }

  void call_python_method(const char* name, vertex_descriptor v, Graph const& g)
  {
    boost::python::object attr = m_visitor.attr( name );
    attr(converter::forward( v ), boost::cref( g ) );
  }

  void initialize_vertex(vertex_descriptor v, Graph const& g)
  {
    call_python_method( "initialize_vertex", v, g );
  }

  void discover_vertex(vertex_descriptor v, Graph const& g)
  {
    call_python_method( "discover_vertex", v, g );
  }

  void examine_vertex(vertex_descriptor v, Graph const& g)
  {
    call_python_method( "examine_vertex", v, g );
  }

  void finish_vertex(vertex_descriptor v, Graph const& g)
  {
    call_python_method( "finish_vertex", v, g );
  }

  void examine_edge(edge_descriptor v, Graph const& g)
  {
    call_python_method( "examine_edge", v, g );
  }

  void tree_edge(edge_descriptor v, Graph const& g)
  {
    call_python_method( "tree_edge", v, g );
  }

  void non_tree_edge(edge_descriptor v, Graph const& g)
  {
    call_python_method( "non_tree_edge", v, g );
  }

  void gray_target(edge_descriptor v, Graph const& g)
  {
    call_python_method( "gray_target", v, g );
  }

  void black_target(edge_descriptor v, Graph const& g)
  {
    call_python_method( "black_target", v, g );
  }
};

template< typename Graph >
struct breadth_first_search_export
{
  typedef Graph graph_type;
  typedef boost::graph_traits< graph_type > graph_traits;
  typedef typename graph_traits::vertex_descriptor vertex_descriptor;
  typedef std::map< vertex_descriptor, boost::default_color_type > color_map_type;
  typedef boost::associative_property_map< color_map_type >
    color_property_map_type;
  typedef graph_export_adaptor::vertex_descriptor_converter< vertex_descriptor > converter;

  static void breadth_first_search(
    graph_type const& graph,
    typename converter::type vertex,
    boost::python::object vis
    )
  {
    using namespace boost;
    color_map_type color_map;
    boost::breadth_first_search(
      graph,
      converter::backward( vertex ),
      visitor( bfs_visitor_adaptor< graph_type >( vis ) ).
      color_map( color_property_map_type( color_map ) )
      );
  }

  static void process()
  {
    using namespace boost::python;

    def(
      "breadth_first_search",
      breadth_first_search,
      ( arg( "graph" ), arg( "vertex" ), arg( "visitor" ) )
      );
  }
};

template< typename EdgeList, typename VertexProperty, typename EdgeProperty >
struct breadth_first_search_export<
  boost::adjacency_list< EdgeList, boost::vecS, boost::undirectedS, VertexProperty, EdgeProperty >
  >
{
  typedef boost::adjacency_list< EdgeList, boost::vecS, boost::undirectedS, VertexProperty, EdgeProperty > graph_type;
  typedef boost::graph_traits< graph_type > graph_traits;
  typedef typename graph_traits::vertex_descriptor vertex_descriptor;

  static void breadth_first_search(
    graph_type const& graph,
    vertex_descriptor vertex,
    boost::python::object vis
    )
  {
    using namespace boost;
    boost::breadth_first_search(
      graph,
      vertex,
      visitor( bfs_visitor_adaptor< graph_type >( vis ) )
      );
  }

  static void process()
  {
    using namespace boost::python;

    def(
      "breadth_first_search",
      breadth_first_search,
      ( arg( "graph" ), arg( "vertex" ), arg( "visitor" ) )
      );
  }
};

struct bfs_exporter
{
  template< typename Export >
  void operator ()(boost::mpl::identity< Export > myexport) const
  {
    typedef typename Export::first graph_type;
    typedef typename Export::second name_type;

    breadth_first_search_export< graph_type >::process();
  }
};

} // namespace <anonymous>
} // namespace boost_adaptbx

BOOST_PYTHON_MODULE(boost_adaptbx_graph_breadth_first_search_ext)
{
  boost_adaptbx::exporting::class_list<
    boost_adaptbx::graph_type::exports,
    boost_adaptbx::bfs_exporter
    >::process();
}
