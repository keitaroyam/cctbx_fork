#ifndef CCTBX_CRYSTAL_COORDINATION_SEQUENCES_H
#define CCTBX_CRYSTAL_COORDINATION_SEQUENCES_H

#include <cctbx/crystal/direct_space_asu.h>
#include <cctbx/crystal/pair_tables.h>

namespace cctbx { namespace crystal {

//! Coordination sequence algorithms.
namespace coordination_sequences {

  struct node
  {
    node() {}

    node(
      direct_space_asu::asu_mappings<> const& asu_mappings,
      unsigned i_seq_,
      sgtbx::rt_mx const& rt_mx_)
    :
      i_seq(i_seq_),
      rt_mx(rt_mx_)
    {
      rt_mx_unique = rt_mx_.multiply(asu_mappings.special_op(i_seq));
    }

    unsigned i_seq;
    sgtbx::rt_mx rt_mx;
    sgtbx::rt_mx rt_mx_unique;
  };

  bool
  find_node(
    node const& test_node,
    std::vector<node> const& node_list)
  {
    for(std::vector<node>::const_iterator
          list_node=node_list.begin();
          list_node!=node_list.end();
          list_node++) {
      if (   list_node->i_seq == test_node.i_seq
          && list_node->rt_mx_unique == test_node.rt_mx_unique) {
        return true;
      }
    }
    return false;
  }

  struct three_shells
  {
    three_shells() {}

    three_shells(
      direct_space_asu::asu_mappings<> const& asu_mappings,
      unsigned i_seq_pivot)
    {
      prev = &a;
      middle = &b;
      next = &c;
      next->push_back(node(asu_mappings, i_seq_pivot, sgtbx::rt_mx(1,1)));
    }

    void
    shift()
    {
      std::vector<node>* tmp = prev;
      prev = middle;
      middle = next;
      next = tmp;
      next->clear();
    }

    std::vector<node> a;
    std::vector<node> b;
    std::vector<node> c;
    std::vector<node>* prev;
    std::vector<node>* middle;
    std::vector<node>* next;
  };

  af::shared<std::vector<unsigned> >
  simple(
    direct_space_asu::asu_mappings<> const& asu_mappings,
    pair_asu_table_table const& pair_asu_table_table_,
    unsigned n_shells)
  {
    af::shared<std::vector<unsigned> > term_table;
    for(unsigned i_seq_pivot=0;
                 i_seq_pivot<pair_asu_table_table_.size();
                 i_seq_pivot++) {
      pair_asu_dict pair_asu_dict_pivot = pair_asu_table_table_[i_seq_pivot];
      sgtbx::rt_mx rt_mx_pivot = asu_mappings.get_rt_mx(i_seq_pivot, 0);
      if (pair_asu_dict_pivot.size() == 0) {
        term_table.push_back(std::vector<unsigned>());
        continue;
      }
      three_shells shells(asu_mappings, i_seq_pivot);
      std::vector<unsigned> terms(1, 1);
      for(unsigned i_shell_minus_1=0;
                   i_shell_minus_1<n_shells;
                   i_shell_minus_1++) {
        shells.shift();
        for(unsigned i_node_m=0;i_node_m<shells.middle->size();i_node_m++) {
          node node_m = (*shells.middle)[i_node_m];
          sgtbx::rt_mx rt_mx_i = asu_mappings.get_rt_mx(node_m.i_seq, 0);
          sgtbx::rt_mx rt_mx_ni = node_m.rt_mx.multiply(rt_mx_i.inverse());
          pair_asu_dict::const_iterator
            pair_asu_dict_end = pair_asu_table_table_[node_m.i_seq].end();
          for(pair_asu_dict::const_iterator
                pair_asu_dict_i = pair_asu_table_table_[node_m.i_seq].begin();
                pair_asu_dict_i != pair_asu_dict_end;
                pair_asu_dict_i++) {
            unsigned j_seq = pair_asu_dict_i->first;
            pair_asu_j_sym_groups const& j_sym_groups=pair_asu_dict_i->second;
            for(unsigned i_group=0; i_group<j_sym_groups.size(); i_group++) {
              pair_asu_j_sym_group j_sym_group = j_sym_groups[i_group];
              pair_asu_j_sym_group::const_iterator
                j_sym_group_end = j_sym_group.end();
              for(pair_asu_j_sym_group::const_iterator
                    j_sym_group_i = j_sym_group.begin();
                    j_sym_group_i != j_sym_group_end;
                    j_sym_group_i++) {
                unsigned j_sym = *j_sym_group_i;
                sgtbx::rt_mx rt_mx_j = asu_mappings.get_rt_mx(j_seq, j_sym);
                node new_node(asu_mappings, j_seq, rt_mx_ni.multiply(rt_mx_j));
                if (   !find_node(new_node, *shells.prev)
                    && !find_node(new_node, *shells.middle)
                    && !find_node(new_node, *shells.next)) {
                  shells.next->push_back(new_node);
                }
              }
            }
          }
        }
        terms.push_back(shells.next->size());
      }
      term_table.push_back(terms);
    }
    return term_table;
  }

}}} // namespace cctbx::crystal::coordination_sequences

#endif // CCTBX_CRYSTAL_COORDINATION_SEQUENCES_H
