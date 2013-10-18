from __future__ import division
import os
import smtbx.refinement
from libtbx.test_utils import approx_equal

def exercise_simple_disorder():
  working_dir = os.path.dirname(__file__)
  ins = os.path.join(working_dir, 'thpp.res')
  model = smtbx.refinement.model.from_shelx(ins)
  ls = model.least_squares()
  assert str(ls.reparametrisation).strip() == """\
digraph dependencies {
168 -> 0;
169 -> 1;
0 [label="independent_occupancy_parameter (C7A) #0"];
1 [label="independent_occupancy_parameter (N3) #1"];
2 [label="independent_site_parameter (F1) #2"];
5 [label="independent_u_star_parameter (F1) #5"];
11 [label="independent_site_parameter (F2) #11"];
14 [label="independent_u_star_parameter (F2) #14"];
20 [label="independent_site_parameter (N8) #20"];
23 [label="independent_u_star_parameter (N8) #23"];
29 [label="independent_site_parameter (N3) #29"];
32 [label="independent_u_iso_parameter (N3) #32"];
33 [label="independent_site_parameter (C9) #33"];
36 [label="independent_u_star_parameter (C9) #36"];
42 [label="independent_site_parameter (C4) #42"];
45 [label="independent_u_star_parameter (C4) #45"];
51 [label="independent_site_parameter (N5) #51"];
54 [label="independent_u_star_parameter (N5) #54"];
60 [label="independent_site_parameter (C2) #60"];
63 [label="independent_u_star_parameter (C2) #63"];
69 [label="independent_site_parameter (C10) #69"];
72 [label="independent_u_star_parameter (C10) #72"];
78 [label="independent_site_parameter (C1) #78"];
81 [label="independent_u_star_parameter (C1) #81"];
87 [label="independent_site_parameter (C11) #87"];
90 [label="independent_u_star_parameter (C11) #90"];
96 [label="independent_site_parameter (C13) #96"];
99 [label="independent_u_star_parameter (C13) #99"];
105 [label="independent_site_parameter (C6) #105"];
108 [label="independent_u_star_parameter (C6) #108"];
114 [label="independent_site_parameter (N12) #114"];
117 [label="independent_u_star_parameter (N12) #117"];
123 [label="independent_site_parameter (C7A) #123"];
126 [label="independent_u_star_parameter (C7A) #126"];
132 [label="independent_site_parameter (C14) #132"];
135 [label="independent_u_star_parameter (C14) #135"];
141 [label="independent_site_parameter (C7B) #141"];
144 [label="independent_u_star_parameter (C7B) #144"];
150 [label="independent_site_parameter (C3) #150"];
153 [label="independent_u_iso_parameter (C3) #153"];
154 [label="independent_occupancy_parameter [cst] (F1) #154"];
155 [label="independent_occupancy_parameter [cst] (F2) #155"];
156 [label="independent_occupancy_parameter [cst] (N8) #156"];
157 [label="independent_occupancy_parameter [cst] (C9) #157"];
158 [label="independent_occupancy_parameter [cst] (C4) #158"];
159 [label="independent_occupancy_parameter [cst] (N5) #159"];
160 [label="independent_occupancy_parameter [cst] (C2) #160"];
161 [label="independent_occupancy_parameter [cst] (C10) #161"];
162 [label="independent_occupancy_parameter [cst] (C1) #162"];
163 [label="independent_occupancy_parameter [cst] (C11) #163"];
164 [label="independent_occupancy_parameter [cst] (C13) #164"];
165 [label="independent_occupancy_parameter [cst] (C6) #165"];
166 [label="independent_occupancy_parameter [cst] (N12) #166"];
167 [label="independent_occupancy_parameter [cst] (C14) #167"];
168 [label="affine_asu_occupancy_parameter (C7B) #168"];
169 [label="affine_asu_occupancy_parameter (C3) #169"]
}
""".strip()
  ls.build_up()
  covann = ls.covariance_matrix_and_annotations()
  assert approx_equal(covann.variance_of('C7B.occ'),
                      covann.variance_of('C7A.occ'))
  assert approx_equal(covann.variance_of('C3.occ'),
                      covann.variance_of('N3.occ'))

def run():
  exercise_simple_disorder()
  print "OK"

if __name__ == '__main__':
  run()
