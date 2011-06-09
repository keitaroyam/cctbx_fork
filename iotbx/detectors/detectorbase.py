import copy
from iotbx.detectors import ReadADSC

class DetectorImageBase(object):
  def __init__(self,filename):
    self.filename=filename
    self.parameters=None
    self.linearintdata=None
    self.bin=1
    self.vendortype = "baseclass"
    self.beam_center_reference_frame = "instrument"#cf beam_center_convention.py
    self.beam_center_convention = None

  def copy_common_attributes_from_parent_instance(self, parentobject):
    self.filename = copy.copy(parentobject.filename)
    self.bin = copy.copy(parentobject.bin)
    self.vendortype = copy.copy(parentobject.vendortype)
    self.beam_center_reference_frame = copy.copy(parentobject.beam_center_reference_frame)
    self.beam_center_convention = copy.copy(parentobject.beam_center_convention)
    self.header = copy.copy(parentobject.header)
    self.headerlines = copy.copy(parentobject.headerlines)

  def setBin(self,bin): #software binning.
                        # the only bin values supported are 1 & 2
    if self.bin!=1 or bin!=2: return
    if self.size1%bin!=0: return
    self.parameters['SIZE1']=self.parameters['SIZE1']//bin
    self.parameters['SIZE2']=self.parameters['SIZE2']//bin
    if self.parameters.has_key('CCD_IMAGE_SATURATION'):
      self.parameters['CCD_IMAGE_SATURATION']=self.parameters['CCD_IMAGE_SATURATION']*bin*bin
    self.parameters['PIXEL_SIZE']=self.parameters['PIXEL_SIZE']*bin
    self.bin = bin
    self.bin_safe_set_data(self.linearintdata)

  def set_beam_center_convention(self,beam_center_convention):
    from iotbx.detectors.beam_center_convention import convert_beam_instrument_to_imageblock
    convert_beam_instrument_to_imageblock(self,beam_center_convention)

  def fileLength(self):
    self.readHeader()
    return self.dataoffset()+self.size1*self.size2*self.integerdepth()
    # dataoffset() and integerdepth() must be defined in derived class
    # pure supposition:
    #  size1 corresponds to number of rows.  Columns are slow.
    #  size2 corresponds to number of columns.  Rows are fast.

  def getEndian(self): pass
    # must be defined in derived class

  def endian_swap_required(self):
    data_is_big_endian = self.getEndian()
    import struct
    platform_is_big_endian = (
      struct.unpack('i',struct.pack('>i',3000))[0] == 3000
    )
    return data_is_big_endian != platform_is_big_endian

  def read(self):
    self.fileLength()
    self.bin_safe_set_data(
         ReadADSC(self.filename,self.dataoffset(),
         self.size1*self.bin,self.size2*self.bin,self.getEndian())
         )

  def bin_safe_set_data(self, new_data_array):
    #private interface for software binning 2 X 2.
    #  Any setting of linearintdata must be through this function
    #  self.bin==2: when data are read lazily, they must be binned
    #  new_data_array.bin2by2==True: the data have been binned
    if self.bin==2 and \
       new_data_array != None and\
       new_data_array.__dict__.get("bin2by2")!=True:
      from iotbx.detectors import Bin2_by_2
      self.linearintdata = Bin2_by_2(new_data_array)
      self.linearintdata.bin2by2 = True
    else:
      self.linearintdata = new_data_array

  data_types = dict( SIZE1=int, SIZE2=int, PIXEL_SIZE=float,
                     DISTANCE=float, TWOTHETA=float, OSC_RANGE=float,
                     OSC_START=float, PHI=float, WAVELENGTH=float,
                     BEAM_CENTER_X=float, BEAM_CENTER_Y=float,
                     CCD_IMAGE_SATURATION=int, DETECTOR_SN=str )

  def debug_write(self,fileout,mod_data=None):
    if not self.parameters.has_key("TWOTHETA"):
      self.parameters["TWOTHETA"]=0.0
    if self.getEndian()==1:
      self.parameters["BYTE_ORDER"]="big_endian"
    else:
      self.parameters["BYTE_ORDER"]="little_endian"
    info = """{
HEADER_BYTES= 1024;
DIM=2;
BYTE_ORDER=%(BYTE_ORDER)s;
TYPE=unsigned_short;
SIZE1=%(SIZE1)4d;
SIZE2=%(SIZE1)4d;
PIXEL_SIZE=%(PIXEL_SIZE)8.6f;
TIME=0.000000;
DISTANCE=%(DISTANCE).2f;
TWOTHETA=%(TWOTHETA).2f;
PHI=%(OSC_START).3f;
OSC_START=%(OSC_START).3f;
OSC_RANGE=%(OSC_RANGE).3f;
WAVELENGTH=%(WAVELENGTH).6f;
BEAM_CENTER_X=%(BEAM_CENTER_X).2f;
BEAM_CENTER_Y=%(BEAM_CENTER_Y).2f;
CCD_IMAGE_SATURATION=65535;
}\f"""%self.parameters
    F = open(fileout,"wb")
    F.write(info)
    len_null=1024-len(info)
    F.write('\0'*len_null)
    F.close()
    from iotbx.detectors import WriteADSC
    if mod_data==None: mod_data=self.linearintdata
    WriteADSC(fileout,mod_data,self.size1,self.size2,self.getEndian())

  def __getattr__(self, attr):
    if   attr=='size1' : return self.parameters['SIZE1']
    elif attr=='size2' : return self.parameters['SIZE2']
    elif attr=='npixels' : return self.parameters['SIZE1'] * self.parameters['SIZE2']
    elif attr=='saturation' : return self.parameters['CCD_IMAGE_SATURATION']
    elif attr=='rawdata' : return self.linearintdata
    elif attr=='pixel_size' : return self.parameters['PIXEL_SIZE']
    elif attr=='osc_start' : return self.parameters['OSC_START']
    elif attr=='distance' : return self.parameters['DISTANCE']
    elif attr=='wavelength' : return self.parameters['WAVELENGTH']
    elif attr=='beamx' : return self.parameters['BEAM_CENTER_X']
    elif attr=='beamy' : return self.parameters['BEAM_CENTER_Y']
    elif attr=='deltaphi' : return self.parameters['OSC_RANGE']
    elif attr=='twotheta' : return self.parameters['TWOTHETA']
    elif attr=='serial_number' : return self.parameters['DETECTOR_SN']

  def show_header(self):
    print "File:",self.filename
    print "Number of pixels: slow=%d fast=%d"%(self.size1,self.size2)
    print "Pixel size: %f mm"%self.pixel_size
    print "Saturation: %.0f"%self.saturation
    print "Detector distance: %.2f mm"%self.distance
    print "Detector 2theta swing: %.2f deg."%self.twotheta
    print "Rotation start: %.2f deg."%self.osc_start
    print "Rotation width: %.2f deg."%self.deltaphi
    print "Beam center x=%.2f mm  y=%.2f mm"%(self.beamx,self.beamy)
    print "Wavelength: %f Ang."%self.wavelength
