from cctbx import restraints
from cctbx.crystal import minimization
from iotbx.kriber import strudat
from iotbx.option_parser import iotbx_option_parser
from cctbx import xray
from cctbx import crystal
from cctbx import sgtbx
from cctbx.crystal.neighbors import is_sym_equiv_interaction, show_distances
from cctbx.array_family import flex
import scitbx.lbfgs
from scitbx import matrix
from scitbx.python_utils.misc import adopt_init_args
from libtbx.itertbx import count
from libtbx.test_utils import approx_equal
import os

if (1):
  flex.set_random_seed(0)

class restraint_parameters:

  def __init__(self, distance_ideal, weight):
    adopt_init_args(self, locals())

restraint_parameters_si_o = restraint_parameters(1.61, 2.0)
restraint_parameters_o_si_o = restraint_parameters(2.629099, 0.41)
restraint_parameters_si_o_si = restraint_parameters(3.070969, 0.2308)

class create_bond_proxies:

  def __init__(self, structure, distance_cutoff=3.5,
                     distance_ideal=3.1,
                     weight=1,
                     heterogeneous_bonds_only=00000,
                     asu_mappings_distance_cutoff=None,
                     distance_cutoff_tolerance=1.e-4,
                     diff_vec_frac_tolerance=1.e-8):
    distance_cutoff_plus = distance_cutoff * (1+distance_cutoff_tolerance)
    distance_cutoff_minus = distance_cutoff * (1-distance_cutoff_tolerance)
    if (asu_mappings_distance_cutoff is None):
      asu_mappings_distance_cutoff = distance_cutoff
    else:
      assert asu_mappings_distance_cutoff >= distance_cutoff
    asu_mappings_distance_cutoff_plus = asu_mappings_distance_cutoff \
                                      * (1+distance_cutoff_tolerance)
    asu_mappings = structure.asu_mappings(
      buffer_thickness=asu_mappings_distance_cutoff_plus)
    pair_generator = crystal.neighbors_simple_pair_generator(
      asu_mappings=asu_mappings,
      distance_cutoff=distance_cutoff_plus)
    distances_list = [flex.double()
      for i in xrange(structure.scatterers().size())]
    pairs_list = [[]
      for i in xrange(structure.scatterers().size())]
    cb_op_to_niggli_cell = structure.change_of_basis_op_to_niggli_cell()
    for pair in pair_generator:
      diff_vec_frac = structure.unit_cell().fractionalize(pair.diff_vec)
      diff_vec_frac_niggli = matrix.col(cb_op_to_niggli_cell.c()*diff_vec_frac)
      if (diff_vec_frac_niggli.each_abs().max() < 1+diff_vec_frac_tolerance):
        distances_list[pair.i_seq].append(pair.dist_sq)
        pairs_list[pair.i_seq].append(pair)
    for i,distances,pairs in zip(count(),distances_list,pairs_list):
      perm = flex.sort_permutation(distances)
      pairs_list[i] = flex.select(pairs, perm)
    site_symmetries = []
    scatterers = structure.scatterers()
    for scatterer in scatterers:
      site_symmetries.append(structure.site_symmetry(scatterer.site))
    proxies = restraints.shared_bond_sym_proxy()
    sorted_proxies = restraints.bond_sorted_proxies(asu_mappings=asu_mappings)
    bond_counts = flex.size_t(structure.scatterers().size(), 0)
    for pairs in pairs_list:
      if (len(pairs) > 0):
        i_seq = pairs[0].i_seq
        scatterer_i = scatterers[i_seq]
        site_i = scatterer_i.site
        site_symmetry_i = site_symmetries[i_seq]
        rt_mx_i_inverse = asu_mappings.get_rt_mx(i_seq=i_seq,i_sym=0).inverse()
      for i_pair,pair in zip(count(), pairs):
        assert pair.i_seq == i_seq
        if (pair.dist_sq**.5 > distance_cutoff):
          break
        scatterer_j = scatterers[pair.j_seq]
        if (    heterogeneous_bonds_only
            and scatterer_i.scattering_type == scatterer_j.scattering_type):
          continue
        site_symmetry_j = site_symmetries[pair.j_seq]
        rt_mx_j = asu_mappings.get_rt_mx(i_seq=pair.j_seq, i_sym=pair.j_sym)
        rt_mx_ji = rt_mx_i_inverse.multiply(rt_mx_j)
        bond_counts[pair.i_seq] += 1
        if (pair.j_sym == 0):
          bond_counts[pair.j_seq] += 1
        proxies.append(restraints.bond_sym_proxy(
          pair=pair,
          distance_ideal=distance_ideal,
          weight=weight))
        sorted_proxies.process(proxy=proxies[-1])
        if (pair.dist_sq**.5 > distance_cutoff_minus):
          for pair_fwd in pairs[i_pair+1:]:
            if (    pair_fwd.j_seq == pair.j_seq
                and   abs(pair_fwd.dist_sq**.5-pair.dist_sq**.5)
                    < distance_cutoff_tolerance):
              rt_mx_j_fwd = asu_mappings.get_rt_mx(
                i_seq=pair_fwd.j_seq, i_sym=pair_fwd.j_sym)
              rt_mx_ji_fwd = rt_mx_i_inverse.multiply(rt_mx_j_fwd)
              if (is_sym_equiv_interaction(
                    unit_cell=structure.unit_cell(),
                    i_seq=i_seq,
                    site_i=site_i,
                    j_seq=pair.j_seq,
                    site_j=scatterer_j.site,
                    special_op_j=site_symmetries[pair.j_seq].special_op(),
                    rt_mx_ji_1=rt_mx_ji,
                    rt_mx_ji_2=rt_mx_ji_fwd)):
                proxies.append(restraints.bond_sym_proxy(
                  pair=pair_fwd,
                  distance_ideal=distance_ideal,
                  weight=weight))
                sorted_proxies.process(proxy=proxies[-1])
                bond_counts[i_seq] += 1
                if (pair_fwd.j_sym == 0):
                  bond_counts[pair_fwd.j_seq] += 1
    self.site_symmetries = site_symmetries
    self.asu_mappings = asu_mappings
    self.proxies = proxies
    self.sorted_proxies = sorted_proxies
    self.bond_counts = bond_counts

def get_bond_site_symmetry(structure, site_i, site_ji):
  special_position_settings = crystal.special_position_settings(
    crystal_symmetry=structure,
    min_distance_sym_equiv=structure.min_distance_sym_equiv()*.5*(1-1.e-5))
  result = special_position_settings.site_symmetry(
    site=(matrix.col(site_i) + matrix.col(site_ji)) / 2)
  assert result.distance_moved() < 1.e-6
  return result

def add_oxygen(si_structure, si_proxies):
  asu_mappings = si_proxies.asu_mappings
  bonds_processed = [{}
    for i in xrange(si_structure.scatterers().size())]
  bond_centers = []
  for proxy in si_proxies.proxies:
    pair = proxy.pair
    if (pair.i_seq > pair.j_seq): continue
    rt_mx_i_inverse=asu_mappings.get_rt_mx(i_seq=pair.i_seq,i_sym=0).inverse()
    rt_mx_j = asu_mappings.get_rt_mx(i_seq=pair.j_seq, i_sym=pair.j_sym)
    rt_mx_ji = rt_mx_i_inverse.multiply(rt_mx_j)
    ij_rt_mx = bonds_processed[pair.i_seq].setdefault(pair.j_seq, [])
    is_sym_equiv = 00000
    for rt_mx_ji_prev in ij_rt_mx:
      if (is_sym_equiv_interaction(
            unit_cell=si_structure.unit_cell(),
            i_seq=pair.i_seq,
            site_i=si_structure.scatterers()[pair.i_seq].site,
            j_seq=pair.j_seq,
            site_j=si_structure.scatterers()[pair.j_seq].site,
            special_op_j=si_proxies.site_symmetries[pair.j_seq].special_op(),
            rt_mx_ji_1=rt_mx_ji,
            rt_mx_ji_2=rt_mx_ji_prev)):
        is_sym_equiv = 0001
        break
    if (not is_sym_equiv):
      bond_site_symmetry = get_bond_site_symmetry(
        structure=si_structure,
        site_i=si_structure.scatterers()[pair.i_seq].site,
        site_ji=rt_mx_ji*si_structure.scatterers()[pair.j_seq].site)
      bond_centers.append(bond_site_symmetry.exact_site())
      ij_rt_mx.append(rt_mx_ji)
  si_o_structure = si_structure.deep_copy_scatterers()
  for i,bond_center in zip(count(1), bond_centers):
    si_o_structure.add_scatterer(xray.scatterer(
      label="O%d"%i,
      site=bond_center))
  return si_o_structure

def add_o_si_o_proxies(structure, proxies, distance_ideal, weight):
  scatterers = structure.scatterers()
  pair_lists = [[] for i in xrange(scatterers.size())]
  for proxy in proxies.proxies:
    pair = proxy.pair
    if (scatterers[pair.i_seq].scattering_type == "Si"):
      assert scatterers[pair.j_seq].scattering_type == "O"
      pair_lists[pair.i_seq].append(pair)
  processed_proxy_dict = {}
  asu_mappings = proxies.asu_mappings
  mappings = asu_mappings.mappings()
  for pair_list in pair_lists:
    for io1 in xrange(len(pair_list)-1):
      pair1 = pair_list[io1]
      rt_mx_j1 = asu_mappings.get_rt_mx(i_seq=pair1.j_seq, i_sym=pair1.j_sym)
      rt_mx_j10 = asu_mappings.get_rt_mx(i_seq=pair1.j_seq, i_sym=0)
      n_sym_1 = len(mappings[pair1.j_seq])
      for io2 in xrange(io1+1,len(pair_list)):
        pair2 = pair_list[io2]
        rt_mx_j2 = asu_mappings.get_rt_mx(i_seq=pair2.j_seq, i_sym=pair2.j_sym)
        rt_mx_j20 = asu_mappings.get_rt_mx(i_seq=pair2.j_seq, i_sym=0)
        n_sym_2 = len(mappings[pair2.j_seq])
        primary_distance = structure.unit_cell().distance(
          rt_mx_j1*scatterers[pair1.j_seq].site,
          rt_mx_j2*scatterers[pair2.j_seq].site)
        if (pair1.j_seq == pair2.j_seq):
          k_sym_start = 1
        else:
          k_sym_start = 0
        rt_mx_ji = rt_mx_j1.inverse().multiply(rt_mx_j2)
        for k_sym in xrange(k_sym_start, n_sym_2):
          pair_key = (pair1.j_seq, pair2.j_seq, k_sym)
          if (pair_key in processed_proxy_dict):
            continue
          rt_mx_k = asu_mappings.get_rt_mx(i_seq=pair2.j_seq, i_sym=k_sym)
          k_distance = structure.unit_cell().distance(
            rt_mx_j10*scatterers[pair1.j_seq].site,
            rt_mx_k*scatterers[pair2.j_seq].site)
          if (abs(k_distance-primary_distance) > primary_distance*1.e-6):
            continue
          rt_mx_kj = rt_mx_j10.inverse().multiply(rt_mx_k)
          if (1):
            ctrl = structure.unit_cell().distance(
              scatterers[pair1.j_seq].site,
              rt_mx_kj*scatterers[pair2.j_seq].site)
            assert abs(ctrl-primary_distance) <= primary_distance*1.e-6
          if (is_sym_equiv_interaction(
                unit_cell=structure.unit_cell(),
                i_seq=pair1.j_seq,
                site_i=structure.scatterers()[pair1.j_seq].site,
                j_seq=pair2.j_seq,
                site_j=structure.scatterers()[pair2.j_seq].site,
                special_op_j
                  =proxies.site_symmetries[pair2.j_seq].special_op(),
                rt_mx_ji_1=rt_mx_ji,
                rt_mx_ji_2=rt_mx_kj)):
            processed_proxy_dict[pair_key] = 0
            if (k_sym != 0 or pair1.j_seq < pair2.j_seq):
              proxies.proxies.append( restraints.bond_sym_proxy(
                pair=asu_mappings.make_pair(
                  i_seq=pair1.j_seq, j_seq=pair2.j_seq, j_sym=k_sym),
                distance_ideal=distance_ideal,
                weight=weight))
              proxies.sorted_proxies.process(proxies.proxies[-1])
              if (1):
                assert abs(  restraints.bond(
                               sites_cart=structure.sites_cart(),
                               asu_mappings=proxies.asu_mappings,
                               proxy=proxies.proxies[-1]).distance_model
                           - primary_distance) <= primary_distance*1.e-6
        if (k_sym_start == 0):
          rt_mx_ji = rt_mx_j2.inverse().multiply(rt_mx_j1)
          for k_sym in xrange(n_sym_1):
            pair_key = (pair2.j_seq, pair1.j_seq, k_sym)
            if (pair_key in processed_proxy_dict):
              continue
            rt_mx_k = asu_mappings.get_rt_mx(i_seq=pair1.j_seq, i_sym=k_sym)
            k_distance = structure.unit_cell().distance(
              rt_mx_j20*scatterers[pair2.j_seq].site,
              rt_mx_k*scatterers[pair1.j_seq].site)
            if (abs(k_distance-primary_distance) > primary_distance*1.e-6):
              continue
            rt_mx_kj = rt_mx_j20.inverse().multiply(rt_mx_k)
            if (1):
              ctrl = structure.unit_cell().distance(
                scatterers[pair2.j_seq].site,
                rt_mx_kj*scatterers[pair1.j_seq].site)
              assert abs(ctrl-primary_distance) <= primary_distance*1.e-6
            if (is_sym_equiv_interaction(
                  unit_cell=structure.unit_cell(),
                  i_seq=pair2.j_seq,
                  site_i=structure.scatterers()[pair2.j_seq].site,
                  j_seq=pair1.j_seq,
                  site_j=structure.scatterers()[pair1.j_seq].site,
                  special_op_j
                    =proxies.site_symmetries[pair1.j_seq].special_op(),
                  rt_mx_ji_1=rt_mx_ji,
                  rt_mx_ji_2=rt_mx_kj)):
              processed_proxy_dict[pair_key] = 0
              if (k_sym != 0 or pair2.j_seq < pair1.j_seq):
                proxies.proxies.append(restraints.bond_sym_proxy(
                  pair=asu_mappings.make_pair(
                    i_seq=pair2.j_seq, j_seq=pair1.j_seq, j_sym=k_sym),
                  distance_ideal=distance_ideal,
                  weight=weight))
                proxies.sorted_proxies.process(proxies.proxies[-1])
                if (1):
                  assert abs(  restraints.bond(
                                 sites_cart=structure.sites_cart(),
                                 asu_mappings=proxies.asu_mappings,
                                 proxy=proxies.proxies[-1]).distance_model
                             - primary_distance) <= primary_distance*1.e-6

def add_si_o_si_proxies(si_proxies, si_o_proxies, distance_ideal, weight):
  assert si_proxies.asu_mappings.mappings().size() \
       < si_o_proxies.asu_mappings.mappings().size()
  for si_mappings,si_o_mappings in zip(si_proxies.asu_mappings.mappings(),
                                       si_o_proxies.asu_mappings.mappings()):
    assert len(si_mappings) == len(si_o_mappings)
    for si_m,si_o_m in zip(si_mappings, si_o_mappings):
      assert si_m.i_sym_op() == si_o_m.i_sym_op()
      assert si_m.unit_shifts() == si_o_m.unit_shifts()
  for si_proxy in si_proxies.proxies:
    si_o_proxies.proxies.append(
      restraints.bond_sym_proxy(
        pair=si_proxy.pair,
        distance_ideal=distance_ideal,
        weight=weight))
    si_o_proxies.sorted_proxies.process(si_o_proxies.proxies[-1])

def write_nodes_as_pdb(label, structure, node_list):
  import iotbx.pdb
  from cctbx import uctbx
  unit_cell = uctbx.unit_cell(
      [p*1.8/3.1 for p in structure.unit_cell().parameters()[:3]]
    + list(structure.unit_cell().parameters()[3:]))
  f = open(label+".pdb", "w")
  for serial,list_node in zip(count(1), node_list):
    site_frac = list_node.rt_mx * structure.scatterers()[list_node.i_seq].site
    site_cart = unit_cell.orthogonalize(site_frac)
    print >> f, iotbx.pdb.format_atom_record(serial=serial, site=site_cart)
  print >> f, "END"
  f.close()

def get_kriber_coseq_file():
  if (not os.path.isfile("coseq")): return {}
  result = {}
  for line in open("coseq"):
    flds = line.split()
    tag = flds[0]
    terms = [int(f) for f in flds[1:]]
    result.setdefault(tag, []).append(terms)
  return result

class node:

  def __init__(self, i_seq, rt_mx, special_ops):
    adopt_init_args(self, locals())
    self.special_op = special_ops[i_seq]
    self.rt_mx_unique = str(rt_mx.multiply(self.special_op))

def find_node(test_node, node_list):
  for list_node in node_list:
    if (    list_node.i_seq == test_node.i_seq
        and list_node.rt_mx_unique == test_node.rt_mx_unique):
      return 0001
  return 00000

class bond_registry:

  def __init__(self):
    self.shells = []

  def start_next_shell(self):
    self.shells.append([])

  def enter(self, entry):
    self.shells[-1].append(entry)

def coordination_sequences(structure, proxies, n_shells=10, coseq_terms=None):
  scatterers = structure.scatterers()
  pair_lists = [[] for i in xrange(scatterers.size())]
  for proxy in proxies.proxies:
    pair = proxy.pair
    pair_lists[pair.i_seq].append(pair)
    if (pair.j_sym == 0):
      pair_lists[pair.j_seq].append(pair)
  assert list(proxies.bond_counts) \
      == [len(pair_list) for pair_list in pair_lists]
  print "site symmetries:", [site_symmetry.point_group_type()
    for site_symmetry in proxies.site_symmetries]
  asu_mappings = proxies.asu_mappings
  special_ops = [site_symmetry.special_op()
    for site_symmetry in proxies.site_symmetries]
  bond_registries = []
  sums_terms = flex.double()
  multiplicities = flex.double()
  for i_seq_pivot in xrange(len(pair_lists)):
    bond_reg = bond_registry()
    if (len(pair_lists[i_seq_pivot]) == 0):
      bond_registries.append(bond_reg)
      continue
    nodes_middle = []
    nodes_next = [node(
      i_seq=i_seq_pivot, rt_mx=sgtbx.rt_mx(), special_ops=special_ops)]
    if (0):
      nodes_for_pdb = nodes_next[:]
    terms = flex.size_t([1])
    for i_shell in xrange(1,n_shells+1):
      nodes_previous = nodes_middle
      nodes_middle = nodes_next
      nodes_next = []
      for node_m in nodes_middle:
        for pair in pair_lists[node_m.i_seq]:
          rt_mx_n = node_m.rt_mx
          rt_mx_i = asu_mappings.get_rt_mx(i_seq=pair.i_seq, i_sym=0)
          rt_mx_j = asu_mappings.get_rt_mx(i_seq=pair.j_seq, i_sym=pair.j_sym)
          if (pair.i_seq == node_m.i_seq):
            new_node = node(
              i_seq=pair.j_seq,
              rt_mx=rt_mx_n.multiply(rt_mx_i.inverse().multiply(rt_mx_j)),
              special_ops=special_ops)
          else:
            assert pair.j_seq == node_m.i_seq
            new_node = node(
              i_seq=pair.i_seq,
              rt_mx=rt_mx_n.multiply(rt_mx_j.inverse().multiply(rt_mx_i)),
              special_ops=special_ops)
          if (    not find_node(test_node=new_node, node_list=nodes_previous)
              and not find_node(test_node=new_node, node_list=nodes_middle)
              and not find_node(test_node=new_node, node_list=nodes_next)):
            nodes_next.append(new_node)
      terms.append(len(nodes_next))
      if (i_shell <= 3):
        bond_reg.start_next_shell()
        for n in nodes_next:
          i_sym = asu_mappings.find_i_sym(i_seq=n.i_seq, rt_mx=n.rt_mx)
          if (i_sym > 0 or i_sym == 0  and i_seq_pivot < n.i_seq):
            bond_reg.enter((n.i_seq, i_sym))
      if (0):
        nodes_for_pdb.extend(nodes_next)
        write_nodes_as_pdb(
          label="shell_%02d_%02d" % (i_seq_pivot, i_shell),
          structure=structure,
          node_list=nodes_for_pdb)
    bond_registries.append(bond_reg)
    sums_terms.append(flex.sum(terms))
    multiplicities.append(scatterers[i_seq_pivot].multiplicity())
    print scatterers[i_seq_pivot].label, list(terms)
    if (coseq_terms is not None and n_shells >= 10):
      ten_terms = list(terms[1:11])
      have_match = 00000
      for cs_terms in coseq_terms:
        if (cs_terms == ten_terms):
          have_match = 0001
          break
      if (not have_match):
        print "Warning: Unknown coordination sequence"
      elif (0):
        print "Found coordination sequence"
  print "TD%d:" % (terms.size()-1), \
        flex.mean_weighted(sums_terms, multiplicities)
  print [bond_reg.shells for bond_reg in bond_registries]

def run(distance_cutoff=3.5):
  command_line = (iotbx_option_parser(
    usage="python distance_ls.py [options] studat_file [...]",
    description="Example: python distance_ls.py strudat --tag=SOD")
    .option(None, "--tag",
      action="store",
      type="string",
      dest="tag",
      help="tag as it appears in the strudat file")
  ).process()
  if (len(command_line.args) == 0):
    command_line.parser.show_help()
    return
  coseq_dict = get_kriber_coseq_file()
  for file_name in command_line.args:
    strudat_entries = strudat.read_all_entries(open(file_name))
    for entry in strudat_entries.entries:
      if (    command_line.options.tag is not None
          and command_line.options.tag != entry.tag):
        continue
      print "strudat tag:", entry.tag
      si_structure = entry.as_xray_structure()
      si_structure.show_summary().show_scatterers()
      show_distances(si_structure, distance_cutoff=distance_cutoff)
      si_proxies = create_bond_proxies(
        structure=si_structure, distance_cutoff=distance_cutoff)
      print "number of bond proxies:", si_proxies.proxies.size()
      print "proxies.bond_counts:", list(si_proxies.bond_counts)
      if (si_proxies.bond_counts.count(4) != si_proxies.bond_counts.size()):
        print "Not fully 4-connected:", entry.tag
      if (1):
        coordination_sequences(
          structure=si_structure,
          proxies=si_proxies,
          coseq_terms=coseq_dict.get(entry.tag, None))
      if (1):
        if (0):
          si_o_structure = si_structure
          si_o_proxies = si_proxies
        else:
          si_o_structure = add_oxygen(si_structure, si_proxies)
          si_o_structure.show_summary().show_scatterers()
          show_distances(
            si_o_structure,
            distance_cutoff=distance_cutoff/2.)
          si_o_proxies = create_bond_proxies(
            structure=si_o_structure,
            distance_cutoff=distance_cutoff/2.,
            distance_ideal=restraint_parameters_si_o.distance_ideal,
            weight=restraint_parameters_si_o.weight,
            heterogeneous_bonds_only=0001,
            asu_mappings_distance_cutoff=distance_cutoff)
          print "complete: number of bond proxies:", \
            si_o_proxies.proxies.size()
          print "complete: proxies.bond_counts:", \
            list(si_o_proxies.bond_counts)
          n_nodes = len(si_proxies.bond_counts)
          assert list(si_o_proxies.bond_counts[:n_nodes]) \
              == list(si_proxies.bond_counts)
          assert list(si_o_proxies.bond_counts[n_nodes:]) \
              == [2] * (len(si_o_proxies.bond_counts) - n_nodes)
          if (1):
            add_o_si_o_proxies(
              structure=si_o_structure,
              proxies=si_o_proxies,
              distance_ideal=restraint_parameters_o_si_o.distance_ideal,
              weight=restraint_parameters_o_si_o.weight)
          if (1):
            add_si_o_si_proxies(
              si_proxies=si_proxies,
              si_o_proxies=si_o_proxies,
              distance_ideal=restraint_parameters_si_o_si.distance_ideal,
              weight=restraint_parameters_si_o_si.weight)
          sites_cart = si_o_structure.sites_cart()
          for proxy in si_o_proxies.proxies:
            print "proxy:",
            scatterers = si_o_structure.scatterers()
            pair = proxy.pair
            print "%s(%d)" % (scatterers[pair.i_seq].label, pair.i_seq),
            print "%s(%d)" % (scatterers[pair.j_seq].label, pair.j_seq),
            print pair.j_sym,
            print proxy.distance_ideal, proxy.weight,
            print restraints.bond(
              sites_cart=sites_cart,
              asu_mappings=si_o_proxies.asu_mappings,
              proxy=proxy).distance_model
          print "sorted_proxies.proxies.size():",
          print si_o_proxies.sorted_proxies.proxies.size()
          print "sorted_proxies.sym_proxies.size():",
          print si_o_proxies.sorted_proxies.sym_proxies.size()
        if (1):
          sites_cart = si_o_structure.sites_cart()
          gradients_cart = flex.vec3_double(sites_cart.size(), [0,0,0])
          residual_sum = restraints.bond_residual_sum(
            sites_cart=sites_cart,
            asu_mappings=si_o_proxies.asu_mappings,
            proxies=si_o_proxies.proxies,
            gradient_array=gradients_cart)
          gradients_frac = gradients_cart \
            * si_o_structure.unit_cell().orthogonalization_matrix()
          print "initial residual sum:", residual_sum
          gradients_cart_2 = flex.vec3_double(sites_cart.size(), [0,0,0])
          residual_sum_2 = restraints.bond_residual_sum(
            sites_cart=sites_cart,
            sorted_proxies=si_o_proxies.sorted_proxies,
            gradient_array=gradients_cart_2)
          print "   ctrl residual sum:", residual_sum_2
          assert approx_equal(residual_sum_2, residual_sum)
          assert approx_equal(gradients_cart, gradients_cart_2)
        if (1):
          for i_site,scatterer in zip(count(),si_o_structure.scatterers()):
            site = scatterer.site
            site_symmetry = si_o_proxies.site_symmetries[i_site]
            special_op = sgtbx.rt_mx(site_symmetry.special_op().r())
            special_op_tp = float(special_op.r().as_rational()).transpose()
            grad_special = (  special_op_tp
                            * matrix.col(gradients_frac[i_site])).elems
            blanks = " "*len(scatterer.label)
            if (not approx_equal(gradients_frac[i_site], grad_special)):
              print scatterer.label, gradients_frac[i_site]
              print blanks, grad_special, special_op
              print "MISMATCH GRAD", si_o_structure.space_group_info(),
              print special_op
              raise AssertionError
            elif (0):
              print scatterer.label, gradients_frac[i_site]
              print blanks, grad_special, special_op
              print "    GOOD GRAD", si_o_structure.space_group_info(),
              print special_op
        if (1):
          best_target_value = None
          best_sites_cart = None
          for i_trial in xrange(10):
            if (1 and i_trial == 0):
              sites_cart = si_o_structure.sites_cart()
            else:
              sites_frac = flex.vec3_double(flex.random_double(
                size=si_o_structure.scatterers().size()*3))
              sites_special = flex.vec3_double()
              for site_frac,site_symmetry in zip(sites_frac,
                                                 si_o_proxies.site_symmetries):
                sites_special.append(site_symmetry.special_op()*site_frac)
              sites_cart = si_o_structure.unit_cell() \
                .orthogonalization_matrix() * sites_special
            if (0):
              minimized = minimization.lbfgs(
                sites_cart=sites_cart,
                site_symmetries=si_o_proxies.site_symmetries,
                asu_mappings=si_o_proxies.asu_mappings,
                bond_sym_proxies=si_o_proxies.proxies,
                lbfgs_termination_params=scitbx.lbfgs.termination_parameters(
                  max_iterations=1000))
            else:
              minimized = minimization.lbfgs(
                sites_cart=sites_cart,
                site_symmetries=si_o_proxies.site_symmetries,
                asu_mappings=si_o_proxies.asu_mappings,
                bond_sorted_proxies=si_o_proxies.sorted_proxies,
                lbfgs_termination_params=scitbx.lbfgs.termination_parameters(
                  max_iterations=1000))
            if (0):
              print minimized.minimizer.error
            if (0):
              print "first_target_value: %12.6f"%minimized.first_target_value,\
              entry.tag
            print "final_target_value: %12.6f" % minimized.final_target_value,\
              entry.tag
            if (   best_target_value is None
                or best_target_value > minimized.final_target_value):
              best_target_value = minimized.final_target_value
              best_sites_cart = sites_cart
          assert best_target_value is not None
          print "best_target_value: %12.6f" % best_target_value, entry.tag
          sites_cart = best_sites_cart
          sites_frac=si_o_structure.unit_cell().fractionalization_matrix() \
                    *sites_cart
          minimized_structure = si_o_structure.deep_copy_scatterers()
          for scatterer,site in zip(minimized_structure.scatterers(),
                                    sites_frac):
            scatterer.site = site
          print "minimized_structure:"
          minimized_structure.show_summary().show_scatterers()
          show_distances(minimized_structure, distance_cutoff=distance_cutoff)
      print

if (__name__ == "__main__"):
  run()
