from cctbx.array_family import flex
from mmtbx import scaling
from mmtbx.scaling import absolute_scaling
from cctbx import uctbx
from cctbx import adptbx
from cctbx import sgtbx
from cctbx import maptbx
from cctbx import crystal
import cctbx.sgtbx.lattice_symmetry
import cctbx.sgtbx.cosets
import scitbx.math
from scitbx.math import chebyshev_lsq
from scitbx.math import chebyshev_polynome
from scitbx.math import chebyshev_lsq_fit
from libtbx.test_utils import approx_equal
from libtbx.utils import Sorry
from cStringIO import StringIO
import math
import sys
from iotbx import data_plots
from libtbx import table_utils

## python routines copied from iotbx.iotbx.reflection_statistics.
## Should be moved but are (for now) in a conveniant place.
class twin_law(object):
  def __init__(self,op,pseudo_merohedral_flag):
    self.operator =  op
    self.twin_type = pseudo_merohedral_flag


class twin_laws(object):
  def __init__(self,
               miller_array,
               lattice_symmetry_max_delta=3.0,
               out=None):

    self.input = miller_array.eliminate_sys_absent(integral_only=True,
                                                   log=out)
    self.change_of_basis_op_to_minimum_cell \
      = self.input.change_of_basis_op_to_minimum_cell()

    self.minimum_cell_symmetry = crystal.symmetry.change_basis(
      self.input,
      cb_op=self.change_of_basis_op_to_minimum_cell)

    self.lattice_group = sgtbx.lattice_symmetry.group(
      self.minimum_cell_symmetry.unit_cell(),
      max_delta=lattice_symmetry_max_delta)

    self.intensity_symmetry = \
      self.minimum_cell_symmetry.reflection_intensity_symmetry(
        anomalous_flag=self.input.anomalous_flag())

    self.euclid = self.intensity_symmetry.space_group_info().type()\
      .expand_addl_generators_of_euclidean_normalizer(flag_k2l=True,
                                                      flag_l2n=True )

    self.operators = []
    self.m=0
    self.pm=0

    cb_op = self.change_of_basis_op_to_minimum_cell.inverse()
    for partition in sgtbx.cosets.left_decomposition(
      g=self.lattice_group,
      h=self.intensity_symmetry.space_group()
          .build_derived_acentric_group()
          .make_tidy()).partitions[1:]:
      if (partition[0].r().determinant() > 0):
        is_pseudo_merohedral=False
        twin_type = '  M'
        self.m+=1
        euclid_check = sgtbx.space_group( self.euclid )
        try:
          euclid_check.expand_smx( partition[0] )
        except KeyboardInterupt: raise
        except:
          is_pseudo_merohedral=True
          twin_type = ' PM'
          self.pm+=1
          self.m-=1

        if ( euclid_check.order_z() != self.euclid.order_z() ):
          is_pseudo_merohedral=True
          if is_pseudo_merohedral:
            twin_type = ' PM'
            self.pm+=1
            self.m-=1

        self.operators.append(twin_law( cb_op.apply(partition[0]),
                                     twin_type)
                           )

  def show(self, out=None):
    if out is None:
      out=sys.stdout

    comments="""\
M:  Merohedral twin law
PM: Pseudomerohedral twin law"""

    if len(self.operators)!=0 :
      print >> out
      print >> out, "The following twin laws have been found:"
      print >> out
      table_labels = ('Type','Twin law             ')
      table_rows = []
      for twin_law in self.operators:
        table_rows.append(
          [twin_law.twin_type , str(twin_law.operator.r().as_hkl())] )
      print >> out, table_utils.format([table_labels]+table_rows,
                                       comments=comments,
                                       has_header=True,
                                       separate_rows=False,
                                       prefix='| ',
                                       postfix=' |')
      print >> out
      print >> out, "%3.0f merohedral twin operators found"%(self.m)
      print >> out, "%3.0f pseudo-merohedral twin operators found"%(self.pm)
      print >> out, "In total, %3.0f twin operator were found"%(len(self.operators))
      print >> out
      print >> out
      assert (self.m + self.pm)==len(self.operators)
    else:
      print >> out
      print >> out, "%3.0f merohedral twin operators found"%(self.m)
      print >> out, "%3.0f pseudo-merohedral twin operators found"%(self.pm)
      print >> out, "In total, %3.0f twin operator were found"%(len(self.operators))
      print >> out
      print >> out
      assert (self.m + self.pm)==len(self.operators)


class wilson_normalised_intensities(object):
  """ making centric and acentric cut """
  def __init__(self,
               miller_array,
               normalise=True,
               out=None,
               verbose=0):

    if out is None:
      out = sys.stdout

    assert not miller_array.space_group().is_centric()
    if not miller_array.is_xray_intensity_array():
      miller_array = miller_array.f_as_f_sq()

    work_array =  miller_array.deep_copy()
    if normalise:
      normalizer = absolute_scaling.kernel_normalisation(
        miller_array, auto_kernel=True)
      work_array = normalizer.normalised_miller.deep_copy()
      work_array = work_array.select(work_array.data()>0)
    else:
      work_array = miller_array.deep_copy().set_observation_type(miller_array)
      work_array = work_array.select(work_array.data()>0)

    self.acentric = work_array.select_acentric().as_intensity_array()
    self.centric = work_array.select_centric().as_intensity_array()

    assert (self.acentric.indices().size()>0)

    if verbose > -10:
      print >> out, "Number of centrics  :", self.centric.data().size()
      print >> out, "Number of acentrics :", self.acentric.data().size()



class detect_pseudo_translations(object):
  def __init__(self,
               miller_array,
               low_limit=10.0,
               high_limit=5.0,
               max_sites=100,
               height_cut=0.0,
               distance_cut=15.0,
               p_value_cut=0.05,
               out=None,verbose=0):
    if out is None:
      out=sys.stdout

    if miller_array.is_xray_intensity_array():
      miller_array = miller_array.f_sq_as_f()
    work_array = miller_array.resolution_filter(low_limit,high_limit)
    work_array = work_array.select(work_array.data()>0).set_observation_type(
      miller_array)
    if work_array.indices().size()<20:
      print >> out
      print >> out," WARNING: "
      print >> out,"  There are only %2.0f reflections between %3.1f and %3.1f A."%(
        work_array.indices().size(), low_limit, high_limit)
      print >> out,"  This might not be enough to obtain a good estimate"
      print >> out,"  of the presence or absense of pseudo translational"
      print >> out,"  symmetry."
    if work_array.indices().size()==0:
      raise Sorry("No low resolution reflections")


    if work_array.anomalous_flag():
      work_array = work_array.average_bijvoet_mates().set_observation_type(
        miller_array)

    everything_okai = True

    if (work_array.indices().size()<0):
      print >> out, \
         "The number of reflection between %3.1f and %3.1f Angstrom" \
         %( low_limit,
            high_limit )
      print >> out, "is equal to %i" %(work_array.indices().size())
      print >> out, " ##  This is not enough to obtain a reasonable estimate of"
      print >> out, " ##  the presence of translational NCS"
      everything_okai = False

    if everything_okai:


      patterson_map = work_array.patterson_map(
        symmetry_flags=maptbx.use_space_group_symmetry).apply_sigma_scaling()

      peak_list = patterson_map.tags().peak_search(
        map=patterson_map.real_map(),
        parameters=maptbx.peak_search_parameters())

      max_height = peak_list.heights()[0]

      sym_equiv_origin = sgtbx.sym_equiv_sites(
        unit_cell=patterson_map.unit_cell(),
        space_group=patterson_map.space_group(),
        original_site=(0,0,0))

      self.suspected_peaks = []

      if max_sites > peak_list.sites().size():
        max_sites = peak_list.sites().size()


      for i_peak in range(max_sites):
        height = peak_list.heights()[i_peak]/max_height*100.0
        site = peak_list.sites()[i_peak]
        dist_info = sgtbx.min_sym_equiv_distance_info(sym_equiv_origin, site)
        if (dist_info.dist() >= distance_cut):
          if (height >= height_cut):
            p_value = self.p_value(height)
            self.suspected_peaks.append( [dist_info.sym_op()*site,
                                          height, p_value,
                                          dist_info.dist()] )
      if len(self.suspected_peaks)==0:

        print >> out
        print >> out, "No patterson vectors with a length larger then"
        print >> out, "%5.2f found. removing distance constraint"%(distance_cut)
        print >> out
        distance_cut = 1e-3
        for i_peak in range(max_sites):
          height = peak_list.heights()[i_peak]/max_height*100.0
          site = peak_list.sites()[i_peak]
          dist_info = sgtbx.min_sym_equiv_distance_info(sym_equiv_origin, site)
          if (dist_info.dist() >= distance_cut):
            if (height >= height_cut):
              p_value = self.p_value(height)
              self.suspected_peaks.append( [dist_info.sym_op()*site,
                                            height, p_value,
                                            dist_info.dist()] )



      self.p_value_cut = p_value_cut
      self.mod_h = 2
      self.mod_k = 2
      self.mod_l = 2
      if everything_okai:
        self.high_peak = self.suspected_peaks[0][1]
        self.high_peak_distance = self.suspected_peaks[0][3]
        self.high_peak_xyz = self.suspected_peaks[0][0]
        self.high_p_value = self.suspected_peaks[0][2]
        if( self.high_p_value <= self.p_value_cut):
          self.guesstimate_mod_hkl()
        if verbose > 0:
          self.show(out)


  def guesstimate_mod_hkl(self):
    tmp_mod_h = 1.0/(self.high_peak_xyz[0]+1.0e-6)
    tmp_mod_k = 1.0/(self.high_peak_xyz[1]+1.0e-6)
    tmp_mod_l = 1.0/(self.high_peak_xyz[2]+1.0e-6)
    tmp_mod_h = int(math.fabs(tmp_mod_h)+0.5)
    if (tmp_mod_h>=8):
      tmp_mod_h = 2
    tmp_mod_k = int(math.fabs(tmp_mod_k)+0.5)
    if (tmp_mod_k>=8):
      tmp_mod_k = 2
    tmp_mod_l = int(math.fabs(tmp_mod_l)+0.5)
    if (tmp_mod_l>=8):
      tmp_mod_l = 2
    self.mod_h = tmp_mod_h
    self.mod_k = tmp_mod_k
    self.mod_l = tmp_mod_l

  def p_value(self, peak_height):
    x= peak_height/100.0
    result=None
    if x<1.0:
      x = x/(1.0-x)
      a = 0.06789
      b = 3.5628
      result = 1.0 - math.exp(- ((x/a)**(-b)) )
    else:
      result=0.0
    return result

  def show(self,out=None):
    if out is None:
      out = sys.stdout
    print >> out
    print >> out," Largest patterson peak with length larger then 15 Angstrom "
    print >> out
    print >> out," Frac. coord.        :%8.3f %8.3f %8.3f" %(self.high_peak_xyz)
    print >> out," Distance to origin  :%8.3f" %(self.high_peak_distance)
    print >> out," Height (origin=100) :%8.3f" %(self.high_peak)
    print >> out," p_value(height)     :%12.3e" %(self.high_p_value)
    print >> out
    print >> out,"   The reported p_value has the following meaning: "
    print >> out,"     The probability that a peak of the specified height "
    print >> out,"     or larger is found in a Patterson function of a "
    print >> out,"     macro molecule that does not have any translational"
    print >> out,"     pseudo symmetry is equal to %10.3e "%(self.high_p_value)
    print >> out,"     p_values smaller then 0.05 might indicate "
    print >> out,"     weak translation pseudo symmetry, or the self vector of "
    print >> out,"     a large anomalous scatterer such as Hg, whereas values "
    print >> out,"     smaller than 1e-3 are a very strong indication for "
    print >> out,"     the presence of translational pseudo symmetry."
    print >> out


    if self.high_p_value <= self.p_value_cut:

      print >> out
      print >> out, "The full list of patterson peaks is: "
      print >> out
      print >> out, "  x      y      z            height   p-value(height)"
      for ii in range(len(self.suspected_peaks)):
        print >> out, "(%6.3f,%6.3f,%6.3f ) :"%(
          self.suspected_peaks[ii][0]),

        print >> out,"%8.3f   (%9.3e)"%(
          self.suspected_peaks[ii][1],
          self.suspected_peaks[ii][2])

        if self.suspected_peaks[ii][2] > self.p_value_cut:
          break



class wilson_moments(object):
  def __init__(self,
               acentric_z,
               centric_z,
               out=None,
               verbose=0):
    if out is None:
      out=sys.stdout

    self.centric_i_ratio = None
    self.centric_f_ratio = None
    self.centric_e_sq_minus_one = None

    self.centric_i_ratio_library= [3.0,2.0]
    self.centric_f_ratio_library = [0.637,0.785]
    self.centric_e_sq_minus_one_library = [0.968,0.736]

    self.acentric_i_ratio = None
    self.acentric_f_ratio = None
    self.acentric_abs_e_sq_minus_one = None

    self.acentric_i_ratio_library= [2.0,1.5]
    self.acentric_f_ratio_library = [0.785,0.885]
    self.acentric_e_sq_minus_one_library = [0.736, 0.541]

    self.compute_ratios(
      acentric_z.data()/acentric_z.epsilons().data().as_double(),
      centric_z.data()/centric_z.epsilons().data().as_double())

    self.centric_present = True
    if centric_z.data().size()==0:
      self.centric_present=False

    if verbose>0:
      self.show(out)

  def compute_ratios(self, ac, c):

    if (ac.size()>0):
      mean_z = flex.mean( ac )
      mean_z_sq = flex.mean( ac*ac )
      mean_e = flex.mean( flex.sqrt(ac) )

      self.acentric_i_ratio = mean_z_sq / (mean_z*mean_z)
      self.acentric_f_ratio = mean_e*mean_e/mean_z
      self.acentric_abs_e_sq_minus_one = flex.mean( flex.abs(ac - 1.0) )

    if (c.size()>0):
      mean_z = flex.mean( c )
      mean_z_sq = flex.mean( c*c )
      mean_e = flex.mean( flex.sqrt(c) )

      self.centric_i_ratio = mean_z_sq / (mean_z*mean_z)
      self.centric_f_ratio = mean_e*mean_e/mean_z
      self.centric_abs_e_sq_minus_one = flex.mean( flex.abs(c - 1.0) )

  def show(self,out=None):
    if out is None:
      out = sys.stdout
    print >> out
    print >> out
    print >> out, "Wilson ratio and moments "
    print >> out
    print >> out, "Acentric reflections "
    print >> out, "   <I^2>/<I>^2    :%4.3f   (untwinned: %4.3f; perfect twin %4.3f)"\
          %(self.acentric_i_ratio,
            self.acentric_i_ratio_library[0],
            self.acentric_i_ratio_library[1])
    print >> out, "   <F>^2/<F^2>    :%4.3f   (untwinned: %4.3f; perfect twin %4.3f)"\
          %(self.acentric_f_ratio,
            self.acentric_f_ratio_library[0],
            self.acentric_f_ratio_library[1])
    print >> out, "   <|E^2 - 1|>    :%4.3f   (untwinned: %4.3f; perfect twin %4.3f)"\
          %(self.acentric_abs_e_sq_minus_one,
            self.acentric_e_sq_minus_one_library[0],
            self.acentric_e_sq_minus_one_library[1])
    print >> out
    print >> out
    if self.centric_present:
      print >> out, "Centric reflections "
      print >> out, "   <I^2>/<I>^2    :%4.3f   (untwinned: %4.3f; perfect twin %4.3f)"\
            %(self.centric_i_ratio,
              self.centric_i_ratio_library[0],
              self.centric_i_ratio_library[1])
      print >> out, "   <F>^2/<F^2>    :%4.3f   (untwinned: %4.3f; perfect twin %4.3f)"\
            %(self.centric_f_ratio,
              self.centric_f_ratio_library[0],
              self.centric_f_ratio_library[1])
      print >> out, "   <|E^2 - 1|>    :%4.3f   (untwinned: %4.3f; perfect twin %4.3f)"\
            %(self.centric_abs_e_sq_minus_one,
              self.centric_e_sq_minus_one_library[0],
              self.centric_e_sq_minus_one_library[1] )
      print >> out
      print >> out




class n_z_test(object):
  def __init__(self,
               normalised_acentric,
               normalised_centric,
               out=None,verbose=0):
    if out is None:
      out = sys.stdout

    centric_available = True
    acentric_available = True
    if normalised_centric.data().size() == 0:
      centric_available = False
    if normalised_acentric.data().size() == 0:
      acentric_available = False


    n_z = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
    ac_theory = flex.double([0.0000, 0.0952, 0.1813, 0.2592, 0.3297, 0.3935,
                             0.4512, 0.5034, 0.5507, 0.5934, 0.6321])

    c_theory =  flex.double([0.0000, 0.2481, 0.3453, 0.4187, 0.4738, 0.5205,
                             0.5614, 0.5972, 0.6289, 0.6572, 0.6833])
    ac_obs = flex.double(11,0)
    c_obs = flex.double(11,0)


    for ii in range(10):
      ac_obs[ii+1] = (
        (normalised_acentric.data() < (ii+1.0)/10.0) ).count(True)
      if (centric_available):
        c_obs[ii+1] = (
          (normalised_centric.data() < (ii+1.0)/10.0) ).count(True)
    if acentric_available:
      ac_obs = ac_obs/float(normalised_acentric.data().size())
    if centric_available:
      c_obs = c_obs/float(normalised_centric.data().size())

    max_deviation_ac = flex.max( flex.abs(ac_obs-ac_theory)  )
    max_deviation_c = flex.max( flex.abs(c_obs-c_theory) )


    n_z_less_then_one_ac = (
      normalised_acentric.data() < 1.0  ).count(True)
    n_z_less_then_one_c =(
      normalised_centric.data() < 1.0  ).count(True)

    d_kolmogorov_smirnov_ac = max_deviation_ac/ac_theory[10]*math.sqrt(
      n_z_less_then_one_ac )
    d_kolmogorov_smirnov_c = max_deviation_c/c_theory[10]*math.sqrt(
      n_z_less_then_one_c  )

    z = flex.double(range(11))/10.0

    self.z = z
    self.ac_obs = ac_obs
    self.ac_untwinned = ac_theory
    self.frac_ac_lt_1 = n_z_less_then_one_ac/normalised_acentric.data().size()
    self.max_diff_ac = max_deviation_ac
    self.kolmogorov_smirnoff_ac = max_deviation_ac/ac_theory[10]*math.sqrt(
      n_z_less_then_one_ac )

    self.c_obs = c_obs
    self.c_untwinned = c_theory

    self.frac_c_lt_1 = 0
    if normalised_centric.data().size()>0:
      self.frac_c_lt_1 = n_z_less_then_one_c/normalised_centric.data().size()
    self.max_diff_c = max_deviation_c
    self.kolmogorov_smirnoff_c = max_deviation_c/c_theory[10]*math.sqrt(
      n_z_less_then_one_c )

    self.mean_diff_ac = flex.sum(self.ac_obs - self.ac_untwinned)/11.0
    self.mean_diff_c = flex.sum(self.c_obs - self.c_untwinned)/11.0

    if verbose > 0:
      self.show(out)



  def show(self,out=None):
    if out is None:
      out = sys.stdout
    print >> out
    print >> out,"NZ test (0<=z<1) to detect twinning and possible translational NCS"
    print >> out
    print >> out
    print >> out,"-----------------------------------------------"
    print >> out,"|  Z  | Nac_obs | Nac_theo | Nc_obs | Nc_theo |"
    print >> out,"-----------------------------------------------"
    for ii in range(11):
      print >> out,"|%4.1f | %7.3f | %8.3f | %6.3f | %7.3f |" \
            %(ii/10.0,
              self.ac_obs[ii],
              self.ac_untwinned[ii],
              self.c_obs[ii],
              self.c_untwinned[ii])

    sign_ac = '+'
    if self.mean_diff_ac < 0:
      sign_ac = '-'

    sign_c = '+'
    if self.mean_diff_c < 0:
      sign_c = '-'

    print >> out,"-----------------------------------------------"
    print >> out,"| Maximum deviation acentric      :  %4.3f    |" \
          %(self.max_diff_ac)
    print >> out,"| Maximum deviation centric       :  %4.3f    |" \
          %(self.max_diff_c)
    print >> out,"|                                             |"
    print >> out,"| <NZ(obs)-NZ(twinned)>_acentric  : %1s%4.3f    |" \
          %(sign_ac,math.fabs(self.mean_diff_ac))
    print >> out,"| <NZ(obs)-NZ(twinned)>_centric   : %1s%4.3f    |" \
          %(sign_c,math.fabs(self.mean_diff_c))
    print >> out,"-----------------------------------------------"




class britton_test(object):
  def __init__(self,
               twin_law,
               miller_array,
               cc_cut_off=0.995,
               out=None,
               verbose=0):
    if out is None:
      out = sys.stdout


    result = [0.5,1.0,0,0]
    miller_array = miller_array.select(
    miller_array.data()>0).set_observation_type(miller_array)

    if not miller_array.is_xray_intensity_array():
      miller_array = miller_array.f_as_f_sq()

    britton_plot_array = []
    britton_plot_alpha = flex.double(range(50))/101.0
    detwin_object = scaling.detwin(miller_array.indices(),
                                   miller_array.data(),
                                   miller_array.sigmas(),
                                   miller_array.space_group(),
                                   miller_array.anomalous_flag(),
                                   twin_law)

    for ii in range(50):
      alpha = (ii)/101.0
      negative_fraction = detwin_object.detwin_with_alpha(alpha)
      britton_plot_array.append(negative_fraction)

    britton_plot_array = flex.double(britton_plot_array)
    britton_plot_array = britton_plot_array - britton_plot_array[0]

    if flex.min( britton_plot_array )==flex.max( britton_plot_array ):
      not_done=False
      estimated_alpha = 0.5
    else:
      estimated_alpha = 0.0
      not_done=True

    while not_done:
      for ii in range(48):
        alpha = ii/101.0
        britton_range = (flex.double(range(ii,50)))/101.0
        britton_obs = britton_plot_array[ii:50]
        result = self.get_alpha(britton_range,britton_obs)
        if result[1]>=cc_cut_off:
          estimated_alpha = result[0]
          not_done=False
          break
      cc_cut_off-=0.005

    ## reset the cc_cut_off one step back
    cc_cut_off+=0.005

    self.alpha_cut = ii/101.0


    britton_plot_fit = flex.double(50,0)
    for ii in range(50):
      alpha = ii/101.0
      if (alpha<estimated_alpha):
        britton_plot_fit[ii]=0.0
      else:
        britton_plot_fit[ii]= result[2] + alpha*result[3]


    self.estimated_alpha = estimated_alpha
    self.correlation = result[1]
    self.britton_alpha =  britton_plot_alpha
    self.britton_obs = britton_plot_array
    self.britton_fit = britton_plot_fit

    if verbose > 0:
      self.show(out)

  def get_alpha(self, x, y):
    assert x.size() == y.size()
    mean_x = flex.mean(x)
    mean_y = flex.mean(y)
    var_x = flex.mean(x*x)-mean_x*mean_x
    var_y = flex.mean(y*y)-mean_y*mean_y
    covar_xy = flex.mean(x*y)-mean_x*mean_y

    N = float(x.size())
    m = flex.sum(x*x)- N*mean_x*mean_x
    b = covar_xy/(var_x+1.0e-6)
    a = mean_y - b*mean_x
    correlation = covar_xy/(math.sqrt(var_x*var_y)+1.0e-6)
    return [-a/(b+1.0e-6) ,  correlation, a, b]


  def show(self, out=None):
    if out is None:
      out = sys.stdout
    print >> out
    print >> out
    print >> out, "Britton analyses"
    print >> out
    print >> out,"  Extrapolation performed on  %3.2f < alpha < 0.495 "\
          %(self.alpha_cut)
    print >> out,"  Estimated twin fraction: %4.3f"%(self.estimated_alpha)
    print >> out,"  Correlation: %5.4f"%(self.correlation)


class h_test(object):
  def __init__(self,
               twin_law,
               miller_array,
               fraction=0.50,
               out=None, verbose=0):
    if out is None:
      out = sys.stdout

    self.fraction = fraction
    miller_array = miller_array.select(
      miller_array.data()>0).set_observation_type(miller_array)

    if not miller_array.is_xray_intensity_array():
      miller_array = miller_array.f_as_f_sq()
    if miller_array.is_real_array():

      acentric_data =  miller_array.select_acentric().set_observation_type(
        miller_array)
      h_test_object  = scaling.h_test(acentric_data.indices(),
                                      acentric_data.data(),
                                      acentric_data.sigmas(),
                                      acentric_data.space_group(),
                                      acentric_data.anomalous_flag(),
                                      twin_law,
                                      fraction)

      self.mean_h = h_test_object.mean_h()
      self.mean_h2 = h_test_object.mean_h2()
      self.estimated_alpha = h_test_object.alpha()
      self.alpha_from_mean_h = (self.mean_h*2.0-1.0)/-2.0
      self.h_array = h_test_object.h_array()
      self.h_values = h_test_object.h_values()
      self.cumul_obs = h_test_object.h_cumul_obs()
      self.cumul_fit = h_test_object.h_cumul_fit()
      if verbose > 0:
        self.show(out)

  def show(self,out=None):
    if out is None:
      out = sys.stdout

    print >> out
    print >> out
    print >> out,"Results of the H-test on a-centric data: "
    print >> out
    print >> out," (Only %3.1f%% of the strongest twin pairs were used)"\
          %(self.fraction*100.0)
    print >> out
    print >> out,"mean |H| : %4.3f" %(self.mean_h) ,\
          "  (0.50: untwinned; 0.0: 50% twinned)"
    print >> out,"mean H^2 : %4.3f" %(self.mean_h2),\
          "  (0.33: untwinned; 0.0: 50% twinned)"
    print >> out,"Estimation of twin fraction via mean |H|: %4.3f" \
          %(self.alpha_from_mean_h)
    print >> out,"Estimation of twin fraction via cum. dist. of H: %4.3f" \
          %( self.estimated_alpha )
    print >> out


class l_test(object):
  def __init__(self, miller_array,
               parity_h=2.0,
               parity_k=2.0,
               parity_l=2.0,
               out=None,verbose=0):
    if out is None:
      out=sys.stdout

    acentric_data = miller_array.select_acentric().set_observation_type(
      miller_array)
    if not miller_array.is_xray_intensity_array():
      acentric_data = acentric_data.f_as_f_sq()
    self.parity_h = parity_h
    self.parity_k = parity_k
    self.parity_l = parity_l

    l_stats = scaling.l_test( acentric_data.indices(),
                              acentric_data.data()/\
                               acentric_data.epsilons().data().as_double(),
                              acentric_data.space_group(),
                              acentric_data.anomalous_flag(),
                              parity_h,
                              parity_k,
                              parity_l,
                              8);

    self.mean_l = l_stats.mean_l()
    self.mean_l2 = l_stats.mean_l2()

    self.l_cumul = l_stats.cumul()
    self.l_values = flex.double(range(self.l_cumul.size()))/float(
      self.l_cumul.size())
    self.l_cumul_untwinned = self.l_values
    self.l_cumul_perfect_twin = self.l_values*(
      3.0-self.l_values*self.l_values)/2.0

    self.ml_alpha = l_stats.ml_alpha()
    if verbose > 0:
      self.show(out)

  def show(self,out=None):
    if out is None:
      out=sys.stdout
    print >> out
    print >> out
    print >> out," L test for acentric data"
    print >> out
    print >> out, " using difference vectors (dh,dk,dl) of the form: "
    print >> out, "(%ihp,%ikp,%ilp)"%(self.parity_h,self.parity_k,self.parity_l)
    print >> out, "  where hp, kp, and lp are random signed integers such that "
    print >> out, "  2 <= |dh| + |dk| + |dl| <= 8 "
    print >> out
    print >> out, "  Mean |L|   :%4.3f  (untwinned: 0.500; perfect twin: 0.375)"\
          %(self.mean_l)
    print >> out, "  Mean  L^2  :%4.3f  (untwinned: 0.333; perfect twin: 0.200)"\
          %(self.mean_l2)
    print >> out
    print >> out, "  The distribution of |L| values indicates a twin fraction of"
    print >> out, "  %3.2f. Note that this estimate is not as reliable as obtained"\
          %(self.ml_alpha)
    print >> out,"  via a britton plot or H-test if twin laws are available. "
    print >> out
    print >> out




class twin_law_dependend_twin_tests(object):
  """Twin law dependent test results"""
  def __init__(self,
               twin_law,
               miller_array, out=None,verbose=0):

    acentric_data = miller_array.select_acentric().set_observation_type(
      miller_array)

    self.twin_law = twin_law

    self.h_test = h_test(twin_law.as_double_array()[0:9],
                         miller_array = acentric_data,
                         out=out,
                         verbose=verbose)

    self.britton_test = britton_test(twin_law.as_double_array()[0:9],
                                     acentric_data,
                                     out=out,
                                     verbose=verbose)


class summary_object(object):
  def __init__(self,
               file_name,
               nz_test,
               wilson_ratios,
               l_test,
               translational_pseudo_symmetry=None,
               twin_law_related_test=None,
               maha_cut = 3.0,
               out=None,
               verbose=0):
    if out is None:
      out = sys.stdout

    self.maha_cut = maha_cut
    self.file_name = file_name
    self.nz_test_max_ac = nz_test.max_diff_ac
    self.i_ratio_ac = wilson_ratios.acentric_i_ratio
    self.f_ratio_ac = wilson_ratios.acentric_f_ratio
    self.l = l_test.mean_l
    self.l2 = l_test.mean_l2

    self.maha_i = 393.383833
    self.maha_f = 0.1951891
    self.maha_if= 0.03802529
    self.maha_mean_i = 1.980972527
    self.mama_mean_f = 0.788604396
    tmp_i = self.i_ratio_ac-self.maha_mean_i
    tmp_f = self.f_ratio_ac-self.mama_mean_f
    self.maha_distance_moments = tmp_i*tmp_i*self.maha_i +\
                                 tmp_f*tmp_f*self.maha_f +\
                                 tmp_i*tmp_f*self.maha_if
    self.maha_distance_moments = math.sqrt(self.maha_distance_moments)


    self.maha_l = 117820.0
    self.maha_l2 = 106570
    self.maha_ll2= -212319
    self.maha_mean_l = 0.487758242
    self.mama_mean_l2 = 0.322836996
    tmp_l = self.l-self.maha_mean_l
    tmp_l2 = self.l2-self.mama_mean_l2
    self.maha_distance_l = tmp_l*tmp_l*self.maha_l +\
                           tmp_l2*tmp_l2*self.maha_l2 +\
                           tmp_l*tmp_l2*self.maha_ll2
    self.maha_distance_l = math.sqrt(self.maha_distance_l)


    self.max_peak_height = None
    self.max_peak_height_p_value = None
    self.p_value_cut =None

    if translational_pseudo_symmetry is not None:
      self.max_peak_height = translational_pseudo_symmetry.high_peak
      self.max_peak_height_p_value = translational_pseudo_symmetry.high_p_value
      self.p_value_cut  = translational_pseudo_symmetry.p_value_cut

    self.twin_law = []
    self.britton_alpha = []
    self.h_test_alpha = []


    self.n_twin_laws = len(twin_law_related_test)

    for ii in range(len(twin_law_related_test)):
      self.twin_law.append( twin_law_related_test[ii].twin_law.r().as_hkl() )
      self.h_test_alpha.append(
        twin_law_related_test[ii].h_test.estimated_alpha )
      self.britton_alpha.append(
        twin_law_related_test[ii].britton_test.estimated_alpha )

    if self.n_twin_laws>0:
      self.largest_twin_fraction = flex.max(flex.double(self.britton_alpha))
      self.twin_law_index = flex.max_index(flex.double(self.britton_alpha))
      self.twin_law_largest = self.twin_law[self.twin_law_index]
    if verbose>0:
      self.show(out)


  def show(self,out=None):
    if out is None:
      out = sys.stdout

    twin = False
    pseudo_trans = False
    undetermined_problem = False
    spacegroup_is_too_low= False

    print >> out
    print >> out,"------------------------------------------------------------------"
    print >> out,"Twin analyses summary "
    print >> out
    print >> out," Twinning tests independent of twin laws "
    print >> out
    print >> out," Ratio of moments of intensity "
    print >> out,"   Intensity ratio                          : %5.3f  "\
          %(self.i_ratio_ac )
    print >> out,"   Amplitude ratio                          : %5.3f " \
          %(self.f_ratio_ac )
    print >> out,"     Mahalanobis distance I and F ratio     : %5.3f " \
          %(self.maha_distance_moments)
    print >> out
    print >> out," L-test "
    print >> out,"   mean |L|                                 : %5.3f "\
          %(self.l  )
    print >> out,"   mean L^2                                 : %5.3f "\
          %(self.l2  )
    print >> out,"     Mahalanobis distance of L-test moments : %5.3f " \
          %(self.maha_distance_l)
    print >> out
    if self.max_peak_height is not None:
      print >> out," Detection of translational pseudo symmtery"
      print >> out,"   Patterson peak height                    : %5.3f (p_value: %8.3e)" \
            %(self.max_peak_height, self.max_peak_height_p_value  )

    print >> out
    if self.n_twin_laws > 0:
      print >> out," Twin law dependent tests "
      for ii in range(self.n_twin_laws):
        print >> out
        print >> out,"   Twin law :", self.twin_law[ii]
        print >> out,"     estimated twin fraction "
        print >> out,"       - via Britton analyses : %3.2f" %(self.britton_alpha[ii])
        print >> out,"       - via H-test           : %3.2f" %(self.h_test_alpha[ii])
      print >> out


    print >> out," Mahalanobis distance: multidimensional equivalent of Z-score."
    print >> out,"   Values of the Mahalanobis distance larger then 4 should be "
    print >> out,"   seen as an indication that the data does not behave as "
    print >> out,"   expected."

    print >> out
    print >> out," Interpretation of results: "
    print >> out
    if self.max_peak_height is not None:
      if self.max_peak_height_p_value < self.p_value_cut:
        pseudo_trans = True
        print >> out," There seems to be a significant off-origin "
        print >> out," peak in the Patterson. Check the Patterson "
        print >> out," section of the logfile for details."
        if self.i_ratio_ac > 2:
          if self.maha_distance_moments > self.maha_cut:
            print >> out," This pseudo translation is also responsible for the large"
            print >> out," mahalanobis distance for the I and F ratio. "
      else:
        print >> out," No significant pseudotranslation is detected "
    else:
      print >> out," Not enough low resolution data to perform detection of "
      print >> out," pseudo translational symmetry."

    if self.maha_distance_l > self.maha_cut:
      if self.l > 0.5:
        print >> out," The values of the L-test indicate that the data has "
        print >> out," some more centric characteristics then expected"
        if self.max_peak_height is not None:
          if self.max_peak_height_p_value < self.p_value_cut:
            print >> out," This might be due to the presence of pseudo translational"
            print >> out," symmetry. Lowering the resolution in the analyses might"
            print >> out," improve the results."
          else:
            print >> out," As there is no significant translational pseudo symmetry detected"
            print >> out," it is not quite clear why this is the case."
      if self.l <= 0.5:
        print >> out," The values of the L-test indicate that the data is twinned."
        if self.i_ratio_ac < 2:
          if self.maha_distance_moments > self.maha_cut:
            print >> out," This suspicion is confirmed by the Intensity ratio."
        if self.n_twin_laws > 0:
          twin = True
          print >> out," As there are twin operators, there is a good possibility"
          print >> out," that your data is actually twinned."
        if  self.n_twin_laws == 0:
          undetermined_problem = True
          print >> out," There are however no twin operators available for this "
          print >> out," crystal and the low L-values present can be explained"
          print >> out," by either poor data quality, an incorrect spacegroup or"
          print >> out," other reasons."

    else:
      print >> out," The data does not appear to be twinned"

    print >> out
    if self.n_twin_laws > 0:
      if not twin:
        print >> out," The data does not appear to be twinned as judged from the "
        print >> out," L-test. "
        if self.largest_twin_fraction < 0.4:
          if self.largest_twin_fraction > 0.05:
            print >> out," The estimated twin fractions via the britton test do however"
            print >> out," indicate a symmetry relation between possible twin related"
            print >> out," intensities. As the data does not apear to be twinned, one"
            print >> out," can interpret this as origination from a 2-fold NCS axis"
            print >> out," parallel to the putative twin axis. It might be usefull to "
            print >> out," refine a putative twin fraction during refinement."
        if self.largest_twin_fraction > 0.4:
          print >> out," The estimated twin fractions via the britton test do however"
          print >> out," indicate a symmetry relation between possible twin related"
          print >> out," intensities. As the data does not apear to be twinned, one"
          print >> out," can interpret this as origination from a 2-fold NCS axis"
          print >> out," parallel to the putative twin axis or that the spacegroup"
          print >> out," is too low. It might be usefull to refine a putative twin fraction"
          print >> out," during refinement and/or re-assess your data processing."
        if self.largest_twin_fraction <= 0.05:
          print >> out," The estimated twin fraction is lower then 0.05; The Britton and"
          print >> out," H-test confirm the suspicion that the data is not seriouly twinned "
          print >> out," It might however be useful to refine a twin fraction in the later "
          print >> out," stages of refinement to be sure."
      else:
        print >> out," The data appears to be twinned."
        if self.n_twin_laws==1:
          print >> out," The estimated twin fraction is %3.2f" %(self.largest_twin_fraction)
        else:
          print >> out," The largest possible twin fraction is equal to : %3.2f" %(self.largest_twin_fraction)
        print >> out," and might be a good start for density modification or refinement "
        print >> out," procedures."


    print >> out,"------------------------------------------------------------------"

class twin_analyses(object):
  """ Perform various twin related tests"""
  def __init__(self,
               miller_array,
               d_star_sq_low_limit=None,
               d_star_sq_high_limit=None,
               d_hkl_for_l_test=None,
               normalise=True, ## If normalised is true, normalisation is done
               out=None,
               out_plots = None,
               verbose = 1):

    ## If resolution limits are not specified
    ## use full resolution limit
    if  d_star_sq_high_limit is None:
      d_star_sq_high_limit = flex.min(miller_array.d_spacings().data())
      d_star_sq_high_limit = d_star_sq_high_limit**2.0
      d_star_sq_high_limit = 1.0/d_star_sq_high_limit
    if  d_star_sq_low_limit is None:
      d_star_sq_low_limit = flex.max(miller_array.d_spacings().data())
      d_star_sq_low_limit = d_star_sq_low_limit**2.0
      d_star_sq_low_limit = 1.0/d_star_sq_low_limit
    if d_hkl_for_l_test is None:
      d_hkl_for_l_test=[2.0,2.0,2.0]

    if out is None:
      out = sys.stdout

    ## sanity check on miller array
    if miller_array.observation_type() is None:
      raise RuntimeError("Observation type unknown")
    if miller_array.is_real_array():
      if miller_array.is_xray_intensity_array():
        miller_array = miller_array.f_sq_as_f()
    else:
      raise RuntimeError("Observations should be a real array.")

    print >> out, "Using data between %4.2f to %4.2f Angstrom."\
          %(math.sqrt(1./d_star_sq_low_limit),
            math.sqrt(1./d_star_sq_high_limit))
    print >> out

    miller_array = miller_array.resolution_filter(
      math.sqrt(1.0/d_star_sq_low_limit),
      math.sqrt(1.0/d_star_sq_high_limit))
    ## Determine possible twin laws
    print >> out, "Determining possible twin laws."
    possible_twin_laws = twin_laws(miller_array)
    possible_twin_laws.show(out=out)
    ##-----------------------------


    self.normalised_intensities = wilson_normalised_intensities(
      miller_array, normalise=normalise, out=out, verbose=verbose)


    ## Try to locat e pseudo translational symm.
    ## If no refls are available at low reso,
    ## an exception is thrown and caught here not to disturb things too much
    self.translation_pseudo_symmetry = None
    try:
      self.translation_pseudo_symmetry = detect_pseudo_translations(
        miller_array,
        out=out, verbose=verbose)
    except Sorry: pass

    centric_cut = self.normalised_intensities.centric

    acentric_cut = self.normalised_intensities.acentric

    self.wilson_moments = wilson_moments(
      acentric_cut,
      centric_cut, out=out, verbose=verbose)

    self.nz_test = n_z_test(
      acentric_cut,
      centric_cut,
      out=out, verbose=verbose)

    self.l_test=None
    if self.translation_pseudo_symmetry is not None:
      self.l_test = l_test(
        acentric_cut,
        self.translation_pseudo_symmetry.mod_h,
        self.translation_pseudo_symmetry.mod_k,
        self.translation_pseudo_symmetry.mod_l,
        out=out, verbose=verbose)
    else:
      self.l_test = l_test(
        acentric_cut,
        2,2,2,
        out=out, verbose=verbose)


    ##--------------------------

    if out_plots is not None:


      ## NZ test
      nz_test_plot  = data_plots.plot_data(
        plot_title = 'NZ test',
        x_label = 'z',
        y_label = 'P(Z>=z)',
        x_data = self.nz_test.z,
        y_data = self.nz_test.ac_obs,
        y_legend = 'Acentric observed',
        comments = 'NZ test, acentric and centric data')
      nz_test_plot.add_data(
        y_data = self.nz_test.ac_untwinned,
        y_legend = 'Acentric untwinned')
      nz_test_plot.add_data(
        y_data = self.nz_test.c_obs,
        y_legend = 'Centric observed')
      nz_test_plot.add_data(
        y_data = self.nz_test.c_untwinned,
        y_legend = 'Centric untwinned')
      data_plots.plot_data_loggraph(nz_test_plot,out_plots)
      ## L test
      l_test_plot  = data_plots.plot_data(
        plot_title = 'L test,acentric data',
        x_label = '|l|',
        y_label = 'P(L>=l)',
        x_data = self.l_test.l_values,
        y_data = self.l_test.l_cumul,
        y_legend = 'Observed',
        comments = 'L test, acentric data')
      l_test_plot.add_data(self.l_test.l_cumul_untwinned,
                           'Acentric theory')

      l_test_plot.add_data(self.l_test.l_cumul_perfect_twin,
                           'Acentric theory, perfect twin')
      data_plots.plot_data_loggraph(l_test_plot,out_plots)
      ##------------------------

    ##--------------------------

    self.n_twin_laws = len(possible_twin_laws.operators)

    self.twin_law_dependent_analyses = []

    for ii in range(self.n_twin_laws):
      print >> out
      print >> out,"---------------------------------------------"
      print >> out," Analysing possible twin law : ", \
            possible_twin_laws.operators[ii].operator.r().as_hkl()
      print >> out,"---------------------------------------------"

      tmp_twin_law_stuff = twin_law_dependend_twin_tests(
        possible_twin_laws.operators[ii].operator,
        acentric_cut,
        out=out,
        verbose=verbose )

      self.twin_law_dependent_analyses.append( tmp_twin_law_stuff)

      ## Plotting section
      ##    Britton plot
      britton_plot = data_plots.plot_data(
        plot_title = 'Britton plot for twin law '\
        + possible_twin_laws.operators[ii].operator.r().as_hkl(),
        x_label = 'alpha',
        y_label = 'percentage negatives',
        x_data = tmp_twin_law_stuff.britton_test.britton_alpha,
        y_data = tmp_twin_law_stuff.britton_test.britton_obs,
        y_legend = 'percentage negatives',
        comments = 'percentage negatives')
      britton_plot.add_data(tmp_twin_law_stuff.britton_test.britton_fit,
                            'fit')
      if out_plots is not None:
        data_plots.plot_data_loggraph(britton_plot,out_plots)
      ##    H test
      h_plot = data_plots.plot_data(
        plot_title = 'H test for possible twin law '\
        +possible_twin_laws.operators[ii].operator.r().as_hkl(),
        x_label = 'H',
        y_label = 'S(H)',
        x_data = tmp_twin_law_stuff.h_test.h_array,
        y_data = tmp_twin_law_stuff.h_test.cumul_obs,
        y_legend = 'Observed S(H)',
        comments = 'H test for Acentric data')
      h_plot.add_data(tmp_twin_law_stuff.h_test.cumul_fit, 'Fitted S(H)')
      if out_plots is not None:
        data_plots.plot_data_loggraph(h_plot,out_plots)

    ##--------------------------

    self.twin_summary = summary_object(miller_array.info(),
                                  self.nz_test,
                                  self.wilson_moments,
                                  self.l_test,
                                  self.translation_pseudo_symmetry,
                                  self.twin_law_dependent_analyses,
                                  out=out, verbose=2 )

def twin_analyses_brief(miller_array,
                        cut_off=4.0,
                        out = None,
                        verbose=0):
  """
  A very brief twin analyses and tries to answer the question whether or
  not the data is twinned.
  possible outputs and the meaning:
  - False: data is not twinned
  - True : data does not behave as expected. One possible explanantion
           is twinning
  - None : data does not behave as expected, and might or might not be
           due to twinning.
  """

  out_tmp = StringIO()
  out_tmp_plot = StringIO()
  twin_results = None
  twinned=None
  try:
    twin_results = twin_analyses(miller_array,
                                 d_star_sq_low_limit=1.0/100.0,
                                 d_star_sq_high_limit=1.0/(0.001**2.0),
                                 out = out_tmp,
                                 out_plots = out_tmp_plot,
                                 verbose=verbose)
  except Sorry, RuntimeError: pass


  if out is None:
    out = sys.stdout
  if twin_results is not None:
    if verbose>0:
      print >> out, "Brief summary of twin analyses"
      print >> out
      print >> out, "  Mahalanobis distance of L test moments: %3.2f"\
            %(twin_results.twin_summary.maha_distance_l)
      print >> out, "  Number of possible twin operators: %3.0f"\
            %(twin_results.n_twin_laws)
      if twin_results.twin_summary.n_twin_laws>0:
        print >> out, "  Largest estimated twin fraction %3.2f"\
              %(twin_results.twin_summary.largest_twin_fraction)
        print >> out, "  corresponding to twin operator :", \
              twin_results.twin_summary.twin_law_largest
      print >> out

    if (twin_results.twin_summary.maha_distance_l>cut_off):
      if twin_results.twin_summary.l <= 0.48:
        twinned = True
    if (twin_results.twin_summary.maha_distance_l<=cut_off):
        twinned = False

  return(twinned)
