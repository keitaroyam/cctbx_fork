#include <boost_adaptbx/graph/graph_type.hpp>
#include <boost_adaptbx/graph/graph_export_adaptor.hpp>
#include <boost_adaptbx/graph/maximum_clique_rascal.hpp>

#include <boost_adaptbx/exporting.hpp>

#include <boost/python/module.hpp>
#include <boost/python/list.hpp>
#include <boost/python/extract.hpp>
#include <boost/python/def.hpp>
#include <boost/python/stl_iterator.hpp>

#include <boost/graph/graph_traits.hpp>
#include <boost/property_map/property_map.hpp>
#include <boost/iterator/transform_iterator.hpp>

#include <boost/mpl/if.hpp>
#include <boost/type_traits.hpp>

#include <map>
#include <vector>

namespace boost_adaptbx
{

template< typename Graph >
class python_callback_adaptor
{
public:
  typedef boost::graph_traits< Graph > graph_traits;
  typedef typename graph_traits::vertex_descriptor vertex_descriptor;
  typedef graph_export_adaptor::vertex_descriptor_converter< vertex_descriptor > converter;

private:
  boost::python::object m_callable;

public:

python_callback_adaptor(boost::python::object callable)
  : m_callable( callable )
{}

~python_callback_adaptor()
{}

template< typename InputIterator >
void operator()(InputIterator begin, InputIterator end)
{
  boost::python::list result;

  for (; begin != end; ++begin)
  {
    result.append( converter::forward( *begin ) );
  }

  m_callable( result );
}
};

template< typename Graph >
class python_component_adaptor
{
public:
  typedef boost::graph_traits< Graph > graph_traits;
  typedef typename graph_traits::vertex_descriptor vertex_descriptor;
  typedef typename graph_traits::vertices_size_type vertices_size_type;
  typedef graph_export_adaptor::vertex_descriptor_converter< vertex_descriptor > converter;

private:
  boost::python::object m_callable;

public:
  python_component_adaptor(boost::python::object callable)
    : m_callable( callable )
  {}

  template< typename Partition >
  vertices_size_type operator ()(Graph const& graph, Partition const& partition) const
  {
    typedef typename Partition::value_type vertex_group_type;

    boost::python::list py_partition;

    for (
      typename Partition::const_iterator pit = partition.begin();
      pit != partition.end();
      ++pit
      )
    {
      boost::python::list vgroup;

      for (
        typename vertex_group_type::const_iterator vgit = pit->begin();
        vgit != pit->end();
        ++vgit
        )
        {
          vgroup.append( converter::forward( *vgit ) );
        }

      py_partition.append( vgroup );
    }

    return boost::python::extract< vertices_size_type >( m_callable( graph, py_partition ) );
  }
};

template< typename Graph >
struct maximum_clique_rascal_export
{
  typedef boost::graph_traits< Graph > graph_traits;
  typedef typename graph_traits::vertex_descriptor vertex_descriptor;
  typedef typename graph_traits::vertices_size_type vertices_size_type;
  typedef std::map< vertex_descriptor, vertices_size_type > component_map_type;
  typedef boost::associative_property_map< component_map_type >
    component_property_map_type;
  typedef std::map< vertex_descriptor, boost::default_color_type > color_map_type;
  typedef boost::associative_property_map< color_map_type >
    color_property_map_type;
  typedef graph_export_adaptor::vertex_descriptor_converter< vertex_descriptor > converter;
  typedef graph_export_adaptor::vertex_descriptor_backconverter< vertex_descriptor > backconverter;
  typedef boost::python::stl_input_iterator< typename converter::result_type > py_vertex_descriptor_iterator;
  typedef boost::transform_iterator< backconverter, py_vertex_descriptor_iterator > py_vertex_iterator;

  static void maximum_clique_rascal_1(
    Graph const& graph,
    boost::python::object callable
    )
  {
    boost_adaptbx::graph::maximum_clique_rascal(
      graph,
      boost_adaptbx::graph::initial_partition_by_vertex_coloring(),
      boost_adaptbx::graph::upper_bound_by_chromatic_number(),
      python_callback_adaptor< Graph >( callable )
      );
  }

  static void maximum_clique_rascal_2(
    Graph const& graph,
    boost::python::object upper_bound,
    boost::python::object callable
    )
  {
    boost_adaptbx::graph::maximum_clique_rascal(
      graph,
      boost_adaptbx::graph::initial_partition_by_vertex_coloring(),
      python_component_adaptor< Graph >( upper_bound ),
      python_callback_adaptor< Graph >( callable )
      );
  }

  static void selected_subgraph(
    Graph const& graph,
    Graph& subgraph,
    boost::python::object iterable
    )
  {
    boost_adaptbx::graph::selected_subgraph(
      graph,
      subgraph,
      py_vertex_iterator(
        py_vertex_descriptor_iterator( iterable ),
        backconverter()
        ),
      py_vertex_iterator(
        py_vertex_descriptor_iterator(),
        backconverter()
        )
      );
  }

  static void process()
  {
    using namespace boost::python;

    def( "rascal", maximum_clique_rascal_1, ( arg( "graph" ), arg( "callable" ) ) );
    def(
      "rascal",
      maximum_clique_rascal_2,
      ( arg( "graph" ), arg( "upper_bound" ), arg( "callable" ) )
      );
    def(
      "selected_subgraph",
      selected_subgraph,
      ( arg( "graph" ), arg( "subgraph" ), arg( "iterable" ) )
      );
  }

};

struct maximum_clique_exporter
{
  template< typename Export >
  void operator ()(boost::mpl::identity< Export > myexport) const
  {
    typedef typename Export::first graph_type;
    typedef typename Export::second name_type;

    typedef boost::graph_traits< graph_type > graph_traits;
    typedef typename boost::mpl::if_<
      boost::is_same<
        typename  graph_traits::directed_category,
        boost::undirected_tag
        >,
      maximum_clique_rascal_export< graph_type >,
      graph_export_adaptor::no_export< graph_type >
      >::type exporter_type;
    exporter_type::process();
  }
};

} // namespace boost_adaptbx

BOOST_PYTHON_MODULE(boost_adaptbx_graph_maximum_clique_ext)
{
  boost_adaptbx::exporting::class_list<
    boost_adaptbx::graph_type::exports,
    boost_adaptbx::maximum_clique_exporter
    >::process();
}
