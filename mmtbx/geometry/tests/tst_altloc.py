from __future__ import division

from mmtbx.geometry import altloc

import unittest

class TestVisitor(object):

  def __init__(self):

    self.regular_calls = []
    self.altloc_calls = []


  def process_regular(self, data, coordinates):

    self.regular_calls.append( ( data, coordinates ) )


  def process_altloc(self, data, coordinates, identifier):

    self.altloc_calls.append( ( data, coordinates, identifier ) )


class TestStrategies(unittest.TestCase):

  def setUp(self):

    self.data = object()
    self.coords = object()
    self.processor = TestVisitor()


  def test_empty(self):

    altloc.Empty(
      data = self.data,
      coordinates = self.coords,
      processor = self.processor,
      )
    self.assertEqual( self.processor.regular_calls, [ ( self.data, self.coords ) ] )
    self.assertEqual( self.processor.altloc_calls, [] )


  def test_altloc(self):

    identifier = object()
    strategy = altloc.Alternate( identifier = identifier )
    strategy( data = self.data, coordinates = self.coords, processor = self.processor )
    self.assertEqual( self.processor.regular_calls, [] )
    self.assertEqual( self.processor.altloc_calls, [ ( self.data, self.coords, identifier ) ] )


class TestDescription(unittest.TestCase):

  def setUp(self):

    self.data = object()
    self.coords = object()
    self.processor = TestVisitor()


  def test_empty(self):

    description = altloc.Description(
      data = self.data,
      coordinates = self.coords,
      altid = None,
      )
    self.assertEqual( description.strategy, altloc.Empty )
    description = altloc.Description(
      data = self.data,
      coordinates = self.coords,
      altid = "",
      )
    self.assertEqual( description.strategy, altloc.Empty )
    description.accept( processor = self.processor )
    self.assertEqual( self.processor.regular_calls, [ ( self.data, self.coords ) ] )
    self.assertEqual( self.processor.altloc_calls, [] )


  def test_altoc(self):

    identifier = object()
    description = altloc.Description(
      data = self.data,
      coordinates = self.coords,
      altid = identifier,
      )
    self.assertTrue( isinstance( description.strategy, altloc.Alternate ) )
    self.assertEqual( description.strategy.identifier, identifier )
    description.accept( processor = self.processor )
    self.assertEqual( self.processor.regular_calls, [] )
    self.assertEqual( self.processor.altloc_calls, [ ( self.data, self.coords, identifier ) ] )


class TestIndexer(unittest.TestCase):

  def test_1(self):

    factory = lambda: object()

    indexer = altloc.Indexer( factory = factory )
    self.assertTrue( isinstance( indexer.regular, object ) )
    self.assertEqual( indexer.factory, factory )
    self.assertEqual( indexer.altlocs, {} )

    altid = object()
    indexer.add( altloc = altid )
    self.assertTrue( altid in indexer.altlocs )
    self.assertTrue( isinstance( indexer.altlocs[ altid ], object ) )


class FakeIndexer(object):

  def __init__(self):

    self.calls = []


  def add(self, object, position):

    self.calls.append( ( object, position ) )


class TestInserter(unittest.TestCase):

  def setUp(self):

    self.inserter = altloc.Inserter( indexer = altloc.Indexer( factory = FakeIndexer ) )


  def test_basic(self):

    self.assertEqual( self.inserter.indexer.regular.calls, [] )
    self.assertEqual( self.inserter.indexer.altlocs, {} )


  def test_regular(self):

    obj1 = object()
    coords1 = object()
    self.inserter.process_regular( data = obj1, coordinates = coords1 )
    self.assertEqual( self.inserter.indexer.regular.calls, [ ( obj1, coords1 ) ] )
    self.assertEqual( self.inserter.indexer.altlocs, {} )

    obj2 = object()
    coords2 = object()
    self.inserter.process_regular( data = obj2, coordinates = coords2 )
    self.assertEqual(
      self.inserter.indexer.regular.calls,
      [ ( obj1, coords1 ), ( obj2, coords2 ) ],
      )
    self.assertEqual( self.inserter.indexer.altlocs, {} )


  def test_altid(self):

    obj1 = object()
    coords1 = object()
    altid1 = object()
    self.inserter.process_altloc( data = obj1, coordinates = coords1, identifier = altid1 )
    self.assertEqual( self.inserter.indexer.regular.calls, [] )
    self.assertEqual( len( self.inserter.indexer.altlocs ), 1 )
    self.assertTrue( altid1 in self.inserter.indexer.altlocs )
    self.assertEqual(
      self.inserter.indexer.altlocs[ altid1 ].calls,
      [ ( obj1, coords1 ) ]
      )

    obj2 = object()
    coords2 = object()
    self.inserter.process_altloc( data = obj2, coordinates = coords2, identifier = altid1 )
    self.assertEqual( self.inserter.indexer.regular.calls, [] )
    self.assertEqual( len( self.inserter.indexer.altlocs ), 1 )
    self.assertTrue( altid1 in self.inserter.indexer.altlocs )
    self.assertEqual(
      self.inserter.indexer.altlocs[ altid1 ].calls,
      [ ( obj1, coords1 ), ( obj2, coords2 ) ],
      )

    altid2 = object()
    self.inserter.process_altloc( data = obj2, coordinates = coords2, identifier = altid2 )
    self.assertEqual( self.inserter.indexer.regular.calls, [] )
    self.assertEqual( len( self.inserter.indexer.altlocs ), 2 )
    self.assertTrue( altid1 in self.inserter.indexer.altlocs )
    self.assertTrue( altid2 in self.inserter.indexer.altlocs )
    self.assertEqual(
      self.inserter.indexer.altlocs[ altid2 ].calls,
      [ ( obj2, coords2 ) ],
      )


suite_strategies = unittest.TestLoader().loadTestsFromTestCase(
  TestStrategies
  )
suite_description = unittest.TestLoader().loadTestsFromTestCase(
  TestDescription
  )
suite_indexer = unittest.TestLoader().loadTestsFromTestCase(
  TestIndexer
  )
suite_inserter = unittest.TestLoader().loadTestsFromTestCase(
  TestInserter
  )

alltests = unittest.TestSuite(
  [
    suite_strategies,
    suite_description,
    suite_indexer,
    suite_inserter,
    ]
  )


def load_tests(loader, tests, pattern):

    return alltests


if __name__ == "__main__":
    unittest.TextTestRunner( verbosity = 2 ).run( alltests )

