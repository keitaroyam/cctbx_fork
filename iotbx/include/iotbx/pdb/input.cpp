#include <iotbx/pdb/input.h>
#include <scitbx/misc/file_utils.h>
#include <scitbx/misc/fill_ranges.h>
#include <scitbx/auto_array.h>
#include <boost/scoped_array.hpp>

namespace iotbx { namespace pdb {

  //! Helper for input::construct_hierarchy_v1().
  template <typename UnsignedConstIterator>
  scitbx::auto_array<unsigned>
  union_of_unique_sorted(
    UnsignedConstIterator a, UnsignedConstIterator a_end,
    UnsignedConstIterator b, UnsignedConstIterator b_end)
  {
    scitbx::auto_array<unsigned> result(new unsigned[(a_end-a)+(b_end-b)]);
    unsigned* r = result.get();
    if      (a == a_end) {
      std::copy(b, b_end, r);
    }
    else if (b == b_end) {
      std::copy(a, a_end, r);
    }
    else {
      while (true) {
        if (*a < *b) {
          *r++ = *a++;
          if (a == a_end) {
            std::copy(b, b_end, r);
            break;
          }
        }
        else {
          *r++ = *b++;
          if (b == b_end) {
            std::copy(a, a_end, r);
            break;
          }
        }
      }
    }
    return result;
  }

  std::string
  line_info::format_exception_message() const
  {
    std::string result;
    if (error_source_info_.size() != 0) {
      result += error_source_info_;
      if (error_line_number_ != 0) {
        result += ", ";
      }
    }
    else if (error_line_number_ != 0) {
      result += "input ";
    }
    if (error_line_number_ != 0) {
      char buf[64];
      std::sprintf(buf, "line %u", error_line_number_);
      result += buf;
    }
    if (result.size() == 0) {
      result = "input line";
    }
    return result + ":\n  " + error_line_
      + "\n  " + std::string(std::max(1u,error_column_)-1, '-')
      + "^\n  " + error_message_;
  }

  //! Fortran-style conversion of an integer input field.
  int
  field_as_int(
    pdb::line_info& line_info,
    unsigned i_begin,
    unsigned i_end)
  {
    int result = 0;
    int sign = 0;
    bool have_non_blank = false;
    unsigned j_end = std::min(i_end, line_info.size);
    while (i_begin < j_end) {
      char c = line_info.data[i_begin++];
      switch (c) {
        case '+':
          if (have_non_blank || sign != 0) {
            line_info.set_error(i_begin, "unexpected plus sign.");
            return 0;
          }
          sign = 1;
          break;
        case '-':
          if (have_non_blank || sign != 0) {
            line_info.set_error(i_begin, "unexpected minus sign.");
            return 0;
          }
          sign = -1;
          break;
        case ' ':
        case '0': result *= 10;              break;
        case '1': result *= 10; result += 1; break;
        case '2': result *= 10; result += 2; break;
        case '3': result *= 10; result += 3; break;
        case '4': result *= 10; result += 4; break;
        case '5': result *= 10; result += 5; break;
        case '6': result *= 10; result += 6; break;
        case '7': result *= 10; result += 7; break;
        case '8': result *= 10; result += 8; break;
        case '9': result *= 10; result += 9; break;
        default:
          line_info.set_error(i_begin, "unexpected character.");
          return 0;
      }
      if (c != ' ') have_non_blank = true;
    }
    while (i_begin++ < i_end) result *= 10;
    if (sign < 0) return -result;
    return result;
  }

  //! Fortran-style conversion of a floating-point input field.
  /*! i_end-i_begin must be less than 32. This is not checked to
      maximize performance.
   */
  double
  field_as_double(
    pdb::line_info& line_info,
    unsigned i_begin,
    unsigned i_end)
  {
    char buf[32];
    char* b = buf;
    bool have_non_blank = false;
    unsigned i_col = i_begin;
    unsigned j_end = std::min(i_end, line_info.size);
    while (i_col < j_end) {
      char c = line_info.data[i_col++];
      if (c == ' ') {
        if (have_non_blank) *b++ = '0';
        else                i_begin++;
      }
      else {
        if (c == 'x' || c == 'X') {
          // suppress conversion of hexadecimal literals
          c = '?'; // any character that triggers an error in strtod()
        }
        *b++ = c;
        have_non_blank = true;
      }
    }
    if (!have_non_blank) return 0;
    while (i_col++ < i_end) *b++ = '0';
    *b = '\0';
    char *endptr;
    double result = std::strtod(buf, &endptr);
    if (endptr == buf) {
      line_info.set_error(i_begin+1, "not a floating-point number.");
    }
    if (endptr != b) {
      line_info.set_error(i_begin+1+(endptr-buf), "unexpected character.");
    }
    return result;
  }

  columns_73_76_evaluator::columns_73_76_evaluator(
    af::const_ref<std::string> const& lines,
    unsigned is_frequent_threshold_atom_records,
    unsigned is_frequent_threshold_other_records)
  :
    finding("Undecided."),
    is_old_style(false),
    number_of_atom_and_hetatm_lines(0)
  {
    columns_73_76_dict_t atom_columns_73_76_dict;
    columns_73_76_dict_t other_columns_73_76_dict;
    af::tiny<char, 4> header_idcode(' ', ' ', ' ', ' ');
    for(const std::string* line=lines.begin();line!=lines.end();line++) {
      if (line->size() < 6) continue;
      const char* line_data = line->data();
      bool is_atom_or_hetatm_record = (
           is_record_type("ATOM  ", line_data)
        || is_record_type("HETATM", line_data));
      if (is_atom_or_hetatm_record) {
        number_of_atom_and_hetatm_lines++;
      }
      if (is_record_type("HEADER", line_data)) {
        if (line->size() < 66) continue;
        const char* l = line_data + 62;
        char* h = header_idcode.begin();
        *h++ = *l++;
        *h++ = *l++;
        *h++ = *l++;
        *h   = *l  ;
      }
      if (line->size() < 80) continue;
      if (line_data[79] == ' ') continue;
      af::tiny<char, 4> columns_73_76;
      {
        bool have_non_blank = false;
        const char* l = line_data+72;
        unsigned i = 0;
        while (i < 4) {
          if (*l != ' ') have_non_blank = true;
          columns_73_76[i++] = *l++;
        }
        if (!have_non_blank) continue;
      }
      if (is_atom_or_hetatm_record) {
        atom_columns_73_76_dict[columns_73_76]++;
      }
      else if (!(   is_record_type("SIGATM", line_data)
                 || is_record_type("ANISOU", line_data)
                 || is_record_type("SIGUIJ", line_data)
                 || is_record_type("TER   ", line_data))) {
        other_columns_73_76_dict[columns_73_76]++;
      }
    }
    if (atom_columns_73_76_dict.size() == 0) {
      finding = "Blank columns 73-76 on ATOM and HETATM records.";
      return;
    }
    if (atom_columns_73_76_dict.size() == 1) {
      columns_73_76_t const& a = atom_columns_73_76_dict.begin()->first;
      if (a[0] != ' ' && a[3] != ' ') {
        if (other_columns_73_76_dict.size() == 0) {
          if (a.all_eq(header_idcode)) {
            is_old_style = true;
          }
        }
        if (other_columns_73_76_dict.size() == 1) {
          if (a.all_eq(other_columns_73_76_dict.begin()->first)) {
            is_old_style = true;
          }
        }
        if (is_old_style) {
          finding = "Exactly one common label in columns 73-76.";
          return;
        }
      }
    }
    unsigned sum_counts_common_four_character_field = 0;
    for(columns_73_76_dict_t::const_iterator
        a_item=atom_columns_73_76_dict.begin();
        a_item!=atom_columns_73_76_dict.end();
        a_item++) {
      columns_73_76_t const& a = a_item->first;
      if (a[0] == ' ' || a[3] == ' ') continue;
      columns_73_76_dict_t::const_iterator
        o_item = other_columns_73_76_dict.find(a);
      if (o_item != other_columns_73_76_dict.end()) {
        if (   a_item->second > is_frequent_threshold_atom_records
            && o_item->second > is_frequent_threshold_other_records) {
          finding = "Frequent common labels in columns 73-76.";
          is_old_style = true;
          return;
        }
        unsigned sum_counts = a_item->second + o_item->second;
        if (sum_counts_common_four_character_field < sum_counts) {
            sum_counts_common_four_character_field = sum_counts;
        }
      }
    }
    if (sum_counts_common_four_character_field == 0) {
      finding = "No common label in columns 73-76.";
      return;
    }
    // Compare first three characters only.
    columns_73_76_t a_begin = atom_columns_73_76_dict.begin()->first;
    if (a_begin[0] == ' ' || a_begin[2] == ' ') return;
    for(columns_73_76_dict_t::const_iterator
          a_item=atom_columns_73_76_dict.begin();
          a_item!=atom_columns_73_76_dict.end();
          a_item++) {
      columns_73_76_t const& a = a_item->first;
      if (   a[0] != a_begin[0]
          || a[1] != a_begin[1]
          || a[2] != a_begin[2]) return;
    }
    for(columns_73_76_dict_t::const_iterator
          o_item=other_columns_73_76_dict.begin();
          o_item!=other_columns_73_76_dict.end();
          o_item++) {
      columns_73_76_t const& o = o_item->first;
      if (   o[0] != a_begin[0]
          || o[1] != a_begin[1]
          || o[2] != a_begin[2]) return;
    }
    finding = "Exactly one common label in columns 73-76"
              " comparing only the first three characters.";
    is_old_style = true;
  }

  //! Fast processing of record types.
  namespace record_type {

    enum section {
      unknown,
      title,
      primary_structure,
      heterogen,
      secondary_structure,
      connectivity_annotation,
      miscellaneous_features,
      crystallographic,
      coordinate,
      connectivity,
      bookkeeping
    };

    enum id {
      xxxxxx,
      // Title Section
      header,
      onhold, // non-standard
      obslte,
      title_,
      caveat,
      compnd,
      source,
      keywds,
      expdta,
      author,
      revdat,
      sprsde,
      jrnl__,
      remark,
      ftnote, // non-standard
      // Primary Structure Section
      dbref_,
      seqadv,
      seqres,
      modres,
      // Heterogen Section
      het___,
      hetnam,
      hetsyn,
      formul,
      // Secondary Structure Section
      helix_,
      sheet_,
      turn__,
      // Connectivity Annotation Section
      ssbond,
      link__,
      hydbnd,
      sltbrg,
      cispep,
      // Miscellaneous Features Section
      site__,
      // Crystallographic and Coordinate Transformation Section
      cryst1,
      origx_,
      scale_,
      mtrix_,
      tvect_,
      // Coordinate Section
      model_,
      atom__,
      sigatm,
      anisou,
      siguij,
      ter___,
      break_, // non-standard
      hetatm,
      endmdl,
      // Connectivity Section
      conect,
      // Bookkeeping Section
      master,
      end___
    };

    /* requirements (not checked to maximize performance):
         line_size > 0
         name must be 6 characters exactly
         name[0] == line_data[0]
     */
    bool
    is_name(const char* name, const char* line_data, unsigned line_size)
    {
      if (line_size > 5) {
        if (*(++line_data) != *(++name)) return false;
        if (*(++line_data) != *(++name)) return false;
        if (*(++line_data) != *(++name)) return false;
        if (*(++line_data) != *(++name)) return false;
        if (*(++line_data) != *(++name)) return false;
        return true;
      }
      else {
        unsigned i = 0;
        while (++i < line_size) {
          if (*(++line_data) != *(++name)) return false;
        }
        while (++i < 6) {
          if (*(++name) != ' ') return false;
        }
      }
      return true;
    }

    bool
    is_name(
      const char* name,
      const char* line_data,
      unsigned line_size,
      const char* digits)
    {
      if (line_size < 6) return false;
      unsigned i = 0;
      while (++i < 5) {
        if (*(++line_data) != *(++name)) return false;
      }
      line_data++;
      while (*digits != '\0') {
        if (*line_data == *digits++) return true;
      }
      return false;
    }

    struct info
    {
      record_type::section section;
      record_type::id id;

      info() {}

      info(
        const char* line_data,
        unsigned line_size)
      {
        if (line_size == 0) {
          set(unknown, xxxxxx);
          return;
        }
        switch (line_data[0]) {
          case 'A':
            if (line_size >= 4) {
              // "ATOM  ": ignore columns 5 & 6 for compatibility with CNS 1.2
              if (   line_data[1] == 'T'
                  && line_data[2] == 'O'
                  && line_data[3] == 'M') {
                set(coordinate, atom__); return;
              }
              if (is_name("ANISOU", line_data, line_size)) {
                set(coordinate, anisou); return;
              }
              if (is_name("AUTHOR", line_data, line_size)) {
                set(title, author); return;
              }
            }
            break;
          case 'H':
            if (is_name("HETATM", line_data, line_size)) {
              set(coordinate, hetatm); return;
            }
            if (is_name("HELIX ", line_data, line_size)) {
              set(secondary_structure, helix_); return;
            }
            if (is_name("HEADER", line_data, line_size)) {
              set(title, header); return;
            }
            if (is_name("HYDBND", line_data, line_size)) {
              set(connectivity_annotation, hydbnd); return;
            }
            if (is_name("HET   ", line_data, line_size)) {
              set(heterogen, het___); return;
            }
            if (is_name("HETNAM", line_data, line_size)) {
              set(heterogen, hetnam); return;
            }
            if (is_name("HETSYN", line_data, line_size)) {
              set(heterogen, hetsyn); return;
            }
            break;
          case 'S':
            if (is_name("SIGATM", line_data, line_size)) {
              set(coordinate, sigatm); return;
            }
            if (is_name("SIGUIJ", line_data, line_size)) {
              set(coordinate, siguij); return;
            }
            if (is_name("SHEET ", line_data, line_size)) {
              set(secondary_structure, sheet_); return;
            }
            if (is_name("SSBOND", line_data, line_size)) {
              set(connectivity_annotation, ssbond); return;
            }
            if (is_name("SLTBRG", line_data, line_size)) {
              set(connectivity_annotation, sltbrg); return;
            }
            if (is_name("SOURCE", line_data, line_size)) {
              set(title, source); return;
            }
            if (is_name("SPRSDE", line_data, line_size)) {
              set(title, sprsde); return;
            }
            if (is_name("SEQADV", line_data, line_size)) {
              set(primary_structure, seqadv); return;
            }
            if (is_name("SEQRES", line_data, line_size)) {
              set(primary_structure, seqres); return;
            }
            if (is_name("SCALE ", line_data, line_size, "123")) {
              set(crystallographic, scale_); return;
            }
            if (is_name("SITE  ", line_data, line_size)) {
              set(miscellaneous_features, site__); return;
            }
          case 'C':
            if (is_name("CONECT", line_data, line_size)) {
              set(connectivity, conect); return;
            }
            if (is_name("CISPEP", line_data, line_size)) {
              set(connectivity_annotation, cispep); return;
            }
            if (is_name("COMPND", line_data, line_size)) {
              set(title, compnd); return;
            }
            if (is_name("CAVEAT", line_data, line_size)) {
              set(title, caveat); return;
            }
            if (is_name("CRYST1", line_data, line_size)) {
              set(crystallographic, cryst1); return;
            }
            break;
          case 'R':
            if (is_name("REMARK", line_data, line_size)) {
              set(title, remark); return;
            }
            if (is_name("REVDAT", line_data, line_size)) {
              set(title, revdat); return;
            }
            break;
          case 'T':
            if (is_name("TER   ", line_data, line_size)) {
              set(coordinate, ter___); return;
            }
            if (is_name("TURN  ", line_data, line_size)) {
              set(secondary_structure, turn__); return;
            }
            if (is_name("TITLE ", line_data, line_size)) {
              set(title, title_); return;
            }
            if (is_name("TVECT ", line_data, line_size)) {
              set(crystallographic, tvect_); return;
            }
            break;
          case 'B':
            if (is_name("BREAK ", line_data, line_size)) {
              set(coordinate, break_); return;
            }
            break;
          case 'L':
            if (is_name("LINK  ", line_data, line_size)) {
              set(connectivity_annotation, link__); return;
            }
            break;
          case 'M':
            if (is_name("MODEL ", line_data, line_size)) {
              set(coordinate, model_); return;
            }
            if (is_name("MODRES", line_data, line_size)) {
              set(primary_structure, modres); return;
            }
            if (is_name("MTRIX ", line_data, line_size, "123")) {
              set(crystallographic, mtrix_); return;
            }
            if (is_name("MASTER", line_data, line_size)) {
              set(bookkeeping, master); return;
            }
            break;
          case 'E':
            if (is_name("ENDMDL", line_data, line_size)) {
              set(coordinate, endmdl); return;
            }
            if (is_name("EXPDTA", line_data, line_size)) {
              set(title, expdta); return;
            }
            if (is_name("END   ", line_data, line_size)) {
              set(bookkeeping, end___); return;
            }
            break;
          case 'F':
            if (is_name("FORMUL", line_data, line_size)) {
              set(heterogen, formul); return;
            }
            if (is_name("FTNOTE", line_data, line_size)) {
              set(title, ftnote); return;
            }
          case 'O':
            if (is_name("ORIGX ", line_data, line_size, "123")) {
              set(crystallographic, origx_); return;
            }
            if (is_name("ONHOLD", line_data, line_size)) {
              set(title, onhold); return;
            }
            if (is_name("OBSLTE", line_data, line_size)) {
              set(title, obslte); return;
            }
          case 'K':
            if (is_name("KEYWDS", line_data, line_size)) {
              set(title, keywds); return;
            }
          case 'J':
            if (is_name("JRNL  ", line_data, line_size)) {
              set(title, jrnl__); return;
            }
          case 'D':
            if (is_name("DBREF ", line_data, line_size)) {
              set(primary_structure, dbref_); return;
            }
          default:
            break;
        }
        set(unknown, xxxxxx);
      }

      void
      set(record_type::section section_, record_type::id id_)
      {
        section = section_;
        id = id_;
      }
    };

  } // namespace record_type

  //! Tolerant processing of MODEL records.
  int
  read_model_number(pdb::line_info& line_info)
  {
    unsigned i_col = 6;
    for(;i_col<line_info.size;i_col++) {
      if (line_info.data[i_col] != ' ') break;
    }
    bool ok = true;
    char buf[16];
    unsigned i_buf = 0;
    for(;i_col<line_info.size;i_col++) {
      if (line_info.data[i_col] == ' ') break;
      buf[i_buf++] = line_info.data[i_col];
      if (i_buf == sizeof buf) {
        ok = false;
        break;
      }
    }
    if (ok && i_buf != 0) {
      buf[i_buf] = '\0';
      char *endptr;
      long result = std::strtol(buf, &endptr, 10);
      if (endptr == buf + i_buf) return result;
    }
    return field_as_int(line_info,10,14);
  }

  std::string
  input_atom_labels::pdb_format() const
  {
    char buf[128];
    std::sprintf(buf, "\"%4.4s%1.1s%3.3s%2.2s%4.4s%1.1s\"",
      name_begin(), altloc_begin(), resname_begin(), chain_begin(),
      resseq_begin(), icode_begin());
    std::string result;
    result += buf;
    if (segid_small().stripped_size() != 0) {
      result += " segid=\"" + segid() + "\"";
    }
    return result;
  }

  void
  input_atom_labels::check_equivalence(pdb::line_info& line_info) const
  {
    if      (!are_equal(line_info,12,4,name_begin())) {
      line_info.set_error(13, "name mismatch.");
    }
    else if (!are_equal(line_info,16,1,altloc_begin())) {
      line_info.set_error(17, "altloc mismatch.");
    }
    else if (!are_equal(line_info,17,3,resname_begin())) {
      line_info.set_error(18, "resname mismatch.");
    }
    else if (!are_equal(line_info,20,2,chain_begin())) {
      line_info.set_error(21, "chain mismatch.");
    }
    else if (!are_equal(line_info,22,4,resseq_begin())) {
      line_info.set_error(23, "resseq mismatch.");
    }
    else if (!are_equal(line_info,26,1,icode_begin())) {
      line_info.set_error(27, "icode mismatch.");
    }
    else if (   chain_begin()[1] == ' '
             && !are_equal(line_info,72,4,segid_begin())) {
      line_info.set_error(74, "segid mismatch.");
    }
  }

  //! Helper for fast sorting of input atom labels.
  struct i_seq_input_atom_labels
  {
    unsigned i_seq;
    input_atom_labels labels;

    bool
    operator<(i_seq_input_atom_labels const& other) const
    {
      switch (labels.compare(other.labels))
      {
        case -1: return true;
        case  1: return false;
        default: break;
      }
      return (i_seq < other.i_seq);
    }

    char
    altloc() const { return *labels.altloc_begin(); }
  };

  scitbx::auto_array<i_seq_input_atom_labels>
  sort_input_atom_labels(
    const pdb::input_atom_labels* input_atom_labels_list,
    unsigned i_begin,
    unsigned i_end)
  {
    scitbx::auto_array<i_seq_input_atom_labels>
      result(new i_seq_input_atom_labels[i_end-i_begin]);
    i_seq_input_atom_labels* r = result.get();
    const pdb::input_atom_labels* ial = input_atom_labels_list + i_begin;
    for(unsigned i_seq=i_begin;i_seq<i_end;i_seq++) {
      r->i_seq = i_seq;
      (r++)->labels = *ial++;
    }
    r = result.get();
    std::sort(r, &r[i_end-i_begin]);
    return result;
  }

  hierarchy_v1::atom
  process_atom_record(pdb::line_info& line_info, bool hetero)
  {
    // 13 - 16  Atom          name          Atom name.
    // 17       Character     altLoc        Alternate location indicator.
    // 31 - 38  Real(8.3)     x             Orthogonal coordinates for X in
    //                                      Angstroms.
    // 39 - 46  Real(8.3)     y             Orthogonal coordinates for Y in
    //                                      Angstroms.
    // 47 - 54  Real(8.3)     z             Orthogonal coordinates for Z in
    //                                      Angstroms.
    // 55 - 60  Real(6.2)     occupancy     Occupancy.
    // 61 - 66  Real(6.2)     tempFactor    Temperature factor.
    // 73 - 76  LString(4)    segID         Segment identifier, left-justified.
    // 77 - 78  LString(2)    element       Element symbol, right-justified.
    // 79 - 80  LString(2)    charge        Charge on the atom.
    return hierarchy_v1::atom(
      str4(line_info.data,line_info.size,12,' '), // name
      str4(line_info.data,line_info.size,72,' '), // segid
      str2(line_info.data,line_info.size,76,' '), // element
      str2(line_info.data,line_info.size,78,' '), // charge
      vec3(
        field_as_double(line_info,30,38),
        field_as_double(line_info,38,46),
        field_as_double(line_info,46,54)), // xyz
      vec3(0,0,0), // sigxyz
      field_as_double(line_info,54,60), // occ
      0, // sigocc
      field_as_double(line_info,60,66), // b
      0, // sigb
      sym_mat3(-1,-1,-1,-1,-1,-1), // uij
      sym_mat3(-1,-1,-1,-1,-1,-1), // siguij
      hetero,
      (   line_info.size > 16
       && line_info.data[16] != blank_altloc_char)); // flag_altloc
  }

  void
  process_sigatm_record(
    pdb::line_info& line_info,
    pdb::input_atom_labels const& input_atom_labels,
    hierarchy_v1::atom_data& atom_data)
  {
    atom_data.sigxyz = vec3(
      field_as_double(line_info,30,38),
      field_as_double(line_info,38,46),
      field_as_double(line_info,46,54));
    atom_data.sigocc = field_as_double(line_info,54,60);
    atom_data.sigb = field_as_double(line_info,60,66);
    input_atom_labels.check_equivalence(line_info);
  }

  void
  process_anisou_record(
    pdb::line_info& line_info,
    pdb::input_atom_labels const& input_atom_labels,
    hierarchy_v1::atom_data& atom_data)
  {
    // 29 - 35  Integer       U(1,1)
    // 36 - 42  Integer       U(2,2)
    // 43 - 49  Integer       U(3,3)
    // 50 - 56  Integer       U(1,2)
    // 57 - 63  Integer       U(1,3)
    // 64 - 70  Integer       U(2,3)
    atom_data.uij[0] = field_as_int(line_info,28,35);
    atom_data.uij[1] = field_as_int(line_info,35,42);
    atom_data.uij[2] = field_as_int(line_info,42,49);
    atom_data.uij[3] = field_as_int(line_info,49,56);
    atom_data.uij[4] = field_as_int(line_info,56,63);
    atom_data.uij[5] = field_as_int(line_info,63,70);
    atom_data.uij *= anisou_factor;
    input_atom_labels.check_equivalence(line_info);
  }

  void
  process_siguij_record(
    pdb::line_info& line_info,
    pdb::input_atom_labels const& input_atom_labels,
    hierarchy_v1::atom_data& atom_data)
  {
    atom_data.siguij[0] = field_as_int(line_info,28,35);
    atom_data.siguij[1] = field_as_int(line_info,35,42);
    atom_data.siguij[2] = field_as_int(line_info,42,49);
    atom_data.siguij[3] = field_as_int(line_info,49,56);
    atom_data.siguij[4] = field_as_int(line_info,56,63);
    atom_data.siguij[5] = field_as_int(line_info,63,70);
    atom_data.siguij *= anisou_factor;
    input_atom_labels.check_equivalence(line_info);
  }

  //! Processing of MODEL & ENDMDL records.
  class model_record_oversight
  {
    protected:
      pdb::line_info& line_info;
      enum styles { unknown, bare, encapsulated };
      int style;
      bool active_block;

    public:
      model_record_oversight(pdb::line_info& line_info_)
      :
        line_info(line_info_),
        style(unknown),
        active_block(false)
      {}

      bool
      atom_is_allowed_here()
      {
        if (style == bare || active_block) return true;
        if (style == unknown) {
          style = bare;
          return true;
        }
        line_info.set_error(1,
          "ATOM or HETATM record is outside MODEL/ENDMDL block.");
        return false;
      }

      bool
      model_is_allowed_here()
      {
        if (style == encapsulated) {
          if (active_block) {
            line_info.set_error(1,
              "Missing ENDMDL for previous MODEL record.");
            active_block = false;
            return false;
          }
          active_block = true;
          return true;
        }
        if (style == unknown) {
          style = encapsulated;
          active_block = true;
          return true;
        }
        line_info.set_error(1,
          "MODEL record must appear before any ATOM or HETATM records.");
        return false;
      }

      bool
      endmdl_is_allowed_here()
      {
        if (style != encapsulated || !active_block) {
          line_info.set_error(1,
            "No matching MODEL record.");
          return false;
        }
        active_block = false;
        return true;
      }

      bool
      expecting_endmdl_record() const { return active_block; }
  };

  //! Detection of chain boundaries.
  class chain_tracker
  {
    protected:
      af::shared<std::vector<unsigned> > chain_indices;
      std::vector<unsigned>* current_chain_indices;
      std::vector<unsigned> current_chain_indices_ignoring_segid;
      unsigned n_atoms;
      char previous_chain_and_segid[2+4];
      std::vector<str4> unique_segids;

      void
      evaluate_unique_segids()
      {
        // if unique_segids contains duplicates ignore segid
        std::set<str4> segid_set;
        std::vector<str4>::const_iterator us_end = unique_segids.end();
        for(std::vector<str4>::const_iterator
              us=unique_segids.begin();us!=us_end;us++) {
          if (!segid_set.insert(*us).second) {
            // we have a duplicate
            current_chain_indices->swap(current_chain_indices_ignoring_segid);
            break;
          }
        }
        current_chain_indices = 0;
        current_chain_indices_ignoring_segid.clear();
        unique_segids.clear();
      }

    public:
      chain_tracker()
      :
        current_chain_indices(0),
        n_atoms(0)
      {
        previous_chain_and_segid[0] = '\n';
      }

      void
      next_atom_labels(const pdb::input_atom_labels& current_labels)
      {
        if (current_chain_indices == 0) {
          chain_indices.push_back(std::vector<unsigned>());
          current_chain_indices = &chain_indices.back();
        }
        char* p = previous_chain_and_segid;
        if (*p != '\n') {
          // test if previous labels and current labels belong to
          // different chains:
          //   - change in chainid
          //   - if common chainid is blank: change in segid
          if (   p[0] != current_labels.chain_begin()[0]
              || p[1] != current_labels.chain_begin()[1]) {
            current_chain_indices->push_back(n_atoms);
            current_chain_indices_ignoring_segid.push_back(n_atoms);
          }
          else if (p[1] == ' ') {
            ++p;
            const char* c = current_labels.segid_begin();
            if (   (*++p != *  c)
                || (*++p != *++c)
                || (*++p != *++c)
                || (*++p != *++c)) {
              current_chain_indices->push_back(n_atoms);
            }
            p = previous_chain_and_segid;
          }
        }
        // copy chain and segid
        *p++ = current_labels.chain_begin()[0];
        *p++ = current_labels.chain_begin()[1];
        const char* c = current_labels.segid_begin();
        *p++ = *c++;
        *p++ = *c++;
        *p++ = *c++;
        *p   = *c;
        // keep track of unique segids
        if (unique_segids.size() == 0) {
          unique_segids.push_back(current_labels.segid_small());
        }
        else {
          c = current_labels.segid_begin();
          p = unique_segids.back().elems;
          if (   *p++ != *c++
              || *p++ != *c++
              || *p++ != *c++
              || *p   != *c) {
            unique_segids.push_back(current_labels.segid_small());
          }
        }
        n_atoms++;
      }

      void
      transition()
      {
        if (*previous_chain_and_segid != '\n') {
          if (current_chain_indices != 0) {
            current_chain_indices->push_back(n_atoms);
            current_chain_indices_ignoring_segid.push_back(n_atoms);
          }
          *previous_chain_and_segid = '\n';
        }
      }

      void
      endmdl()
      {
        transition();
        if (current_chain_indices == 0) {
          chain_indices.push_back(std::vector<unsigned>());
        }
        else {
          evaluate_unique_segids();
        }
      }

      af::shared<std::vector<unsigned> >
      finish()
      {
        transition();
        if (current_chain_indices != 0) {
          evaluate_unique_segids();
        }
        return chain_indices;
      }
  };

  void
  pre_allocate_atom_parents(
    hierarchy_v1::atom& atom, unsigned number_of_parents)
  {
     bool number_of_old_parents = atom.reset_parents();
     SCITBX_ASSERT(number_of_old_parents == 0);
     atom.pre_allocate_parents(number_of_parents);
  }

  input::input(std::string const& file_name)
  :
    source_info_("file " + file_name)
  {
    process(scitbx::misc::file_to_lines(file_name).const_ref());
  }

  input::input(
    const char* source_info,
    af::const_ref<std::string> const& lines)
  :
    source_info_(source_info ? source_info : "")
  {
    process(lines);
  }

  void
  input::process(af::const_ref<std::string> const& lines)
  {
    name_selection_cache_is_up_to_date_ = false;
    altloc_selection_cache_is_up_to_date_ = false;
    resname_selection_cache_is_up_to_date_ = false;
    chain_selection_cache_is_up_to_date_ = false;
    resseq_selection_cache_is_up_to_date_ = false;
    icode_selection_cache_is_up_to_date_ = false;
    segid_selection_cache_is_up_to_date_ = false;
    columns_73_76_evaluator columns_73_76_eval(lines);
    input_atom_labels_list_.reserve(
        input_atom_labels_list_.size()
      + columns_73_76_eval.number_of_atom_and_hetatm_lines);
    atom_serial_number_strings_.reserve(
        atom_serial_number_strings_.size()
      + columns_73_76_eval.number_of_atom_and_hetatm_lines);
    atoms_.reserve(
        atoms_.size()
      + columns_73_76_eval.number_of_atom_and_hetatm_lines);
    input_atom_labels* current_input_atom_labels = 0;
    hierarchy_v1::atom_data* current_atom_data = 0;
    bool expect_anisou = false;
    bool expect_sigatm = false;
    bool expect_siguij = false;
    const char* error_message_no_matching_atom
      = "no matching ATOM or HETATM record.";
    unsigned atom___counts = 0;
    unsigned hetatm_counts = 0;
    unsigned sigatm_counts = 0;
    unsigned anisou_counts = 0;
    unsigned siguij_counts = 0;
    pdb::line_info line_info(source_info_.c_str());
    pdb::model_record_oversight model_record_oversight(line_info);
    pdb::chain_tracker chain_tracker;
    for(unsigned i_line=0;i_line<lines.size();i_line++) {
      std::string const& line = lines[i_line];
      line_info.line_number++;
      line_info.size = static_cast<unsigned>(line.size());
      if (   columns_73_76_eval.is_old_style
          && line_info.size > 72) {
        line_info.size = 72;
      }
      line_info.data = line.data();
      record_type::info record_type_info(line_info.data, line_info.size);
      if      (record_type_info.id == record_type::atom__) {
        if (model_record_oversight.atom_is_allowed_here()) {
          input_atom_labels_list_.push_back(input_atom_labels(line_info));
          atom_serial_number_strings_.push_back(std::string(
            input_atom_labels::extract_serial_number_string(
              line_info).begin(), 5));
          atoms_.push_back(process_atom_record(line_info,/*hetero*/false));
          if (line_info.error_occured()) {
            input_atom_labels_list_.pop_back();
            atom_serial_number_strings_.pop_back();
            atoms_.pop_back();
          }
          else {
            atom___counts++;
            current_input_atom_labels = &input_atom_labels_list_.back();
            chain_tracker.next_atom_labels(*current_input_atom_labels);
            current_atom_data = atoms_.back().data.get();
            expect_anisou = true;
            expect_sigatm = true;
            expect_siguij = true;
          }
        }
      }
      else if (record_type_info.id == record_type::hetatm) {
        if (model_record_oversight.atom_is_allowed_here()) {
          input_atom_labels_list_.push_back(input_atom_labels(line_info));
          atom_serial_number_strings_.push_back(std::string(
            input_atom_labels::extract_serial_number_string(
              line_info).begin(), 5));
          atoms_.push_back(process_atom_record(line_info,/*hetero*/true));
          if (line_info.error_occured()) {
            input_atom_labels_list_.pop_back();
            atom_serial_number_strings_.pop_back();
            atoms_.pop_back();
          }
          else {
            hetatm_counts++;
            current_input_atom_labels = &input_atom_labels_list_.back();
            chain_tracker.next_atom_labels(*current_input_atom_labels);
            current_atom_data = atoms_.back().data.get();
            expect_anisou = true;
            expect_sigatm = true;
            expect_siguij = true;
          }
        }
      }
      else if (record_type_info.id == record_type::anisou) {
        if (!expect_anisou) {
          line_info.set_error(1, error_message_no_matching_atom);
        }
        else {
          expect_anisou = false;
          anisou_counts++;
          process_anisou_record(
            line_info, *current_input_atom_labels, *current_atom_data);
        }
      }
      else if (record_type_info.id == record_type::sigatm) {
        if (!expect_sigatm) {
          line_info.set_error(1, error_message_no_matching_atom);
        }
        else {
          expect_sigatm = false;
          sigatm_counts++;
          process_sigatm_record(
            line_info, *current_input_atom_labels, *current_atom_data);
        }
      }
      else if (record_type_info.id == record_type::siguij) {
        if (!expect_siguij) {
          line_info.set_error(1, error_message_no_matching_atom);
        }
        else {
          expect_siguij = false;
          siguij_counts++;
          process_siguij_record(
            line_info, *current_input_atom_labels, *current_atom_data);
        }
      }
      else {
        record_type_counts_[
          str6(line_info.data, line_info.size, 0, ' ')]++;
        current_input_atom_labels = 0;
        current_atom_data = 0;
        expect_anisou = false;
        expect_sigatm = false;
        expect_siguij = false;
        if      (   record_type_info.id == record_type::remark
                 || record_type_info.id == record_type::ftnote) {
          remark_section_.push_back(line_info.strip_data());
        }
        else if (record_type_info.id == record_type::ter___) {
          ter_indices_.push_back(input_atom_labels_list_.size());
          chain_tracker.transition();
        }
        else if (record_type_info.id == record_type::break_) {
          break_indices_.push_back(input_atom_labels_list_.size());
          break_record_line_numbers.push_back(line_info.line_number);
        }
        else if (record_type_info.id == record_type::model_) {
          if (model_record_oversight.model_is_allowed_here()) {
            model_numbers_.push_back(read_model_number(line_info));
          }
        }
        else if (record_type_info.id == record_type::endmdl) {
          if (model_record_oversight.endmdl_is_allowed_here()) {
            model_indices_.push_back(input_atom_labels_list_.size());
            chain_tracker.endmdl();
          }
        }
        else if (record_type_info.section == record_type::title) {
          title_section_.push_back(line_info.strip_data());
          chain_tracker.transition();
        }
        else if (record_type_info.section
                 == record_type::primary_structure) {
          primary_structure_section_.push_back(line_info.strip_data());
          chain_tracker.transition();
        }
        else if (record_type_info.section
                 == record_type::heterogen) {
          heterogen_section_.push_back(line_info.strip_data());
          chain_tracker.transition();
        }
        else if (record_type_info.section
                 == record_type::secondary_structure) {
          secondary_structure_section_.push_back(line_info.strip_data());
          chain_tracker.transition();
        }
        else if (record_type_info.section
                 == record_type::connectivity_annotation) {
          connectivity_annotation_section_.push_back(
            line_info.strip_data());
          chain_tracker.transition();
        }
        else if (record_type_info.section
                 == record_type::miscellaneous_features) {
          miscellaneous_features_section_.push_back(
            line_info.strip_data());
          chain_tracker.transition();
        }
        else if (record_type_info.section
                 == record_type::crystallographic) {
          crystallographic_section_.push_back(line_info.strip_data());
          chain_tracker.transition();
        }
        else if (record_type_info.section
                 == record_type::connectivity) {
          connectivity_section_.push_back(line_info.strip_data());
          chain_tracker.transition();
        }
        else if (record_type_info.section
                 == record_type::bookkeeping) {
          bookkeeping_section_.push_back(line_info.strip_data());
          chain_tracker.transition();
        }
        else if (!line_info.is_blank_line()) {
          unknown_section_.push_back(line_info.strip_data());
        }
      }
      line_info.check_and_throw_runtime_error();
    }
    chain_indices_ = chain_tracker.finish();
    if (model_record_oversight.expecting_endmdl_record()) {
      throw std::runtime_error("ENDMDL record missing at end of input.");
    }
    if (   model_indices_.size() == 0
        && input_atom_labels_list_.size() != 0) {
      model_numbers_.push_back(0);
      model_indices_.push_back(input_atom_labels_list_.size());
    }
    SCITBX_ASSERT(model_indices_.size() == model_numbers_.size());
    SCITBX_ASSERT(model_indices_.size() == chain_indices_.size());
    if (atom___counts != 0) record_type_counts_["ATOM  "] += atom___counts;
    if (hetatm_counts != 0) record_type_counts_["HETATM"] += hetatm_counts;
    if (sigatm_counts != 0) record_type_counts_["SIGATM"] += sigatm_counts;
    if (anisou_counts != 0) record_type_counts_["ANISOU"] += anisou_counts;
    if (siguij_counts != 0) record_type_counts_["SIGUIJ"] += siguij_counts;
    construct_hierarchy_v1_was_called_before = false;
    number_of_alternative_groups_with_blank_altloc_ = 0;
    number_of_alternative_groups_without_blank_altloc_ = 0;
    number_of_chains_with_altloc_mix_ = 0;
  }

  bool
  input::model_numbers_are_unique() const
  {
    std::set<int> unique_numbers(
      model_numbers_.begin(), model_numbers_.end());
    return (unique_numbers.size() == model_numbers_.size());
  }

  af::shared<std::size_t>
  input::model_atom_counts() const
  {
    af::shared<std::size_t> result(af::reserve(model_indices_.size()));
    range_loop<std::size_t> mr(model_indices_.const_ref());
    while (mr.next()) result.push_back(mr.size);
    return result;
  }

  af::shared<std::vector<unsigned> >
  input::find_duplicate_atom_labels() const
  {
    af::shared<std::vector<unsigned> > result;
    const input_atom_labels* iall = input_atom_labels_list_.begin();
    range_loop<std::size_t> mr(model_indices_.const_ref());
    while (mr.next()) {
      if (mr.size < 2) continue;
      std::map<unsigned, std::vector<unsigned> > dup_map;
      scitbx::auto_array<i_seq_input_atom_labels> sorted_ials(
        sort_input_atom_labels(iall, mr.begin, mr.end));
      const i_seq_input_atom_labels* sj = sorted_ials.get();
      const i_seq_input_atom_labels* si = sj++;
      for(unsigned js=1;js<mr.size;js++) {
        if (sj->labels != si->labels) {
          si = sj++;
        }
        else {
          dup_map[si->i_seq].push_back((sj++)->i_seq);
        }
      }
      for(std::map<unsigned, std::vector<unsigned> >::iterator
            di=dup_map.begin(); di!=dup_map.end(); di++) {
        di->second.push_back(di->first);
        std::sort(di->second.begin(), di->second.end());
        result.push_back(std::vector<unsigned>());
        result.back().swap(di->second); // swap avoids deep copy
      }
    }
    return result;
  }

  hierarchy_v1::root
  input::construct_hierarchy_v1()
  {
    number_of_alternative_groups_with_blank_altloc_ = 0;
    number_of_alternative_groups_without_blank_altloc_ = 0;
    number_of_chains_with_altloc_mix_ = 0;
    i_seqs_alternative_group_with_blank_altloc_.clear();
    i_seqs_alternative_group_without_blank_altloc_.clear();
    af::const_ref<int>
      model_numbers = model_numbers_.const_ref();
    af::const_ref<std::vector<unsigned> >
      chain_indices = chain_indices_.const_ref();
    SCITBX_ASSERT(chain_indices.size() == model_numbers.size());
    hierarchy_v1::root result;
    result.new_models(model_numbers.size());
    af::shared<std::size_t>
      first_i_seqs_alternative_group_with_blank_altloc;
    static const std::size_t large_residue_size = 100; // not critical
    std::vector<unsigned> residue_indices;       // outside loop to
    residue_indices.reserve(large_residue_size); // allocate only once
    const input_atom_labels* iall = input_atom_labels_list_.begin();
    hierarchy_v1::atom* atoms = atoms_.begin();
    unsigned next_chain_range_begin = 0;
    for(unsigned i_model=0;i_model<model_numbers.size();i_model++) {
      hierarchy_v1::model model = result.models()[i_model];
      model.data->id = model_numbers[i_model];
      model.new_chains(chain_indices[i_model].size());
      range_loop<unsigned> ch_r(
        chain_indices[i_model], next_chain_range_begin);
      for(unsigned i_chain=0;ch_r.next();i_chain++) {
        hierarchy_v1::chain chain = model.get_chain(i_chain);
        chain.data->id = iall[ch_r.begin].chain();
        // convert break_indices to break_range_ids
        boost::scoped_array<unsigned>
          break_range_ids(new unsigned[ch_r.size]);
        scitbx::misc::fill_ranges(
          ch_r.begin, ch_r.end,
          break_indices_.begin(), break_indices_.end(),
          break_range_ids.get());
        // separate conformers
        std::vector<unsigned> common_sel;
        common_sel.reserve(ch_r.size);
        typedef std::map<char, std::vector<unsigned> > alt_t;
        alt_t alternatives;
        {
          unsigned n_alternative_groups_with_blank_altloc = 0;
          unsigned n_alternative_groups_without_blank_altloc = 0;
          scitbx::auto_array<i_seq_input_atom_labels> sorted_ials(
            sort_input_atom_labels(iall, ch_r.begin, ch_r.end));
          const i_seq_input_atom_labels* si = sorted_ials.get();
          const i_seq_input_atom_labels* se = si + ch_r.size;
          const i_seq_input_atom_labels* sj = si;
          while (sj != se) {
            if (sj->altloc() == blank_altloc_char) {
              // skip over all blank altlocs
              sj++;
            }
            else {
              bool this_group_has_blank_altloc = false;
              alternatives[sj->altloc()].push_back(sj->i_seq);
              const i_seq_input_atom_labels* sb = sj;
              while (sb != si) {
                // scan backwards to find beginning of group
                if (!sj->labels.equal_ignoring_altloc((--sb)->labels)) {
                  sb++;
                  break;
                }
                alternatives[blank_altloc_char].push_back(sb->i_seq);
                this_group_has_blank_altloc = true;
              }
              // process all preceeding with blank altlocs
              while (si != sb) common_sel.push_back((si++)->i_seq);
              si = sj;
              while (++si != se) {
                // scan forward to find end of group
                if (!sj->labels.equal_ignoring_altloc(si->labels)) {
                  break;
                }
                alternatives[si->altloc()].push_back(si->i_seq);
                if (si->altloc() == blank_altloc_char) {
                  this_group_has_blank_altloc = true;
                }
              }
              sj = si;
              if (this_group_has_blank_altloc) {
                n_alternative_groups_with_blank_altloc++;
                // keep track of i_seqs, for comprehensive error reporting
                if (i_seqs_alternative_group_with_blank_altloc_.size()
                      == 0) {
                  i_seqs_alternative_group_with_blank_altloc_.reserve(
                    static_cast<std::size_t>(si - sb));
                  while (sb != si) {
                    i_seqs_alternative_group_with_blank_altloc_
                      .push_back((sb++)->i_seq);
                  }
                  if (first_i_seqs_alternative_group_with_blank_altloc
                        .size() == 0) {
                    first_i_seqs_alternative_group_with_blank_altloc =
                      i_seqs_alternative_group_with_blank_altloc_
                        .deep_copy();
                  }
                }
              }
              else {
                n_alternative_groups_without_blank_altloc++;
                // keep track of i_seqs, for comprehensive error reporting
                if (i_seqs_alternative_group_without_blank_altloc_.size()
                      == 0) {
                  i_seqs_alternative_group_without_blank_altloc_.reserve(
                    static_cast<std::size_t>(si - sb));
                  while (sb != si) {
                    i_seqs_alternative_group_without_blank_altloc_
                      .push_back((sb++)->i_seq);
                  }
                }
              }
            }
          }
          // process all remaining with blank altlocs
          while (si != se) common_sel.push_back((si++)->i_seq);
          number_of_alternative_groups_with_blank_altloc_
            += n_alternative_groups_with_blank_altloc;
          number_of_alternative_groups_without_blank_altloc_
            += n_alternative_groups_without_blank_altloc;
          if (   n_alternative_groups_with_blank_altloc != 0
              && n_alternative_groups_without_blank_altloc != 0) {
            number_of_chains_with_altloc_mix_++;
          }
          if (number_of_chains_with_altloc_mix_ == 0) {
            i_seqs_alternative_group_with_blank_altloc_.clear();
            i_seqs_alternative_group_without_blank_altloc_.clear();
          }
        }
        std::sort(common_sel.begin(), common_sel.end());
        // trick to simplify this algorithm
        std::size_t alternatives_size = alternatives.size();
        if (alternatives_size == 0) {
          alternatives[blank_altloc_char] = std::vector<unsigned>();
          alternatives_size++;
        }
        // pre-allocate to avoid repeated re-allocation
        unsigned n_cs = common_sel.size();
        if (n_cs != 0) {
          const unsigned* cs_i = &*common_sel.begin();
          pre_allocate_atom_parents(atoms[*cs_i], alternatives_size);
          for(unsigned i_cs=1;i_cs<n_cs;i_cs++) {
            pre_allocate_atom_parents(atoms[*(++cs_i)], alternatives_size);
          }
        }
        // loop over conformers
        chain.new_conformers(alternatives_size);
        alt_t::iterator a_end = alternatives.end();
        unsigned i_conformer = 0;
        for(alt_t::iterator
              alt=alternatives.begin();alt!=a_end;alt++,i_conformer++) {
          std::vector<unsigned>& alt_sel = alt->second;
          std::sort(alt_sel.begin(), alt_sel.end());
          unsigned n_as = alt_sel.size();
          if (n_as) {
            const unsigned* as_i = &*alt_sel.begin();
            pre_allocate_atom_parents(atoms[*as_i], 1U);
            for(unsigned i_as=1;i_as<n_as;i_as++) {
              pre_allocate_atom_parents(atoms[*(++as_i)], 1U);
            }
          }
          // combine common_sel and alt_sel to obtain the selection
          // for one conformer
          unsigned n_cfs = n_as + n_cs;
          scitbx::auto_array<unsigned> conf_sel;
          const unsigned* cfs_i0;
          if (n_as == 0) {
            cfs_i0 = (n_cs ? &*common_sel.begin() : 0);
          }
          else {
            conf_sel = union_of_unique_sorted(
              common_sel.begin(), common_sel.end(),
              alt_sel.begin(), alt_sel.end());
            cfs_i0 = conf_sel.get();
          }
          // loop over atoms to determine residues
          if (n_cfs != 0) {
            // pre-scan to determine the number of residues
            const unsigned* cfs_i = cfs_i0;
            const input_atom_labels* leading_ial = &iall[*cfs_i];
            residue_indices.clear();
            for(unsigned i_cfs=1;i_cfs<n_cfs;i_cfs++) {
              const input_atom_labels* ial = &iall[*(++cfs_i)];
              if (!ial->is_in_same_residue(*leading_ial)) {
                leading_ial = ial;
                residue_indices.push_back(i_cfs);
              }
            }
            residue_indices.push_back(n_cfs);
            hierarchy_v1::conformer
              conformer = chain.get_conformer(i_conformer);
            conformer.data->id = std::string(1, alt->first);
            // pre-allocate to avoid repeated re-allocation
            conformer.pre_allocate_residues(residue_indices.size());
            // copy atoms to residues
            unsigned prev_break_range_id = ch_r.size;
            range_loop<unsigned> res_r(af::const_ref<unsigned>(
              &*residue_indices.begin(), residue_indices.size()));
            cfs_i = cfs_i0;
            for(unsigned i_res=0;res_r.next();i_res++) {
              const input_atom_labels* ial = &iall[*cfs_i];
              unsigned curr_break_range_id \
                = break_range_ids[(*cfs_i)-ch_r.begin];
              hierarchy_v1::residue residue = conformer.new_residue(
                ial->resname_small().elems,
                ial->resseq_small().elems,
                ial->icode_small().elems,
                prev_break_range_id==curr_break_range_id);
              prev_break_range_id = curr_break_range_id;
              residue.pre_allocate_atoms(res_r.size);
              residue.add_atom(atoms[*cfs_i]);
              for(unsigned i=1;i<res_r.size;i++) {
                residue.add_atom(atoms[*(++cfs_i)]);
              }
              if (break_range_ids[(*cfs_i++)-ch_r.begin]
                  != prev_break_range_id) {
                char buf[64];
                std::sprintf(buf,
                  "Misplaced BREAK record (%s line %u).",
                  source_info_.size()
                    ? (source_info_ + ",").c_str()
                    : "input",
                  break_record_line_numbers[prev_break_range_id]);
                throw std::runtime_error(buf);
              }
            }
            SCITBX_ASSERT(conformer.residues().size()
                       == residue_indices.size());
          }
        }
      }
      next_chain_range_begin = ch_r.end;
    }
    if (number_of_chains_with_altloc_mix_ == 0) {
      i_seqs_alternative_group_with_blank_altloc_.swap(
        first_i_seqs_alternative_group_with_blank_altloc);
      // free memory
      {
        af::shared<std::size_t> empty;
        i_seqs_alternative_group_without_blank_altloc_.swap(empty);
      }
    }
    construct_hierarchy_v1_was_called_before = true;
    return result;
  }

  std::map<std::string, unsigned>
  input::atom_element_counts() const
  {
    std::map<std::string, unsigned> result;
    std::map<str2, unsigned> counts;
    const hierarchy_v1::atom* atoms_end = atoms_.end();
    for(const hierarchy_v1::atom* a=atoms_.begin();a!=atoms_end;a++) {
      counts[a->data->element]++;
    }
    for(std::map<str2, unsigned>::const_iterator
          i=counts.begin();
          i!=counts.end();i++) {
      result[i->first.elems] = i->second;
    }
    return result;
  }

  af::shared<std::size_t>
  input::extract_atom_hetero() const
  {
    af::shared<std::size_t> result;
    const hierarchy_v1::atom* atoms_end = atoms_.end();
    std::size_t i_seq = 0;
    for(const hierarchy_v1::atom* a=atoms_.begin();a!=atoms_end;a++,i_seq++) {
      if (a->data->hetero) result.push_back(i_seq);
    }
    return result;
  }

  af::shared<std::size_t>
  input::extract_atom_flag_altloc() const
  {
    af::shared<std::size_t> result;
    const hierarchy_v1::atom* atoms_end = atoms_.end();
    std::size_t i_seq = 0;
    for(const hierarchy_v1::atom* a=atoms_.begin();a!=atoms_end;a++,i_seq++) {
      if (a->data->flag_altloc) result.push_back(i_seq);
    }
    return result;
  }

  void
  input::reset_atom_tmp(int first_value, int increment) const
  {
    const hierarchy_v1::atom* atoms_end = atoms_.end();
    int value = first_value;
    for(const hierarchy_v1::atom* a=atoms_.begin();a!=atoms_end;a++) {
      a->data->tmp = value;
      value += increment;
    }
  }

}} // namespace iotbx::pdb
