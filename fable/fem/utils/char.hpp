#ifndef FEM_UTILS_CHAR_HPP
#define FEM_UTILS_CHAR_HPP

namespace fem { namespace utils {

  inline
  bool
  is_end_of_line(
    int c)
  {
    return (c == '\r'
         || c == '\n');
  }

  inline
  bool
  is_whitespace(
    int c)
  {
    return (c == ' '
         || c == '\t'
         || is_end_of_line(c));
  }

  //! Assumes ASCII or similar.
  inline
  bool
  is_digit(
    int c)
  {
    return (c >= '0' && c <= '9');
  }

  //! Assumes ASCII or similar.
  inline
  int
  digit_as_int(
    int c)
  {
    return c - '0';
  }

  //! To avoid locale environment surprises (assumes ASCII or similar).
  inline
  int
  to_lower(
    int c)
  {
    if (c < 'A') return c;
    if (c > 'Z') return c;
    return c + ('a' - 'A');
  }

}} // namespace fem::utils

#endif // GUARD
