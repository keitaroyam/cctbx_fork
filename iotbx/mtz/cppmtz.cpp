#include "iotbx/cppmtz.h"
#include <scitbx/constants.h>
#include <scitbx/mat3.h>

namespace bpmtz = iotbx::mtz;

bpmtz::Mtz::Mtz(std::string s):mtz(CMtz::MtzGet(s.c_str(),1)){
    if (!mtz) {throw bpmtz::Error("Mtz read failed"); }
}
bpmtz::Mtz::~Mtz(){
  CMtz::MtzFree(mtz);}

std::string bpmtz::Mtz::title(){return std::string(mtz->title);}
std::string bpmtz::Mtz::SpaceGroup(){return mtz->mtzsymm.spcgrpname;}

cctbx::sgtbx::space_group 
bpmtz::Mtz::getSgtbxSpaceGroup(){
  cctbx::sgtbx::space_group sg;
  for  (int i = 0; i < mtz->mtzsymm.nsym; ++i) {
    scitbx::mat3<double> r_double;
    scitbx::vec3<double> t_double;
    for (int p=0;p<3;p++) {
      for (int q=0;q<3;q++) {
        r_double(p,q) = mtz->mtzsymm.sym[i][p][q];
      }
      t_double[p] = mtz->mtzsymm.sym[i][p][3];
    }
    sg.expand_smx(cctbx::sgtbx::rt_mx(r_double,t_double));
  }
  return sg;
}

int bpmtz::Mtz::nsym() const {return mtz->mtzsymm.nsym;}
int& bpmtz::Mtz::size(){return mtz->nref;}
int& bpmtz::Mtz::ncrystals() const {return mtz->nxtal;}
int bpmtz::Mtz::ndatasets(const int& xtal) {return mtz->xtal[xtal]->nset;}
int& bpmtz::Mtz::ncolumns(const int& xtal, const int& set) {return mtz->xtal[xtal]->set[set]->ncol;}

af::shared<std::string> bpmtz::Mtz::history(){
   af::shared<std::string> answer;
   for (int i = 0; i < mtz->histlines; ++i) {
     char* buffer=new char[MTZRECORDLENGTH+1];
     char* src= mtz->hist+ MTZRECORDLENGTH*i;
     char* dst= buffer;
     for (;dst-buffer<MTZRECORDLENGTH;) {*dst++=*src++;}
     buffer[MTZRECORDLENGTH]='\0';
     answer.push_back(std::string(buffer));
     delete [] buffer;
   }
   return answer;
}

af::shared<std::string> bpmtz::Mtz::columns() const {
   af::shared<std::string> answer;
   /* Loop over crystals */
    for (int i = 0; i < mtz->nxtal; ++i) {
   /* Loop over datasets for each crystal */
     for (int j = 0; j < mtz->xtal[i]->nset; ++j) {
   /* Loop over columns for each dataset */
      for (int k = 0; k < mtz->xtal[i]->set[j]->ncol; ++k) {
       if (mtz->xtal[i]->set[j]->col[k]->active) {
         answer.push_back(mtz->xtal[i]->set[j]->col[k]->label);
       }
      }
     }
    }
   return answer;
}

bpmtz::Column bpmtz::Mtz::getColumn(std::string s){
  return bpmtz::Column(CMtz::MtzColLookup(mtz,s.c_str()));
}

bpmtz::Crystal bpmtz::Mtz::getCrystal(const int& xtalid) const{
  return bpmtz::Crystal(CMtz::MtzIxtal(mtz, xtalid));
}

bpmtz::Crystal bpmtz::Mtz::columnToCrystal(std::string s) const{
  af::shared<std::string> cols = this->columns();
  bool foundlabel=false;
  for (int i = 0; i<cols.size(); ++i) {
    if (cols[i]==s) {
      foundlabel=true;
      break;
    }
  }
  if (!foundlabel) throw iotbx::mtz::Error("no such column label");

  for (int i = 0; i < this->ncrystals(); ++i) {
    iotbx::mtz::Crystal cryst = this->getCrystal(i);
    for (int j = 0; j < cryst.ndatasets(); ++j) {
      iotbx::mtz::Dataset data = cryst.getDataset(j);
      for (int k = 0; k < data.ncolumns(); ++k) {
        if (data.getColumn(k).label() == s) {
          return cryst;}
      }
    }
  }
  throw iotbx::mtz::Error("no such column label");//Never get here but make compiler happy
}

af::shared< cctbx::miller::index<> > bpmtz::Mtz::MIx() {
  bpmtz::Column H(getColumn("H"));
  bpmtz::Column K(getColumn("K"));
  bpmtz::Column L(getColumn("L"));
  af::shared<cctbx::miller::index<> > miller(this->size());
  for (int j=0; j<this->size(); j++) {
    miller[j] = cctbx::miller::index<>(H.lookup(j),K.lookup(j),L.lookup(j));
  }
  return miller;
}

void bpmtz::Mtz::printHeader(int detail = 1){
  CMtz::ccp4_lhprt(mtz,detail);
}

void bpmtz::Mtz::printHeaderAdv(int detail = 1){
  CMtz::ccp4_lhprt_adv(mtz,detail);
}

cctbx::uctbx::unit_cell bpmtz::Mtz::UnitCell(const int& xtal){
  af::tiny<double,6> answer;
  for (int j=0; j<6; j++) {answer[j] = mtz->xtal[xtal]->cell[j];}
  return cctbx::uctbx::unit_cell(answer);
}

af::shared<cctbx::miller::index<> >
bpmtz::Mtz::valid_indices(
  std::string const& column_label)
{
  bpmtz::Column h(getColumn("H"));
  bpmtz::Column k(getColumn("K"));
  bpmtz::Column l(getColumn("L"));
  bpmtz::Column v(getColumn(column_label));
  af::shared<cctbx::miller::index<> > result((af::reserve(size())));
  for (int j=0; j<size(); j++) {
    if (!v.isnan(j)) {
      result.push_back(cctbx::miller::index<>(
        h.lookup(j), k.lookup(j), l.lookup(j)));
    }
  }
  return result;
}

af::shared<cctbx::miller::index<> >
bpmtz::Mtz::valid_indices_anomalous(
  std::string const& column_label_plus,
  std::string const& column_label_minus)
{
  bpmtz::Column h(getColumn("H"));
  bpmtz::Column k(getColumn("K"));
  bpmtz::Column l(getColumn("L"));
  bpmtz::Column v_plus(getColumn(column_label_plus));
  bpmtz::Column v_minus(getColumn(column_label_minus));
  af::shared<cctbx::miller::index<> > result((af::reserve(2*size())));
  for (int j=0; j<size(); j++) {
    if (!v_plus.isnan(j)) {
      result.push_back(cctbx::miller::index<>(
        h.lookup(j), k.lookup(j), l.lookup(j)));
    }
    if (!v_minus.isnan(j)) {
      result.push_back(cctbx::miller::index<>(
        -h.lookup(j), -k.lookup(j), -l.lookup(j)));
    }
  }
  return result;
}

af::shared<double>
bpmtz::Mtz::valid_values(
  std::string const& column_label)
{
  bpmtz::Column v(getColumn(column_label));
  af::shared<double> result((af::reserve(size())));
  for (int j=0; j<size(); j++) {
    if (!v.isnan(j)) result.push_back(v.lookup(j));
  }
  return result;
}

af::shared<double>
bpmtz::Mtz::valid_values_anomalous(
  std::string const& column_label_plus,
  std::string const& column_label_minus)
{
  bpmtz::Column h(getColumn("H"));
  bpmtz::Column k(getColumn("K"));
  bpmtz::Column l(getColumn("L"));
  bpmtz::Column v_plus(getColumn(column_label_plus));
  bpmtz::Column v_minus(getColumn(column_label_minus));
  af::shared<double> result((af::reserve(2*size())));
  for (int j=0; j<size(); j++) {
    if (!v_plus.isnan(j)) result.push_back(v_plus.lookup(j));
    if (!v_minus.isnan(j)) result.push_back(v_minus.lookup(j));
  }
  return result;
}

namespace {
  inline std::complex<double>
  polar_deg(double ampl, double phi)
  {
    return std::polar(ampl, phi*scitbx::constants::pi_180);
  }
}

af::shared<std::complex<double> >
bpmtz::Mtz::valid_complex(
  std::string const& column_label_ampl,
  std::string const& column_label_phi)
{
  bpmtz::Column v_ampl(getColumn(column_label_ampl));
  bpmtz::Column v_phi(getColumn(column_label_phi));
  af::shared<std::complex<double> > result((af::reserve(size())));
  for (int j=0; j<size(); j++) {
    if (v_ampl.isnan(j) != v_phi.isnan(j)) {
      throw bpmtz::Error("Unexpected NAN while extracting complex array.");
    }
    if (!v_ampl.isnan(j)) {
      result.push_back(polar_deg(
        v_ampl.lookup(j), v_phi.lookup(j)));
    }
  }
  return result;
}

af::shared<std::complex<double> >
bpmtz::Mtz::valid_complex_anomalous(
  std::string const& column_label_ampl_plus,
  std::string const& column_label_phi_plus,
  std::string const& column_label_ampl_minus,
  std::string const& column_label_phi_minus)
{
  bpmtz::Column v_ampl_plus(getColumn(column_label_ampl_plus));
  bpmtz::Column v_phi_plus(getColumn(column_label_phi_plus));
  bpmtz::Column v_ampl_minus(getColumn(column_label_ampl_minus));
  bpmtz::Column v_phi_minus(getColumn(column_label_phi_minus));
  af::shared<std::complex<double> > result((af::reserve(2*size())));
  for (int j=0; j<size(); j++) {
    if (v_ampl_plus.isnan(j) != v_phi_plus.isnan(j)) {
      throw bpmtz::Error("Unexpected NAN while extracting complex array.");
    }
    if (!v_ampl_plus.isnan(j)) {
      result.push_back(polar_deg(
        v_ampl_plus.lookup(j), v_phi_plus.lookup(j)));
    }
    if (v_ampl_minus.isnan(j) != v_phi_minus.isnan(j)) {
      throw bpmtz::Error("Unexpected NAN while extracting complex array.");
    }
    if (!v_ampl_minus.isnan(j)) {
      result.push_back(polar_deg(
        v_ampl_minus.lookup(j), v_phi_minus.lookup(j)));
    }
  }
  return result;
}

af::shared<cctbx::hendrickson_lattman<> >
bpmtz::Mtz::valid_hl(
  std::string const& column_label_a,
  std::string const& column_label_b,
  std::string const& column_label_c,
  std::string const& column_label_d)
{
  bpmtz::Column v_a(getColumn(column_label_a));
  bpmtz::Column v_b(getColumn(column_label_b));
  bpmtz::Column v_c(getColumn(column_label_c));
  bpmtz::Column v_d(getColumn(column_label_d));
  af::shared<cctbx::hendrickson_lattman<> > result((af::reserve(size())));
  for (int j=0; j<size(); j++) {
    if (   v_a.isnan(j) != v_b.isnan(j)
        || v_a.isnan(j) != v_c.isnan(j)
        || v_a.isnan(j) != v_d.isnan(j)) {
      throw bpmtz::Error(
        "Unexpected NAN while extracting Hendrickson-Lattman array.");
    }
    if (!v_a.isnan(j)) {
      result.push_back(cctbx::hendrickson_lattman<>(
        v_a.lookup(j), v_b.lookup(j), v_c.lookup(j), v_d.lookup(j)));
    }
  }
  return result;
}

std::string bpmtz::Crystal::crystal_name() {
  return std::string(p_xtal->xname);
}

std::string bpmtz::Crystal::project_name() {
  return std::string(p_xtal->pname);
}

cctbx::uctbx::unit_cell bpmtz::Crystal::UnitCell(){
  af::tiny<double,6> answer;
  for (int j=0; j<6; j++) {answer[j] = p_xtal->cell[j];}
  return cctbx::uctbx::unit_cell(answer);
}

int bpmtz::Crystal::ndatasets() {return p_xtal->nset;}

bpmtz::Dataset bpmtz::Crystal::getDataset(const int& setid){
  return bpmtz::Dataset(CMtz::MtzIsetInXtal(p_xtal, setid));
}

std::string bpmtz::Dataset::dataset_name() {
  return std::string(p_set->dname);
}

double bpmtz::Dataset::wavelength() {
  return p_set->wavelength;
}

int bpmtz::Dataset::ncolumns() {
  return p_set->ncol;
}

bpmtz::Column bpmtz::Dataset::getColumn(const int& colid){
  return bpmtz::Column(CMtz::MtzIcolInSet(p_set, colid));
}

std::string bpmtz::Column::label() {
  return std::string(p_col->label);
}

std::string bpmtz::Column::type() {
  return std::string(p_col->type);
}

