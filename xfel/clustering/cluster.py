from __future__ import division
import os
import math
import logging
from xfel.clustering.singleframe import SingleFrame
from cctbx.uctbx.determine_unit_cell import NCDist
import numpy as np
import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt

""" This package is designed to provide tools to deal with clusters of
singleframe objects. The class Cluster allows the creation, storage and
manipulation of these sets of frames. Methods exist to create sub-clusters (new
cluster objects) or to act on an existing cluster, e.g. to plot the unit cell
distributions.
"""
__author__ = 'zeldin'


class Cluster:
  """Groups single XFEL images (here described by SingleImage objects) as
  cluster objects. You can create a cluster object directly, by using the
  __init__ method, which takes in a list of SingleImage objects, and some
  string-info, or by using a classmethod e.g. to create an object from a folder
  full of integration pickles. SingleImage objects have most of the stuff from
  an integration pickle, but can also have methods to calculate things relating
  to one image at a time. Whenever a method can plot, there is the option of
  passing it an appropriate number of matplotlib axes objects, which will then
  get returned for use in composite plots. See cluster.42 for an example.
  If no axes are passed, the methods will just plot the result to the screen.
  Clustering filters can act on these to break them up into cluster objects with
  different members. A 'filter' is just a clustering procedure that puts the
  passes and fails into different clusters. This is acheived through the
  make_sub_cluster() method. This also keeps track of a sub-clusters heritage
  through the .info string, which is appended to. The idea is to be able to
  write filter scripts for each data. e.g:

    test_cluster = Cluster.from_directories(["~/test_data"],
                                          'test_script')
    P3_only = test_cluster.point_group_filer('P3')
    sub_clusters = P3_only.ab_cluster(1200)
    big_cluster = max(sub_clusters, key=lambda x: len(x.members))
    best_data = big_cluster.total_intensity_filter(res=6.5,
                                                   completeness_threshold=0.1,
                                                   plot=False)
    print best_data.info

  cxi.postrefine (or any other merging thing) will be able to be called on the
  ouput of a cluster object method (ToDo)
  """

  def __init__(self, data, cname, info):
    """
    Contains a list of SingFrame objects, as well as information about these
    as a cluster (e.g. mean unit cell).

    :param:data: a list of SingleFrame objects
    :param:cname: the name of the cluster, as a string.
    :param:info: an info-string for the cluster.
    :return: a Cluster object
    """

    self.cname = cname
    self.members = data
    self.info = info

    # Calculate medians and stdevs
    unit_cells = np.zeros([len(self.members), 6])
    self.pg_composition = {}
    for i, member in enumerate(self.members):
      unit_cells[i, :] = member.uc
      # Calculate point group composition
      if member.pg in self.pg_composition.keys():
        self.pg_composition[member.pg] += 1
      else:
        self.pg_composition[member.pg] = 1

    self.medians = np.median(unit_cells, 0).tolist()
    self.stdevs = np.std(unit_cells, 0).tolist()
    #ToDo
    self.res = None

  @classmethod
  def from_directories(cls, path_to_integration_dir,
                       _prefix='cluster_from_dir',
                       use_b=True):
    """Constructor to get a cluster from pickle files, from the recursively
    walked paths. Can take more than one argument for multiple folders.
    usage: Cluster.from_directories(..)
    :param:path_to_integration_dir: list of directories containing pickle files.
    Will be searched recursively.
    :param:use_b: Boolean. If True, intialise Scale and B. If false, use only
    mean intensity scalling.
    """
    data = []
    for arg in path_to_integration_dir:
      for (dirpath, dirnames, filenames) in os.walk(arg):
        for filename in filenames:
          path = os.path.join(dirpath, filename)
          this_frame = SingleFrame(path, filename, use_b_factor=use_b)
          if hasattr(this_frame, 'name'):
            data.append(this_frame)
          else:
            logging.info('skipping file {}'.format(filename))
    return cls(data, _prefix,
               'Made from files in {}'.format(path_to_integration_dir[:]))

  @classmethod
  def from_files(cls, pickle_list,
                       _prefix='cluster_from_file',
                       use_b=True):
    """Constructor to get a cluster from a list of pickle files.
    :param:pickle_list: list of pickle files
    :param:use_b: Boolean. If True, intialise Scale and B. If false, use only
    mean intensity scalling.
    """
    data = []
    for filename in pickle_list:
      name_only = filename.split('/')[-1]
      this_frame = SingleFrame(filename, name_only, use_b_factor=use_b)
      if hasattr(this_frame, 'name'):
        data.append(this_frame)
      else:
        logging.info('skipping file {}'.format(filename))
    return cls(data, _prefix, 'Made by Cluster.from_files')

  def make_sub_cluster(self, new_members, new_prefix, new_info):
    """ Make a sub-cluster from a list of SingleFrame objects from the old
    SingleFrame array.
    """
    return Cluster(new_members, new_prefix,
                   ('{}\n{} Next filter {}\n{}\n{} of {} images passed'
                    'on to this cluster').format(
                     self.info, '#' * 30, '#' * 30, new_info,
                     len(new_members), len(self.members)))

  def print_ucs(self):
    """ Prints a list of all the unit cells in the cluster to CSV."""
    outfile = "{}_niggli_ucs".format(self.cname)
    out_str = ["File name, Point group, a, b, c, alpha, beta, gamma"]
    for image in self.members:
      out_str.append("{}, {}, {}, {}, {}, {}, {}, {}".format(
        image.name, image.pg,
        image.uc[0], image.uc[1],
        image.uc[2], image.uc[3],
        image.uc[4], image.uc[5]))
    with open("{}.csv".format(outfile), 'w') as _outfile:
      _outfile.write("\n".join(out_str))

  def point_group_filter(self, point_group):
    """ Return all the SingleFrames that have a given pointgroup. """
    new_prefix = '{}_only'.format(point_group)
    new_info = 'Cluster filtered by for point group {}.'.format(point_group)
    return self.make_sub_cluster([image
                                  for image
                                  in self.members
                                  if image.pg == point_group],
                                 new_prefix,
                                 new_info)

  def total_intensity_filter(self, res='',
                             completeness_threshold=0.95,
                             plot=False):
    """ Creates a sub-cluster using the highest total intensity images that
          yield a dataset specified by:
          res -- desired resolution. Defaults to that of the dataset.
          completeness -- the desired completeness of the subset
          multiplicity -- the desired multiplicity of the subset
    """
    logging.info(("Performing intensity filtering, aiming for {}% overall "
                  "completenes at {} A resolution").format(
      completeness_threshold * 100, res))

    # 0. Check that the cluster has consistent point_group (completness doesn't
    #  mean much otherwise...
    assert all(i.pg == self.members[0].pg for i in self.members)

    # 1. Sort SingleFrames by total intensity
    sorted_cluster = sorted(self.members, key=lambda y: -1 * y.total_i)

    if plot:
      plt.plot([x.total_i for x in sorted_cluster])
      plt.show()

    if res == '':
      res = sorted_cluster[0].d_min()  # Use the high-res limit from the
      # brightest image. ToDo: make this better
      logging.warning(("no resolution limit specified, using the res limit of"
                       "the top-rankeed image: {} A").format(res))

    # 2. Incrementally merge frames until criterion are matched

    temp_miller_indicies = sorted_cluster[0].miller_array
    for idx, image in enumerate((x.miller_array for x in sorted_cluster[1:])):
      temp_miller_indicies = temp_miller_indicies. \
        concatenate(image, assert_is_similar_symmetry=False)
      current_completeness = temp_miller_indicies.merge_equivalents() \
                                                .array() \
                                                .completeness()
      logging.debug(
        "{} images: {:.2f}% complete".format(idx, current_completeness * 100))
      if current_completeness <= completeness_threshold:
        temp_miller_indicies.concatenate(image,
                                         assert_is_similar_symmetry=False)
        if idx + 1 == len(sorted_cluster[1:]):
          logging.warning("Desired completeness could not be acheived, sorry.")
          file_threshold = idx
          break
      else:
        file_threshold = idx
        break

    return self.make_sub_cluster(sorted_cluster[:file_threshold],
                                 'I_threshold_d{}_{}comp'.format(res,
                                                        completeness_threshold),
                                 ("Subset cluster made using "
                                  "total_intensity_filter() with"
                                  "\nRes={}\ncompleteness_threshold={}").format(
                                   res,
                                   completeness_threshold))


  def ab_cluster(self, threshold=10000, method='distance',
                 linkage_method='single', log=False, ax=None):
    """ Do hierarchical clustering using the Andrews-Berstein distance from
    Andrews & Bernstein J Appl Cryst 47:346 (2014) on the Niggli cells. Returns
    the largest cluster if max_only is true, otherwise a list of clusters. Also
    return a matplotlib axes object for display of a dendogram.
    :return: A list of Clusters ordered by largest Cluster to smallest
    """

    logging.info("Hierarchical clustering of unit cells using Andrews-Bernstein"
                 "Distance from Andrews & Bernstein J Appl Cryst 47:346 (2014)")
    import scipy.spatial.distance as dist
    import scipy.cluster.hierarchy as hcluster

    # 1. Create a numpy array of G6 cells
    g6_cells = np.array([SingleFrame.make_g6(image.uc)
                         for image in self.members])

    # 2. Do hierarchichal clustering, using the find_distance method above.
    pair_distances = dist.pdist(g6_cells,
                                metric=lambda a, b: NCDist(a, b))
    logging.debug("Distances have been calculated")
    this_linkage = hcluster.linkage(pair_distances,
                                    method=linkage_method,
                                    metric=lambda a, b: NCDist(a, b))
    cluster_ids = hcluster.fcluster(this_linkage,
                                    threshold,
                                    criterion=method)
    logging.debug("Clusters have been calculated")

    # 3. Create an array of sub-cluster objects from the clustering
    sub_clusters = []
    for cluster in range(max(cluster_ids)):
      info_string = ('Made using ab_cluster with t={},'
                     ' {} method, and {} linkage').format(threshold,
                                                          method,
                                                          linkage_method)
      sub_clusters.append(self.make_sub_cluster([self.members[i]
                                                 for i in
                                                 range(len(self.members))
                                                 if
                                                 cluster_ids[i] == cluster + 1],
                                                'cluster_{}'.format(
                                                  cluster + 1),
                                                info_string))

      sub_clusters = sorted(sub_clusters, key=lambda x: len(x.members))

    # 4. Plot a dendogram to the axes if no axis is passed, otherwise just
    #    return the axes object
    if ax is None:
      fig = plt.figure("Distance Dendogram")
      ax = fig.gca()
      direct_visualisation = True
    else:
      direct_visualisation = False

    hcluster.dendrogram(this_linkage,
                        labels=[image.name for image in self.members],
                        leaf_font_size=8, leaf_rotation=90.0,
                        color_threshold=threshold, ax=ax)
    if log:
      ax.set_yscale("log")
    else:
      ax.set_ylim(-ax.get_ylim()[1] / 100, ax.get_ylim()[1])

    if direct_visualisation:
      fig.savefig("{}_dendogram.pdf".format(self.cname))
      plt.show()

    return sub_clusters, ax

  def dump_file_list(self, out_file_name=None):
    """ Simply dumps a list of paths to inegration pickle files to a file. One
    line per image
    """
    if out_file_name is None:
      out_file_name = self.cname

    with open("{}.members".format(out_file_name), 'wb') as outfile:
      for i in self.members:
        outfile.write(i.path + "\n")

  def visualise_orientational_distribution(self, axes_to_return=None,
                                           cbar=True):

    """ Creates a plot of the orientational distribution of the unit cells. Will
    plot if given no axes, otherwise, requires 3 axes objects, and will return
    them.
    """
    from mpl_toolkits.basemap import Basemap
    import scipy.ndimage as ndi
    from cctbx.array_family import flex

    def cart2sph(x, y, z):
      # cctbx (+z to source, y to ceiling) to
      # lab frame (+x to source, z to ceiling)
      z, x, y = x, y, z
      dxy = np.sqrt(x ** 2 + y ** 2)
      r = np.sqrt(dxy ** 2 + z ** 2)
      theta = np.arctan2(y, x)
      phi = np.arctan2(z, dxy)  # angle of the z axis relative to xy plane
      theta, phi = np.rad2deg([theta, phi])
      return theta % 360, phi, r

    def xy_lat_lon_from_orientation(orientation_array, axis_id):
      logging.debug("axis_id: {}".format(axis_id))
      dist = math.sqrt(orientation_array[axis_id][0] ** 2 +
                       orientation_array[axis_id][1] ** 2 +
                       orientation_array[axis_id][2] ** 2)
      flon, flat, bla = cart2sph(orientation_array[axis_id][0] / dist,
                                 orientation_array[axis_id][1] / dist,
                                 orientation_array[axis_id][2] / dist)
      x, y = euler_map(flon, flat)
      return x, y, flon, flat

    orientations = [flex.vec3_double(flex.double(
      image.orientation.direct_matrix()))
      for image in self.members]

    space_groups = [image.orientation.unit_cell().lattice_symmetry_group()
                    for image in self.members]

    # Now do all the plotting
    if axes_to_return is None:
      plt.figure(figsize=(10, 14))
      axes_to_return = [plt.subplot2grid((3, 1), (0, 0)),
                        plt.subplot2grid((3, 1), (1, 0)),
                        plt.subplot2grid((3, 1), (2, 0))]
      show_image = True
    else:
      assert len(axes_to_return) == 3, "If using axes option, must hand" \
                                       " 3 axes to function."
      show_image = False

    axis_ids = [0, 1, 2]
    labels = ["a",
              "b",
              "c"]

    for ax, axis_id, label in zip(axes_to_return, axis_ids, labels):

      # Lists of x,y,lat,long for the master orientation, and for all
      # symmetry mates.
      x_coords = []
      y_coords = []
      lon = []
      lat = []
      sym_x_coords = []
      sym_y_coords = []
      sym_lon = []
      sym_lat = []
      euler_map = Basemap(projection='eck4', lon_0=0, ax=ax)

      for orientation, point_group_type in zip(orientations, space_groups):

        # Get position of main spots.
        main_x, main_y, main_lon, main_lat \
          = xy_lat_lon_from_orientation(list(orientation), axis_id)
        x_coords.append(main_x)
        y_coords.append(main_y)
        lon.append(main_lon)
        lat.append(main_lat)

        # Get position of symetry mates
        symmetry_operations = list(point_group_type.smx())[1:]
        for mx in symmetry_operations:
          rotated_orientation = list(mx.r().as_double() * orientation)
          sym_x, sym_y, sym_lo, sym_la \
            = xy_lat_lon_from_orientation(rotated_orientation, axis_id)
          #assert (sym_x, sym_y) != (main_x, main_y)
          sym_x_coords.append(sym_x)
          sym_y_coords.append(sym_y)
          sym_lon.append(sym_lo)
          sym_lat.append(sym_la)

      # Plot each image as a yellow sphere
      logging.debug(len(x_coords))
      euler_map.plot(x_coords, y_coords, 'oy',
                     markersize=4,
                     markeredgewidth=0.5)

      # Plot the symetry mates as black crosses
      #euler_map.plot(sym_x_coords, sym_y_coords, 'kx')

      # Use a histogram to bin the data in lattitude/longitude space, smooth it,
      # then plot this as a contourmap. This is for all the symetry-related
      # copies
      density_hist = np.histogram2d(lat + sym_lat, lon + sym_lon,
                                    bins=[range(-90, 91), range(0, 361)])
      smoothed = ndi.gaussian_filter(density_hist[0], (15, 15), mode='wrap')
      local_intensity = []
      x_for_plot = []
      y_for_plot = []
      for _lat in range(0, 180):
        for _lon in range(0, 360):
          _x, _y = euler_map(density_hist[2][_lon], density_hist[1][_lat])
          x_for_plot.append(_x)
          y_for_plot.append(_y)
          local_intensity.append(smoothed[_lat, _lon])
      cs = euler_map.contourf(np.array(x_for_plot),
                              np.array(y_for_plot),
                              np.array(local_intensity), tri=True)

      #  Pretty up graph
      if cbar:
        _cbar = plt.colorbar(cs, ax=ax)
        _cbar.ax.set_ylabel('spot density [AU]')
      middle = euler_map(0, 0)
      path_effect = [patheffects.withStroke(linewidth=3, foreground="w")]
      euler_map.plot(middle[0], middle[1], 'o', markersize=10, mfc='none')
      euler_map.plot(middle[0], middle[1], 'x', markersize=8)
      ax.annotate("beam", xy=(0.52, 0.52), xycoords='axes fraction',
                  size='medium', path_effects=path_effect)
      euler_map.drawmeridians(np.arange(0, 360, 60),
                              labels=[0, 0, 1, 0],
                              fontsize=10)
      euler_map.drawparallels(np.arange(-90, 90, 30),
                              labels=[1, 0, 0, 0],
                              fontsize=10)
      ax.annotate(label, xy=(-0.05, 0.9), xycoords='axes fraction',
                  size='x-large', weight='demi')

    if show_image:
      plt.show()

    return axes_to_return


  def intensity_statistics(self, ax=None):
    """
    Uses the per-frame B and G fits (gradient and intercept of the ln(i) vs
    (sin(theta)/lambda)**2 plot) to create three agregate plots:
    1) histogram of standard errors on the per-frame fits
    2) histogram of B factors
    3) scatter  plot of intercept vs. gradient (G vs. B)
    :param:ax: optionally hand the method three matplotlib axes objects to plot
    onto. If not specified, will plot the data.
    :return: the three axes, with the data plotted onto them.
    """
    if ax is None:
      plt.figure(figsize=(10, 14))
      axes_to_return = [plt.subplot2grid((3, 1), (0, 0)),
                        plt.subplot2grid((3, 1), (1, 0)),
                        plt.subplot2grid((3, 1), (2, 0))]
      show_image = True
    else:
      assert len(ax) == 3, "If using axes option, must hand" \
                                       " 3 axes to function."
      axes_to_return = ax
      show_image = False

    errors = [i.wilson_err['Standard Error'] for i in self.members]
    axes_to_return[0].hist(errors, 50, range=[0, 200])
    axes_to_return[0].set_title("Distribution of Standard Errors on the Wilson fit")

    rs = [-1 * i.minus_2B / 2 for i in self.members]
    axes_to_return[1].hist(rs, 50, range=[-50, 200])
    axes_to_return[1].set_title("Distribution of B values for the Wilson plot")

    axes_to_return[2].plot([i.G for i in self.members],
             [-1 * i.minus_2B / 2 for i in self.members], 'x')
    axes_to_return[2].set_xlabel("G")
    axes_to_return[2].set_ylabel("B")
    axes_to_return[2].set_title("G and B for all members")

    plt.tight_layout()

    if show_image:
      plt.show()

    return axes_to_return

  def all_frames_intensity_stats(self, ax=None, smoothing_width=2000):
    """
    Goes through all frames in the cluster, and plots all the partial intensites.
    Then does a linear fit through these, and  rolling average/
    :param:smoothing_width: the width of the smoothing window. Default 2000
    reflections.
    :param:ax: Optional matplotlib axes object to plot to.
    :return: the axis, with the data plotted onto it.
    """
    from scipy.stats import linregress
    from xfel.clustering.singleframe import SingleFrame as Sf

    if ax is None:
      fig = plt.figure("All images intensity statistics")
      ax = fig.gca()
      direct_visualisation = True
    else:
      direct_visualisation = False


    all_logi = []
    all_one_over_d_squared = []

    for frame in self.members:
      all_logi.append(frame.log_i)
      all_one_over_d_squared.append(frame.sinsqtheta_over_lambda_sq)

    all_logi = np.concatenate(all_logi)
    all_one_over_d_squared = np.concatenate(all_one_over_d_squared)

    plotting_data = sorted(zip(all_logi, all_one_over_d_squared),
                           key = lambda x: x[1])

    log_i, one_over_d_square = zip(*[i for i in plotting_data
                                     if i[0] >=0])
    minus_2B, G, r_val, _, std_err = linregress(one_over_d_square, log_i)
    fit_info = "G: {}, -2B: {}, r: {}, std_err: {}".format(G, minus_2B,
                                                            r_val, std_err)

    smooth = Sf._moving_average(log_i, n=smoothing_width)
    ax.plot(one_over_d_square, log_i, 'bo', ms=1)
    ax.plot(one_over_d_square[smoothing_width - 1:], smooth,'--r', lw=2)
    plt.xlim([0, max(one_over_d_square)])
    ax.plot([0, -1 * G / minus_2B], [G, 0], 'y-', lw=2)
    plt.xlabel("(sin(theta)/lambda)^2")
    plt.ylabel("ln(I)")
    plt.title("Simple Wilson fit\n{}".format(fit_info))
    plt.tight_layout()

    if direct_visualisation:
      fig.savefig("{}_dendogram.pdf".format(self.cname))
      plt.show()

    return ax
