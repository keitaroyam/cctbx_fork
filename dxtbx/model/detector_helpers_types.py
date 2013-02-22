from __future__ import division
#!/usr/bin/env python
# detector_helpers_types.py
#
#   Copyright (C) 2011 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# Helpers for the detector class... this time enumerating all of the common
# detector types, hashed by the sensor type, image dimensions and pixel
# dimensions.

import os
import sys

from detector_helpers import detector_helper_sensors
from detector import detector_factory

class detector_helpers_types:
    '''A singleton class to help with identifying specific detectors used for
    macromolecular crystallography.'''

    def __init__(self):

        import dxtbx

        detector_lib = os.path.join(os.path.split(dxtbx.__file__)[0],
                                    'data', 'detectors.lib')

        if not os.path.exists(detector_lib):
            raise RuntimeError, 'detector library not found'

        self._detectors = { }

        for record in open(detector_lib):
            if 'Sensor' in record[:6]:
                continue
            if '------' in record[:6]:
                continue

            text = record.split('#')[0].strip()

            if not text:
                continue

            tokens = text.split()

            assert(len(tokens) == 6)

            sensor = detector_factory.sensor(tokens[0])
            fast, slow, df, ds = map(int, tokens[1:5])

            self._detectors[(sensor, fast, slow, df, ds)] = tokens[5]

        return

    def get(self, sensor, fast, slow, df, ds):
        '''Look up a name for a detector with this sensor type (listed in
        detector_helpers) these image dimensions in the fast and slow
        directions, these corresponding pixel sizes, in microns (integers).
        If the sensor is unknown, all sensor types will be tested - be warned
        if there are duplicates.'''

        sensor = detector_factory.sensor(sensor)

        if sensor == detector_helper_sensors.SENSOR_UNKNOWN:
            for s in detector_helper_sensors.all():
                try:
                    return self.get(s, fast, slow, df, ds)
                except: # intentional
                    pass

            raise RuntimeError, 'detector %s %d %d %d %d unknown' % \
                  (sensor, fast, slow, df, ds)

        if (sensor, fast, slow, df, ds) in self._detectors:
            return self._detectors[(sensor, fast, slow, df, ds)]

        # OK allow for small variations in the recorded pixel dimensions

        for ddf in -2, -1, 1, 2:
            for dds in -2, -1, 1, 2:
                if (sensor, fast, slow, df + ddf, ds + dds) in self._detectors:
                    return self._detectors[
                        (sensor, fast, slow, df + ddf, ds + dds)]

        raise RuntimeError, 'detector %s %d %d %d %d unknown' % \
              (sensor, fast, slow, df, ds)

detector_helpers_types = detector_helpers_types()

if __name__ == '__main__':
    sensor = sys.argv[1]
    fast, slow, df, ds = map(int, sys.argv[2:6])

    print detector_helpers_types.get(sensor, fast, slow, df, ds)
