#include <cctbx/boost_python/flex_fwd.h>

#include <boost/python/module.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <boost/python/overloads.hpp>
#include <boost/python/tuple.hpp>
#include <scitbx/boost_python/stl_map_as_dict.h>
#include <scitbx/boost_python/array_as_list.h>
#include <cStringIO.h>
#include <iotbx/pdb/hierarchy_atoms.h>
#include <iotbx/pdb/hierarchy_bpl.h>

namespace iotbx { namespace pdb { namespace hierarchy {

void atom_bpl_wrap();
namespace atoms { void bpl_wrap(); }

namespace {

  struct cstringio_write : stream_write
  {
    PyObject* sio;

    cstringio_write(PyObject* sio_) : sio(sio_) {}

    virtual void
    operator()(const char* s, unsigned n)
    {
      PycStringIO->cwrite(
        sio,
#if PY_VERSION_HEX >= 0x02050000
        s,
#else
        const_cast<char*>(s),
#endif
        static_cast<boost::python::ssize_t>(n));
    }
  };

#define IOTBX_PDB_HIERARCHY_GET_CHILDREN(parent_t, child_t, method) \
  static \
  boost::python::list \
  get_##method(parent_t const& parent) \
  { \
    boost::python::list result; \
    std::vector<child_t> const& children = parent.method(); \
    unsigned n = static_cast<unsigned>(children.size()); \
    for(unsigned i=0;i<n;i++) result.append(children[i]); \
    return result; \
  }

#define IOTBX_PDB_HIERARCHY_DEF_APPEND_ETC(C) \
        .def(#C "s", get_##C##s) \
        .def(#C "s_size", &w_t::C##s_size) \
        .def("find_" #C "_index", &w_t::find_##C##_index, \
          find_##C##_index_overloads(( \
            arg_(#C), arg_("must_be_present")=false))) \
        .def("pre_allocate_" #C "s", &w_t::pre_allocate_##C##s, \
          (arg_("number_of_additional_" #C "s"))) \
        .def("insert_" #C, &w_t::insert_##C, (arg_("i"), arg_(#C))) \
        .def("append_" #C, &w_t::append_##C, (arg_(#C))) \
        .def("remove_" #C, \
          (void(w_t::*)(long)) &w_t::remove_##C, (arg_("i"))) \
        .def("remove_" #C, \
          (void(w_t::*)(C&)) &w_t::remove_##C, (arg_(#C)))

  template <typename ElementType>
  af::shared<ElementType>
  std_vector_as_af_shared(
    std::vector<ElementType> const& v)
  {
    if (v.size() == 0) return af::shared<ElementType>();
    return af::shared<ElementType>(&*v.begin(), &*v.end());
  }

  struct atom_group_wrappers
  {
    typedef atom_group w_t;

    IOTBX_PDB_HIERARCHY_DATA_WRAPPERS_SMALL_STR_GET_SET(altloc)
    IOTBX_PDB_HIERARCHY_DATA_WRAPPERS_SMALL_STR_GET_SET(resname)

    static
    af::shared<atom>
    get_atoms(w_t const& self)
    {
      return std_vector_as_af_shared(self.atoms());
    }

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      find_atom_index_overloads, find_atom_index, 1, 2)

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("atom_group", no_init)
        .def(init<
          residue_group const&,
            optional<const char*, const char*> >((
              arg_("parent"), arg_("altloc")="", arg_("resname")="")))
        .def(init<
          optional<const char*, const char*> >((
            arg_("altloc")="", arg_("resname")="")))
        .def(init<residue_group const&, atom_group const&>((
          arg_("parent"), arg_("other"))))
        .add_property("altloc",
          make_function(get_altloc), make_function(set_altloc))
        .add_property("resname",
          make_function(get_resname), make_function(set_resname))
        .def("detached_copy", &w_t::detached_copy)
        .def("memory_id", &w_t::memory_id)
        .def("parent", get_parent<atom_group, residue_group>::wrapper)
        IOTBX_PDB_HIERARCHY_DEF_APPEND_ETC(atom)
        .def("confid", &w_t::confid)
      ;
    }
  };

  struct residue_group_wrappers
  {
    typedef residue_group w_t;

    IOTBX_PDB_HIERARCHY_DATA_WRAPPERS_SMALL_STR_GET_SET(resseq)
    IOTBX_PDB_HIERARCHY_DATA_WRAPPERS_SMALL_STR_GET_SET(icode)

    static bool
    get_link_to_previous(w_t const& self)
    {
      return self.data->link_to_previous;
    }

    static void
    set_link_to_previous(w_t const& self, bool new_link_to_previous)
    {
      self.data->link_to_previous = new_link_to_previous;
    }

    IOTBX_PDB_HIERARCHY_GET_CHILDREN(residue_group, atom_group, atom_groups)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      find_atom_group_index_overloads, find_atom_group_index, 1, 2)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(atoms_overloads, atoms, 0, 1)

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("residue_group", no_init)
        .def(init<chain const&, optional<const char*, const char*, bool> >((
          arg_("parent"),
          arg_("resseq")="", arg_("icode")="", arg_("link_to_previous")=true)))
        .def(init<optional<const char*, const char*, bool> >((
          arg_("resseq")="", arg_("icode")="", arg_("link_to_previous")=true)))
        .def(init<chain const&, residue_group const&>((
          arg_("parent"), arg_("other"))))
        .add_property("resseq",
          make_function(get_resseq), make_function(set_resseq))
        .add_property("icode",
          make_function(get_icode), make_function(set_icode))
        .add_property("link_to_previous",
          make_function(get_link_to_previous),
          make_function(set_link_to_previous))
        .def("detached_copy", &w_t::detached_copy)
        .def("memory_id", &w_t::memory_id)
        .def("parent", get_parent<residue_group, chain>::wrapper)
        IOTBX_PDB_HIERARCHY_DEF_APPEND_ETC(atom_group)
        .def("atoms_size", &w_t::atoms_size)
        .def("atoms", &w_t::atoms, atoms_overloads((
          arg_("interleaved_conf")=0)))
        .def("resid", &w_t::resid)
        .def("have_conformers", &w_t::have_conformers)
        .def("merge_atom_groups", &w_t::merge_atom_groups, (
          arg_("primary"), arg_("secondary")))
        .def("move_blank_altloc_atom_groups_to_front",
          &w_t::move_blank_altloc_atom_groups_to_front)
        .def("edit_blank_altloc", &w_t::edit_blank_altloc)
        .def("is_identical_hierarchy", &w_t::is_identical_hierarchy, (
          arg_("other")))
        .def("is_similar_hierarchy", &w_t::is_similar_hierarchy, (
          arg_("other")))
      ;
    }
  };

  struct chain_wrappers
  {
    typedef chain w_t;

    static std::string
    get_id(w_t const& self) { return self.data->id; }

    static void
    set_id(w_t const& self, std::string const& new_id)
    {
      self.data->id = new_id;
    }

    IOTBX_PDB_HIERARCHY_GET_CHILDREN(chain, residue_group, residue_groups)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      find_residue_group_index_overloads, find_residue_group_index, 1, 2)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      find_pure_altloc_ranges_overloads, find_pure_altloc_ranges, 0, 1)

    static
    boost::python::object
    conformers(
      w_t const& self)
    {
      af::shared<conformer> result = self.conformers();
      return scitbx::boost_python::array_as_list(
        result.begin(), result.size());
    }

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(atoms_overloads, atoms, 0, 1)

    static void
    write_atom_record_groups(
      w_t const& self,
      boost::python::object cstringio,
      int interleaved_conf=0,
      bool atom_hetatm=true,
      bool sigatm=true,
      bool anisou=true,
      bool siguij=true)
    {
      if (!PycStringIO_OutputCheck(cstringio.ptr())) {
        throw std::invalid_argument(
          "cstringio argument must be a cStringIO.StringIO instance.");
      }
      cstringio_write write(cstringio.ptr());
      atom_label_columns_formatter label_formatter;
      label_formatter.chain_id = self.data->id.c_str();
      residue_groups_as_pdb_string(
        write,
        label_formatter,
        self.residue_groups(),
        interleaved_conf,
        atom_hetatm, sigatm, anisou, siguij);
    }

    BOOST_PYTHON_FUNCTION_OVERLOADS(
      write_atom_record_groups_overloads, write_atom_record_groups, 2, 7)

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("chain", no_init)
        .def(init<model const&, optional<std::string const&> >((
          arg_("parent"), arg_("id")="")))
        .def(init<std::string const&>((
          arg_("id")="")))
        .def(init<model const&, chain const&>((
          arg_("parent"), arg_("other"))))
        .add_property("id", make_function(get_id), make_function(set_id))
        .def("detached_copy", &w_t::detached_copy)
        .def("memory_id", &w_t::memory_id)
        .def("parent", get_parent<chain, model>::wrapper)
        IOTBX_PDB_HIERARCHY_DEF_APPEND_ETC(residue_group)
        .def("atoms_size", &w_t::atoms_size)
        .def("atoms", &w_t::atoms, atoms_overloads((
          arg_("interleaved_conf")=0)))
        .def("merge_residue_groups", &w_t::merge_residue_groups, (
          arg_("primary"), arg_("secondary")))
        .def("merge_disconnected_residue_groups_with_pure_altloc",
          &w_t::merge_disconnected_residue_groups_with_pure_altloc)
        .def("find_pure_altloc_ranges", &w_t::find_pure_altloc_ranges,
          find_pure_altloc_ranges_overloads((
            arg_("common_residue_name_class_only")=0)))
        .def("conformers", conformers)
        .def("is_identical_hierarchy", &w_t::is_identical_hierarchy, (
          arg_("other")))
        .def("is_similar_hierarchy", &w_t::is_similar_hierarchy, (
          arg_("other")))
        .def("write_atom_record_groups", write_atom_record_groups,
          write_atom_record_groups_overloads((
          arg_("self"),
          arg_("cstringio"),
          arg_("interleaved_conf")=0,
          arg_("atom_hetatm")=true,
          arg_("sigatm")=true,
          arg_("anisou")=true,
          arg_("siguij")=true)))
      ;
    }
  };

  struct model_wrappers
  {
    typedef model w_t;

    static std::string
    get_id(w_t const& self) { return self.data->id; }

    static void
    set_id(w_t const& self, std::string const& new_id)
    {
      self.data->id = new_id;
    }

    IOTBX_PDB_HIERARCHY_GET_CHILDREN(model, chain, chains)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      find_chain_index_overloads, find_chain_index, 1, 2)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(atoms_overloads, atoms, 0, 1)

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("model", no_init)
        .def(init<root const&, optional<std::string> >((
          arg_("parent"), arg_("id")="")))
        .def(init<std::string>((arg_("id")="")))
        .def(init<root const&, model const&>((
          arg_("parent"), arg_("other"))))
        .add_property("id", make_function(get_id), make_function(set_id))
        .def("detached_copy", &w_t::detached_copy)
        .def("memory_id", &w_t::memory_id)
        .def("parent", get_parent<model, root>::wrapper)
        IOTBX_PDB_HIERARCHY_DEF_APPEND_ETC(chain)
        .def("atoms_size", &w_t::atoms_size)
        .def("atoms", &w_t::atoms, atoms_overloads((
          arg_("interleaved_conf")=0)))
        .def("is_identical_hierarchy", &w_t::is_identical_hierarchy, (
          arg_("other")))
        .def("is_similar_hierarchy", &w_t::is_similar_hierarchy, (
          arg_("other")))
        .def("transfer_chains_from_other", &w_t::transfer_chains_from_other, (
          arg_("other")))
      ;
    }
  };

  struct root_wrappers
  {
    typedef root w_t;

    static af::shared<std::string>
    get_info(w_t const& self) { return self.data->info; }

    static void
    set_info(w_t const& self, af::shared<std::string> const& new_info)
    {
      self.data->info = new_info;
    }

    IOTBX_PDB_HIERARCHY_GET_CHILDREN(root, model, models)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      find_model_index_overloads, find_model_index, 1, 2)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(atoms_overloads, atoms, 0, 1)

    static void
    as_pdb_string_cstringio(
      w_t const& self,
      boost::python::object cstringio,
      bool append_end=false,
      int interleaved_conf=0,
      boost::optional<int>
        atoms_reset_serial_first_value=boost::optional<int>(),
      bool atom_hetatm=true,
      bool sigatm=true,
      bool anisou=true,
      bool siguij=true)
    {
      if (!PycStringIO_OutputCheck(cstringio.ptr())) {
        throw std::invalid_argument(
          "cstringio argument must be a cStringIO.StringIO instance.");
      }
      if (atoms_reset_serial_first_value) {
        atoms::reset_serial(
          self.atoms(interleaved_conf).const_ref(),
          *atoms_reset_serial_first_value);
      }
      cstringio_write write(cstringio.ptr());
      models_as_pdb_string(
        write,
        self.models(),
        append_end,
        interleaved_conf,
        atom_hetatm,
        sigatm,
        anisou,
        siguij);
    }

    BOOST_PYTHON_FUNCTION_OVERLOADS(
      as_pdb_string_cstringio_overloads, as_pdb_string_cstringio, 2, 9)

    BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(
      write_pdb_file_overloads, write_pdb_file, 1, 9)

    static void
    get_overall_counts(
      w_t const& self,
      boost::python::object result)
    {
      using scitbx::boost_python::array_as_list;
      using scitbx::boost_python::stl_map_as_dict;
#define IOTBX_LOC_SA(N) \
      result.attr(#N) = oc.N;
      //
#define IOTBX_LOC_SAA(N) \
      result.attr(#N) = array_as_list(oc.N.begin(), oc.N.size());
      //
#define IOTBX_LOC_SAM(N) \
      result.attr(#N) = stl_map_as_dict(oc.N);
      //
#define IOTBX_LOC_SAO(N) \
      { \
        boost::python::object v; \
        if (oc.N) v = boost::python::object(*oc.N); \
        result.attr(#N) = v; \
      }
      //
      hierarchy::overall_counts oc(self);
      IOTBX_LOC_SA(root)
      IOTBX_LOC_SA(n_empty_models)
      IOTBX_LOC_SA(n_empty_chains)
      IOTBX_LOC_SA(n_empty_residue_groups)
      IOTBX_LOC_SA(n_empty_atom_groups)
      IOTBX_LOC_SA(n_duplicate_model_ids)
      IOTBX_LOC_SA(n_duplicate_chain_ids)
      IOTBX_LOC_SA(n_duplicate_atom_labels)
      IOTBX_LOC_SAA(duplicate_atom_labels)
      IOTBX_LOC_SA(n_models)
      IOTBX_LOC_SA(n_chains)
      IOTBX_LOC_SA(n_alt_conf)
      IOTBX_LOC_SA(n_residues)
      IOTBX_LOC_SA(n_residue_groups)
      IOTBX_LOC_SA(n_explicit_chain_breaks)
      IOTBX_LOC_SA(n_atoms)
      IOTBX_LOC_SA(n_anisou)
      IOTBX_LOC_SAM(model_ids)
      IOTBX_LOC_SAM(chain_ids)
      IOTBX_LOC_SAM(alt_conf_ids)
      IOTBX_LOC_SAM(resnames)
      IOTBX_LOC_SAM(resname_classes)
      IOTBX_LOC_SAM(element_charge_types)
      IOTBX_LOC_SA(n_alt_conf_none)
      IOTBX_LOC_SA(n_alt_conf_pure)
      IOTBX_LOC_SA(n_alt_conf_proper)
      IOTBX_LOC_SA(n_alt_conf_improper)
      IOTBX_LOC_SAO(alt_conf_proper)
      IOTBX_LOC_SAO(alt_conf_improper)
      {
        boost::python::list l;
        std::size_t n = oc.consecutive_residue_groups_with_same_resid.size();
        for(std::size_t i=0;i<n;i++) {
          af::tiny<residue_group, 2> const&
            rgs = oc.consecutive_residue_groups_with_same_resid[i];
          l.append(boost::python::make_tuple(rgs[0], rgs[1]));
        }
        result.attr("consecutive_residue_groups_with_same_resid") = l;
      }
      IOTBX_LOC_SA(n_chains_with_mix_of_proper_and_improper_alt_conf)
      IOTBX_LOC_SAA(residue_groups_with_multiple_resnames_using_same_altloc)
      //
#undef IOTBX_LOC_SA
#undef IOTBX_LOC_SAA
#undef IOTBX_LOC_SAM
#undef IOTBX_LOC_SAO
    }

    static void
    get_atom_selection_cache(
      w_t const& self,
      boost::python::object result)
    {
      atom_selection_cache asc(self);
#define IOTBX_LOC(A) \
      result.attr(#A) = asc.A;
      IOTBX_LOC(n_seq)
      IOTBX_LOC(name)
      IOTBX_LOC(altloc)
      IOTBX_LOC(resname)
      IOTBX_LOC(chain_id)
      IOTBX_LOC(resseq)
      IOTBX_LOC(icode)
      IOTBX_LOC(resid)
      IOTBX_LOC(segid)
      IOTBX_LOC(model_id)
      IOTBX_LOC(element)
      IOTBX_LOC(charge)
      IOTBX_LOC(anisou)
#undef IOTBX_LOC
    }

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("root", no_init)
        .def(init<>())
        .add_property("info", make_function(get_info), make_function(set_info))
        .def("deep_copy", &w_t::deep_copy)
        .def("memory_id", &w_t::memory_id)
        IOTBX_PDB_HIERARCHY_DEF_APPEND_ETC(model)
        .def("atoms_size", &w_t::atoms_size)
        .def("atoms", &w_t::atoms, atoms_overloads((
          arg_("interleaved_conf")=0)))
        .def("is_similar_hierarchy", &w_t::is_similar_hierarchy, (
          arg_("other")))
        .def("as_pdb_string_cstringio", as_pdb_string_cstringio,
          as_pdb_string_cstringio_overloads((
            arg_("self"),
            arg_("cstringio"),
            arg_("append_end")=false,
            arg_("interleaved_conf")=0,
            arg_("atoms_reset_serial_first_value")=boost::optional<int>(),
            arg_("atom_hetatm")=true,
            arg_("sigatm")=true,
            arg_("anisou")=true,
            arg_("siguij")=true)))
        .def("write_pdb_file", &w_t::write_pdb_file, write_pdb_file_overloads((
          arg_("file_name"),
          arg_("open_append")=false,
          arg_("append_end")=false,
          arg_("interleaved_conf")=0,
          arg_("atoms_reset_serial_first_value")=boost::optional<int>(),
          arg_("atom_hetatm")=true,
          arg_("sigatm")=true,
          arg_("anisou")=true,
          arg_("siguij")=true)))
        .def("get_overall_counts", get_overall_counts)
        .def("get_atom_selection_cache", get_atom_selection_cache)
      ;
    }
  };

  struct residue_wrappers
  {
    typedef residue w_t;

    IOTBX_PDB_HIERARCHY_DATA_WRAPPERS_SMALL_STR_GET(resname)
    IOTBX_PDB_HIERARCHY_DATA_WRAPPERS_SMALL_STR_GET(resseq)
    IOTBX_PDB_HIERARCHY_DATA_WRAPPERS_SMALL_STR_GET(icode)

    static bool
    get_link_to_previous(w_t const& self)
    {
      return self.data->link_to_previous;
    }

    static bool
    get_is_pure_main_conf(w_t const& self)
    {
      return self.data->is_pure_main_conf;
    }

    static
    af::shared<atom>
    get_atoms(w_t const& self)
    {
      return std_vector_as_af_shared(self.atoms());
    }

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("residue", no_init)
        .add_property("resname", make_function(get_resname))
        .add_property("resseq", make_function(get_resseq))
        .add_property("icode", make_function(get_icode))
        .add_property("link_to_previous", make_function(get_link_to_previous))
        .add_property("is_pure_main_conf",make_function(get_is_pure_main_conf))
        .def("memory_id", &w_t::memory_id)
        .def("parent", get_parent<residue, conformer>::wrapper)
        .def("atoms_size", &w_t::atoms_size)
        .def("atoms", get_atoms)
        .def("resid", &w_t::resid)
      ;
    }
  };

  struct conformer_wrappers
  {
    typedef conformer w_t;

    static std::string
    get_altloc(w_t const& self) { return self.data->altloc; }

    IOTBX_PDB_HIERARCHY_GET_CHILDREN(conformer, residue, residues)

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("conformer", no_init)
        .def(init<chain const&, std::string const&>((
          arg_("parent"), arg_("altloc"))))
        .add_property("altloc", make_function(get_altloc))
        .def("memory_id", &w_t::memory_id)
        .def("parent", get_parent<conformer, chain>::wrapper)
        .def("residues_size", &w_t::residues_size)
        .def("residues", get_residues)
        .def("atoms_size", &w_t::atoms_size)
        .def("atoms", &w_t::atoms)
      ;
    }
  };

  void
  wrap_hierarchy()
  {
    atom_bpl_wrap();
    atom_group_wrappers::wrap();
    residue_group_wrappers::wrap();
    chain_wrappers::wrap();
    model_wrappers::wrap();
    root_wrappers::wrap();

    residue_wrappers::wrap();
    conformer_wrappers::wrap();

    atoms::bpl_wrap();
  }

}}}} // namespace iotbx::pdb::hierarchy::<anonymous>

BOOST_PYTHON_MODULE(iotbx_pdb_hierarchy_ext)
{
  PycString_IMPORT;
  iotbx::pdb::hierarchy::wrap_hierarchy();
}
