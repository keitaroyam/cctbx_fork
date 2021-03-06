from __future__ import division
import logging
from scitbx.matrix import sqr
from cctbx.uctbx import unit_cell
from cctbx import miller
from cctbx import crystal
from cctbx.array_family import flex
from iotbx import mtz
from iotbx import reflection_file_reader
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

class intensities_scaler(object):
  '''
  classdocs
  '''

  def __init__(self):
    '''
    Constructor
    '''

  def calc_average_I_sigI(self, I, sigI, G, B, p, SE_I, sin_theta_over_lambda_sq, avg_mode, SE, iph, d_spacings):
    for i in range(len(d_spacings)):
      if (d_spacings[i] < iph.d_min_partiality):
        p[i] = 1.0

    I_full = I/(G * flex.exp(-2*B*sin_theta_over_lambda_sq) * p)
    sigI_full = sigI/(G * flex.exp(-2*B*sin_theta_over_lambda_sq) * p)

    #filter out outliers
    if np.std(I_full) > 0:
      I_full_as_sigma = (I_full - np.mean(I_full))/ np.std(I_full)
      i_sel = (flex.abs(I_full_as_sigma) <= iph.sigma_max_merge)
      I_full = I_full.select(i_sel)
      sigI_full = sigI_full.select(i_sel)
      SE = SE.select(i_sel)

    #normalize the SE
    max_w = 1.0
    min_w = 0.6
    if len(SE) == 1 or ((flex.min(SE)-flex.max(SE)) == 0):
      SE_norm = flex.double([min_w+((max_w - min_w)/2)]*len(SE))
    else:
      m = (max_w - min_w)/(flex.min(SE)-flex.max(SE))
      b = max_w - (m*flex.min(SE))
      SE_norm = (m*SE) + b

    if avg_mode == 'weighted':
      I_avg = flex.sum(SE_norm * I_full)/flex.sum(SE_norm)
      sigI_avg = flex.sum(SE_norm * sigI_full)/flex.sum(SE_norm)
    elif avg_mode== 'average':
      I_avg = flex.mean(I_full)
      sigI_avg = flex.mean(sigI_full)

    #Rmeas, Rmeas_w, multiplicity
    multiplicity = len(I_full)
    if multiplicity == 1:
      r_meas_w_top = 0
      r_meas_w_btm = 0
      r_meas_top = 0
      r_meas_btm = 0
    else:
      n_obs = multiplicity
      r_meas_w_top = flex.sum(((I_full - I_avg)*SE_norm)**2)*math.sqrt(n_obs/(n_obs-1))
      r_meas_w_btm = flex.sum((I_full*SE_norm)**2)
      r_meas_top = flex.sum((I_full - I_avg)**2)*math.sqrt(n_obs/(n_obs-1))
      r_meas_btm = flex.sum((I_full)**2)


    #for calculattion of cc1/2
    #sepearte the observations into two groups
    if multiplicity == 1:
      I_avg_even = 0
      I_avg_odd = 0
    else:
      i_even = range(0,len(I_full),2)
      i_odd = range(1,len(I_full),2)
      I_even = I_full.select(i_even)
      sigI_even = sigI_full.select(i_even)
      SE_norm_even = SE_norm.select(i_even)
      I_odd = I_full.select(i_odd)
      sigI_odd = sigI_full.select(i_odd)
      SE_norm_odd = SE_norm.select(i_odd)
      if len(i_even) > len(i_odd):
        I_odd.append(I_even[len(I_even)-1])
        sigI_odd.append(sigI_even[len(I_even)-1])
        SE_norm_odd.append(SE_norm_even[len(I_even)-1])

      if avg_mode == 'weighted':
        I_avg_even = flex.sum(SE_norm_even * I_even)/flex.sum(SE_norm_even)
        I_avg_odd = flex.sum(SE_norm_odd * I_odd)/flex.sum(SE_norm_odd)
      elif avg_mode== 'average':
        I_avg_even = flex.mean(I_even)
        I_avg_odd = flex.mean(I_odd)

    return I_avg, sigI_avg, (r_meas_w_top, r_meas_w_btm, r_meas_top, r_meas_btm, multiplicity), I_avg_even, I_avg_odd

  def calc_mean_unit_cell(self, results, iph, uc_len_tol, uc_angle_tol):
    a_all = flex.double()
    b_all = flex.double()
    c_all = flex.double()
    alpha_all = flex.double()
    beta_all = flex.double()
    gamma_all = flex.double()
    for pres in results:
      if pres is not None:
        #check unit-cell
        if (abs(pres.uc_params[0]-iph.target_unit_cell[0]) <= uc_len_tol and abs(pres.uc_params[1]-iph.target_unit_cell[1]) <= uc_len_tol \
        and abs(pres.uc_params[2]-iph.target_unit_cell[2]) <= uc_len_tol and abs(pres.uc_params[3]-iph.target_unit_cell[3]) <= uc_angle_tol \
        and abs(pres.uc_params[4]-iph.target_unit_cell[4]) <= uc_angle_tol and abs(pres.uc_params[5]-iph.target_unit_cell[5]) <= uc_angle_tol):
          a_all.append(pres.uc_params[0])
          b_all.append(pres.uc_params[1])
          c_all.append(pres.uc_params[2])
          alpha_all.append(pres.uc_params[3])
          beta_all.append(pres.uc_params[4])
          gamma_all.append(pres.uc_params[5])

    uc_mean = flex.double([np.median(a_all), np.median(b_all), np.median(c_all), np.median(alpha_all), np.median(beta_all), np.median(gamma_all)])

    return uc_mean

  def output_mtz_files(self, results, iph, output_mtz_file_prefix, avg_mode):
    partiality_filter = 0.1
    sigma_filter = 8

    if avg_mode == 'average':
      cc_thres = 0
    else:
      cc_thres = iph.frame_accept_min_cc

    #prepare data for merging
    miller_indices_all = flex.miller_index()
    I_all = flex.double()
    sigI_all = flex.double()
    G_all = flex.double()
    B_all = flex.double()
    k_all = flex.double()
    p_all = flex.double()
    SE_I_all = flex.double()
    SE_all = flex.double()
    sin_sq_all = flex.double()
    cn_good_frame = 0
    cn_bad_frame_uc = 0
    cn_bad_frame_cc = 0
    for pres in results:
      if pres is not None:
        fh = file_handler()
        img_filename = fh.get_imgname_from_pickle_filename(iph.file_name_in_img, pres.pickle_filename)
        #check cc
        if pres.stats[2] >= cc_thres:
          #check unit-cell
          if (abs(pres.uc_params[0]-iph.target_unit_cell[0]) <= iph.uc_len_tol and abs(pres.uc_params[1]-iph.target_unit_cell[1]) <= iph.uc_len_tol \
          and abs(pres.uc_params[2]-iph.target_unit_cell[2]) <= iph.uc_len_tol and abs(pres.uc_params[3]-iph.target_unit_cell[3]) <= iph.uc_angle_tol \
          and abs(pres.uc_params[4]-iph.target_unit_cell[4]) <= iph.uc_angle_tol and abs(pres.uc_params[5]-iph.target_unit_cell[5]) <= iph.uc_angle_tol):
            cn_good_frame += 1
            sin_theta_over_lambda_sq = pres.observations.two_theta(wavelength=pres.wavelength).sin_theta_over_lambda_sq().data()
            for miller_index, i_obs, sigi_obs, p, se_i, sin_sq in zip(
                pres.observations.indices(), pres.observations.data(),
                pres.observations.sigmas(), pres.partiality, pres.SE_I, sin_theta_over_lambda_sq):

              miller_indices_all.append(miller_index)
              I_all.append(i_obs)
              sigI_all.append(sigi_obs)
              G_all.append(pres.G)
              B_all.append(pres.B)
              p_all.append(p)
              SE_I_all.append(se_i)
              sin_sq_all.append(sin_sq)
              SE_all.append(pres.stats[0])
            print pres.frame_no, img_filename, ' merged'
          else:
            print pres.frame_no, img_filename, ' discarded - unit-cell exceeds the limits (%6.2f %6.2f %6.2f %5.2f %5.2f %5.2f)'%(pres.uc_params[0], pres.uc_params[1], pres.uc_params[2], pres.uc_params[3], pres.uc_params[4], pres.uc_params[5])
            cn_bad_frame_uc += 1
        else:
          print pres.frame_no, img_filename, ' discarded - C.C. too low (C.C.=%5.2f%%)'%(pres.stats[2]*100)
          cn_bad_frame_cc += 1
    #plot stats
    self.plot_stats(results, iph, iph.uc_len_tol, iph.uc_angle_tol)

    #calculate average unit cell
    uc_mean = self.calc_mean_unit_cell(results, iph, iph.uc_len_tol, iph.uc_angle_tol)
    unit_cell_mean = unit_cell((uc_mean[0], uc_mean[1], uc_mean[2], uc_mean[3], uc_mean[4], uc_mean[5]))

    #from all observations merge them
    crystal_symmetry = crystal.symmetry(
        unit_cell=(uc_mean[0], uc_mean[1], uc_mean[2], uc_mean[3], uc_mean[4], uc_mean[5]),
        space_group_symbol=iph.target_space_group)
    miller_set_all=miller.set(
                crystal_symmetry=crystal_symmetry,
                indices=miller_indices_all,
                anomalous_flag=iph.target_anomalous_flag)
    miller_array_all = miller_set_all.array(
              data=I_all,
              sigmas=sigI_all).set_observation_type_xray_intensity()

    #sort reflections according to asymmetric-unit symmetry hkl
    perm = miller_array_all.sort_permutation(by_value="packed_indices")
    miller_indices_all_sort = miller_array_all.indices().select(perm)
    I_obs_all_sort = miller_array_all.data().select(perm)
    sigI_obs_all_sort = miller_array_all.sigmas().select(perm)
    d_spacings_sort = miller_array_all.d_spacings().data().select(perm)
    G_all_sort = G_all.select(perm)
    B_all_sort = B_all.select(perm)
    p_all_sort = p_all.select(perm)
    SE_I_all_sort = SE_I_all.select(perm)
    sin_sq_all_sort = sin_sq_all.select(perm)
    SE_all_sort = SE_all.select(perm)

    refl_now = 0
    miller_indices_merge = flex.miller_index()
    I_merge = flex.double()
    sigI_merge = flex.double()
    stat_all = []
    I_even = flex.double()
    I_odd = flex.double()
    while refl_now < len(I_obs_all_sort)-1:
      miller_index_group = miller_indices_all_sort[refl_now]
      I_obs_group = flex.double()
      sigI_obs_group = flex.double()
      d_spacings_group = flex.double()
      G_group = flex.double()
      B_group = flex.double()
      p_group = flex.double()
      SE_I_group = flex.double()
      sin_sq_group = flex.double()
      SE_group = flex.double()
      for i in range(refl_now, len(I_obs_all_sort)):
        if miller_indices_all_sort[i][0] == miller_index_group[0] and \
            miller_indices_all_sort[i][1] == miller_index_group[1] and \
            miller_indices_all_sort[i][2] == miller_index_group[2]:

          #select only reflections with higher partiality
          if p_all_sort[i] >= partiality_filter:
            I_obs_group.append(I_obs_all_sort[i])
            sigI_obs_group.append(sigI_obs_all_sort[i])
            d_spacings_group.append(d_spacings_sort[i])
            G_group.append(G_all_sort[i])
            B_group.append(B_all_sort[i])
            p_group.append(p_all_sort[i])
            SE_I_group.append(SE_I_all_sort[i])
            sin_sq_group.append(sin_sq_all_sort[i])
            SE_group.append(SE_all_sort[i])
          if i == (len(I_obs_all_sort) - 1):
            refl_now = i
            break
        else:
          refl_now = i
          break

      if len(I_obs_group) > 0:
        I_avg, sigI_avg, stat, I_avg_even, I_avg_odd = self.calc_average_I_sigI(I_obs_group, sigI_obs_group,
            G_group, B_group, p_group, SE_I_group, sin_sq_group, avg_mode, SE_group, iph, d_spacings_group)

        if math.isnan(stat[0]) or math.isinf(stat[0]) or math.isnan(stat[1]) or math.isinf(stat[1]):
          print miller_index_group, ' not merged (Qw=%.4g/%.4g)'%(stat[0],stat[1])
        else:
          miller_indices_merge.append(miller_index_group)
          I_merge.append(I_avg)
          sigI_merge.append(sigI_avg)
          stat_all.append(stat)
          I_even.append(I_avg_even)
          I_odd.append(I_avg_odd)


    #output mtz file and report binning stat
    miller_set_merge=miller.set(
              crystal_symmetry=crystal_symmetry,
              indices=miller_indices_merge,
              anomalous_flag=iph.target_anomalous_flag)
    miller_array_merge = miller_set_merge.array(data=I_merge,
              sigmas=sigI_merge).set_observation_type_xray_intensity()

    #remove outliers
    binner_merge = miller_array_merge.setup_binner(n_bins=iph.n_bins)
    binner_merge_indices = binner_merge.bin_indices()
    miller_indices_merge_filter = flex.miller_index()
    I_merge_filter = flex.double()
    sigI_merge_filter = flex.double()
    I_even_filter = flex.double()
    I_odd_filter = flex.double()
    stat_filter = []
    i_seq = flex.int([j for j in range(len(binner_merge_indices))])
    for i in range(1,iph.n_bins+1):
      i_binner = (binner_merge_indices == i)
      if len(miller_array_merge.data().select(i_binner)) > 0:
        I_obs_bin = miller_array_merge.data().select(i_binner)
        sigI_obs_bin = miller_array_merge.sigmas().select(i_binner)
        miller_indices_bin = miller_array_merge.indices().select(i_binner)
        stat_bin = [stat_all[j] for j in i_seq.select(i_binner)]
        I_even_bin = I_even.select(i_binner)
        I_odd_bin = I_odd.select(i_binner)

        i_filter = flex.abs((I_obs_bin - np.median(I_obs_bin))/np.median(I_obs_bin)) < sigma_filter
        I_obs_bin_filter = I_obs_bin.select(i_filter)
        sigI_obs_bin_filter = sigI_obs_bin.select(i_filter)
        miller_indices_bin_filter = miller_indices_bin.select(i_filter)
        i_seq_bin = flex.int([j for j in range(len(i_filter))])
        stat_bin_filter = [stat_bin[j] for j in i_seq_bin.select(i_filter)]
        I_even_bin_filter = I_even_bin.select(i_filter)
        I_odd_bin_filter = I_odd_bin.select(i_filter)

        for i_obs, sigi_obs, miller_index, stat, i_even, i_odd in zip(I_obs_bin_filter, sigI_obs_bin_filter,
            miller_indices_bin_filter, stat_bin_filter, I_even_bin_filter, I_odd_bin_filter):
          I_merge_filter.append(i_obs)
          sigI_merge_filter.append(sigi_obs)
          miller_indices_merge_filter.append(miller_index)
          stat_filter.append(stat)
          I_even_filter.append(i_even)
          I_odd_filter.append(i_odd)

    miller_set_merge=miller.set(
              crystal_symmetry=crystal_symmetry,
              indices=miller_indices_merge_filter,
              anomalous_flag=iph.target_anomalous_flag)
    miller_array_merge = miller_set_merge.array(data=I_merge_filter,
              sigmas=sigI_merge_filter).set_observation_type_xray_intensity()

    if output_mtz_file_prefix != '':
      mtz_dataset_merge = miller_array_merge.as_mtz_dataset(column_root_label="IOBS")
      mtz_dataset_merge.mtz_object().write(file_name=output_mtz_file_prefix+'_merge.mtz')

    #report binning stats
    miller_array_template_asu = miller_array_merge.complete_set().resolution_filter(
      d_min=iph.d_min, d_max=iph.d_max)
    binner_template_asu = miller_array_template_asu.setup_binner(n_bins=iph.n_bins)
    binner_template_asu_indices = binner_template_asu.bin_indices()

    csv_out = ""
    csv_out +='Bin, Low, High, Completeness, <N_obs>, Qmeas, Qw, CC1/2, N_ind, CCiso, N_ind, <I/sigI>\n'
    txt_out = '\n'
    txt_out += 'Summary for '+output_mtz_file_prefix+'_merge.mtz\n'
    txt_out += 'Bin Resolution Range     Completeness      <N_obs>  |Qmeas    Qw     CC1/2   N_ind |CCiso  N_ind| <I/sigI>\n'
    txt_out += '--------------------------------------------------------------------------------------------------------\n'
    sum_r_meas_w_top = 0
    sum_r_meas_w_btm = 0
    sum_r_meas_top = 0
    sum_r_meas_btm = 0
    for i in range(1,iph.n_bins+1):
      i_binner = (binner_template_asu_indices == i)
      miller_indices_bin = miller_array_template_asu.indices().select(i_binner)

      matches_template = miller.match_multi_indices(
                  miller_indices_unique=miller_indices_bin,
                  miller_indices=miller_array_merge.indices())

      I_bin = flex.double([miller_array_merge.data()[pair[1]] for pair in matches_template.pairs()])
      sigI_bin = flex.double([miller_array_merge.sigmas()[pair[1]] for pair in matches_template.pairs()])
      miller_indices_obs_bin = flex.miller_index([miller_array_merge.indices()[pair[1]] for pair in matches_template.pairs()])

      if len(I_bin) == 0:
        mean_i_over_sigi_bin = 0
        multiplicity_bin = 0
        r_meas_w_bin = 0
        r_meas_bin = 0
        cc12 = 0
      else:
        mean_i_over_sigi_bin = flex.mean(I_bin/sigI_bin)
        stat_bin = [stat_filter[pair[1]] for pair in matches_template.pairs()]
        sum_r_meas_w_top_bin = 0
        sum_r_meas_w_btm_bin = 0
        sum_r_meas_top_bin = 0
        sum_r_meas_btm_bin = 0
        sum_mul_bin = 0
        for stat in stat_bin:
          r_meas_w_top, r_meas_w_btm, r_meas_top, r_meas_btm, mul = stat

          sum_r_meas_w_top_bin += r_meas_w_top
          sum_r_meas_w_btm_bin += r_meas_w_btm
          sum_r_meas_top_bin += r_meas_top
          sum_r_meas_btm_bin += r_meas_btm
          sum_mul_bin += mul
          sum_r_meas_w_top += r_meas_w_top
          sum_r_meas_w_btm += r_meas_w_btm
          sum_r_meas_top += r_meas_top
          sum_r_meas_btm += r_meas_btm

        multiplicity_bin = sum_mul_bin/len(I_bin)
        if sum_r_meas_w_btm_bin > 0:
          r_meas_w_bin = sum_r_meas_w_top_bin/ sum_r_meas_w_btm_bin
        else:
          r_meas_w_bin = float('Inf')

        if sum_r_meas_btm_bin > 0:
          r_meas_bin = sum_r_meas_top_bin/ sum_r_meas_btm_bin
        else:
          r_meas_bin = float('Inf')

        I_even_filter_bin = flex.double([I_even_filter[pair[1]] for pair in matches_template.pairs()])
        I_odd_filter_bin = flex.double([I_odd_filter[pair[1]] for pair in matches_template.pairs()])
        #for cc1/2, use only non-zero I (zero when there is only one observation)
        i_even_filter_sel = (I_even_filter_bin > 0)
        n_refl_cc12_bin = len(I_even_filter_bin.select(i_even_filter_sel))
        cc12_bin = 0
        if n_refl_cc12_bin > 0:
          cc12_bin = np.corrcoef(I_even_filter_bin.select(i_even_filter_sel), I_odd_filter_bin.select(i_even_filter_sel))[0,1]

      completeness = len(miller_indices_obs_bin)/len(miller_indices_bin)

      #calculate CCiso
      cc_iso_bin = 0
      n_refl_cciso_bin = 0
      if iph.file_name_iso_mtz != '':
        matches_iso = miller.match_multi_indices(
                  miller_indices_unique=iph.miller_array_iso.indices(),
                  miller_indices=miller_indices_obs_bin)

        I_iso = flex.double([iph.miller_array_iso.data()[pair[0]] for pair in matches_iso.pairs()])
        I_merge_match_iso = flex.double([I_bin[pair[1]] for pair in matches_iso.pairs()])
        n_refl_cciso_bin = len(matches_iso.pairs())
        if len(matches_iso.pairs()) > 0 :
          cc_iso_bin = np.corrcoef(I_merge_match_iso, I_iso)[0,1]

        if iph.flag_plot:
          plt.scatter(I_iso, I_merge_match_iso,s=10, marker='x', c='r')
          plt.title('bin %3.0f CC=%.4g meanI=%.4g std=%.4g sqrt_meanI=%.4g mul=%.4g'%(i, cc_iso_bin, np.mean(I_merge_match_iso), np.std(I_merge_match_iso), math.sqrt(np.mean(I_merge_match_iso)), math.sqrt(np.mean(I_merge_match_iso))*2.5))
          plt.xlabel('I_ref')
          plt.ylabel('I_obs')
          plt.show()

      txt_out += '%02d %7.2f - %7.2f %5.1f %6.0f / %6.0f %7.2f %7.2f %7.2f %7.2f %6.0f %7.2f %6.0f %7.2f' \
          %(i, binner_template_asu.bin_d_range(i)[0], binner_template_asu.bin_d_range(i)[1], completeness*100, \
          len(miller_indices_obs_bin), len(miller_indices_bin),\
          multiplicity_bin, r_meas_bin*100, r_meas_w_bin*100, cc12_bin*100, n_refl_cc12_bin, cc_iso_bin*100, n_refl_cciso_bin, mean_i_over_sigi_bin)
      txt_out += '\n'
      csv_out += '%02d, %7.2f, %7.2f, %5.1f, %6.0f, %7.2f, %7.2f, %7.2f, %7.2f, %6.0f, %7.2f, %6.0f, %7.2f\n' \
                 %(i, binner_template_asu.bin_d_range(i)[0], binner_template_asu.bin_d_range(i)[1], completeness*100/len(miller_indices_obs_bin),
                   len(miller_indices_bin), multiplicity_bin, r_meas_bin*100, r_meas_w_bin*100, cc12_bin*100, n_refl_cc12_bin, cc_iso_bin*100,
                   n_refl_cciso_bin, mean_i_over_sigi_bin)

    #calculate CCiso
    cc_iso = 0
    n_refl_iso = 0
    if iph.file_name_iso_mtz != '':
      matches_iso = miller.match_multi_indices(
                miller_indices_unique=iph.miller_array_iso.indices(),
                miller_indices=miller_array_merge.indices())

      I_iso = flex.double([iph.miller_array_iso.data()[pair[0]] for pair in matches_iso.pairs()])
      I_merge_match_iso = flex.double([miller_array_merge.data()[pair[1]] for pair in matches_iso.pairs()])
      if len(matches_iso.pairs()) > 0 :
        cc_iso = np.corrcoef(I_merge_match_iso, I_iso)[0,1]
        n_refl_iso = len(matches_iso.pairs())
      if iph.flag_plot:
        plt.scatter(I_iso, I_merge_match_iso,s=10, marker='x', c='r')
        plt.title('CC=%.4g'%(cc_iso))
        plt.xlabel('I_ref')
        plt.ylabel('I_obs')
        plt.show()

    #calculate cc12
    i_even_filter_sel = (I_even_filter > 0)
    cc12 = np.corrcoef(I_even_filter.select(i_even_filter_sel), I_odd_filter.select(i_even_filter_sel))[0,1]

    #calculate Qmeas and Qw
    if sum_r_meas_w_btm > 0:
      r_meas_w = sum_r_meas_w_top/sum_r_meas_w_btm
    else:
      r_meas_w = float('Inf')

    if sum_r_meas_btm > 0:
      r_meas = sum_r_meas_top/sum_r_meas_btm
    else:
      r_meas = float('Inf')

    txt_out += '--------------------------------------------------------------------------------------------------------\n'
    txt_out += '        TOTAL        %5.1f %6.0f / %6.0f %7.2f %7.2f %7.2f %7.2f %6.0f %7.2f %6.0f %7.2f\n' \
    %((len(miller_array_merge.indices())/len(miller_array_template_asu.indices()))*100, len(miller_array_merge.indices()), \
     len(miller_array_template_asu.indices()), len(miller_indices_all)/len(miller_array_merge.data()), \
     r_meas*100, r_meas_w*100, cc12*100, len(I_even_filter.select(i_even_filter_sel)), cc_iso*100, \
     n_refl_iso, np.mean(miller_array_merge.data()/miller_array_merge.sigmas()))
    txt_out += '--------------------------------------------------------------------------------------------------------\n'
    txt_out += 'No. of total observed reflections: %9.0f from %5.0f frames' %(len(miller_indices_all), cn_good_frame)
    txt_out += '\n'
    txt_out += 'No. of discarded frames - initial unit cell exceeds the limit: %5.0f frames; C.C. too low: %5.0f'%(cn_bad_frame_uc, cn_bad_frame_cc)
    txt_out += '\n'
    txt_out += 'Average unit-cell parameters: (%6.2f, %6.2f, %6.2f %6.2f, %6.2f, %6.2f)'%(uc_mean[0], uc_mean[1], uc_mean[2], uc_mean[3], uc_mean[4], uc_mean[5])
    txt_out += '\n'
    print txt_out

    return miller_array_merge, txt_out, csv_out

  def plot_stats(self, results, iph, uc_len_tol, uc_angle_tol):
    #retrieve stats from results and plot them
    G_frame = flex.double()
    B_frame = flex.double()
    rotx_frame = flex.double()
    roty_frame = flex.double()
    ry_frame = flex.double()
    rz_frame = flex.double()
    re_frame = flex.double()
    uc_a_frame = flex.double()
    uc_b_frame = flex.double()
    uc_c_frame = flex.double()
    uc_alpha_frame = flex.double()
    uc_beta_frame = flex.double()
    uc_gamma_frame = flex.double()
    SE_all = flex.double()
    R_sq_all = flex.double()
    cc_all = flex.double()
    sum_var_I_p_all = flex.double()
    sum_var_k_all = flex.double()
    sum_var_p_all = flex.double()
    SE_I_all = flex.double()

    for pres in results:
      if pres is not None:
        if (abs(pres.uc_params[0]-iph.target_unit_cell[0]) <= uc_len_tol and abs(pres.uc_params[1]-iph.target_unit_cell[1]) <= uc_len_tol \
        and abs(pres.uc_params[2]-iph.target_unit_cell[2]) <= uc_len_tol and abs(pres.uc_params[3]-iph.target_unit_cell[3]) <= uc_angle_tol \
        and abs(pres.uc_params[4]-iph.target_unit_cell[4]) <= uc_angle_tol and abs(pres.uc_params[5]-iph.target_unit_cell[5]) <= uc_angle_tol):
          G_frame.append(pres.G)
          B_frame.append(pres.B)
          rotx_frame.append(pres.rotx*180/math.pi)
          roty_frame.append(pres.roty*180/math.pi)
          ry_frame.append(pres.ry)
          rz_frame.append(pres.rz)
          re_frame.append(pres.re)
          uc_a_frame.append(pres.uc_params[0])
          uc_b_frame.append(pres.uc_params[1])
          uc_c_frame.append(pres.uc_params[2])
          uc_alpha_frame.append(pres.uc_params[3])
          uc_beta_frame.append(pres.uc_params[4])
          uc_gamma_frame.append(pres.uc_params[5])
          SE_all.append(pres.stats[0])
          R_sq_all.append(pres.stats[1])
          cc_all.append(pres.stats[2])
          sum_var_I_p_all.append(np.median(pres.var_I_p))
          sum_var_k_all.append(np.median(pres.var_k))
          sum_var_p_all.append(np.median(pres.var_p))

          for se_i in pres.SE_I:
            SE_I_all.append(se_i)


    if iph.flag_plot:
      plt.subplot(231)
      x = SE_all.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('SE distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(232)
      x = cc_all.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('CC distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(233)
      x = SE_I_all.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('SE I all observations distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(234)
      x = sum_var_I_p_all.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('SE I distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(235)
      x = sum_var_k_all.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('SE G distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(236)
      x = sum_var_p_all.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('SE p distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.show()


      plt.subplot(241)
      x = G_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('G distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(242)
      x = B_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('B distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(243)
      x = rotx_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('Delta rot_x distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(244)
      x = roty_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('Delta rot_y distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(245)
      x = ry_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('ry distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(246)
      x = rz_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('rz distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(247)
      x = re_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('re distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.show()

      plt.subplot(231)
      x = uc_a_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('a distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(232)
      x = uc_b_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('b distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(233)
      x = uc_c_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('c distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(234)
      x = uc_alpha_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('alpha distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(235)
      x = uc_beta_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('beta distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))

      plt.subplot(236)
      x = uc_gamma_frame.as_numpy_array()
      mu = np.mean(x)
      med = np.median(x)
      sigma = np.std(x)
      num_bins = 10
      n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.ylabel('Frequencies')
      plt.title('gamma distribution\nmean %5.3f median %5.3f sigma %5.3f' %(mu, med, sigma))
      plt.show()

class input_handler(object):
  '''
  handle reading txt file
  '''

  def __init__(self):
    '''
    Constructor
    '''

  def read_input(self, file_name_input):

    self.run_no = ''
    self.title = ''
    self.d_min = 0
    self.d_max = 99
    self.sigma_max = 1.5
    self.sigma_max_merge=1.5
    self.target_unit_cell = ''
    self.target_space_group = ''
    self.target_pointgroup = ''
    self.target_anomalous_flag = False
    self.flag_polar = False
    self.index_basis_in = ''
    self.file_name_iso_mtz = ''
    self.file_name_ref_mtz = ''
    self.file_name_in_energy = ''
    self.file_name_in_img = ''
    self.n_postref_cycle = 1
    self.miller_array_iso = None
    self.flag_plot = False
    self.n_bins=25
    self.pixel_size_mm = 0
    self.frame_accept_min_cc = 0.25
    self.flag_force_accept_all_frames = True
    self.uc_len_tol = 3.5
    self.uc_angle_tol = 3.5
    self.flag_force_no_postrefine = False
    self.d_min_partiality = 1.5

    file_input = open(file_name_input, 'r')
    data_input = file_input.read().split('\n')

    for line_input in data_input:
      pair=line_input.split('=')
      if len(pair) == 2:
        param_name = pair[0].strip()
        param_val = pair[1].strip()
        if param_name=='run_no':
          self.run_no=param_val
        elif param_name=='title':
          self.title=param_val
        elif param_name=='d_min':
          self.d_min=float(param_val)
        elif param_name=='d_max':
          self.d_max=float(param_val)
        elif param_name=='sigma_max':
          self.sigma_max=float(param_val)
        elif param_name=='sigma_max_merge':
          self.sigma_max_merge=float(param_val)
        elif param_name=='target_unit_cell':
          tmp_uc = param_val.split(',')
          if len(tmp_uc) != 6:
            print 'Parameter: target_unit_cell has wrong format (usage: target_unit_cell= a,b,c,alpha,beta,gamma)'
            exit()
          else:
            self.target_unit_cell = (float(tmp_uc[0]), float(tmp_uc[1]), float(tmp_uc[2]), \
              float(tmp_uc[3]), float(tmp_uc[4]), float(tmp_uc[5]))
        elif param_name=='target_space_group':
          self.target_space_group=param_val
        elif param_name=='target_anomalous_flag':
          if param_val=='True':
            self.target_anomalous_flag=True
        elif param_name=='target_pointgroup':
          tmp_pg = param_val.split(' ')
          if len(tmp_pg) > 1:
            self.target_pointgroup = tmp_pg[0]+''+tmp_pg[1]
          else:
            self.target_pointgroup = param_val
        elif param_name=='flag_polar':
          if param_val=='True':
            self.flag_polar=True
        elif param_name=='index_basis_in':
          self.index_basis_in=param_val
        elif param_name=='hklisoin':
          self.file_name_iso_mtz=param_val
        elif param_name=='hklrefin':
          self.file_name_ref_mtz=param_val
        elif param_name=='energyin':
          self.file_name_in_energy=param_val
        elif param_name=='imagein':
          self.file_name_in_img=param_val
        elif param_name=='n_postref_cycle':
          self.n_postref_cycle=int(param_val)
        elif param_name=='flag_plot':
          if param_val=='True':
            self.flag_plot=True
        elif param_name=='n_bins':
          self.n_bins=int(param_val)
        elif param_name=='pixel_size_mm':
          self.pixel_size_mm=float(param_val)
        elif param_name=='frame_accept_min_cc':
          self.frame_accept_min_cc=float(param_val)
        elif param_name=='flag_force_accept_all_frames':
          if param_val=='False':
            self.flag_force_accept_all_frames=False
        elif param_name.lower()=='logging_level':
          if param_val.lower()=='critical':
            logging.getLogger().setLevel(logging.CRITICAL)
          elif param_val.lower()=='info':
            logging.getLogger().setLevel(logging.INFO)
          elif param_val.lower()=='debug':
            logging.getLogger().setLevel(logging.DEBUG)
        elif param_name=='uc_len_tol':
          self.uc_len_tol=float(param_val)
        elif param_name=='uc_angle_tol':
          self.uc_angle_tol=float(param_val)
        elif param_name=='flag_force_no_postrefine':
          if param_val=='True':
            self.flag_force_accept_all_frames=True



    if self.target_space_group == '':
      print 'Parameter: target_space_group - please specify space_group (usage: target_space_group=SGSYMBOL)'
      exit()

    if self.flag_polar and self.index_basis_in =='':
      print 'Conflict of parameters: you turned flag_polar on, please also input indexing basis (usage: index_basis_in=reverse_lookup.pickle)'
      exit()

    if self.pixel_size_mm == 0:
      print 'pixel size (in mm) is required (usage: pixel_size_mm = 0.079346 for MAR or = 0.11 for CSPAD)'
      exit()

    #fetch isomorphous structure
    if self.file_name_iso_mtz != '':
      reflection_file_iso = reflection_file_reader.any_reflection_file(self.file_name_iso_mtz)
      miller_arrays_iso=reflection_file_iso.as_miller_arrays()
      is_found_iso_as_intensity_array = False
      is_found_iso_as_amplitude_array = False
      for miller_array_iso in miller_arrays_iso:
        if miller_array_iso.is_xray_intensity_array():
          self.miller_array_iso = miller_array_iso
          is_found_iso_as_intensity_array = True
          break
        elif miller_array_iso.is_xray_amplitude_array():
          is_found_iso_as_amplitude_array = True
          miller_array_iso_converted_to_intensity = miller_array_iso.as_intensity_array()
      if is_found_iso_as_intensity_array == False:
        if is_found_iso_as_amplitude_array:
          print 'Found amplitude array, convert it to intensity array'
          self.miller_array_iso = miller_array_iso_converted_to_intensity
        else:
          print 'Cannot find intensity array in the isomorphous-reference mtz'
          exit()

      self.miller_array_iso = self.miller_array_iso.expand_to_p1().generate_bijvoet_mates()


    self.txt_out = ''
    self.txt_out += 'Input parameters\n'
    self.txt_out += 'run_no '+str(self.run_no)+'\n'
    self.txt_out += 'title '+str(self.title)+'\n'
    self.txt_out += 'd_min '+str(self.d_min)+'\n'
    self.txt_out += 'd_max '+str(self.d_max)+'\n'
    self.txt_out += 'sigma_max '+str(self.sigma_max)+'\n'
    self.txt_out += 'sigma_max_merge '+str(self.sigma_max_merge)+'\n'
    self.txt_out += 'target_unit_cell '+str(self.target_unit_cell)+'\n'
    self.txt_out += 'target_space_group '+str(self.target_space_group)+'\n'
    self.txt_out += 'target_anomalous_flag '+str(self.target_anomalous_flag)+'\n'
    self.txt_out += 'flag_polar '+str(self.flag_polar)+'\n'
    self.txt_out += 'index_basis_in '+str(self.index_basis_in)+'\n'
    self.txt_out += 'hklisoin '+str(self.file_name_iso_mtz)+'\n'
    self.txt_out += 'hklrefin '+str(self.file_name_ref_mtz)+'\n'
    self.txt_out += 'energyin '+str(self.file_name_in_energy)+'\n'
    self.txt_out += 'imagein '+str(self.file_name_in_img)+'\n'
    self.txt_out += 'flag_plot '+str(self.flag_plot)+'\n'
    self.txt_out += 'n_bins '+str(self.n_bins)+'\n'
    self.txt_out += 'pixel_size_mm '+str(self.pixel_size_mm)+'\n'
    self.txt_out += 'frame_accept_min_cc '+str(self.frame_accept_min_cc)+'\n'
    self.txt_out += 'flag_force_accept_all_frames '+str(self.flag_force_accept_all_frames)+'\n'
    self.txt_out += 'uc_len_tol '+str(self.uc_len_tol)+'\n'
    self.txt_out += 'uc_angle_tol '+str(self.uc_angle_tol)+'\n'
    self.txt_out += 'flag_force_no_postrefine '+str(self.flag_force_no_postrefine)+'\n'

    print self.txt_out

class file_handler(object):
  '''
  handle reading txt file
  '''

  def __init__(self):
    '''
    Constructor
    '''

  def get_imgname_from_pickle_filename(self, file_name_in_img, pickle_filename):

    img_filename = pickle_filename

    if file_name_in_img == '':
      return img_filename

    file_img = open(file_name_in_img, 'r')
    data_img = file_img.read().split('\n')
    for line_img in data_img:
      data_img = line_img.split(' ')
      if pickle_filename.find(data_img[0]) > 0:
        img_filename = data_img[1]
        break

    return img_filename



class basis_handler(object):
  '''
  classdocs
  '''

  def __init__(self):
    '''
    Constructor
    '''

  def calc_direct_space_matrix(self, my_unit_cell, rotation_matrix):

    #calculate the conversion matrix (from fractional to cartesian coordinates
    frac2cart_matrix = my_unit_cell.orthogonalization_matrix()
    frac2cart_matrix = sqr(frac2cart_matrix)

    #calculate direct_space matrix
    direct_space_matrix = frac2cart_matrix.transpose()*rotation_matrix

    return direct_space_matrix


class svd_handler(object):
  '''
  Singular value decomposion
  Solve linear equations with best fit basis
  '''


  # Input: expects Nx3 matrix of points
  # Returns R,t
  # R = 3x3 rotation matrix
  # t = 3x1 column vector

  def __init__(self):
    '''
    Constructor
    '''

  def rigid_transform_3D(self, A, B):

      assert len(A) == len(B)

      N = A.shape[0]; # total points

      centroid_A = np.mean(A, axis=0)
      centroid_B = np.mean(B, axis=0)

      # centre the points
      AA = A - np.tile(centroid_A, (N, 1))
      BB = B - np.tile(centroid_B, (N, 1))

      # dot is matrix multiplication for array
      H = np.transpose(AA) * BB

      U, S, Vt = np.linalg.svd(H)

      R = Vt.T * U.T

      # special reflection case
      if np.linalg.det(R) < 0:
         #print "Reflection detected"
         Vt[2,:] *= -1
         R = Vt.T * U.T

      t = -R*centroid_A.T + centroid_B.T


      return R, t
