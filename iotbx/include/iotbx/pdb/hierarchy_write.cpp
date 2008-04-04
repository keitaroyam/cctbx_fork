#include <iotbx/pdb/hierarchy_atoms.h>
#include <fstream>

namespace iotbx { namespace pdb { namespace hierarchy {

namespace {

  void
  rstrip_in_place(std::string& s)
  {
    unsigned i = static_cast<unsigned>(s.size());
    if (i == 0) return;
    for(;;) {
      i--;
      if (!isspace(s[i])) {
        s.resize(i+1U);
        return;
      }
      if (i == 0) {
        s.resize(0);
        return;
      }
    }
  }

} // namespace <anonymous>

  void
  residue_groups_as_pdb_string(
    stream_write& write,
    atom_label_columns_formatter& label_formatter,
    std::vector<residue_group> const& residue_groups,
    int interleaved_conf,
    bool atom_hetatm,
    bool sigatm,
    bool anisou,
    bool siguij)
  {
    char buf[81U + 81U + 81U + 81U];
    unsigned n_rg = static_cast<unsigned>(residue_groups.size());
    for(unsigned i_rg=0;i_rg<n_rg;i_rg++) {
      residue_group const& rg = residue_groups[i_rg];
      if (i_rg != 0 && !rg.data->link_to_previous) {
        write("BREAK\n", 6U);
      }
      label_formatter.resseq = rg.data->resseq.elems;
      label_formatter.icode = rg.data->icode.elems;
      if (interleaved_conf <= 0) {
        unsigned n_ag = rg.atom_groups_size();
        for(unsigned i_ag=0;i_ag<n_ag;i_ag++) {
          atom_group const& ag = rg.atom_groups()[i_ag];
          label_formatter.altloc = ag.data->altloc.elems;
          label_formatter.resname = ag.data->resname.elems;
          typedef std::vector<atom> va;
          va const& atoms = ag.atoms();
          va::const_iterator atoms_end = atoms.end();
          for(va::const_iterator
                atom=atoms.begin();atom!=atoms_end;atom++) {
#define IOTBX_LOC \
            unsigned str_len = atom->format_atom_record_group( \
              buf, &label_formatter, \
              atom_hetatm, sigatm, anisou, siguij); \
            if (str_len != 0) { \
              buf[str_len] = '\n'; \
              write(buf, str_len+1U); \
            }
            IOTBX_LOC
          }
        }
      }
      else { // interleaved_conf > 0
        af::shared<atom> atoms_ilc = rg.atoms_interleaved_conf(
          /* group_residue_names */ (interleaved_conf < 2));
        af::const_ref<atom> ats = atoms_ilc.const_ref();
        unsigned n_at = static_cast<unsigned>(ats.size());
        for(unsigned i_at=0;i_at<n_at;i_at++) {
          hierarchy::atom const* atom = &ats[i_at];
          shared_ptr<atom_group_data> ag_data = atom->parent_ptr();
          label_formatter.altloc = ag_data->altloc.elems;
          label_formatter.resname = ag_data->resname.elems;
          IOTBX_LOC
        }
      }
#undef IOTBX_LOC
    }
  }

  void
  models_as_pdb_string(
    stream_write& write,
    std::vector<model> const& models,
    bool append_end,
    int interleaved_conf,
    bool atom_hetatm,
    bool sigatm,
    bool anisou,
    bool siguij)
  {
    atom_label_columns_formatter label_formatter;
    unsigned n_mds = static_cast<unsigned>(models.size());
    for(unsigned i_md=0;i_md<n_mds;i_md++) {
      if (n_mds != 1U) {
        write("MODEL", 5U);
        std::string model_id = models[i_md].data->id;
        rstrip_in_place(model_id);
        unsigned n = static_cast<unsigned>(model_id.size());
        if (n != 0) {
          write(" ", 1U);
          for(unsigned i=n;i<8U;i++) write(" ", 1U);
          write(model_id.c_str(), n);
        }
        write("\n", 1U);
      }
      unsigned n_chs = models[i_md].chains_size();
      std::vector<chain> const& chains = models[i_md].chains();
      for(unsigned i_ch=0;i_ch<n_chs;i_ch++) {
        chain const& ch = chains[i_ch];
        label_formatter.chain_id = ch.data->id.c_str();
        residue_groups_as_pdb_string(
          write,
          label_formatter,
          ch.residue_groups(),
          interleaved_conf,
          atom_hetatm, sigatm, anisou, siguij);
        write("TER\n", 4U);
      }
      if (n_mds != 1U) {
        write("ENDMDL\n", 7U);
      }
    }
    if (append_end) {
      write("END\n", 4U);
    }
  }

  struct fstream_write : stream_write
  {
    std::ofstream* stream;

    fstream_write(std::ofstream* stream_) : stream(stream_) {}

    virtual void
    operator()(const char* s, unsigned n)
    {
      stream->write(s, n);
    }
  };

  void
  root::write_pdb_file(
    const char* file_name,
    bool open_append,
    bool append_end,
    int interleaved_conf,
    boost::optional<int> const& atoms_reset_serial_first_value,
    bool atom_hetatm,
    bool sigatm,
    bool anisou,
    bool siguij) const
  {
    SCITBX_ASSERT(file_name != 0);
    if (atoms_reset_serial_first_value) {
      atoms::reset_serial(
        atoms(interleaved_conf).const_ref(),
        *atoms_reset_serial_first_value);
    }
    std::ios::openmode mode = std::ios::out | std::ios::binary;
    if (open_append) mode |= std::ios::app;
    std::ofstream out(file_name, mode);
    if (out.fail()) {
      throw std::runtime_error(
        "Cannot open file for writing: \"" + std::string(file_name) + "\"");
    }
    fstream_write write(&out);
    models_as_pdb_string(
      write,
      models(),
      append_end,
      interleaved_conf,
      atom_hetatm,
      sigatm,
      anisou,
      siguij);
    if (out.fail()) {
      throw std::runtime_error(
        "Failure writing to file: \"" + std::string(file_name) + "\"");
    }
    out.close();
  }

}}} // namespace iotbx::pdb::hierarchy
