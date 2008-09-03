"""
Construct all subgroup graphs and their relations between them from a single space group.
"""


from cctbx import sgtbx
from cctbx.sgtbx import show_cosets
from cctbx.sgtbx import pointgroup_tools
from cctbx.development import debug_utils
import sys,os


def reverse_dict( dict ):
  new_dict = {}
  for item in dict:
    for value in dict[item]:
      if value is not None:
        if new_dict.has_key( value ):
          tmp = new_dict[ value ]
          tmp.append( item )
          new_dict.update( {value:tmp} )
        else:
          new_dict.update( {value:[item]} )
  return new_dict

def get_maximal_subgroup( sg_name, reverse_graph ):
  subgroups = []
  if reverse_graph.has_key( sg_name ):
    subgroups = reverse_graph[ sg_name ]

  maximal = {}
  for sg in subgroups:
    maximal.update( {sg:True} )
  result = []
  for trial_sg in subgroups:
    tmp = {}
    if reverse_graph.has_key( trial_sg ):
      tmp = reverse_graph[ trial_sg ]
    is_trial_sg_a_subgroup_of_items_in_subgroups=False
    for item in tmp:
      if item in subgroups:
        maximal.update( {item:False} )
        is_trial_sg_a_subgroup_of_subgroups=True
  for item in maximal:
    if maximal[item]:
      result.append( item )
  return result





def create_all_subgroups( sg1,show_all=True, reverse=False ):
  sg_high = sgtbx.space_group_info( sg1  ).group()
  sg_low  = sgtbx.space_group_info( "p1" ).group()
  graph_object =  pointgroup_tools.point_group_graph( sg_low, sg_high, False,True)
  highest_sg = str( sgtbx.space_group_info( sg1  ) )
  rev_dict = reverse_dict( graph_object.graph.o )
  maximal_subgroups = get_maximal_subgroup( highest_sg, rev_dict )
  if show_all:
    print "Subgroups of input space groups which can be constructed by introducing one single operator (and group completion) in the subgroup:"
    for sg in rev_dict[ highest_sg ]:
      line = "       "
      line += sg+(30-len(sg))*" "+str(graph_object.graph.edge_objects[ sg ][highest_sg])+(90-len( str(graph_object.graph.edge_objects[ sg ][highest_sg]) ))*" "
      print line

    print
    print "Maximal subgroup detected in the full sub-group-graph: "
    for sg in maximal_subgroups:
      line = "       "
      line += sg
      print line

    print
    print
    print
    print " Cosets for each maximal sub-group and the input space group are listed:"
    for sg in maximal_subgroups:
      print "-----------------------------------------------------------------"
      show_cosets.run( sg,highest_sg )
      print "-----------------------------------------------------------------"
      print
      print
      print
      print

  else:
    print "Maximal subgroups of %s: "%(sg1)
    for sg in maximal_subgroups:
      line = "       "
      line += sg
      print line
    print
    print
    print

  if reverse:
    print "Minimal supergroups generated by the sub-groups of the input space group:"
    tmp_sg = sgtbx.space_group_info( sg1 )
    for sg in maximal_subgroups:
      tmp_sgsg = sgtbx.space_group_info( sg )
      cb_op = tmp_sgsg.change_of_basis_op_to_reference_setting()
      okai=False
      try:
        new_sg = tmp_sg.change_basis( cb_op )
        okai=True
        print new_sg ," is a minimal supergroup of ", tmp_sgsg.change_basis(cb_op)
      except: pass
      if not okai:
        print "%s (%s) is a minimal supergroup of %s     [*]"%(tmp_sg,cb_op, tmp_sgsg.change_basis(cb_op))
    print
    print
    print




def run_single(sg1, show=False, reverse=False):
  create_all_subgroups( sg1, show, reverse )

def run_all():
  sglist = debug_utils.get_test_space_group_symbols( False, False, True, False)
  for sg in sglist:
    run_single(sg)


if __name__=="__main__":
  if len(sys.argv)>1:
    run_single( sys.argv[1],True,True )
  else:
    run_all()
