#include <iotbx/pdb/hierarchy_v2_atoms.h>

namespace iotbx { namespace pdb { namespace hierarchy_v2 { namespace atoms {

#define IOTBX_LOC(attr, attr_type) \
  af::shared<attr_type > \
  extract_##attr( \
    af::const_ref<atom> const& atoms) \
  { \
    af::shared<attr_type > result( \
      atoms.size(), af::init_functor_null<attr_type >()); \
    attr_type* r = result.begin(); \
    const hierarchy_v2::atom* atoms_end = atoms.end(); \
    for(const hierarchy_v2::atom* a=atoms.begin();a!=atoms_end;a++) { \
      *r++ = a->data->attr; \
    } \
    return result; \
  }

  IOTBX_LOC(xyz, vec3)
  IOTBX_LOC(sigxyz, vec3)
  IOTBX_LOC(occ, double)
  IOTBX_LOC(sigocc, double)
  IOTBX_LOC(b, double)
  IOTBX_LOC(sigb, double)
  IOTBX_LOC(uij, sym_mat3)
  IOTBX_LOC(siguij, sym_mat3)

#undef IOTBX_LOC

  af::shared<std::size_t>
  extract_hetero(
    af::const_ref<atom> const& atoms)
  {
    af::shared<std::size_t> result;
    const hierarchy_v2::atom* atoms_end = atoms.end();
    std::size_t i_seq = 0;
    for(const hierarchy_v2::atom* a=atoms.begin();a!=atoms_end;a++,i_seq++) {
      if (a->data->hetero) result.push_back(i_seq);
    }
    return result;
  }

  void
  reset_tmp(
    af::const_ref<atom> const& atoms,
    int first_value,
    int increment)
  {
    int value = first_value;
    for(const atom* a=atoms.begin();a!=atoms.end();a++) {
      a->data->tmp = value;
      value += increment;
    }
  }

  void
  reset_tmp_for_occupancy_groups_simple(
    af::const_ref<atom> const& atoms)
  {
    int value = 0;
    for(const atom* a=atoms.begin();a!=atoms.end();a++,value++) {
      a->data->tmp = (a->element_is_hydrogen() ? -1 : value);
    }
  }

}}}} // namespace iotbx::pdb::hierarchy_v2::atoms
