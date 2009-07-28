#ifndef SCITBX_RIGID_BODY_TARDY_H
#define SCITBX_RIGID_BODY_TARDY_H

#include <boost/python/object.hpp>
#include <boost/python/extract.hpp>

#include <scitbx/rigid_body/body_lib.h>
#include <scitbx/rigid_body/featherstone.h>
#include <scitbx/array_family/selections.h>
#include <scitbx/optional_copy.h>
#include <vector>

namespace scitbx { namespace rigid_body { namespace tardy {

  template <typename ElementType>
  af::shared<ElementType>
  python_sequence_as_af_shared(
    boost::python::object const& seq)
  {
    namespace bp = boost::python;
    bp::ssize_t n = bp::len(seq);
    af::shared<ElementType>
      result((af::reserve(boost::numeric_cast<std::size_t>(n))));
    for(bp::ssize_t i=0;i<n;i++) {
      result.push_back(bp::extract<ElementType>(seq[i])());
    }
    return result;
  }

  template <typename FloatType>
  struct is_singular_revolute
  {
    typedef FloatType ft;

    vec3<ft> const& pivot;
    vec3<ft> axis;
    bool is_singular;

    is_singular_revolute(
      vec3<ft> const& normal_sites_0,
      vec3<ft> const& normal_sites_1,
      af::const_ref<vec3<ft> > const& body_sites,
      ft const& abs_cos_limit)
    :
      pivot(normal_sites_1),
      axis(pivot - normal_sites_0),
      is_singular(true)
    {
      ft axis_length = axis.length();
      if (axis_length != 0) {
        axis /= axis_length;
        for(std::size_t i=0;i<body_sites.size();i++) {
          vec3<ft> diff = body_sites[i] - pivot;
          ft diff_length = diff.length();
          if (diff_length != 0) {
            diff /= diff_length;
            ft abs_cos = axis * diff;
            if (abs_cos < abs_cos_limit) {
              is_singular = false;
              return;
            }
          }
        }
      }
    }
  };

  template <typename FloatType>
  af::shared<shared_ptr<body_t<FloatType> > >
  construct_bodies(
    af::const_ref<vec3<FloatType> > const& sites,
    af::const_ref<FloatType> const& masses,
    boost::python::object const& cluster_manager,
    FloatType const& near_singular_hinges_angular_tolerance_deg=5)
  {
    SCITBX_ASSERT(masses.size() == sites.size());
    namespace bp = boost::python;
    bp::object none;
    typedef FloatType ft;
    af::shared<shared_ptr<body_t<ft> > > result;
    ft abs_cos_limit = fn::absolute(std::cos(
      near_singular_hinges_angular_tolerance_deg * constants::pi_180));
    bp::object fvgci = cluster_manager.attr(
      "fixed_vertices_given_cluster_index_dict")();
    bp::object clusters = cluster_manager.attr("clusters");
    unsigned nc = boost::numeric_cast<unsigned>(bp::len(clusters));
    for(unsigned ic=0;ic<nc;ic++) {
      af::shared<unsigned>
        cluster = python_sequence_as_af_shared<unsigned>(clusters[ic]);
      af::shared<vec3<ft> >
        body_sites = af::select(sites, cluster.const_ref());
      af::shared<ft>
        body_masses = af::select(masses, cluster.const_ref());
      bp::object he = cluster_manager.attr("hinge_edges")[ic];
      SCITBX_ASSERT(bp::len(he) == 2);
      int he_0 = bp::extract<int>(he[0])();
      int he_1 = bp::extract<int>(he[1])();
      SCITBX_ASSERT(he_0 >= -1);
      SCITBX_ASSERT(he_1 >= 0);
      bp::object fixed_vertices_ = fvgci.attr("get")(ic);
      shared_ptr<body_t<ft> > body;
      if (fixed_vertices_.ptr() != none.ptr()) {
        af::shared<unsigned>
          fixed_vertices = python_sequence_as_af_shared<unsigned>(
            fixed_vertices_);
        if (   fixed_vertices.size() > 2
            || fixed_vertices.size() == cluster.size()) {
          body = shared_ptr<body_t<ft> >(new
            body_lib::zero_dof<ft>(
              body_sites.const_ref(),
              body_masses.const_ref()));
        }
        else if (fixed_vertices.size() == 1) {
          body = shared_ptr<body_t<ft> >(new
            body_lib::spherical<ft>(
              body_sites.const_ref(),
              body_masses.const_ref(),
              /*pivot*/ sites[fixed_vertices[0]]));
        }
        else if (fixed_vertices.size() == 2) {
          is_singular_revolute<ft> decision(
            /*normal_sites_0*/ sites[fixed_vertices[0]],
            /*normal_sites_1*/ sites[fixed_vertices[1]],
            body_sites.const_ref(),
            abs_cos_limit);
          if (decision.is_singular) {
            body = shared_ptr<body_t<ft> >(new
              body_lib::zero_dof<ft>(
                body_sites.const_ref(),
                body_masses.const_ref()));
          }
          else {
            body = shared_ptr<body_t<ft> >(new
              body_lib::revolute<ft>(
                body_sites.const_ref(),
                body_masses.const_ref(),
                decision.pivot,
                decision.axis));
          }
        }
        else {
          throw SCITBX_INTERNAL_ERROR(); // unreachable
        }
        body->parent = -1;
      }
      else if (he_0 == -1) {
        if (body_sites.size() == 1) {
          body = shared_ptr<body_t<ft> >(new
            body_lib::translational<ft>(
              body_sites.const_ref(),
              body_masses.const_ref()));
        }
        else {
          body = shared_ptr<body_t<ft> >(new
            body_lib::six_dof<ft>(
              body_sites.const_ref(),
              body_masses.const_ref()));
        }
        body->parent = -1;
      }
      else {
        vec3<ft> const& normal_sites_0 = sites[he_0];
        vec3<ft> const& normal_sites_1 = sites[he_1];
        body = shared_ptr<body_t<ft> >(new
          body_lib::revolute<ft>(
            body_sites.const_ref(),
            body_masses.const_ref(),
            /*pivot*/ normal_sites_1,
            /*normal*/ (normal_sites_1-normal_sites_0).normalize()));
        body->parent = bp::extract<int>(
          cluster_manager.attr("cluster_indices")[he_1])();
      }
      result.push_back(body);
    }
    return result;
  }

  template <typename FloatType=double>
  struct model : boost::noncopyable
  {
    typedef FloatType ft;

    // constructor arguments
    af::shared<std::string> labels;
    af::shared<vec3<ft> > sites;
    af::shared<ft> masses;
    boost::python::object tardy_tree;
    boost::python::object potential_obj;

    // set in constructor
    af::shared<shared_ptr<body_t<FloatType> > > bodies;
    unsigned degrees_of_freedom;

    // dynamically maintained
    protected:
      boost::optional<featherstone::system_model<ft> >
        featherstone_system_model_;
      boost::optional<std::vector<rotr3<ft> > > aja_array_;
      boost::optional<std::vector<mat3<ft> > > jar_array_;
      boost::optional<af::shared<vec3<ft> > > sites_moved_;
      boost::optional<ft> e_pot_;
      boost::optional<std::vector<vec3<ft> > > d_e_pot_d_sites_;
      boost::optional<std::vector<af::tiny<ft, 6> > > f_ext_array_;
      boost::optional<std::vector<af::small<ft, 6> > > qdd_array_;
      boost::optional<ft> e_kin_;
    public:

    unsigned
    bodies_size() const
    {
      return boost::numeric_cast<unsigned>(bodies.size());
    }

    model() {}

    model(
      af::shared<std::string> const& labels_,
      af::shared<vec3<ft> > const& sites_,
      af::shared<ft> const& masses_,
      boost::python::object const& tardy_tree_,
      boost::python::object const& potential_obj_,
      ft const& near_singular_hinges_angular_tolerance_deg=5)
    :
      labels(labels_),
      sites(sites_),
      masses(masses_),
      tardy_tree(tardy_tree_),
      potential_obj(potential_obj_),
      bodies(construct_bodies(
        sites.const_ref(),
        masses.const_ref(),
        tardy_tree.attr("cluster_manager"),
        near_singular_hinges_angular_tolerance_deg)),
      degrees_of_freedom(0)
    {
      unsigned nb = bodies_size();
      for(unsigned ib=0;ib<nb;ib++) {
        body_t<ft> const* body = bodies[ib].get();
        degrees_of_freedom += body->joint->degrees_of_freedom;
      }
      flag_positions_as_changed();
    }

    void
    flag_positions_as_changed()
    {
      featherstone_system_model_.reset();
      aja_array_.reset();
      jar_array_.reset();
      sites_moved_.reset();
      e_pot_.reset();
      d_e_pot_d_sites_.reset();
      f_ext_array_.reset();
      flag_velocities_as_changed();
    }

    void
    flag_velocities_as_changed()
    {
      qdd_array_.reset();
      e_kin_.reset();
    }

    af::shared<std::size_t>
    root_indices() const
    {
      af::shared<std::size_t> result;
      std::size_t nb = bodies.size();
      for(std::size_t ib=0;ib<nb;ib++) {
        body_t<ft> const* body = bodies[ib].get();
        if (body->parent == -1) {
          result.push_back(ib);
        }
      }
      return result;
    }

#define SCITBX_LOC(A, T) \
    af::shared<std::pair<unsigned, T> > \
    A##_in_each_tree() const \
    { \
      af::shared<std::pair<unsigned, T> > result; \
      unsigned nb = bodies_size(); \
      boost::scoped_array<T> accu(new T[nb]); \
      std::fill_n(accu.get(), nb, T(0)); \
      for(unsigned ib=nb;ib!=0;) { \
        ib--; \
        body_t<ft> const* body = bodies[ib].get(); \
        accu[ib] += body->A; \
        if (body->parent == -1) { \
          result.push_back(std::pair<unsigned, T>(ib, accu[ib])); \
        } \
        else { \
          accu[body->parent] += accu[ib]; \
        } \
      } \
      return result; \
    }

    SCITBX_LOC(number_of_sites, unsigned)
    SCITBX_LOC(sum_of_masses, ft)
#undef SCITBX_LOC

    boost::optional<vec3<ft> >
    mean_linear_velocity(
      af::const_ref<std::pair<unsigned, unsigned> >
        number_of_sites_in_each_tree) const
    {
      vec3<ft> sum_v(0,0,0);
      unsigned sum_n = 0;
#define SCITBX_LOC \
      optional_copy<af::shared<std::pair<unsigned, unsigned> > > nosiet; \
      if (number_of_sites_in_each_tree.begin() == 0) { \
        nosiet = this->number_of_sites_in_each_tree(); \
        number_of_sites_in_each_tree = nosiet->const_ref(); \
      } \
      SCITBX_ASSERT(number_of_sites_in_each_tree.size() == bodies.size()); \
      unsigned nb = bodies_size(); \
      for( \
        std::pair<unsigned, unsigned> const* nosiet_it=nosiet->begin(); \
        nosiet_it!=nosiet->end(); \
        nosiet_it++) \
      { \
        unsigned ib = nosiet_it->first; \
        SCITBX_ASSERT(ib < nb);
SCITBX_LOC
        body_t<ft> const* body = bodies[ib].get();
        boost::optional<vec3<ft> >
          v = body->joint->get_linear_velocity(body->qd());
        if (!v) continue;
        unsigned n = nosiet_it->second;
        sum_v += (*v) * boost::numeric_cast<ft>(n);
        sum_n += n;
      }
      if (sum_n == 0) {
        return boost::optional<vec3<ft> >();
      }
      return boost::optional<vec3<ft> >(
        sum_v / boost::numeric_cast<ft>(sum_n));
    }

    void
    subtract_from_linear_velocities(
      af::const_ref<std::pair<unsigned, unsigned> >
        number_of_sites_in_each_tree,
      vec3<ft> const& value)
    {
SCITBX_LOC
#undef SCITBX_LOC
        body_t<ft>* body = bodies[ib].get();
        boost::optional<vec3<ft> >
          v = body->joint->get_linear_velocity(body->qd());
        if (!v) continue;
        body->set_qd(
          body->joint->new_linear_velocity(body->qd(), (*v)-value));
      }
    }

    featherstone::system_model<ft>&
    featherstone_system_model()
    {
      if (!featherstone_system_model_) {
        featherstone_system_model_ = featherstone::system_model<ft>(bodies);
      }
      return *featherstone_system_model_;
    }

    std::vector<rotr3<ft> > const&
    aja_array()
    {
      if (!aja_array_) {
        unsigned nb = bodies_size();
        aja_array_ = std::vector<rotr3<ft> >();
        aja_array_->reserve(nb);
        for(std::size_t ib=0;ib<nb;ib++) {
          body_t<ft> const* body = bodies[ib].get();
          rotr3<ft>
            aja = body->alignment->cb_b0
                * body->joint->cb_sp
                * body->alignment->cb_0b;
          if (body->parent != -1) {
            aja = (*aja_array_)[body->parent] * aja;
          }
          aja_array_->push_back(aja);
        }
      }
      return *aja_array_;
    }

    std::vector<mat3<ft> > const&
    jar_array()
    {
      if (!jar_array_) {
        aja_array();
        unsigned nb = bodies_size();
        jar_array_ = std::vector<mat3<ft> >();
        jar_array_->reserve(nb);
        for(std::size_t ib=0;ib<nb;ib++) {
          body_t<ft> const* body = bodies[ib].get();
          mat3<ft> jar = body->joint->cb_ps.r * body->alignment->cb_0b.r;
          if (body->parent != -1) {
            jar = jar * (*aja_array_)[body->parent].r.transpose();
          }
          jar_array_->push_back(jar);
        }
      }
      return *jar_array_;
    }
  };

}}} // namespace scitbx::rigid_body::tardy

#endif // GUARD
