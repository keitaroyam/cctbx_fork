#ifndef CCTBX_SGTBX_FACET_COLLECTION_H
#define CCTBX_SGTBX_FACET_COLLECTION_H

//! \cond

#include <memory>
#include <iosfwd>

#include "cut.h"

namespace cctbx { namespace sgtbx { namespace asu {

  class facet_collection
  {
  public:
    typedef std::auto_ptr<facet_collection> pointer;

    virtual bool is_inside(const rvector3_t &p) const = 0;
    virtual pointer new_copy() const = 0;
    virtual pointer new_volume_only() const = 0;
    virtual size_type size() const = 0;
    virtual void change_basis(const change_of_basis_op &) =0;
    virtual void get_nth_plane(size_type i, cut &plane) const = 0;
    virtual void print(std::ostream &os) const = 0;

    virtual ~facet_collection() {};
  }; // class facet_collection

  typedef facet_collection::pointer (*asu_func)();

  extern asu_func asu_table[230];


}}}
//! \endcond

#endif

