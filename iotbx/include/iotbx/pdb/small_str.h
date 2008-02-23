#ifndef IOTBX_PDB_SMALL_STR_H
#define IOTBX_PDB_SMALL_STR_H

#include <cstring>
#include <ctype.h> // cannot use <cctype> since MIPSpro 7.3.1.2 defines macros

namespace iotbx { namespace pdb {

  inline
  void
  copy_padded(
    char* dest,
    unsigned dest_size,
    const char *src,
    unsigned src_size,
    char pad_with)
  {
    unsigned i = 0;
    if (src != 0) {
      unsigned n = (dest_size < src_size ? dest_size : src_size);
      while(i<n) {
        char c = src[i];
        if (c == '\0') break;
        dest[i++] = c;
      }
    }
    while(i<dest_size) dest[i++] = pad_with;
  }

  template <unsigned N>
  struct small_str
  {
    char elems[N+1];

    small_str() { elems[0] = '\0'; }

    small_str(char c)
    {
      elems[0] = c;
      elems[1] = '\0';
    }

    small_str(const char* s)
    {
      replace_with(s);
    }

    small_str(
      const char* s_data,
      unsigned s_size,
      unsigned i_begin=0,
      char pad_with='\0')
    {
      unsigned j = 0;
      while (i_begin < s_size) {
        if (j == N) {
          elems[j] = '\0';
          return;
        }
        elems[j++] = s_data[i_begin++];
      }
      if (pad_with != '\0') {
        while (j < N) {
          elems[j++] = ' ';
        }
      }
      elems[j] = '\0';
    }

    bool
    replace_with(const char* s)
    {
      if (s == 0) s = "";
      unsigned i = 0;
      while(i<N) {
        elems[i++] = *s;
        if (*s++ == '\0') return true;
      }
      elems[i] = '\0';
      return (*s == '\0');
    }

    static
    unsigned
    capacity() { return N; }

    unsigned
    size() const { return std::strlen(elems); }

    unsigned
    stripped_size() const
    {
      const char* e = elems;
      do {
        if (*e == '\0') return 0;
      }
      while (isspace(*e++));
      unsigned i = 0;
      for(unsigned j=0;e[j]!='\0';j++) {
        if (!isspace(e[j])) i = j;
      }
      return i+1;
    }

    bool
    operator==(small_str const& other) const
    {
      return (std::strcmp(elems, other.elems) == 0);
    }

    bool
    operator!=(small_str const& other) const
    {
      return (std::strcmp(elems, other.elems) != 0);
    }

    bool
    operator<(small_str const& other) const
    {
      return (std::strcmp(elems, other.elems) < 0);
    }

    bool
    operator>(small_str const& other) const
    {
      return (std::strcmp(elems, other.elems) > 0);
    }

    bool
    operator<=(small_str const& other) const
    {
      return (std::strcmp(elems, other.elems) <= 0);
    }

    bool
    operator>=(small_str const& other) const
    {
      return (std::strcmp(elems, other.elems) >= 0);
    }

    void
    copy_padded(char* dest, unsigned dest_size, char pad_with) const
    {
      pdb::copy_padded(dest, dest_size, elems, N, pad_with);
    }
  };

  typedef small_str<1> str1;
  typedef small_str<2> str2;
  typedef small_str<3> str3;
  typedef small_str<4> str4;
  typedef small_str<6> str6;

}} // namespace iotbx::pdb

#endif // IOTBX_PDB_SMALL_STR_H
