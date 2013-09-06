#include "iotbx/xplor/map_writer.h"
#include <iotbx/error.h>
#include <cctbx/uctbx.h>
#include <scitbx/array_family/tiny_algebra.h>

#include <fstream>
#include <cstdlib>
#include <cstdio>

namespace iotbx { namespace xplor {

namespace af = scitbx::af;

template <unsigned Width>
struct format_e
{
  static void
  throw_error()
  {
    throw scitbx::error("Floating-point value too large for format.");
  }

  format_e(const char* fmt, double val)
  {
    if(std::fabs(val)<1e-99) val=0.;
#if !defined(BOOST_MSVC)
    s = buf;
    std::sprintf(buf, fmt, val);
    if (*(s + Width)) throw_error();
#else
    s = buf + 1;
    std::sprintf(s, fmt, val);
    char* p = s + Width;
    if (*p) {
      p++;
      if (*p) throw_error();
    }
    else {
      s--;
      *s = ' ';
    }
    if (*(p-3) != '0') throw_error();
    *(p-3) = *(p-2);
    *(p-2) = *(p-1);
    *(p-1) = '\0';
#endif
  }

  char buf[32];
  char* s;
};

static FILE*
write_head(
  std::string const& file_name,
  cctbx::uctbx::unit_cell const& unit_cell)
{
  FILE* fh = fopen(file_name.c_str(), "ab");
  IOTBX_ASSERT(fh != 0);
  for(std::size_t i=0;i<6;i++) {
    fprintf(fh, "%s",
      format_e<12>("%12.5E", unit_cell.parameters()[i]).s);
  }
  fprintf(fh, "\n");
  fprintf(fh, "ZYX\n");
  return fh;
}

static FILE*
write_head(
  std::string const& file_name,
  cctbx::uctbx::unit_cell const& unit_cell,
  const scitbx::af::int3 &n,
  const scitbx::af::int3 &first,
  const scitbx::af::int3 &last)
{
  FILE* fh = fopen(file_name.c_str(), "wb");
  CCTBX_ASSERT(fh != 0);
  fprintf(fh, "\n%8d !NTITLE\n", 1);
  fprintf(fh, "%-264s\n", " REMARKS iotbx::xplor");
  fprintf(fh, " %7d %7d %7d %7d %7d %7d %7d %7d %7d\n", n[0], first[0], last[0],
      n[1], first[1], last[1], n[2], first[2], last[2]);
  for(std::size_t i=0;i<6;i++) {
    fprintf(fh, "%s",
      format_e<12>("%12.5E", unit_cell.parameters()[i]).s);
  }
  fprintf(fh, "\n");
  fprintf(fh, "ZYX\n");
  return fh;
}

static void
write_tail(
  FILE* fh,
  double average,
  double standard_deviation)
{
  fprintf(fh, "   -9999\n");
  fprintf(fh, "%s%s\n",
    format_e<12>("%12.4E", average).s,
    format_e<12>("%12.4E", standard_deviation).s);
  fclose(fh);
}

void
map_writer_box(
  std::string const& file_name,
  cctbx::uctbx::unit_cell const& unit_cell,
  af::const_ref<double, af::flex_grid<> > const& data,
  double average,
  double standard_deviation)
{
  IOTBX_ASSERT(data.accessor().nd() == 3);
  IOTBX_ASSERT(data.accessor().all().all_gt(0));
  IOTBX_ASSERT(!data.accessor().is_padded());
  FILE* fh = write_head(file_name, unit_cell);
  af::const_ref<double, af::c_grid<3> > data_ref(
    data.begin(),
    af::c_grid<3>(af::adapt(data.accessor().all())));
  for(std::size_t iz=0;iz<data_ref.accessor()[2];iz++) {
    fprintf(fh, "%8lu\n", static_cast<unsigned long>(iz));
    int i_fld = 0;
    for(std::size_t iy=0;iy<data_ref.accessor()[1];iy++) {
      for(std::size_t ix=0;ix<data_ref.accessor()[0];ix++) {
        fprintf(fh, "%s", format_e<12>("%12.5E", data_ref(ix,iy,iz)).s);
        i_fld++;
        if (i_fld == 6) {
          fprintf(fh, "\n");
          i_fld = 0;
        }
      }
    }
    if (i_fld > 0) {
      fprintf(fh, "\n");
    }
  }
  write_tail(fh, average, standard_deviation);
}

void
map_writer(
  std::string const& file_name,
  cctbx::uctbx::unit_cell const& unit_cell,
  af::const_ref<double, af::flex_grid<> > const& data,
  const scitbx::af::tiny<unsigned,3> &whole_unit_cell_size)
{
  IOTBX_ASSERT(data.accessor().nd() == 3);
  IOTBX_ASSERT(data.accessor().all().all_gt(0));
  IOTBX_ASSERT(!data.accessor().is_padded());
  af::int3 first( af::adapt(data.accessor().origin()) ),
    last( af::adapt(data.accessor().last()) );
  last -= 1; // open range -> close range
  FILE* fh=write_head(file_name, unit_cell, whole_unit_cell_size, first, last);
  af::const_ref<double, af::c_grid<3> > data_ref(data.begin(),
    af::c_grid<3>(af::adapt(data.accessor().all())));
  double mean=0., esd=0.;
  for(std::size_t iz=0;iz<data_ref.accessor()[2];iz++) {
    fprintf(fh, "%8lu\n", static_cast<unsigned long>(iz));
    int i_fld = 0;
    for(std::size_t iy=0;iy<data_ref.accessor()[1];iy++) {
      for(std::size_t ix=0;ix<data_ref.accessor()[0];ix++) {
        double value = data_ref(ix,iy,iz);
        mean += value;
        esd += value*value;
        fprintf(fh, "%s", format_e<12>("%12.5E", value).s);
        i_fld++;
        if (i_fld == 6) {
          fprintf(fh, "\n");
          i_fld = 0;
        }
      }
    }
    if (i_fld > 0) {
      fprintf(fh, "\n");
    }
  }
  std::size_t n = data_ref.accessor().size_1d();
  IOTBX_ASSERT( n>0U );
  mean /= n;
  esd = esd / n - mean*mean;
  IOTBX_ASSERT( esd>=0. );
  esd = std::sqrt(esd);
  write_tail(fh, mean, esd);
}

void
map_writer_p1_cell(
  std::string const& file_name,
  cctbx::uctbx::unit_cell const& unit_cell,
  af::int3 const& gridding_first,
  af::int3 const& gridding_last,
  af::const_ref<double, af::c_grid_padded_periodic<3> > const& data,
  double average,
  double standard_deviation)
{
  FILE* fh = write_head(file_name, unit_cell);
  unsigned i_section = 0;
  for(int iz=gridding_first[2];iz<=gridding_last[2];iz++,i_section++) {
    fprintf(fh, "%8u\n", i_section);
    int i_fld = 0;
    for(int iy=gridding_first[1];iy<=gridding_last[1];iy++) {
      for(int ix=gridding_first[0];ix<=gridding_last[0];ix++) {
        fprintf(fh, "%s", format_e<12>("%12.5E", data(ix,iy,iz)).s);
        i_fld++;
        if (i_fld == 6) {
          fprintf(fh, "\n");
          i_fld = 0;
        }
      }
    }
    if (i_fld > 0) {
      fprintf(fh, "\n");
    }
  }
  write_tail(fh, average, standard_deviation);
}

}}
