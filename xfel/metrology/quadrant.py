from __future__ import division
from scitbx.matrix import sqr,col
from math import sin,cos,pi
from scitbx.array_family import flex
class one_sensor(object):
  def __init__(self,image,sensor,manager):
    self.image = image
    self.sensor = sensor
    self.manager = manager
    self.tiling = self.manager.effective_tiling_as_flex_int(
                    encode_inactive_as_zeroes=True)

    print list( self.tiling[4*self.sensor[0]:4+4*self.sensor[0]] )



    grid_radius = 20
    mapp = flex.double(flex.grid(2*grid_radius+1, 2*grid_radius+1))
    print mapp.focus()

    # not sure if this is the correct beam center; take provisional value
    beam_center = col((float(880.5),float(880.5)))
    gmax = 0.0
    coordmax = (0,0)
    for xi in range(-grid_radius, grid_radius+1):
      for yi in range(-grid_radius, grid_radius+1):
        VV = self.CC(beam_center + col((xi,yi)))
        if VV>gmax:
          gmax = VV
          coordmax = col((xi,yi))
        mapp[(xi+grid_radius,yi+grid_radius)]=VV

    print "max cc %7.4F is at "%gmax,
    if False:
      npy = mapp.as_numpy_array()
      from matplotlib import pyplot as plt
      plt.imshow(npy, cmap="hot")
      plt.plot([coordmax[1]+grid_radius],[coordmax[0]+grid_radius],"k.")
      plt.show()

    self.coordmax = coordmax

  def CC(self, beam_center):
    quad = self.tiling[4*self.sensor[0]:4+4*self.sensor[0]]

    asic = self.image.linearintdata.matrix_copy_block(quad[0],quad[1],
                                    quad[2]-quad[0],quad[3]-quad[1])

    #npy = asic.as_numpy_array()
    #from matplotlib import pyplot as plt
    #plt.imshow(npy, cmap="hot")
    #plt.show()

    asci_origin = col((float(quad[0]),float(quad[1])))

    rot45 = sqr((sin(pi/4.),-cos(pi/4.),cos(pi/4.),sin(pi/4.)))

    from xfel.metrology.legacy_scale import quadrant_self_correlation
    REF,ROT = quadrant_self_correlation(asic,asci_origin,beam_center,rot45)
    CCRR = flex.linear_correlation(REF,ROT)

    """initial python implementation
    #rot_asic = flex.double(asic.accessor())
    F0,F1 = asic.focus()

    ref_data = flex.double()
    rot_data = flex.double()
    constant = rot45*(asci_origin - beam_center) +beam_center - asci_origin
    for xcoord in xrange(quad[2]-quad[0]):
      for ycoord in xrange(quad[3]-quad[1]):

        acoord = col((float(xcoord),float(ycoord)))
        #prime = rot45*(acoord + asci_origin - beam_center) + beam_center - asci_origin
        prime = rot45*acoord + constant
        prime = (int(round(prime[0],0)),int(round(prime[1],0)))
        if 0<=prime[0]<F0 and 0<=prime[1]<F1:
          #rot_asic[(xcoord,ycoord)]=asic[prime]

          ref_data.append(asic[(xcoord,ycoord)])
          rot_data.append(asic[prime])
    CC = flex.linear_correlation(ref_data,rot_data)

    print "Correlation_coefficient %7.4f %7.4f"%(CC.coefficient(),CCRR.coefficient())
    """

    return CCRR.coefficient()

    #npy = rot_asic.as_numpy_array()
    #from matplotlib import pyplot as plt
    #plt.imshow(npy,cmap="hot")
    #plt.show()
