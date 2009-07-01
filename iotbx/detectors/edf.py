import struct
from scitbx.array_family import flex

def file_object_from_file_name(filename):
 return open(filename,"rb")

class EDFImage:
 def __init__(self,filename):
   self.obj = file_object_from_file_name(filename)
   self.headersize=0
   self.data_dimension=[0,0]
   self.parameters = {}
   self.header = []
   self.linearintdata = None

 def readHeader(self,external_keys=None):
   ptr = 0
   self.obj.seek(0)

   while True:
       newchr = self.obj.read(1)
       assert ord(newchr)!=0
       if ptr==1:  assert ord(self.header[0])==0x7b
       self.header.append(newchr)
       if newchr == "}": break
       ptr += 1

   assert self.obj.read(1) == "\n"
   self.headersize = 1 + len(self.header)
   assert self.headersize%512==0

   headertext = "".join(self.header[1:])
   headerpairs = headertext.split(";")

   for pair in headerpairs:
     bare = pair.strip()
     if bare.find("=")<0: continue
     key,value = bare.split("=")
     key,value = (key.strip(), value.strip())
     self.parameters[key]=value

   #forced typing of attributes:
   for attribute in ['run','Image','Size','Dim_1','Dim_2']:
     if self.parameters.has_key(attribute):
       self.parameters[attribute]=int(self.parameters[attribute])
   for attribute in ['count_time',]:
     if self.parameters.has_key(attribute):
       self.parameters[attribute]=float(self.parameters[attribute])

   self.type_size = {'SignedInteger':4}[self.parameters['DataType']]
   assert self.parameters['Size']==self.parameters['Dim_1']*self.parameters['Dim_2']*self.type_size

 def read(self):
   self.obj.seek(self.headersize)

   endian_code = {'LowByteFirst':'<','HighByteFirst':'>'}[self.parameters['ByteOrder']]
   type_code = {'SignedInteger':'i','UnsignedInteger':'I'}[self.parameters['DataType']]

   assert self.parameters['DataType'] == 'SignedInteger'
   # if it is unsigned, a flex.int() will exceed type limits

   rawdata = self.obj.read(self.parameters['Size'])
   uncoded_data = struct.unpack(endian_code+type_code*(self.parameters['Dim_2']*self.parameters['Dim_1']),rawdata)
   self.linearintdata = flex.int(uncoded_data)
   self.linearintdata.reshape(flex.grid((self.parameters['Dim_2'],self.parameters['Dim_1'])))

if __name__=="__main__":
 import sys
 P = EDFImage(sys.argv[1])
 P.readHeader()
 P.read()
 print "".join(P.header)
 print P.parameters
 count=0
 for ii in xrange( P.parameters["Dim_2"] ):
   for jj in xrange( P.parameters["Dim_1"] ):
      print P.linearintdata[count]
      count += 1
   print
