from __future__ import division
import math
from scitbx.lstbx import normal_eqns
from cctbx.array_family import flex
from scitbx.matrix import col, sqr
from mod_partiality import partiality_handler

def get_overall_correlation (data_a, data_b) :
  """
  Correlate the averaged intensities to the intensities from the
  reference data set.
  """

  assert len(data_a) == len(data_b)
  corr = 0
  slope = 0
  try:
    sum_xx = 0
    sum_xy = 0
    sum_yy = 0
    sum_x  = 0
    sum_y  = 0
    N      = 0
    for i in xrange(len(data_a)):
      I_r       = data_a[i]
      I_o       = data_b[i]
      N      += 1
      sum_xx += I_r**2
      sum_yy += I_o**2
      sum_xy += I_r * I_o
      sum_x  += I_r
      sum_y  += I_o
    slope = (N * sum_xy - sum_x * sum_y) / (N * sum_xx - sum_x**2)
    corr  = (N * sum_xy - sum_x * sum_y) / (math.sqrt(N * sum_xx - sum_x**2) *
               math.sqrt(N * sum_yy - sum_y**2))
  except Exception:
    pass

  return corr, slope

class normal_eqns_handler(object):
  '''
  An interface class that handles non linear least-squares solving using
  scitbx.lstbx library.
  '''

  def __init__(self):
    '''
    Constructor
    '''

  def compute_cost_refine_scale(self, I_ref, observations_original_sel, wavelength, parameters):
    G = parameters[0]
    B_factor = parameters[1]

    I_obs = observations_original_sel.data()
    sigI_obs = observations_original_sel.sigmas()
    observations_original_sel_two_theta = observations_original_sel.two_theta(wavelength=wavelength)
    two_theta = observations_original_sel_two_theta.data()
    sin_theta_over_lambda_sq = observations_original_sel_two_theta.sin_theta_over_lambda_sq().data()

    excursions = ((G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs) - I_ref) / sigI_obs

    return excursions

  def compute_cost_refine_crystal(self, I_ref, observations_original_sel, crystal_init_orientation,
            wavelength, parameters):
    G = parameters[0]
    B_factor = parameters[1]
    rotx = parameters[2]
    roty = parameters[3]
    ry = parameters[4]
    rz = parameters[5]

    I_obs = observations_original_sel.data()
    sigI_obs = observations_original_sel.sigmas()
    observations_original_sel_two_theta = observations_original_sel.two_theta(wavelength=wavelength)
    two_theta = observations_original_sel_two_theta.data()
    sin_theta_over_lambda_sq = observations_original_sel_two_theta.sin_theta_over_lambda_sq().data()

    effective_orientation = crystal_init_orientation.rotate_thru((1,0,0),rotx
           ).rotate_thru((0,1,0),roty)

    effective_a_star = sqr(effective_orientation.reciprocal_matrix())
    ph = partiality_handler(wavelength, 0)
    partiality = ph.calc_partiality_anisotropy_set(effective_a_star, observations_original_sel.indices(), ry, rz, two_theta)

    excursions = (((G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs)/partiality) - I_ref) / sigI_obs

    return excursions

  def get_helper_refine_scale(self, I_ref, observations_original_sel,
              wavelength, parameters):

      class per_frame_helper(normal_eqns.non_linear_ls, normal_eqns.non_linear_ls_mixin):
        def __init__(pfh):
          super(per_frame_helper, pfh).__init__(n_parameters=len(parameters))
          pfh.x_0 = flex.double(parameters)
          pfh.restart()

        def restart(pfh):
          pfh.x = pfh.x_0.deep_copy()
          pfh.old_x = None

        def step_forward(pfh):
          pfh.old_x = pfh.x.deep_copy()
          pfh.x += pfh.step()

        def step_backward(pfh):
          assert pfh.old_x is not None
          pfh.x, pfh.old_x = pfh.old_x, None

        def parameter_vector_norm(pfh):
          return pfh.x.norm()

        def build_up(pfh, objective_only=False):
          residuals = pfh.fvec_callable(pfh.x)

          pfh.reset()
          if objective_only:
            pfh.add_residuals(residuals, weights=None)
          else:
            grad_r = pfh.jacobian_callable(pfh.x)
            jacobian = flex.double(
              flex.grid(len(I_ref), pfh.n_parameters))
            for j, der_r in enumerate(grad_r):
              jacobian.matrix_paste_column_in_place(der_r,j)
            pfh.add_equations(residuals, jacobian, weights=None)

        def fvec_callable(pfh,current_values):

          G = current_values[0]
          B_factor = current_values[1]

          I_obs = observations_original_sel.data()
          sigI_obs = observations_original_sel.sigmas()
          observations_original_sel_two_theta = observations_original_sel.two_theta(wavelength=wavelength)
          two_theta = observations_original_sel_two_theta.data()
          sin_theta_over_lambda_sq = observations_original_sel_two_theta.sin_theta_over_lambda_sq().data()

          excursions = ((G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs) - I_ref) / sigI_obs

          corr_now, slope_now = get_overall_correlation(G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs, I_ref)

          """
          print "SCALE G=%5.3f B_factor=%5.3f J=%6.3f cc=%6.3f slope=%6.3f"% \
          (G, B_factor, sum(excursions**2), corr_now, slope_now)


          plt.scatter(I_ref,(G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs),s=10, marker='x', c='r')
          plt.title('J=%6.5f CC=%6.5f Slope=%6.5f'%(sum(excursions**2), corr_now, slope_now))
          plt.xlabel('Reference intensity')
          plt.ylabel('Observed intensity (scaled)')
          plt.show()
          """

          return excursions


        def jacobian_callable(pfh,current_values):

          G = current_values[0]
          B_factor = current_values[1]

          I_obs = observations_original_sel.data()
          sigI_obs = observations_original_sel.sigmas()
          observations_original_sel_two_theta = observations_original_sel.two_theta(wavelength=wavelength)
          two_theta = observations_original_sel_two_theta.data()
          sin_theta_over_lambda_sq = observations_original_sel_two_theta.sin_theta_over_lambda_sq().data()

          delta_G = 0.00000001
          delta_B = 0.00000001

          pDg_pDG = flex.double()
          pDg_pDB_factor = flex.double()
          for j in range(len(observations_original_sel.indices())):
            #for G
            pDg_pDG.append((math.exp(-2*B_factor*sin_theta_over_lambda_sq[j]) * I_obs[j]) / sigI_obs[j])

            #for B_factor
            pDg_pDk = (G * I_obs[j])/sigI_obs[j]
            pDk_pDB_factor =-2 * sin_theta_over_lambda_sq[j] * math.exp(-2*B_factor*sin_theta_over_lambda_sq[j])
            pDg_pDB_factor.append(pDg_pDk * pDk_pDB_factor)


          """
          #checking partial derivatives
          g_now = self.compute_cost_refine_scale(I_ref, observations_original_sel, wavelength, (G,B_factor))
          g_delta_G = self.compute_cost_refine_scale(I_ref, observations_original_sel, wavelength, (G+delta_G,B_factor))
          g_delta_B = self.compute_cost_refine_scale(I_ref, observations_original_sel, wavelength, (G,B_factor+delta_B))

          pDg_pDG_fd = (g_delta_G - g_now)/delta_G
          pDg_pDB_factor_fd = (g_delta_B - g_now)/delta_B

          print sum(flex.abs(pDg_pDG_fd)), sum(flex.abs(pDg_pDG_fd-pDg_pDG))
          print sum(flex.abs(pDg_pDB_factor_fd)), sum(flex.abs(pDg_pDB_factor_fd-pDg_pDB_factor))
          print
          """

          return pDg_pDG, pDg_pDB_factor

      return per_frame_helper()

  def get_helper_refine_crystal_rotation(self, I_ref, observations_original_sel,
              wavelength, parameters, scale_factors, spot_radius, crystal_init_orientation):

      class per_frame_helper(normal_eqns.non_linear_ls, normal_eqns.non_linear_ls_mixin):
        def __init__(pfh):
          super(per_frame_helper, pfh).__init__(n_parameters=len(parameters))
          pfh.x_0 = flex.double(parameters)
          pfh.restart()

        def restart(pfh):
          pfh.x = pfh.x_0.deep_copy()
          pfh.old_x = None

        def step_forward(pfh):
          pfh.old_x = pfh.x.deep_copy()
          pfh.x += pfh.step()

        def step_backward(pfh):
          assert pfh.old_x is not None
          pfh.x, pfh.old_x = pfh.old_x, None

        def parameter_vector_norm(pfh):
          return pfh.x.norm()

        def build_up(pfh, objective_only=False):
          residuals = pfh.fvec_callable(pfh.x)

          pfh.reset()
          if objective_only:
            pfh.add_residuals(residuals, weights=None)
          else:
            grad_r = pfh.jacobian_callable(pfh.x)
            jacobian = flex.double(
              flex.grid(len(I_ref), pfh.n_parameters))
            for j, der_r in enumerate(grad_r):
              jacobian.matrix_paste_column_in_place(der_r,j)
            pfh.add_equations(residuals, jacobian, weights=None)

        def fvec_callable(pfh,current_values):

          rotx = current_values[0]
          roty = current_values[1]
          ry = spot_radius
          rz = spot_radius
          G = scale_factors[0]
          B_factor = scale_factors[1]


          I_obs = observations_original_sel.data()
          sigI_obs = observations_original_sel.sigmas()
          observations_original_sel_two_theta = observations_original_sel.two_theta(wavelength=wavelength)
          two_theta = observations_original_sel_two_theta.data()
          sin_theta_over_lambda_sq = observations_original_sel_two_theta.sin_theta_over_lambda_sq().data()

          effective_orientation = crystal_init_orientation.rotate_thru((1,0,0),rotx
           ).rotate_thru((0,1,0),roty)

          effective_a_star = sqr(effective_orientation.reciprocal_matrix())
          ph = partiality_handler(wavelength, 0)
          partiality = ph.calc_partiality_anisotropy_set(effective_a_star, observations_original_sel.indices(), ry, rz, two_theta)

          excursions = (((G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs)/partiality) - I_ref) / sigI_obs

          corr_now, slope_now = get_overall_correlation((G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs)/partiality, I_ref)

          """
          print "ROTATION G=%5.3f B_factor=%5.3f rotx=%6.5f roty=%6.5f ry=%6.5f rz=%6.5f J=%6.3f cc=%6.3f slope=%6.3f p_mean=%6.3f"% \
          (G, B_factor, rotx*180/math.pi, roty*180/math.pi, ry, rz, sum(excursions**2), corr_now, slope_now, flex.mean(partiality))


          plt.scatter(I_ref,(G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs)/partiality,s=10, marker='x', c='r')
          plt.title('J=%6.5f CC=%6.5f Slope=%6.5f'%(sum(excursions**2), corr_now, slope_now))
          plt.xlabel('Reference intensity')
          plt.ylabel('Observed intensity (scaled)')
          plt.show()
          """

          return excursions


        def jacobian_callable(pfh,current_values):

          rotx = current_values[0]
          roty = current_values[1]
          ry = spot_radius
          rz = spot_radius
          G = scale_factors[0]
          B_factor = scale_factors[1]

          I_obs = observations_original_sel.data()
          sigI_obs = observations_original_sel.sigmas()
          observations_original_sel_two_theta = observations_original_sel.two_theta(wavelength=wavelength)
          two_theta = observations_original_sel_two_theta.data()
          sin_theta_over_lambda_sq = observations_original_sel_two_theta.sin_theta_over_lambda_sq().data()

          delta_rot = 0.0001*math.pi/180
          delta_r = 0.00000001

          #0. Calculate current partiality based on current rotx
          crystal_current_orientation = crystal_init_orientation.rotate_thru((1,0,0),rotx
            ).rotate_thru((0,1,0),roty)
          a_star = sqr(crystal_current_orientation.reciprocal_matrix())
          ph = partiality_handler(wavelength, 0)

          #1. Calculate partial derivatives of J function
          Ai = sqr(crystal_init_orientation.reciprocal_matrix())
          Rx = col((1,0,0)).axis_and_angle_as_r3_rotation_matrix(rotx)
          Ry = col((0,1,0)).axis_and_angle_as_r3_rotation_matrix(roty)
          Rz = col((0,0,1)).axis_and_angle_as_r3_rotation_matrix(0.0)
          dRx_drotx = col((1,0,0)).axis_and_angle_as_r3_derivative_wrt_angle(rotx)
          dRy_droty = col((0,1,0)).axis_and_angle_as_r3_derivative_wrt_angle(roty)
          dA_drotx = Rz * Ry * dRx_drotx * Ai
          dA_droty = Rz * dRy_droty * Rx * Ai

          s0 = -1*col((0,0,1./wavelength))
          pDg_pDrotx = flex.double()
          pDg_pDroty = flex.double()
          pDg_pDry = flex.double()
          pDg_pDrz = flex.double()
          for j in range(len(observations_original_sel.indices())):
            miller_index = observations_original_sel.indices()[j]
            hvec = col(miller_index)
            xvec = a_star * hvec
            svec = s0 + xvec
            p, rh, rs = ph.calc_partiality_anisotropy(a_star, miller_index, ry, rz, two_theta[j])

            #for rotx
            pDxvec_pDrotx = dA_drotx * hvec
            pDrh_pDrotx = (svec.dot(pDxvec_pDrotx))/svec.length()

            #for roty
            pDxvec_pDroty = dA_droty * hvec
            pDrh_pDroty = (svec.dot(pDxvec_pDroty))/svec.length()

            #shared derivatives on rotx and roty
            pDP_pDrh = (-4*(rs**2)*rh)/((2*(rh**2))+(rs**2))**2
            pDg_pDP = (-1 * G * (math.exp(-2*B_factor*sin_theta_over_lambda_sq[j])) * I_obs[j])/(sigI_obs[j]*(p**2))


            pDg_pDrotx.append(pDg_pDP * pDP_pDrh * pDrh_pDrotx)
            pDg_pDroty.append(pDg_pDP * pDP_pDrh * pDrh_pDroty)

          """
          #checking partial derivatives
          g_now = self.compute_cost_refine_crystal(I_ref, observations_original_sel, crystal_init_orientation, wavelength, (G,B_factor,rotx,roty,ry,rz))
          g_delta_rotx = self.compute_cost_refine_crystal(I_ref, observations_original_sel, crystal_init_orientation, wavelength, (G,B_factor,rotx+delta_rot,roty,ry,rz))
          g_delta_roty = self.compute_cost_refine_crystal(I_ref, observations_original_sel, crystal_init_orientation, wavelength, (G,B_factor,rotx,roty+delta_rot,ry,rz))

          pDg_pDrotx_fd = (g_delta_rotx - g_now)/delta_rot
          pDg_pDroty_fd = (g_delta_roty - g_now)/delta_rot

          print sum(flex.abs(pDg_pDrotx_fd)), sum(flex.abs(pDg_pDrotx_fd-pDg_pDrotx))
          print sum(flex.abs(pDg_pDroty_fd)), sum(flex.abs(pDg_pDroty_fd-pDg_pDroty))
          print
          """

          return pDg_pDrotx, pDg_pDroty

      return per_frame_helper()


  def get_helper_refine_reflecting_range(self, I_ref, observations_original_sel,
              wavelength, parameters, scale_factors, rotations, crystal_init_orientation):

      class per_frame_helper(normal_eqns.non_linear_ls, normal_eqns.non_linear_ls_mixin):
        def __init__(pfh):
          super(per_frame_helper, pfh).__init__(n_parameters=len(parameters))
          pfh.x_0 = flex.double(parameters)
          pfh.restart()

        def restart(pfh):
          pfh.x = pfh.x_0.deep_copy()
          pfh.old_x = None

        def step_forward(pfh):
          pfh.old_x = pfh.x.deep_copy()
          pfh.x += pfh.step()

        def step_backward(pfh):
          assert pfh.old_x is not None
          pfh.x, pfh.old_x = pfh.old_x, None

        def parameter_vector_norm(pfh):
          return pfh.x.norm()

        def build_up(pfh, objective_only=False):
          residuals = pfh.fvec_callable(pfh.x)

          pfh.reset()
          if objective_only:
            pfh.add_residuals(residuals, weights=None)
          else:
            grad_r = pfh.jacobian_callable(pfh.x)
            jacobian = flex.double(
              flex.grid(len(I_ref), pfh.n_parameters))
            for j, der_r in enumerate(grad_r):
              jacobian.matrix_paste_column_in_place(der_r,j)
            pfh.add_equations(residuals, jacobian, weights=None)

        def fvec_callable(pfh,current_values):

          ry = current_values[0]
          rz = current_values[1]
          G = scale_factors[0]
          B_factor = scale_factors[1]
          rotx = rotations[0]
          roty = rotations[1]

          I_obs = observations_original_sel.data()
          sigI_obs = observations_original_sel.sigmas()
          observations_original_sel_two_theta = observations_original_sel.two_theta(wavelength=wavelength)
          two_theta = observations_original_sel_two_theta.data()
          sin_theta_over_lambda_sq = observations_original_sel_two_theta.sin_theta_over_lambda_sq().data()

          effective_orientation = crystal_init_orientation.rotate_thru((1,0,0),rotx
           ).rotate_thru((0,1,0),roty)

          effective_a_star = sqr(effective_orientation.reciprocal_matrix())
          ph = partiality_handler(wavelength, 0)
          partiality = ph.calc_partiality_anisotropy_set(effective_a_star, observations_original_sel.indices(), ry, rz, two_theta)

          excursions = (((G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs)/partiality) - I_ref) / sigI_obs

          corr_now, slope_now = get_overall_correlation((G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs)/partiality, I_ref)

          """
          print "RS G=%5.3f B_factor=%5.3f rotx=%6.5f roty=%6.5f ry=%6.5f rz=%6.5f J=%6.3f cc=%6.3f slope=%6.3f p_mean=%6.3f"% \
          (G, B_factor, rotx*180/math.pi, roty*180/math.pi, ry, rz, sum(excursions**2), corr_now, slope_now, flex.mean(partiality))


          plt.scatter(I_ref,(G * (flex.exp(-2*B_factor*sin_theta_over_lambda_sq)) * I_obs)/partiality,s=10, marker='x', c='r')
          plt.title('J=%6.5f CC=%6.5f Slope=%6.5f'%(sum(excursions**2), corr_now, slope_now))
          plt.xlabel('Reference intensity')
          plt.ylabel('Observed intensity (scaled)')
          plt.show()
          """

          return excursions


        def jacobian_callable(pfh,current_values):

          ry = current_values[0]
          rz = current_values[1]
          G = scale_factors[0]
          B_factor = scale_factors[1]
          rotx = rotations[0]
          roty = rotations[1]

          I_obs = observations_original_sel.data()
          sigI_obs = observations_original_sel.sigmas()
          observations_original_sel_two_theta = observations_original_sel.two_theta(wavelength=wavelength)
          two_theta = observations_original_sel_two_theta.data()
          sin_theta_over_lambda_sq = observations_original_sel_two_theta.sin_theta_over_lambda_sq().data()

          delta_r = 0.00000001

          #0. Calculate current partiality based on current rotx
          crystal_current_orientation = crystal_init_orientation.rotate_thru((1,0,0),rotx
            ).rotate_thru((0,1,0),roty)
          a_star = sqr(crystal_current_orientation.reciprocal_matrix())
          ph = partiality_handler(wavelength, 0)

          pDg_pDry = flex.double()
          pDg_pDrz = flex.double()
          for j in range(len(observations_original_sel.indices())):
            miller_index = observations_original_sel.indices()[j]
            p, rh, rs = ph.calc_partiality_anisotropy(a_star, miller_index, ry, rz, two_theta[j])

            pDg_pDP = (-1 * G * (math.exp(-2*B_factor*sin_theta_over_lambda_sq[j])) * I_obs[j])/(sigI_obs[j]*(p**2))
            pDP_pDrs = (4*rs*(rh**2))/(((2*(rh**2))+(rs**2))**2)
            rs_as_k = math.sqrt(((ry * math.cos(two_theta[j]))**2)+((rz * math.sin(two_theta[j]))**2))
            pDrs_pDry = ry * (math.cos(two_theta[j])**2)/ rs_as_k
            pDrs_pDrz = rz * (math.sin(two_theta[j])**2)/ rs_as_k

            pDg_pDry.append(pDg_pDP * pDP_pDrs * pDrs_pDry)
            pDg_pDrz.append(pDg_pDP * pDP_pDrs * pDrs_pDrz)

          """
          #checking partial derivatives
          g_now = self.compute_cost_refine_crystal(I_ref, observations_original_sel, crystal_init_orientation, wavelength, (G,B_factor,rotx,roty,ry,rz))
          g_delta_ry = self.compute_cost_refine_crystal(I_ref, observations_original_sel, crystal_init_orientation, wavelength, (G,B_factor,rotx,roty,ry+delta_r,rz))
          g_delta_rz = self.compute_cost_refine_crystal(I_ref, observations_original_sel, crystal_init_orientation, wavelength, (G,B_factor,rotx,roty,ry,rz+delta_r))

          pDg_pDry_fd = (g_delta_ry - g_now)/ delta_r
          pDg_pDrz_fd = (g_delta_rz - g_now)/ delta_r

          print sum(flex.abs(pDg_pDry_fd)), sum(flex.abs(pDg_pDry_fd-pDg_pDry))
          print sum(flex.abs(pDg_pDrz_fd)), sum(flex.abs(pDg_pDrz_fd-pDg_pDrz))
          print
          """

          return pDg_pDry, pDg_pDrz

      return per_frame_helper()
