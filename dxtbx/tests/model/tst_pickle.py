
from __future__ import division
from dxtbx.model import Beam, Goniometer
from dxtbx.model import Panel, Detector, Scan, PanelGroup

def pickle_then_unpickle(obj):
    '''Pickle to a temp file then un-pickle.'''
    import pickle
    import tempfile

    # Create a tmp file
    temp = tempfile.TemporaryFile()

    # Pickle the object
    pickle.dump(obj, temp)

    # Read the object
    temp.flush()
    temp.seek(0)
    return pickle.load(temp)

def tst_beam():
    '''Test pickling the beam object.'''
    obj1 = Beam((1, 1, 1))
    obj2 = pickle_then_unpickle(obj1)
    assert(obj1 == obj2)
    print "OK"

def tst_goniometer():
    '''Test pickling the goniometer object.'''
    obj1 = Goniometer()
    obj2 = pickle_then_unpickle(obj1)
    assert(obj1 == obj2)
    print "OK"

def tst_panel():
    '''Test pickling the panel object.'''
    obj1 = Panel()
    obj1.set_local_frame((1, 0, 0), (0, 1, 0), (0, 0, 1))
    obj2 = pickle_then_unpickle(obj1)
    assert(obj1 == obj2)
    print "OK"

def tst_detector():
    '''Test pickling the detector object.'''
    p = Panel()
    p.set_local_frame((1, 0, 0), (0, 1, 0), (0, 0, 1))
    obj1 = Detector(p)
    root = obj1.hierarchy()
    root.add_panel(obj1[0])
    root.add_group()
    obj2 = pickle_then_unpickle(obj1)
    assert(obj2.hierarchy()._container == obj2)
    assert(obj2.hierarchy()[0] == obj2[0])
    assert(obj2.hierarchy()[0] in obj2)
    assert(type(obj2.hierarchy()[1]) == PanelGroup)
    assert(obj1 == obj2)
    print "OK"

def tst_scan():
    '''Test pickling the scan data object.'''
    obj1 = Scan((1, 2), (1, 1))
    obj2 = pickle_then_unpickle(obj1)
    assert(obj1 == obj2)
    print "OK"

def run():
    '''Run all the tests'''
    tst_beam()
    tst_goniometer()
    tst_panel()
    tst_detector()
    tst_scan()

if __name__ == '__main__':
    run()
