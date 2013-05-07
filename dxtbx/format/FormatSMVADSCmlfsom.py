from __future__ import division

from dxtbx.format.FormatSMVADSC import FormatSMVADSC

class FormatSMVADSCmlfsom(FormatSMVADSC):
    '''A class for reading SMV::ADSC-format images generated by MLFSOM
      simulation.'''

    @staticmethod
    def understand(image_file):

        size, header = FormatSMVADSC.get_smv_header(image_file)

        unwanted_header_items = ['TIME','DATE']

        for header_item in unwanted_header_items:
            if header_item in header:
                return False

        return True

    def __init__(self, image_file):
        '''Initialise the image structure from the given file, including a
        proper model of the experiment.'''

        assert(self.understand(image_file))

        FormatSMVADSC.__init__(self, image_file)

    def _scan(self):
        '''Return the scan information for this image.'''

        format = self._scan_factory.format('SMV')
        exposure_time = 1. # dummy argument; ought to be explicitly output by MLFSOM!
        epoch = None

        # assert(epoch)
        osc_start = float(self._header_dictionary['OSC_START'])
        osc_range = float(self._header_dictionary['OSC_RANGE'])

        return self._scan_factory.single(
            self._image_file, format, exposure_time,
            osc_start, osc_range, epoch)

if __name__ == '__main__':

    import sys

    for arg in sys.argv[1:]:
        print FormatSMVADSCmlfsom.understand(arg)
