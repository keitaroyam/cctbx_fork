#ifndef MMTBX_NCS_RESTRAINTS_H
#define MMTBX_NCS_RESTRAINTS_H

#include <mmtbx/error.h>
#include <scitbx/array_family/selections.h>
#include <map>
#include <vector>

namespace mmtbx { namespace ncs { namespace restraints {

  namespace af = scitbx::af;

  struct pair_registry : boost::noncopyable
  {
    typedef std::map<unsigned, unsigned> table_entry_t;
    typedef std::vector<table_entry_t> table_t;
    table_t table_;
    std::vector<unsigned> counts_;
    unsigned number_of_additional_isolated_sites;

    pair_registry(unsigned n_seq, unsigned n_ncs)
    :
      table_(n_seq),
      counts_(n_ncs, 0),
      number_of_additional_isolated_sites(0)
    {}

    void
    register_additional_isolated_sites(unsigned number)
    {
      number_of_additional_isolated_sites += number;
    }

    int
    enter(unsigned i_seq, unsigned j_seq, unsigned j_ncs)
    {
      unsigned n_seq = table_.size();
      MMTBX_ASSERT(i_seq < n_seq);
      MMTBX_ASSERT(j_seq < n_seq);
      MMTBX_ASSERT(j_ncs > 0);
      MMTBX_ASSERT(j_ncs < counts_.size());
      if (i_seq > j_seq) std::swap(i_seq, j_seq);
      table_t::iterator tab_i = table_.begin() + i_seq;
      table_entry_t::const_iterator tab_ij = tab_i->find(j_seq);
      if (tab_ij == tab_i->end()) {
        (*tab_i)[j_seq] = j_ncs;
        counts_[j_ncs]++;
        return 1;
      }
      if (tab_ij->second != j_ncs) return -tab_ij->second;
      return 0;
    }

    std::auto_ptr<pair_registry>
    proxy_select(af::const_ref<bool> const& selection) const
    {
      MMTBX_ASSERT(   selection.size()
                   == table_.size() + number_of_additional_isolated_sites);
      unsigned n_seq = static_cast<unsigned>(table_.size());
      af::reindexing_given_bool_selection<unsigned> reindexing(
        af::const_ref<bool>(selection.begin(), n_seq));
      std::auto_ptr<pair_registry> result(
        new pair_registry(reindexing.n_selected, counts_.size()));
      unsigned* result_counts = &*result->counts_.begin();
      unsigned* reindexing_array_begin = reindexing.array.begin();
      for(unsigned i_seq=0;i_seq<n_seq;i_seq++) {
        unsigned result_i_seq = reindexing_array_begin[i_seq];
        if (result_i_seq == n_seq) continue;
        table_entry_t& result_tab_i = result->table_[result_i_seq];
        table_t::const_iterator tab_i = table_.begin() + i_seq;
        table_entry_t::const_iterator tab_ij_end = tab_i->end();
        for(table_entry_t::const_iterator
              tab_ij=tab_i->begin();
              tab_ij!=tab_ij_end;
              tab_ij++) {
          unsigned result_j_seq = reindexing_array_begin[tab_ij->first];
          if (result_j_seq == n_seq) continue;
          unsigned j_ncs = tab_ij->second;
          result_tab_i[result_j_seq] = j_ncs;
          result_counts[j_ncs]++;
        }
      }
      unsigned n = 0;
      for(unsigned
            i_seq=n_seq;
            i_seq<n_seq+number_of_additional_isolated_sites;
            i_seq++) {
        if (selection[i_seq]) n++;
      }
      result->number_of_additional_isolated_sites = n;
      return result;
    }

    std::vector<af::tiny<af::shared<std::size_t>, 2> >
    selection_pairs() const
    {
      unsigned n_ncs = counts_.size();
      std::vector<af::tiny<af::shared<std::size_t>, 2> > result;
      result.reserve(n_ncs-1);
      for(unsigned j_ncs=1;j_ncs<n_ncs;j_ncs++) {
        result.resize(j_ncs);
        af::tiny<af::shared<std::size_t>, 2>& result_j = result[j_ncs-1];
        unsigned n_pairs = counts_[j_ncs];
        result_j[0].reserve(n_pairs);
        result_j[1].reserve(n_pairs);
      }
      unsigned n_seq = table_.size();
      for(unsigned i_seq=0;i_seq<n_seq;i_seq++) {
        table_t::const_iterator tab_i = table_.begin() + i_seq;
        for(table_entry_t::const_iterator
              tab_ij=tab_i->begin();
              tab_ij!=tab_i->end();
              tab_ij++) {
          unsigned j_seq = tab_ij->first;
          unsigned j_ncs = tab_ij->second;
          af::tiny<af::shared<std::size_t>, 2>& result_j = result[j_ncs-1];
          result_j[0].push_back(i_seq);
          result_j[1].push_back(j_seq);
        }
      }
      return result;
    }

    double
    adp_iso_residual_sum(
      double weight,
      double average_power,
      af::const_ref<double> const& u_isos,
      double u_average_min,
      af::ref<double> const& gradients)
    {
      CCTBX_ASSERT(   u_isos.size()
                   == table_.size() + number_of_additional_isolated_sites);
      CCTBX_ASSERT(   gradients.size() == 0
                   ||    gradients.size()
                      == table_.size() + number_of_additional_isolated_sites);
      unsigned n_ncs = counts_.size();
      std::vector<unsigned> i_seq_buffer;
      i_seq_buffer.reserve(n_ncs);
      unsigned n_seq = table_.size();
      double unweighted_residual_sum = 0;
      for(unsigned i_seq=0;i_seq<n_seq;i_seq++) {
        table_t::const_iterator tab_i = table_.begin() + i_seq;
        if (tab_i->size() > 0) {
          i_seq_buffer.clear();
          i_seq_buffer.push_back(i_seq);
          double u_sum = u_isos[i_seq];
          for(table_entry_t::const_iterator
                tab_ij=tab_i->begin();
                tab_ij!=tab_i->end();
                tab_ij++) {
            unsigned j_seq = tab_ij->first;
            i_seq_buffer.push_back(j_seq);
            u_sum += u_isos[j_seq];
          }
          unsigned n = i_seq_buffer.size();
          double u_ave = u_sum / n;
          if (u_ave >= u_average_min) {
            double u_ave_pow = std::pow(u_ave, average_power);
            double u_diff_sum = 0;
            double u_diff_sum_sq = 0;
            for(unsigned i=0;i<n;i++) {
              unsigned i_seq = i_seq_buffer[i];
              double u_diff = u_ave - u_isos[i_seq];
              u_diff_sum_sq += u_diff * u_diff;
              if (gradients.size() != 0) {
                u_diff_sum += u_diff;
              }
            }
            unweighted_residual_sum += u_diff_sum_sq / u_ave_pow;
            if (gradients.size() != 0) {
              double n_ave_pow = n * u_ave_pow;
              double f1 = weight * 2 / n_ave_pow;
              double t2 = weight * average_power / (n_ave_pow * u_ave)
                        * u_diff_sum_sq;
              for(unsigned i=0;i<n;i++) {
                unsigned i_seq = i_seq_buffer[i];
                double u_diff = u_isos[i_seq] - u_ave;
                gradients[i_seq] += (f1 * (u_diff * n - u_diff_sum)) - t2;
              }
            }
          }
        }
      }
      return weight * unweighted_residual_sum;
    }
  };

}}} // namespace mmtbx::ncs::restraints

#endif // MMTBX_NCS_RESTRAINTS_H
