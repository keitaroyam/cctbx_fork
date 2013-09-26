
from dxtbx.model.detector2 import Detector2

class Test:

    def __init__(self):
        detector = Detector2()
        detector.set_name("D1")
        detector.set_type("D")

        quad1 = detector.add_group()
        quad1.set_name("Q1")
        quad1.set_type("Q")

        panel1 = quad1.add_panel()
        panel1.set_name("P1")
        panel1.set_type("P")

        panel2 = quad1.add_panel()
        panel2.set_name("P2")
        panel2.set_type("P")

        quad2 = detector.add_group()
        quad2.set_name("Q2")
        quad2.set_type("Q")

        panel3 = quad2.add_panel()
        panel3.set_name("P3")
        panel3.set_type("P")

        panel4 = quad2.add_panel()
        panel4.set_name("P4")
        panel4.set_type("P")

        self.detector = detector

    def run(self):
        self.tst_iterate_and_index()
        self.tst_get_uninitialized_D_matrix()
        self.tst_get_valid_D_matrix()

    def tst_iterate_and_index(self):
        ''' Test iteration and indexing through the detector in various ways. '''

        # Iterate through the detector's children and check output
        expected_types = ['Q', 'Q',]
        expected_names = ['Q1', 'Q2']
        names = []
        types = []
        for p in self.detector:
            names.append(p.get_name())
            types.append(p.get_type())
        assert(all(n == en for n, en in zip(names, expected_names)))
        assert(all(t == et for t, et in zip(types, expected_types)))

        # Iterate through the detector's children in reverse and check output
        expected_types = ['Q', 'Q',]
        expected_names = ['Q2', 'Q1']
        names = []
        types = []
        for p in self.detector.reverse():
            names.append(p.get_name())
            types.append(p.get_type())
        assert(all(n == en for n, en in zip(names, expected_names)))
        assert(all(t == et for t, et in zip(types, expected_types)))

        # Use an index to access the detector children
        assert(len(self.detector) == 2)
        group = self.detector[1]
        assert(group.get_name() == 'Q2' and group.get_type() == 'Q')
        assert(len(group) == 2)
        panel = group[0]
        assert(panel.get_name() == 'P3' and panel.get_type() == 'P')

        # Iterate through the tree pre-order and check output
        expected_types = ['D', 'Q', 'P', 'P', 'Q', 'P', 'P']
        expected_names = ['D1', 'Q1', 'P1', 'P2', 'Q2', 'P3', 'P4']
        names = []
        types = []
        for p in self.detector.iter_preorder():
            names.append(p.get_name())
            types.append(p.get_type())
        assert(all(n == en for n, en in zip(names, expected_names)))
        assert(all(t == et for t, et in zip(types, expected_types)))

        # Iterate through the tree level-order and check output
        expected_types = ['D', 'Q', 'Q', 'P', 'P', 'P', 'P']
        expected_names = ['D1', 'Q1', 'Q2', 'P1', 'P2', 'P3', 'P4']
        names = []
        types = []
        for p in self.detector.iter_levelorder():
            names.append(p.get_name())
            types.append(p.get_type())
        assert(all(n == en for n, en in zip(names, expected_names)))
        assert(all(t == et for t, et in zip(types, expected_types)))

        # Iterate through the panels in pre-order and check output
        expected_types = ['P', 'P', 'P', 'P']
        expected_names = ['P1', 'P2', 'P3', 'P4']
        names = []
        types = []
        for p in self.detector.iter_panels():
            names.append(p.get_name())
            types.append(p.get_type())
        assert(all(n == en for n, en in zip(names, expected_names)))
        assert(all(t == et for t, et in zip(types, expected_types)))

        # Get a flex array of panels and check then length
        panels = self.detector.panels()
        assert(len(panels) == 4)

        print 'OK'

    def tst_get_uninitialized_D_matrix(self):
        ''' Try to get bad D matrix and check that an exception is thrown. '''
        panels = self.detector.panels()
        for p in panels:
            try:
                p.get_D_matrix()
                assert(False)
            except Exception:
                pass

        print 'OK'

    def tst_get_valid_D_matrix(self):
        ''' Setup the hierarchy of frames and check it's all consistent. '''
        from scitbx import matrix

        # Set a valid frame for the top level detector
        self.detector.set_local_frame(
            (1, 0, 0),     # Fast axis
            (0, 1, 0),     # Slow axis
            (0, 0, 100))   # Origin

        # Check that all sub groups have the same frame and that we can get
        # a valid D matrix
        for obj in self.detector.iter_preorder():
            fast = matrix.col(obj.get_fast_axis())
            slow = matrix.col(obj.get_slow_axis())
            orig = matrix.col(obj.get_origin())
            assert(abs(fast - matrix.col((1, 0, 0))) < 1e-7)
            assert(abs(slow - matrix.col((0, 1, 0))) < 1e-7)
            assert(abs(orig - matrix.col((0, 0, 100))) < 1e-7)
            D = obj.get_D_matrix()

        # Get the quadrants and set their frames
        q1, q2 = self.detector.children()
        q1.set_local_frame(
            (1, 1, 0),      # Fast axis relative to detector frame
            (-1, 1, 0),     # Slow axis relative to detector frame
            (10, 10, 0))    # Origin relative to detector frame
        q2.set_local_frame(
            (1, -1, 0),     # Fast axis relative to detector frame
            (1, 1, 0),      # Slow axis relative to detector frame
            (20, 20, 0))    # Origin relative to detector frame

        # Get the panels and set their frames
        p1, p2 = q1.children()
        p1.set_local_frame(
            (1, -1, 0),     # Fast axis relative to q1 frame
            (1, 1, 0),      # Slow axis relative to q1 frame
            (5, 0, 10))     # Origin relative to q1 frame
        p2.set_local_frame(
            (1, 1, 0),      # Fast axis relative to q1 frame
            (-1, 1, 0),     # Slow axis relative to q1 frame
            (0, 5, -10))    # Origin relative to q1 frame

        # Get the panels and set their frames
        p3, p4 = q2.children()
        p3.set_local_frame(
            (1, -1, 0),     # Fast axis relative to q2 frame
            (1, 1, 0),      # Slow axis relative to q2 frame
            (0, 5, -10))    # Origin relative to q2 frame
        p4.set_local_frame(
            (1, 1, 0),      # Fast axis relative to q2 frame
            (-1, 1, 0),     # Slow axis relative to q2 frame
            (5, 0, 10))     # Origin relative to q2 frame

        # Test the panel coordinate systems
        from math import sqrt
        eps = 1e-7
        p1_d0 = matrix.col((10.0 + sqrt(5.0**2 / 2), 10.0 + sqrt(5.0**2 / 2), 110))
        p2_d0 = matrix.col((10.0 - sqrt(5.0**2 / 2), 10.0 + sqrt(5.0**2 / 2), 90))
        p3_d0 = matrix.col((20.0 + sqrt(5.0**2 / 2), 20.0 + sqrt(5.0**2 / 2), 90))
        p4_d0 = matrix.col((20.0 + sqrt(5.0**2 / 2), 20.0 - sqrt(5.0**2 / 2), 110))
        p1_d1 = matrix.col((1, 0, 0))
        p2_d1 = matrix.col((0, 1, 0))
        p3_d1 = matrix.col((0, -1, 0))
        p4_d1 = matrix.col((1, 0, 0))
        p1_d2 = matrix.col((0, 1, 0))
        p2_d2 = matrix.col((-1, 0, 0))
        p3_d2 = matrix.col((1, 0, 0))
        p4_d2 = matrix.col((0, 1, 0))
        assert(abs(matrix.col(p1.get_origin()) - p1_d0) < eps)
        assert(abs(matrix.col(p2.get_origin()) - p2_d0) < eps)
        assert(abs(matrix.col(p3.get_origin()) - p3_d0) < eps)
        assert(abs(matrix.col(p4.get_origin()) - p4_d0) < eps)
        assert(abs(matrix.col(p1.get_fast_axis()) - p1_d1) < eps)
        assert(abs(matrix.col(p2.get_fast_axis()) - p2_d1) < eps)
        assert(abs(matrix.col(p3.get_fast_axis()) - p3_d1) < eps)
        assert(abs(matrix.col(p4.get_fast_axis()) - p4_d1) < eps)
        assert(abs(matrix.col(p1.get_slow_axis()) - p1_d2) < eps)
        assert(abs(matrix.col(p2.get_slow_axis()) - p2_d2) < eps)
        assert(abs(matrix.col(p3.get_slow_axis()) - p3_d2) < eps)
        assert(abs(matrix.col(p4.get_slow_axis()) - p4_d2) < eps)

        print 'OK'


if __name__ == '__main__':
    test = Test()
    test.run()
