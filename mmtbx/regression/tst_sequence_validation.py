
from __future__ import division
from libtbx import easy_mp
from libtbx import easy_pickle
from libtbx.utils import Sorry, null_out
import os

def exercise () :
  import libtbx.utils
  if (libtbx.utils.detect_multiprocessing_problem() is not None) :
    print "multiprocessing not available, skipping this test"
    return
  if (os.name == "nt"):
    print "easy_mp fixed_func not supported under Windows, skipping this test"
    return
  from mmtbx.validation.sequence import validation, get_sequence_n_copies, \
    get_sequence_n_copies_from_files
  import iotbx.bioinformatics
  import iotbx.pdb
  from iotbx import file_reader
  import libtbx.load_env # import dependency
  from libtbx.test_utils import Exception_expected, contains_lines, approx_equal
  from cStringIO import StringIO
  pdb_in = iotbx.pdb.input(source_info=None, lines="""\
ATOM      2  CA  ARG A  10      -6.299  36.344   7.806  1.00 55.20           C
ATOM     25  CA  TYR A  11      -3.391  33.962   7.211  1.00 40.56           C
ATOM     46  CA  ALA A  12      -0.693  34.802   4.693  1.00 67.95           C
ATOM     56  CA  ALA A  13       0.811  31.422   3.858  1.00 57.97           C
ATOM     66  CA  GLY A  14       4.466  31.094   2.905  1.00 49.24           C
ATOM     73  CA  ALA A  15       7.163  28.421   2.671  1.00 54.70           C
ATOM     83  CA  ILE A  16       6.554  24.685   2.957  1.00 51.79           C
ATOM    102  CA  LEU A  17       7.691  23.612   6.406  1.00 42.30           C
ATOM    121  CA  PTY A  18       7.292  19.882   5.861  1.00 36.68           C
ATOM    128  CA  PHE A  19       5.417  16.968   4.327  1.00 44.99           C
ATOM    148  CA  GLY A  20       3.466  14.289   6.150  1.00 41.99           C
ATOM    155  CA  GLY A  21       1.756  11.130   4.965  1.00 35.77           C
ATOM    190  CA  ALA A  24       1.294  19.658   3.683  1.00 47.02           C
ATOM    200  CA  VAL A  24A      2.361  22.009   6.464  1.00 37.13           C
ATOM    216  CA  HIS A  25       2.980  25.633   5.535  1.00 42.52           C
ATOM    234  CA  LEU A  26       4.518  28.425   7.577  1.00 47.63           C
ATOM    253  CA  ALA A  27       2.095  31.320   7.634  1.00 38.61           C
ATOM    263  CA  ARG A  28       1.589  34.719   9.165  1.00 37.04           C
END""")
  seq1 = iotbx.bioinformatics.sequence("MTTPSHLSDRYELGEILGFGGMSEVHLARD".lower())
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=[seq1],
    log=null_out(),
    nproc=1)
  out = StringIO()
  v.show(out=out)
  assert contains_lines(out.getvalue(), """\
  sequence identity: 76.47%
  13 residue(s) missing from PDB chain (9 at start, 1 at end)
  2 gap(s) in chain
  4 mismatches to sequence
    residue IDs:  12 13 15 24""")
  cif_block = v.as_cif_block()
  assert list(cif_block['_struct_ref.pdbx_seq_one_letter_code']) == [
    'MTTPSHLSDRYELGEILGFGGMSEVHLARD']
  assert approx_equal(cif_block['_struct_ref_seq.pdbx_auth_seq_align_beg'],
                      ['10', '14', '16', '19', '24'])
  assert approx_equal(cif_block['_struct_ref_seq.pdbx_auth_seq_align_end'],
                      ['11', '14', '17', '21', '28'])
  assert approx_equal(cif_block['_struct_ref_seq.db_align_beg'],
                      ['10', '14', '16', '19', '25'])
  assert approx_equal(cif_block['_struct_ref_seq.db_align_end'],
                      ['11', '14', '17', '21', '29'])
  assert cif_block['_struct_ref_seq.pdbx_seq_align_beg_ins_code'][4] == 'A'
  seq2 = iotbx.bioinformatics.sequence("MTTPSHLSDRYELGEILGFGGMSEVHLA")
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=[seq2],
    log=null_out(),
    nproc=1)
  out = StringIO()
  v.show(out=out)
  assert contains_lines(out.getvalue(), """\
  1 residues not found in sequence
    residue IDs:  28""")
  try :
    v = validation(
      pdb_hierarchy=pdb_in.construct_hierarchy(),
      sequences=[],
      log=null_out(),
      nproc=1)
  except AssertionError :
    pass
  else :
    raise Exception_expected
  cif_block = v.as_cif_block()
  assert list(cif_block['_struct_ref.pdbx_seq_one_letter_code']) == [
    'MTTPSHLSDRYELGEILGFGGMSEVHLA-']
  assert approx_equal(cif_block['_struct_ref_seq.pdbx_auth_seq_align_end'],
                      ['11', '14', '17', '21', '27'])
  assert approx_equal(cif_block['_struct_ref_seq.db_align_end'],
                      ['11', '14', '17', '21', '28'])
  #
  pdb_in2 = iotbx.pdb.input(source_info=None, lines="""\
ATOM      2  CA  ARG A  10      -6.299  36.344   7.806  1.00 55.20           C
ATOM     25  CA  TYR A  11      -3.391  33.962   7.211  1.00 40.56           C
ATOM     46  CA  ALA A  12      -0.693  34.802   4.693  1.00 67.95           C
ATOM     56  CA  ALA A  13       0.811  31.422   3.858  1.00 57.97           C
ATOM     66  CA  GLY A  14       4.466  31.094   2.905  1.00 49.24           C
ATOM     73  CA  ALA A  15       7.163  28.421   2.671  1.00 54.70           C
ATOM     83  CA  ILE A  16       6.554  24.685   2.957  1.00 51.79           C
ATOM    102  CA  LEU A  17       7.691  23.612   6.406  1.00 42.30           C
TER
ATOM   1936  P     G B   2     -22.947 -23.615  15.323  1.00123.20           P
ATOM   1959  P     C B   3     -26.398 -26.111  19.062  1.00110.06           P
ATOM   1979  P     U B   4     -29.512 -30.638  21.164  1.00101.06           P
ATOM   1999  P     C B   5     -30.524 -36.109  21.527  1.00 92.76           P
ATOM   2019  P     U B   6     -28.684 -41.458  21.223  1.00 87.42           P
ATOM   2062  P     G B   8     -18.396 -45.415  21.903  1.00 80.35           P
ATOM   2085  P     A B   9     -13.852 -43.272  24.156  1.00 77.76           P
ATOM   2107  P     G B  10      -8.285 -44.242  26.815  1.00 79.86           P
END
""")
  seq3 = iotbx.bioinformatics.sequence("AGCUUUGGAG")
  v = validation(
    pdb_hierarchy=pdb_in2.construct_hierarchy(),
    sequences=[seq2,seq3],
    log=null_out(),
    nproc=1,
    extract_coordinates=True)
  out = StringIO()
  v.show(out=out)
  cif_block = v.as_cif_block()
  assert approx_equal(cif_block['_struct_ref.pdbx_seq_one_letter_code'],
                      ['MTTPSHLSDRYELGEILGFGGMSEVHLA', 'AGCUUUGGAG'])
  assert approx_equal(cif_block['_struct_ref_seq.pdbx_auth_seq_align_beg'],
                      ['10', '14', '16', '2', '6', '8'])
  assert approx_equal(cif_block['_struct_ref_seq.pdbx_auth_seq_align_end'],
                      ['11', '14', '17', '4', '6', '10'])
  assert (len(v.chains[0].get_outliers_table()) == 3)
  assert (len(v.get_table_data()) == 4)
  assert approx_equal(
    v.chains[0].get_mean_coordinate_for_alignment_range(11,11),
    (-0.693, 34.802, 4.693))
  assert approx_equal(
    v.chains[0].get_mean_coordinate_for_alignment_range(11,14),
    (2.93675, 31.43475, 3.53175))
  assert (v.chains[0].get_highlighted_residues() == [11,12,14])
  assert contains_lines(out.getvalue(), """\
  3 mismatches to sequence
    residue IDs:  12 13 15""")
  assert contains_lines(out.getvalue(), """\
  sequence identity: 87.50%
  2 residue(s) missing from PDB chain (1 at start, 0 at end)
  1 gap(s) in chain
  1 mismatches to sequence
    residue IDs:  5""")
  s = easy_pickle.dumps(v)
  seq4 = iotbx.bioinformatics.sequence("")
  try :
    v = validation(
      pdb_hierarchy=pdb_in2.construct_hierarchy(),
      sequences=[seq4],
      log=null_out(),
      nproc=1,
      extract_coordinates=True)
  except AssertionError :
    pass
  else :
    raise Exception_expected
  # check that nucleic acid chain doesn't get aligned against protein sequence
  pdb_in = iotbx.pdb.input(source_info=None, lines="""\
ATOM  18932  P  B DG D   1     -12.183  60.531  25.090  0.50364.79           P
ATOM  18963  P  B DG D   2      -9.738  55.258  20.689  0.50278.77           P
ATOM  18994  P  B DA D   3     -10.119  47.855  19.481  0.50355.17           P
ATOM  19025  P  B DT D   4     -13.664  42.707  21.119  0.50237.06           P
ATOM  19056  P  B DG D   5     -19.510  39.821  21.770  0.50255.45           P
ATOM  19088  P  B DA D   6     -26.096  40.001  21.038  0.50437.49           P
ATOM  19120  P  B DC D   7     -31.790  41.189  18.413  0.50210.00           P
ATOM  19149  P  B DG D   8     -34.639  41.306  12.582  0.50313.99           P
ATOM  19179  P  B DA D   9     -34.987  38.244   6.813  0.50158.92           P
ATOM  19210  P  B DT D  10     -32.560  35.160   1.082  0.50181.38           P
HETATM19241  P  BTSP D  11     -27.614  30.137   0.455  0.50508.17           P
""")
  sequences, _ = iotbx.bioinformatics.fasta_sequence_parse.parse(
    """>4GFH:A|PDBID|CHAIN|SEQUENCE
MSTEPVSASDKYQKISQLEHILKRPDTYIGSVETQEQLQWIYDEETDCMIEKNVTIVPGLFKIFDEILVNAADNKVRDPS
MKRIDVNIHAEEHTIEVKNDGKGIPIEIHNKENIYIPEMIFGHLLTSSNYDDDEKKVTGGRNGYGAKLCNIFSTEFILET
ADLNVGQKYVQKWENNMSICHPPKITSYKKGPSYTKVTFKPDLTRFGMKELDNDILGVMRRRVYDINGSVRDINVYLNGK
SLKIRNFKNYVELYLKSLEKKRQLDNGEDGAAKSDIPTILYERINNRWEVAFAVSDISFQQISFVNSIATTMGGTHVNYI
TDQIVKKISEILKKKKKKSVKSFQIKNNMFIFINCLIENPAFTSQTKEQLTTRVKDFGSRCEIPLEYINKIMKTDLATRM
FEIADANEENALKKSDGTRKSRITNYPKLEDANKAGTKEGYKCTLVLTEGDSALSLAVAGLAVVGRDYYGCYPLRGKMLN
VREASADQILKNAEIQAIKKIMGLQHRKKYEDTKSLRYGHLMIMTDQDHDGSHIKGLIINFLESSFPGLLDIQGFLLEFI
TPIIKVSITKPTKNTIAFYNMPDYEKWREEESHKFTWKQKYYKGLGTSLAQEVREYFSNLDRHLKIFHSLQGNDKDYIDL
AFSKKKADDRKEWLRQYEPGTVLDPTLKEIPISDFINKELILFSLADNIRSIPNVLDGFKPGQRKVLYGCFKKNLKSELK
VAQLAPYVSECTAYHHGEQSLAQTIIGLAQNFVGSNNIYLLLPNGAFGTRATGGKDAAAARYIYTELNKLTRKIFHPADD
PLYKYIQEDEKTVEPEWYLPILPMILVNGAEGIGTGWSTYIPPFNPLEIIKNIRHLMNDEELEQMHPWFRGWTGTIEEIE
PLRYRMYGRIEQIGDNVLEITELPARTWTSTIKEYLLLGLSGNDKIKPWIKDMEEQHDDNIKFIITLSPEEMAKTRKIGF
YERFKLISPISLMNMVAFDPHGKIKKYNSVNEILSEFYYVRLEYYQKRKDHMSERLQWEVEKYSFQVKFIKMIIEKELTV
TNKPRNAIIQELENLGFPRFNKEGKPYYGSPNDEIAEQINDVKGATSDEEDEESSHEDTENVINGPEELYGTYEYLLGMR
IWSLTKERYQKLLKQKQEKETELENLLKLSAKDIWNTDLKAFEVGYQEFLQRDAEAR
>4GFH:D|PDBID|CHAIN|SEQUENCE
GGATGACGATX
""")
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=sequences,
    log=null_out(),
    nproc=1,)
  out = StringIO()
  v.show(out=out)
  assert v.chains[0].n_missing == 0
  assert v.chains[0].n_missing_end == 0
  assert v.chains[0].n_missing_start == 0
  assert len(v.chains[0].alignment.matches()) == 11
  #
  pdb_in = iotbx.pdb.input(source_info=None, lines="""\
ATOM      2  CA  GLY A   1       1.367   0.551   0.300  1.00  7.71           C
ATOM      6  CA  CYS A   2       2.782   3.785   1.683  1.00  5.18           C
ATOM     12  CA  CYS A   3      -0.375   5.128   3.282  1.00  5.21           C
ATOM     18  CA  SER A   4      -0.870   2.048   5.492  1.00  7.19           C
ATOM     25  CA  LEU A   5       2.786   2.056   6.642  1.00  6.78           C
ATOM     33  CA  PRO A   6       3.212   4.746   9.312  1.00  7.03           C
ATOM     40  CA  PRO A   7       6.870   5.690   8.552  1.00  7.97           C
ATOM     47  CA  CYS A   8       6.021   6.070   4.855  1.00  6.48           C
ATOM     53  CA  ALA A   9       2.812   8.041   5.452  1.00  7.15           C
ATOM     58  CA  LEU A  10       4.739  10.382   7.748  1.00  8.36           C
ATOM     66  CA  SER A  11       7.292  11.200   5.016  1.00  7.00           C
ATOM     73  CA  ASN A  12       4.649  11.435   2.264  1.00  5.40           C
ATOM     81  CA  PRO A  13       1.879  13.433   3.968  1.00  5.97           C
ATOM     88  CA  ASP A  14       0.485  15.371   0.986  1.00  7.70           C
ATOM     96  CA  TYR A  15       0.565  12.245  -1.180  1.00  6.55           C
ATOM    108  CA  CYS A  16      -1.466  10.260   1.363  1.00  7.32           C
ATOM    113  N   NH2 A  17      -2.612  12.308   2.058  1.00  8.11           N
""")
  seq = iotbx.bioinformatics.sequence("GCCSLPPCALSNPDYCX")
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=[seq],
    log=null_out(),
    nproc=1,)
  out = StringIO()
  v.show(out=out)
  assert v.chains[0].n_missing == 0
  assert v.chains[0].n_missing_end == 0
  assert v.chains[0].n_missing_start == 0
  assert len(v.chains[0].alignment.matches()) == 17
  #
  pdb_in = iotbx.pdb.input(source_info=None, lines="""\
ATOM   2518  CA  PRO C   3      23.450  -5.848  45.723  1.00 85.24           C
ATOM   2525  CA  GLY C   4      20.066  -4.416  44.815  1.00 79.25           C
ATOM   2529  CA  PHE C   5      19.408  -0.913  46.032  1.00 77.13           C
ATOM   2540  CA  GLY C   6      17.384  -1.466  49.208  1.00 83.44           C
ATOM   2544  CA  GLN C   7      17.316  -5.259  49.606  1.00 89.25           C
ATOM   2553  CA  GLY C   8      19.061  -6.829  52.657  1.00 90.67           C
""")
  sequences, _ = iotbx.bioinformatics.fasta_sequence_parse.parse(
    """>1JN5:A|PDBID|CHAIN|SEQUENCE
MASVDFKTYVDQACRAAEEFVNVYYTTMDKRRRLLSRLYMGTATLVWNGNAVSGQESLSEFFEMLPSSEFQISVVDCQPV
HDEATPSQTTVLVVICGSVKFEGNKQRDFNQNFILTAQASPSNTVWKIASDCFRFQDWAS
>1JN5:B|PDBID|CHAIN|SEQUENCE
APPCKGSYFGTENLKSLVLHFLQQYYAIYDSGDRQGLLDAYHDGACCSLSIPFIPQNPARSSLAEYFKDSRNVKKLKDPT
LRFRLLKHTRLNVVAFLNELPKTQHDVNSFVVDISAQTSTLLCFSVNGVFKEVDGKSRDSLRAFTRTFIAVPASNSGLCI
VNDELFVRNASSEEIQRAFAMPAPTPSSSPVPTLSPEQQEMLQAFSTQSGMNLEWSQKCLQDNNWDYTRSAQAFTHLKAK
GEIPEVAFMK
>1JN5:C|PDBID|CHAIN|SEQUENCE
GQSPGFGQGGSV
""")
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=sequences,
    log=null_out(),
    nproc=1,)
  out = StringIO()
  v.show(out=out)
  assert v.chains[0].n_missing_start == 3
  assert v.chains[0].n_missing_end == 3
  assert v.chains[0].identity == 1.0
  assert v.chains[0].alignment.match_codes == 'iiimmmmmmiii'
  #
  pdb_in = iotbx.pdb.input(source_info=None, lines="""\
ATOM      2  CA  ALA A   2      -8.453  57.214 -12.754  1.00 52.95           C
ATOM      7  CA  LEU A   3      -8.574  59.274  -9.471  1.00 24.33           C
ATOM     15  CA  ARG A   4     -12.178  60.092  -8.575  1.00 28.40           C
ATOM     26  CA  GLY A   5     -14.170  61.485  -5.667  1.00 26.54           C
ATOM     30  CA  THR A   6     -17.784  60.743  -4.783  1.00 31.78           C
ATOM     37  CA  VAL A   7     -19.080  64.405  -4.464  1.00 21.31           C
""")
  seq = iotbx.bioinformatics.sequence("XALRGTV")
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=[seq],
    log=null_out(),
    nproc=1,)
  out = StringIO()
  v.show(out=out)
  assert v.chains[0].n_missing_start == 1
  assert v.chains[0].n_missing_end == 0
  assert v.chains[0].identity == 1.0
  assert v.chains[0].alignment.match_codes == 'immmmmm'
  #
  pdb_in = iotbx.pdb.input(source_info=None, lines="""\
ATOM   2171  CA  ASP I 355       5.591 -11.903   1.133  1.00 41.60           C
ATOM   2175  CA  PHE I 356       7.082  -8.454   0.828  1.00 39.82           C
ATOM   2186  CA  GLU I 357       5.814  -6.112  -1.877  1.00 41.12           C
ATOM   2195  CA  GLU I 358       8.623  -5.111  -4.219  1.00 42.70           C
ATOM   2199  CA  ILE I 359      10.346  -1.867  -3.363  1.00 43.32           C
ATOM   2207  CA  PRO I 360      11.658   0.659  -5.880  1.00 44.86           C
ATOM   2214  CA  GLU I 361      14.921  -0.125  -7.592  1.00 44.32           C
ATOM   2219  CA  GLU I 362      15.848   3.489  -6.866  1.00 44.27           C
HETATM 2224  CA  TYS I 363      16.482   2.005  -3.448  1.00 44.52           C
""")
  seq = iotbx.bioinformatics.sequence("NGDFEEIPEEYL")
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=[seq],
    log=null_out(),
    nproc=1,)
  out = StringIO()
  v.show(out=out)
  assert v.chains[0].n_missing_start == 2
  assert v.chains[0].n_missing_end == 1
  assert v.chains[0].identity == 1.0
  pdb_in = iotbx.pdb.input(source_info=None, lines="""\
ATOM    450  CA  ASN A   1      37.242  41.665  44.160  1.00 35.89           C
ATOM    458  CA  GLY A   2      37.796  38.269  42.523  1.00 30.13           C
HETATM  463  CA AMSE A   3      35.878  39.005  39.326  0.54 22.83           C
HETATM  464  CA BMSE A   3      35.892  39.018  39.323  0.46 22.96           C
ATOM    478  CA  ILE A   4      37.580  38.048  36.061  1.00 22.00           C
ATOM    486  CA  SER A   5      37.593  40.843  33.476  1.00 18.73           C
ATOM    819  CA  ALA A   8      25.982  34.781  27.220  1.00 18.43           C
ATOM    824  CA  ALA A   9      23.292  32.475  28.614  1.00 19.60           C
HETATM  830  CA BMSE A  10      22.793  30.814  25.223  0.41 22.60           C
HETATM  831  CA CMSE A  10      22.801  30.850  25.208  0.59 22.54           C
ATOM    845  CA  GLU A  11      26.504  30.054  24.966  1.00 25.19           C
ATOM    854  CA  GLY A  12      25.907  28.394  28.320  1.00 38.88           C
""")
  seq = iotbx.bioinformatics.sequence("NGMISAAAAMEG")
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=[seq],
    log=null_out(),
    nproc=1,)
  out = StringIO()
  v.show(out=out)
  assert v.chains[0].alignment.a == 'NGMISXXAAMEG'
  assert v.chains[0].alignment.b == 'NGMISAAAAMEG'
  pdb_in = iotbx.pdb.input(source_info=None, lines="""\
ATOM   4615  CA  ALA C   1       1.000   1.000   1.000  1.00 10.00
ATOM   4622  CA  ALA C   2       1.000   1.000   1.000  1.00 10.00
ATOM   4627  CA  ALA C   3       1.000   1.000   1.000  1.00 10.00
ATOM   4634  CA  ALA C   4       1.000   1.000   1.000  1.00 10.00
ATOM   4646  CA  ALA C   5       1.000   1.000   1.000  1.00 10.00
ATOM   4658  CA  ALA C   6       1.000   1.000   1.000  1.00 10.00
ATOM   4664  CA  ALA C   7       1.000   1.000   1.000  1.00 10.00
ATOM   4669  CA  ALA C   8       1.000   1.000   1.000  1.00 10.00
ATOM   4680  CA  ARG C   9       1.000   1.000   1.000  1.00 10.00
ATOM   4690  CA  GLY C  10       1.000   1.000   1.000  1.00 10.00
ATOM   4698  CA  PRO C  11       1.000   1.000   1.000  1.00 10.00
ATOM   4705  CA  LYS C  12       1.000   1.000   1.000  1.00 10.00
ATOM   4712  CA  TRP C  13       1.000   1.000   1.000  1.00 10.00
ATOM   4726  CA  GLU C  14       1.000   1.000   1.000  1.00 10.00
ATOM   4738  CA  SER C  15       1.000   1.000   1.000  1.00 10.00
ATOM   4744  CA  THR C  16       1.000   1.000   1.000  1.00 10.00
ATOM   4751  CA  GLY C  17       1.000   1.000   1.000  1.00 10.00
ATOM   4755  CA  TYR C  18       1.000   1.000   1.000  1.00 10.00
ATOM   4767  CA  PHE C  19       1.000   1.000   1.000  1.00 10.00
ATOM   4778  CA  ALA C  20       1.000   1.000   1.000  1.00 10.00
ATOM   4786  CA  ALA C  21       1.000   1.000   1.000  1.00 10.00
ATOM   4798  CA  TRP C  22       1.000   1.000   1.000  1.00 10.00
ATOM   4812  CA  GLY C  23       1.000   1.000   1.000  1.00 10.00
ATOM   4816  CA  GLN C  24       1.000   1.000   1.000  1.00 10.00
ATOM   4822  CA  GLY C  25       1.000   1.000   1.000  1.00 10.00
ATOM   4826  CA  THR C  26       1.000   1.000   1.000  1.00 10.00
ATOM   4833  CA  LEU C  27       1.000   1.000   1.000  1.00 10.00
ATOM   4841  CA  VAL C  28       1.000   1.000   1.000  1.00 10.00
ATOM   4848  CA  THR C  29       1.000   1.000   1.000  1.00 10.00
ATOM   4855  CA  VAL C  30       1.000   1.000   1.000  1.00 10.00
ATOM   4862  CA  SER C  31       1.000   1.000   1.000  1.00 10.00
ATOM   4868  CA  SER C  32       1.000   1.000   1.000  1.00 10.00
END
""")
  seq = iotbx.bioinformatics.sequence(
    "AAAAAAAARGKWESPAALLKKAAWCSGTLVTVSSASAPKWKSTSGCYFAAPWNKRALRVTVLQSS")
  v = validation(
    pdb_hierarchy=pdb_in.construct_hierarchy(),
    sequences=[seq],
    log=null_out(),
    nproc=1,)
  out = StringIO()
  v.show(out=out)
  # all tests below here have additional dependencies
  if (not libtbx.env.has_module("ksdssp")) :
    print "Skipping advanced tests (require ksdssp module)"
    return
  pdb_file = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/pdb/1ywf.pdb",
    test=os.path.isfile)
  if (pdb_file is not None) :
    seq = iotbx.bioinformatics.sequence("MGSSHHHHHHSSGLVPRGSHMAVRELPGAWNFRDVADTATALRPGRLFRSSELSRLDDAGRATLRRLGITDVADLRSSREVARRGPGRVPDGIDVHLLPFPDLADDDADDSAPHETAFKRLLTNDGSNGESGESSQSINDAATRYMTDEYRQFPTRNGAQRALHRVVTLLAAGRPVLTHCFAGKDRTGFVVALVLEAVGLDRDVIVADYLRSNDSVPQLRARISEMIQQRFDTELAPEVVTFTKARLSDGVLGVRAEYLAAARQTIDETYGSLGGYLRDAGISQATVNRMRGVLLG")
    pdb_in = file_reader.any_file(pdb_file, force_type="pdb")
    hierarchy = pdb_in.file_object.hierarchy
    v = validation(
      pdb_hierarchy=hierarchy,
      sequences=[seq],
      log=null_out(),
      nproc=1,
      include_secondary_structure=True,
      extract_coordinates=True)
    out = StringIO()
    v.show(out=out)
    aln1, aln2, ss = v.chains[0].get_alignment(include_sec_str=True)
    assert ("HHH" in ss) and ("LLL" in ss) and ("---" in ss)
    cif_block = v.as_cif_block()
    assert cif_block['_struct_ref.pdbx_seq_one_letter_code'] == seq.sequence
    assert list(
      cif_block['_struct_ref_seq.pdbx_auth_seq_align_beg']) == ['4', '117']
    assert list(
      cif_block['_struct_ref_seq.pdbx_auth_seq_align_end']) == ['85', '275']
    assert list(cif_block['_struct_ref_seq.seq_align_beg']) == ['1', '114']
    assert list(cif_block['_struct_ref_seq.seq_align_end']) == ['82', '272']
    # determine relative counts of sequences and chains
    n_seq = get_sequence_n_copies(
      pdb_hierarchy=hierarchy,
      sequences=[seq] * 4,
      copies_from_xtriage=4,
      out=null_out())
    assert (n_seq == 1)
    hierarchy = hierarchy.deep_copy()
    chain2 = hierarchy.only_model().chains()[0].detached_copy()
    hierarchy.only_model().append_chain(chain2)
    n_seq = get_sequence_n_copies(
      pdb_hierarchy=hierarchy,
      sequences=[seq] * 4,
      copies_from_xtriage=2,
      out=null_out())
    assert (n_seq == 1)
    n_seq = get_sequence_n_copies(
      pdb_hierarchy=hierarchy,
      sequences=[seq],
      copies_from_xtriage=2,
      out=null_out())
    assert (n_seq == 4)
    try :
      n_seq = get_sequence_n_copies(
        pdb_hierarchy=hierarchy,
        sequences=[seq] * 3,
        copies_from_xtriage=2,
        out=null_out())
    except Sorry, s :
      assert ("round number" in str(s))
    else :
      raise Exception_expected
    n_seq = get_sequence_n_copies(
      pdb_hierarchy=hierarchy,
      sequences=[seq] * 3,
      copies_from_xtriage=2,
      force_accept_composition=True,
      out=null_out())
    assert (n_seq == 1)
    try :
      n_seq = get_sequence_n_copies(
        pdb_hierarchy=hierarchy,
        sequences=[seq] * 4,
        copies_from_xtriage=1,
        out=null_out())
    except Sorry, s :
      assert ("less than" in str(s))
    else :
      raise Exception_expected
    n_seq = get_sequence_n_copies(
      pdb_hierarchy=hierarchy,
      sequences=[seq] * 4,
      copies_from_xtriage=1,
      assume_xtriage_copies_from_sequence_file=True,
      out=null_out())
    assert (n_seq == 0.5)
    hierarchy = hierarchy.deep_copy()
    chain2 = hierarchy.only_model().chains()[0].detached_copy()
    hierarchy.only_model().append_chain(chain2)
    try :
      n_seq = get_sequence_n_copies(
        pdb_hierarchy=hierarchy,
        sequences=[seq] * 2,
        copies_from_xtriage=2,
        out=null_out())
    except Sorry, s :
      assert ("round number" in str(s))
    else :
      raise Exception_expected
    n_seq = get_sequence_n_copies(
      pdb_hierarchy=hierarchy,
      sequences=[seq],
      copies_from_xtriage=1,
      out=null_out())
    assert (n_seq == 3)
    hierarchy = hierarchy.deep_copy()
    chain2 = hierarchy.only_model().chains()[0].detached_copy()
    hierarchy.only_model().append_chain(chain2)
    n_seq = get_sequence_n_copies(
      pdb_hierarchy=hierarchy,
      sequences=[seq] * 2,
      copies_from_xtriage=2,
      out=null_out())
    assert (n_seq == 4)
    # now with files as input
    seq_file = "tmp_mmtbx_validation_sequence.fa"
    open(seq_file, "w").write(">1ywf\n%s" % seq.sequence)
    n_seq = get_sequence_n_copies_from_files(
      pdb_file=pdb_file,
      seq_file=seq_file,
      copies_from_xtriage=4,
      out=null_out())
    try :
      assert (n_seq == 4)
    finally :
      os.remove(seq_file)

if (__name__ == "__main__") :
  exercise()
  print "OK"
