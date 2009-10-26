from iotbx.shelx.from_ins import from_ins
from cctbx import crystal, adp_restraints

def run(structure_file_path):
  xs = from_ins(file_name=structure_file_path)

  asu_mappings = xs.asu_mappings(buffer_thickness=2)
  bond_table = crystal.pair_asu_table(asu_mappings)
  bond_table.add_covalent_pairs(xs.scattering_types())
  pair_sym_table = bond_table.extract_pair_sym_table()

  rigid_bonds = adp_restraints.shared_rigid_bond_proxy()
  scatterer = xs.scatterers()
  for sym_pair in pair_sym_table.iterator():
    i, j, op = sym_pair.i_seq, sym_pair.j_seq, sym_pair.rt_mx_ji
    if 'H' in [ scatterer[idx].scattering_type for idx in (i,j) ]: continue
    rigid_bonds.append(adp_restraints.rigid_bond_proxy((i,j), 1.))
  #rigid_bonds.show_sorted(
    #by_value="delta",
    #sites_cart=xs.sites_cart(),
    #site_labels=xs.scatterers().extract_labels(),
    #u_cart=xs.scatterers().extract_u_cart(xs.unit_cell()))
  deltas = rigid_bonds.deltas(
    sites_cart=xs.sites_cart(),
    u_cart=xs.scatterers().extract_u_cart(xs.unit_cell()))
  for bond, delta in zip(rigid_bonds, deltas):
    i, j = bond.i_seqs
    sc_1, sc_2 = scatterer[i], scatterer[j]
    print "%s <-> %s: %.3g" % (sc_1.label, sc_2.label, delta)



if __name__ == '__main__':
  import sys
  run(sys.argv[1])
