#!/usr/bin/env python
# Registry.py
#   Copyright (C) 2011 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# A registry class to handle Format classes and provide lists of them when
# this is useful for i.e. identifying the best tool to read a given range
# of image formats.

from __future__ import division

from RegistryHelpers import LoadFormatClasses

class _Registry:
    '''A class to handle all of the recognised image formats within xia2
    working towards the generalization project in #1555 and specifically
    to address the requirements in #1573.'''

    def __init__(self):
        '''Set myself up - N.B. this could trigger a directory search for
        different Format classes to auto-register them.'''

        self._formats = []

        self._setup = False

        return

    def setup(self):
        '''Look to import format defining modules from around the place -
        this will look in dxtbx/format and $HOME/.xia2/ for files starting
        with Format and ending in .py to allow user extensibility.'''

        if self._setup:
            return

        LoadFormatClasses()

        self._setup = True

        return

    def add(self, format):
        '''Register a new image format with the registry. N.B. to work
        this object must be inherited from the base Format class.'''

        from dxtbx.format.Format import Format

        assert(issubclass(format, Format))
        if not format in self._formats:
            self._formats.append(format)

        return

    def get(self):
        '''Get a list of image formats registered here.'''

        return tuple(self._formats)

    def find(self, image_file):
        '''More useful - find the best format handler in the registry for your
        image file. N.B. this is in principle a factory function.'''

        self.setup()

        # Recursively check whether any of the children understand
        # image_file, in which case they are preferred over the parent
        # format.
        def recurse(format, image_file):
            for child in format._children:
                if child.understand(image_file):
                    return recurse(child, image_file)
            return format

        for format in self._formats:
            if format.understand(image_file):
                return recurse(format, image_file)

        raise IOError, 'no format support found for %s' % image_file

class Registry:
    '''A class to turn the registry above into a singleton, so that we
    can work around some of the more knotty dependency loops which come
    out of things like this. This is something of a boiler plate.'''

    __instance = None

    def __init__(self):

        if Registry.__instance is None:
            Registry.__instance = _Registry()
        return

    def __call__(self):
        return self

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

Registry = Registry()
