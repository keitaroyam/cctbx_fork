#ifndef IOTBX_PDB_HIERARCHY_V2_H
#define IOTBX_PDB_HIERARCHY_V2_H

#if defined(__INTEL_COMPILER) // XXX exercise on one platform
#define IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
#endif

#include <iotbx/pdb/namespace.h>
#include <iotbx/pdb/small_str.h>
#include <boost/optional.hpp>
#include <boost/noncopyable.hpp>
#include <map>
#include <set>
#include <vector>
#include <string>

namespace iotbx { namespace pdb {

//! Hierarchy organizing PDB atom objects.
/*! Data hierarchy:
<pre>
  model
    parent
    id
    chain(s)
      parent
      id
      residue_group(s)
        parent
        resseq
        icode
        link_to_previous
        atom_group(s)
          parent
          altloc
          resname
          atom(s)
            parent
            name
            segid
            element
            charge
            serial
            xyz sigxyz
            occ sigocc
            b sigb
            uij siguij
            hetero
</pre>
Convenience objects:
<pre>
  residue
    parent
    resname
    resseq
    icode
    link_to_previous
    is_pure_main_conf
    atoms
</pre>
A residue object is NOT a parent of the atoms.
<p>
<pre>
  conformer
    parent
    altloc
    residues
</pre>
 */

namespace hierarchy_v2 {

  static const char blank_altloc_char = ' ';
  static const char blank_altloc_cstr[2] = {blank_altloc_char, '\0'};

  class root_data;
  class root;
  class model_data;
  class model;
  class chain_data;
  class chain;
  class residue_group_data;
  class residue_group;
  class atom_group_data;
  class atom_group;
  class atom_data;
  class atom;

  class conformer_data;
  class conformer;
  class residue_data;
  class residue;

  //! Holder for root attributes (to be held by a shared_ptr).
  class root_data : boost::noncopyable
  {
    protected:
      friend class root;
    public:
      af::shared<std::string> info;
    protected:
      std::vector<model> models;
  };

  //! Holder for model attributes (to be held by a shared_ptr).
  class model_data : boost::noncopyable
  {
    protected:
      friend class model;
      friend class atom; // to support efficient backtracking to parents
      weak_ptr<root_data> parent;
    public:
      std::string id;
    protected:
      std::vector<chain> chains;

      inline
      model_data(
        weak_ptr<root_data> const& parent,
        std::string const& id);

      inline
      model_data(
        std::string const& id);

      inline
      model_data(
        weak_ptr<root_data> const& parent_,
        model_data const& other);
  };

  //! Holder for chain attributes (to be held by a shared_ptr).
  class chain_data : boost::noncopyable
  {
    protected:
      friend class chain;
      friend class atom_label_columns_formatter;
      weak_ptr<model_data> parent;
    public:
      std::string id;
    protected:
      std::vector<residue_group> residue_groups;

      inline
      chain_data(
        weak_ptr<model_data> const& parent,
        std::string const& id);

      inline
      chain_data(
        std::string const& id);

      inline
      chain_data(
        weak_ptr<model_data> const& parent_,
        chain_data const& other);
  };

  //! Holder for residue_group attributes (to be held by a shared_ptr).
  class residue_group_data : boost::noncopyable
  {
    protected:
      friend class residue_group;
      friend class atom_label_columns_formatter;
      weak_ptr<chain_data> parent;
    public:
      str4 resseq;
      str1 icode;
      bool link_to_previous;
    protected:
      std::vector<atom_group> atom_groups;

      inline
      residue_group_data(
        weak_ptr<chain_data> const& parent,
        const char* resseq_,
        const char* icode_,
        bool link_to_previous_);

      inline
      residue_group_data(
        const char* resseq_,
        const char* icode_,
        bool link_to_previous_);

      inline
      residue_group_data(
        weak_ptr<chain_data> const& parent_,
        residue_group_data const& other);
  };

  //! Holder for atom_group attributes (to be held by a shared_ptr).
  class atom_group_data : boost::noncopyable
  {
    protected:
      friend class atom_group;
      friend class atom_label_columns_formatter;
      weak_ptr<residue_group_data> parent;
    public:
      str1 altloc;
      str3 resname;
    protected:
      std::vector<atom> atoms;

      inline
      atom_group_data(
        weak_ptr<residue_group_data> const& parent_,
        const char* altloc_,
        const char* resname_);

      inline
      atom_group_data(
        const char* altloc_,
        const char* resname_);

      inline
      atom_group_data(
        weak_ptr<residue_group_data> const& parent_,
        atom_group_data const& other);
  };

  //! Holder for atom attributes (to be held by a shared_ptr).
  class atom_data : boost::noncopyable
  {
    protected:
      friend class atom;
      friend class atom_label_columns_formatter;
      weak_ptr<atom_group_data> parent;
    public:
      vec3 xyz;
      vec3 sigxyz;
      double occ;
      double sigocc;
      double b;
      double sigb;
      sym_mat3 uij;
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
      sym_mat3 siguij;
#endif
      unsigned i_seq;
      int tmp;
      bool hetero;
      str5 serial;
      str4 name;
      str4 segid;
      str2 element;
      str2 charge;

    protected:
      atom_data(
        weak_ptr<atom_group_data> const& parent_,
        vec3 const& xyz_, vec3 const& sigxyz_,
        double occ_, double sigocc_,
        double b_, double sigb_,
        sym_mat3 const& uij_,
        sym_mat3 const&
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
                        siguij_
#endif
                               ,
        bool hetero_, str5 serial_, str4 name_,
        str4 segid_, str2 element_, str2 charge_)
      :
        parent(parent_),
        xyz(xyz_), sigxyz(sigxyz_),
        occ(occ_), sigocc(sigocc_),
        b(b_), sigb(sigb_),
        uij(uij_),
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
        siguij(siguij_),
#endif
        i_seq(0), tmp(0),
        hetero(hetero_), serial(serial_), name(name_),
        segid(segid_), element(element_), charge(charge_)
      {}

      atom_data(
        vec3 const& xyz_, vec3 const& sigxyz_,
        double occ_, double sigocc_,
        double b_, double sigb_,
        sym_mat3 const& uij_,
        sym_mat3 const&
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
                        siguij_
#endif
                               ,
        bool hetero_, str5 serial_, str4 name_,
        str4 segid_, str2 element_, str2 charge_)
      :
        xyz(xyz_), sigxyz(sigxyz_),
        occ(occ_), sigocc(sigocc_),
        b(b_), sigb(sigb_),
        uij(uij_),
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
        siguij(siguij_),
#endif
        i_seq(0), tmp(0),
        hetero(hetero_), serial(serial_), name(name_),
        segid(segid_), element(element_), charge(charge_)
      {}

      atom_data(
        weak_ptr<atom_group_data> const& parent_,
        atom_data const& other);
  };

  //! Holder for conformer attributes (to be held by a shared_ptr).
  class conformer_data : boost::noncopyable
  {
    protected:
      friend class conformer;
      weak_ptr<chain_data> parent;
    public:
      std::string altloc;
    protected:
      std::vector<residue> residues;

      inline
      conformer_data(
        weak_ptr<chain_data> const& parent_,
        std::string const& altloc_);
  };

  //! Holder for residue attributes (to be held by a shared_ptr).
  class residue_data : boost::noncopyable
  {
    protected:
      friend class residue;
      weak_ptr<conformer_data> parent;
    public:
      str3 resname;
      str4 resseq;
      str1 icode;
      bool link_to_previous;
      bool is_pure_main_conf;
    protected:
      std::vector<atom> atoms;

      inline
      residue_data(
        weak_ptr<conformer_data> const& parent_,
        const char* resname_,
        const char* resseq_,
        const char* const& icode_,
        bool link_to_previous_,
        bool is_pure_main_conf_,
        std::vector<atom> const& atoms_);
  };

  //! Not available in Python.
  struct atom_label_columns_formatter
  {
    const char* name;
    const char* altloc;
    const char* resname;
    const char* resseq;
    const char* icode;
    const char* chain_id;

    //! All labels must be defined externally.
    /*! result must point to an array of size 15 (or greater).
        On return, result is NOT null-terminated.
     */
    void
    format(
      char* result) const;

    //! All labels are extracted from the atom and its parents.
    /*! result must point to an array of size 15 (or greater).
        On return, result is NOT null-terminated.
     */
    void
    format(
      char* result,
      hierarchy_v2::atom const& atom);
  };

  //! Atom attributes.
  class atom
  {
    public:
      shared_ptr<atom_data> data;

    protected:
      friend class atom_group; // to support atom_group::append_atom()

      atom&
      set_parent(atom_group const& parent);

      void
      clear_parent() { data->parent.reset(); }

    public:
      inline
      explicit
      atom(
        atom_group const& parent,
        vec3 const& xyz=vec3(0,0,0), vec3 const& sigxyz=vec3(0,0,0),
        double occ=0, double sigocc=0,
        double b=0, double sigb=0,
        sym_mat3 const& uij=sym_mat3(-1,-1,-1,-1,-1,-1),
        sym_mat3 const& siguij=sym_mat3(-1,-1,-1,-1,-1,-1),
        bool hetero=false, const char* serial="", const char* name="",
        const char* segid="", const char* element="", const char* charge="");

      explicit
      atom(
        vec3 const& xyz=vec3(0,0,0), vec3 const& sigxyz=vec3(0,0,0),
        double occ=0, double sigocc=0,
        double b=0, double sigb=0,
        sym_mat3 const& uij=sym_mat3(-1,-1,-1,-1,-1,-1),
        sym_mat3 const& siguij=sym_mat3(-1,-1,-1,-1,-1,-1),
        bool hetero=false, const char* serial="", const char* name="",
        const char* segid="", const char* element="", const char* charge="")
      :
        data(new atom_data(
          xyz, sigxyz,
          occ, sigocc,
          b, sigb,
          uij,
          siguij,
          hetero, serial, name,
          segid, element, charge))
      {}

      explicit
      atom(
        vec3 const& xyz, vec3 const& sigxyz,
        double occ, double sigocc,
        double b, double sigb,
        sym_mat3 const& uij,
        sym_mat3 const& siguij,
        bool hetero, str5 serial, str4 name,
        str4 segid, str2 element, str2 charge)
      :
        data(new atom_data(
          xyz, sigxyz,
          occ, sigocc,
          b, sigb,
          uij,
          siguij,
          hetero, serial, name,
          segid, element, charge))
      {}

      inline
      atom(
        atom_group const& parent,
        atom const& other);

      atom
      detached_copy() const;

      atom&
      set_xyz(vec3 const& new_xyz)
      {
        data->xyz = new_xyz;
        return *this;
      }

      atom&
      set_sigxyz(vec3 const& new_sigxyz)
      {
        data->sigxyz = new_sigxyz;
        return *this;
      }

      atom&
      set_occ(double new_occ)
      {
        data->occ = new_occ;
        return *this;
      }

      atom&
      set_sigocc(double new_sigocc)
      {
        data->sigocc = new_sigocc;
        return *this;
      }

      atom&
      set_b(double new_b)
      {
        data->b = new_b;
        return *this;
      }

      atom&
      set_sigb(double new_sigb)
      {
        data->sigb = new_sigb;
        return *this;
      }

      atom&
      set_uij(sym_mat3 const& new_uij)
      {
        data->uij = new_uij;
        return *this;
      }

      atom&
      set_siguij(sym_mat3 const&
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
                                 new_siguij
#endif
                                           )
      {
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
        data->siguij = new_siguij;
#endif
        return *this;
      }

      atom&
      set_hetero(double new_hetero)
      {
        data->hetero = new_hetero;
        return *this;
      }

      atom&
      set_serial(const char* new_serial)
      {
        data->serial = new_serial;
        return *this;
      }

      atom&
      set_name(const char* new_name)
      {
        data->name = new_name;
        return *this;
      }

      atom&
      set_segid(const char* new_segid)
      {
        data->segid = new_segid;
        return *this;
      }

      atom&
      set_element(const char* new_element)
      {
        data->element = new_element;
        return *this;
      }

      atom&
      set_charge(const char* new_charge)
      {
        data->charge = new_charge;
        return *this;
      }

      std::size_t
      memory_id() const { return reinterpret_cast<std::size_t>(data.get()); }

      static
      std::size_t
      sizeof_data() { return sizeof(atom_data); }

      //! Not available in Python.
      shared_ptr<atom_group_data>
      parent_ptr() const { return data->parent.lock(); }

      boost::optional<atom_group>
      parent() const;

      bool
      uij_is_defined() const
      {
        return !data->uij.const_ref().all_eq(-1);
      }

      static
      bool
      has_siguij()
      {
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
        return true;
#else
        return false;
#endif
      }

      bool
      siguij_is_defined() const
      {
#ifdef IOTBX_PDB_ENABLE_ATOM_DATA_SIGUIJ
        return !data->siguij.const_ref().all_eq(-1);
#else
        return false;
#endif
      }

      //! Not available in Python.
      /*! result must point to an array of size 27 (or greater).
          The first 6 characters are not modified.
          On return, result is NOT null-terminated.
       */
      void
      format_atom_record_serial_label_columns(
        char* result,
        atom_label_columns_formatter* label_formatter=0) const;

      //! Not available in Python.
      /*! result must point to an array of size 81 (or greater).
          On return, result is null-terminated.
       */
      unsigned
      format_atom_record_segid_element_charge_columns(
        char* result,
        unsigned segid_start,
        unsigned blanks_start_at) const;

      //! Not available in Python.
      /*! result must point to an array of size 4 (or greater).
          On return, result is NOT null-terminated.
       */
      void
      format_pdb_element_charge_columns(
        char* result) const;

      std::string
      pdb_label_columns() const;

      //! Not available in Python.
      small_str<19>
      pdb_label_columns_segid_small_str() const;

      std::string
      pdb_element_charge_columns() const;

      //! Not available in Python.
      /*! result must point to an array of size 81 (or greater).
          On return, result is null-terminated.
       */
      unsigned
      format_atom_record(
        char* result,
        atom_label_columns_formatter* label_formatter=0,
        const char* replace_floats_with=0) const;

      //! Not available in Python.
      /*! result must point to an array of size 81 (or greater).
          On return, result is null-terminated.
       */
      unsigned
      format_sigatm_record(
        char* result,
        atom_label_columns_formatter* label_formatter) const;

      //! Not available in Python.
      /*! result must point to an array of size 81 (or greater).
          On return, result is null-terminated.
       */
      unsigned
      format_anisou_record(
        char* result,
        atom_label_columns_formatter* label_formatter=0) const;

      //! Not available in Python.
      /*! result must point to an array of size 81 (or greater).
          On return, result is null-terminated.
       */
      unsigned
      format_siguij_record(
        char* result,
        atom_label_columns_formatter* label_formatter=0) const;

      //! Not available in Python.
      /*! result must point to an array of size 324 (or greater).
          On return, result is null-terminated.
       */
      unsigned
      format_atom_record_group(
        char* result,
        atom_label_columns_formatter* label_formatter,
        bool atom_hetatm,
        bool sigatm,
        bool anisou,
        bool siguij) const;

      bool
      element_is_hydrogen() const;

      boost::optional<std::string>
      determine_chemical_element_simple() const;
  };

  //! atom_group attributes.
  class atom_group
  {
    public:
      shared_ptr<atom_group_data> data;

    protected:
      friend class atom; // to support atom::parent()

      atom_group(
        shared_ptr<atom_group_data> const& data_, bool) : data(data_) {}

      friend class residue_group; // to support atom_group::append_atom_group()

      atom_group&
      set_parent(residue_group const& parent);

      void
      clear_parent() { data->parent.reset(); }

    public:
      inline
      explicit
      atom_group(
        residue_group const& parent,
        const char* altloc="",
        const char* resname="");

      explicit
      atom_group(
        const char* altloc="",
        const char* resname="")
      :
        data(new atom_group_data(altloc, resname))
      {}

      explicit
      atom_group(const atom_group_data* other)
      :
        data(new atom_group_data(
          other->altloc.elems,
          other->resname.elems))
      {}

      atom_group(
        residue_group const& parent,
        atom_group const& other);

      atom_group
      detached_copy() const;

      std::size_t
      memory_id() const { return reinterpret_cast<std::size_t>(data.get()); }

      shared_ptr<residue_group_data>
      parent_ptr() const { return data->parent.lock(); }

      boost::optional<residue_group>
      parent() const;

      unsigned
      atoms_size() const;

      std::vector<atom> const&
      atoms() const;

      std::vector<atom>::iterator
      atoms_begin() const { return data->atoms.begin(); }

      long
      find_atom_index(
        hierarchy_v2::atom const& atom,
        bool must_be_present=false) const;

      void
      pre_allocate_atoms(unsigned number_of_additional_atoms);

      void
      insert_atom(long i, hierarchy_v2::atom& atom);

      void
      append_atom(hierarchy_v2::atom& atom);

      void
      remove_atom(long i);

      void
      remove_atom(hierarchy_v2::atom& atom);

      std::string
      confid() const;

      //! Not available in Python.
      bool
      is_identical_topology(
        atom_group const& other) const;
  };

  //! residue_group attributes.
  class residue_group
  {
    public:
      shared_ptr<residue_group_data> data;

    protected:
      friend class atom_group; // to support atom_group::parent()

      residue_group(
        shared_ptr<residue_group_data> const& data_, bool) : data(data_) {}

      friend class chain; // to support chain::append_residue_group()

      residue_group&
      set_parent(chain const& parent);

      void
      clear_parent() { data->parent.reset(); }

    public:
      inline
      explicit
      residue_group(
        chain const& parent,
        const char* resseq="",
        const char* icode="",
        bool link_to_previous=true);

      explicit
      residue_group(
        const char* resseq="",
        const char* icode="",
        bool link_to_previous=true)
      :
        data(new residue_group_data(resseq, icode, link_to_previous))
      {}

      explicit
      residue_group(const residue_group_data* other)
      :
        data(new residue_group_data(
          other->resseq.elems,
          other->icode.elems,
          other->link_to_previous))
      {}

      residue_group(
        chain const& parent,
        residue_group const& other);

      residue_group
      detached_copy() const;

      std::size_t
      memory_id() const { return reinterpret_cast<std::size_t>(data.get()); }

      shared_ptr<chain_data>
      parent_ptr() const { return data->parent.lock(); }

      boost::optional<chain>
      parent() const;

      unsigned
      atom_groups_size() const;

      std::vector<atom_group> const&
      atom_groups() const;

      std::vector<atom_group>::iterator
      atom_groups_begin() const { return data->atom_groups.begin(); }

      long
      find_atom_group_index(
        hierarchy_v2::atom_group const& atom_group,
        bool must_be_present=false) const;

      void
      pre_allocate_atom_groups(unsigned number_of_additional_atom_groups);

      void
      insert_atom_group(long i, hierarchy_v2::atom_group& atom_group);

      void
      append_atom_group(hierarchy_v2::atom_group& atom_group);

      void
      remove_atom_group(long i);

      void
      remove_atom_group(hierarchy_v2::atom_group& atom_group);

      unsigned
      atoms_size() const;

      af::shared<atom>
      atoms() const;

      std::string
      resid() const;

      //! Not available in Python.
      str5
      resid_small_str() const;

      bool
      have_conformers() const;

      void
      merge_atom_groups(
        atom_group& primary,
        atom_group& secondary);

      unsigned
      move_blank_altloc_atom_groups_to_front();

      af::tiny<unsigned, 2>
      edit_blank_altloc();

      //! Not available in Python.
      bool
      is_identical_topology(
        residue_group const& other) const;

      af::shared<atom>
      atoms_interleaved_conf(
        bool group_residue_names=true) const;
  };

  //! Chain attributes.
  class chain
  {
    public:
      shared_ptr<chain_data> data;

    protected:
      friend class residue_group; // to support residue_group::parent()
      friend class conformer; // to support conformer::parent()

      chain(shared_ptr<chain_data> const& data_, bool) : data(data_) {}

      friend class model; // to support model::append_chain()

      chain&
      set_parent(model const& parent);

      void
      clear_parent() { data->parent.reset(); }

    public:
      inline
      explicit
      chain(
        model const& parent,
        std::string const& id="");

      explicit
      chain(
        std::string const& id="")
      :
        data(new chain_data(id))
      {}

      explicit
      chain(const chain_data* other)
      :
        data(new chain_data(other->id))
      {}

      chain(
        model const& parent,
        chain const& other);

      chain
      detached_copy() const;

      std::size_t
      memory_id() const { return reinterpret_cast<std::size_t>(data.get()); }

      shared_ptr<model_data>
      parent_ptr() const { return data->parent.lock(); }

      boost::optional<model>
      parent() const;

      unsigned
      residue_groups_size() const;

      std::vector<residue_group> const&
      residue_groups() const;

      std::vector<residue_group>::iterator
      residue_groups_begin() const { return data->residue_groups.begin(); }

      long
      find_residue_group_index(
        hierarchy_v2::residue_group const& residue_group,
        bool must_be_present=false) const;

      void
      pre_allocate_residue_groups(unsigned number_of_additional_residue_groups);

      void
      insert_residue_group(long i, hierarchy_v2::residue_group& residue_group);

      void
      append_residue_group(hierarchy_v2::residue_group& residue_group);

      void
      remove_residue_group(long i);

      void
      remove_residue_group(hierarchy_v2::residue_group& residue_group);

      unsigned
      atoms_size() const;

      af::shared<atom>
      atoms() const;

      void
      merge_residue_groups(
        residue_group& primary,
        residue_group& secondary);

      af::shared<std::size_t>
      merge_disconnected_residue_groups_with_pure_altloc();

      af::shared<af::tiny<std::size_t, 2> >
      find_pure_altloc_ranges(
        const char* common_residue_name_class_only=0) const;

      //! Not available in Python.
      bool
      is_identical_topology(
        chain const& other) const;

      af::shared<conformer>
      conformers() const;
  };

  //! Model attributes.
  class model
  {
    public:
      shared_ptr<model_data> data;

    protected:
      friend class chain; // to support chain::parent()
      model(shared_ptr<model_data> const& data_, bool) : data(data_) {}

      friend class root; // to support root::append_model()

      model&
      set_parent(root const& parent);

      void
      clear_parent() { data->parent.reset(); }

    public:
      inline
      explicit
      model(
        root const& parent,
        std::string const& id="");

      explicit
      model(std::string const& id="") : data(new model_data(id)) {}

      explicit
      model(const model_data* other)
      :
        data(new model_data(other->id))
      {}

      model(
        root const& parent,
        model const& other);

      model
      detached_copy() const;

      std::size_t
      memory_id() const { return reinterpret_cast<std::size_t>(data.get()); }

      shared_ptr<root_data>
      parent_ptr() const { return data->parent.lock(); }

      boost::optional<root>
      parent() const;

      unsigned
      chains_size() const;

      std::vector<chain> const&
      chains() const;

      std::vector<chain>::iterator
      chains_begin() const { return data->chains.begin(); }

      long
      find_chain_index(
        hierarchy_v2::chain const& chain,
        bool must_be_present=false) const;

      void
      pre_allocate_chains(unsigned number_of_additional_chains);

      void
      insert_chain(long i, hierarchy_v2::chain& chain);

      void
      append_chain(hierarchy_v2::chain& chain);

      void
      remove_chain(long i);

      void
      remove_chain(hierarchy_v2::chain& chain);

      unsigned
      atoms_size() const;

      af::shared<atom>
      atoms() const;

      bool
      is_identical_topology(
        model const& other) const;

      void
      transfer_chains_from_other(
        model& other);
  };

  //! Root attributes.
  class root
  {
    public:
      shared_ptr<root_data> data;

    protected:
      friend class model; // to support model::parent()

      root(shared_ptr<root_data> const& data_, bool) : data(data_) {}

    public:
      root() : data(new root_data) {}

      root
      deep_copy() const;

      std::size_t
      memory_id() const { return reinterpret_cast<std::size_t>(data.get()); }

      unsigned
      models_size() const;

      std::vector<model> const&
      models() const;

      std::vector<model>::iterator
      models_begin() const { return data->models.begin(); }

      long
      find_model_index(
        hierarchy_v2::model const& model,
        bool must_be_present=false) const;

      void
      pre_allocate_models(unsigned number_of_additional_models);

      void
      insert_model(long i, hierarchy_v2::model& model);

      void
      append_model(hierarchy_v2::model& model);

      void
      remove_model(long i);

      void
      remove_model(hierarchy_v2::model& model);

      unsigned
      atoms_size() const;

      af::shared<atom>
      atoms() const;
  };

  struct overall_counts : boost::noncopyable
  {
    hierarchy_v2::root root;
    unsigned n_empty_models;
    unsigned n_empty_chains;
    unsigned n_empty_residue_groups;
    unsigned n_empty_atom_groups;
    unsigned n_duplicate_model_ids;
    unsigned n_duplicate_chain_ids;
    unsigned n_duplicate_atom_labels;
    af::shared<af::shared<atom> > duplicate_atom_labels;
    unsigned n_models;
    unsigned n_chains;
    unsigned n_alt_conf;
    unsigned n_residues;
    unsigned n_residue_groups;
    unsigned n_explicit_chain_breaks;
    unsigned n_atoms;
    std::map<std::string, unsigned> model_ids;
    std::map<std::string, unsigned> chain_ids;
    std::map<std::string, unsigned> alt_conf_ids;
    std::map<std::string, unsigned> resnames;
    std::map<std::string, unsigned> resname_classes;
    std::map<std::string, unsigned> element_charge_types;
    unsigned n_alt_conf_none;
    unsigned n_alt_conf_pure;
    unsigned n_alt_conf_proper;
    unsigned n_alt_conf_improper;
    boost::optional<residue_group> alt_conf_proper;
    boost::optional<residue_group> alt_conf_improper;
    af::shared<af::tiny<residue_group, 2> >
      consecutive_residue_groups_with_same_resid;
    unsigned n_chains_with_mix_of_proper_and_improper_alt_conf;
    af::shared<residue_group>
      residue_groups_with_multiple_resnames_using_same_altloc;

    overall_counts(
      hierarchy_v2::root const& root_);
  };

  struct atom_selection_cache : boost::noncopyable
  {
    typedef std::map<std::string, std::vector<unsigned> > map;
    unsigned n_seq;
    map name;
    map altloc;
    map resname;
    map chain_id;
    map resseq;
    map icode;
    map resid;
    map segid;
    map model_id;
    map element;
    map charge;
    af::shared<std::size_t> anisou;

    atom_selection_cache(
      hierarchy_v2::root const& root);
  };

  //! Residue attributes.
  class residue
  {
    public:
      shared_ptr<residue_data> data;

    protected:
      friend class conformer; // to support conformer:append_residue

      residue(
        conformer const& parent,
        const char* resname,
        const char* resseq,
        const char* icode,
        bool link_to_previous,
        bool is_pure_main_conf,
        std::vector<atom> const& atoms);

    public:
      std::size_t
      memory_id() const { return reinterpret_cast<std::size_t>(data.get()); }

      boost::optional<conformer>
      parent() const;

      unsigned
      atoms_size() const
      {
        return static_cast<unsigned>(data->atoms.size());
      }

      std::vector<atom> const&
      atoms() const { return data->atoms; }

      std::string
      resid() const;
  };

  //! Conformer attributes.
  class conformer
  {
    public:
      shared_ptr<conformer_data> data;

    protected:
      friend class residue; // to support residue::parent()

      conformer(shared_ptr<conformer_data> const& data_, bool) : data(data_) {}

      friend class chain; // to support chain::conformers()

      void
      append_residue(
        const char* resname,
        const char* resseq,
        const char* icode,
        bool link_to_previous,
        bool is_pure_main_conf,
        std::vector<atom> const& atoms);

    public:
      conformer(
        chain const& parent,
        std::string const& altloc)
      :
        data(new conformer_data(parent.data, altloc))
      {}

      std::size_t
      memory_id() const { return reinterpret_cast<std::size_t>(data.get()); }

      boost::optional<chain>
      parent() const;

      unsigned
      residues_size() const
      {
        return static_cast<unsigned>(data->residues.size());
      }

      std::vector<residue> const&
      residues() const { return data->residues; }

      unsigned
      atoms_size() const;

      af::shared<atom>
      atoms() const;
  };

  inline
  model_data::model_data(
    weak_ptr<root_data> const& parent_,
    std::string const& id_)
  :
    parent(parent_),
    id(id_)
  {}

  inline
  model_data::model_data(std::string const& id_) : id(id_) {}

  inline
  model_data::model_data(
    weak_ptr<root_data> const& parent_,
    model_data const& other)
  :
    parent(parent_),
    id(other.id)
  {}

  inline
  model::model(
    root const& parent,
    std::string const& id)
  :
    data(new model_data(parent.data, id))
  {}

  inline
  chain_data::chain_data(
    weak_ptr<model_data> const& parent_,
    std::string const& id_)
  :
    parent(parent_),
    id(id_)
  {}

  inline
  chain_data::chain_data(
    std::string const& id_)
  :
    id(id_)
  {}

  inline
  chain_data::chain_data(
    weak_ptr<model_data> const& parent_,
    chain_data const& other)
  :
    parent(parent_),
    id(other.id)
  {}

  inline
  chain::chain(
    model const& parent,
    std::string const& id)
  :
    data(new chain_data(parent.data, id))
  {}

  inline
  residue_group_data::residue_group_data(
    weak_ptr<chain_data> const& parent_,
    const char* resseq_,
    const char* icode_,
    bool link_to_previous_)
  :
    parent(parent_),
    resseq(resseq_),
    icode(icode_),
    link_to_previous(link_to_previous_)
  {}

  inline
  residue_group_data::residue_group_data(
    const char* resseq_,
    const char* icode_,
    bool link_to_previous_)
  :
    resseq(resseq_),
    icode(icode_),
    link_to_previous(link_to_previous_)
  {}

  inline
  residue_group_data::residue_group_data(
    weak_ptr<chain_data> const& parent_,
    residue_group_data const& other)
  :
    parent(parent_),
    resseq(other.resseq),
    icode(other.icode),
    link_to_previous(other.link_to_previous)
  {}

  inline
  residue_group::residue_group(
    chain const& parent,
    const char* resseq,
    const char* icode,
    bool link_to_previous)
  :
    data(new residue_group_data(parent.data, resseq, icode, link_to_previous))
  {}

  inline
  atom_group_data::atom_group_data(
    weak_ptr<residue_group_data> const& parent_,
    const char* altloc_,
    const char* resname_)
  :
    parent(parent_),
    altloc(altloc_),
    resname(resname_)
  {}

  inline
  atom_group_data::atom_group_data(
    const char* altloc_,
    const char* resname_)
  :
    altloc(altloc_),
    resname(resname_)
  {}

  inline
  atom_group_data::atom_group_data(
    weak_ptr<residue_group_data> const& parent_,
    atom_group_data const& other)
  :
    parent(parent_),
    altloc(other.altloc),
    resname(other.resname)
  {}

  inline
  atom_group::atom_group(
    residue_group const& parent,
    const char* altloc,
    const char* resname)
  :
    data(new atom_group_data(parent.data, altloc, resname))
  {}

  inline
  atom::atom(
    atom_group const& parent,
    vec3 const& xyz, vec3 const& sigxyz,
    double occ, double sigocc,
    double b, double sigb,
    sym_mat3 const& uij,
    sym_mat3 const& siguij,
    bool hetero, const char* serial, const char* name,
    const char* segid, const char* element, const char* charge)
  :
    data(new atom_data(
      parent.data,
      xyz, sigxyz,
      occ, sigocc,
      b, sigb,
      uij,
      siguij,
      hetero, serial, name,
      segid, element, charge))
  {}

  inline
  atom::atom(
    atom_group const& parent,
    atom const& other)
  :
    data(new atom_data(parent.data, *other.data))
  {}

  inline
  residue_data::residue_data(
    weak_ptr<conformer_data> const& parent_,
    const char* resname_,
    const char* resseq_,
    const char* const& icode_,
    bool link_to_previous_,
    bool is_pure_main_conf_,
    std::vector<atom> const& atoms_)
  :
    parent(parent_),
    resname(resname_),
    resseq(resseq_),
    icode(icode_),
    link_to_previous(link_to_previous_),
    is_pure_main_conf(is_pure_main_conf_),
    atoms(atoms_.begin(), atoms_.end())
  {}

  inline
  conformer_data::conformer_data(
    weak_ptr<chain_data> const& parent_,
    std::string const& altloc_)
  :
    parent(parent_),
    altloc(altloc_)
  {}

}}} // namespace iotbx::pdb::hierarchy_v2

#endif // IOTBX_PDB_HIERARCHY_V2_H
