# -*- coding: utf-8 -*-

"""
Primitive operations, like 'a is b'.
"""

from __future__ import print_function, division, absolute_import

import operator

from .obj import NoneType
from .. import jit, typeof, overlay

#===------------------------------------------------------------------===
# Implementations
#===------------------------------------------------------------------===

@jit('a -> b -> bool')
def is_(a, b):
    return False

# TODO: Overload for variants !

@jit('NoneType -> NoneType -> bool')
def is_(a, b):
    return True

#===------------------------------------------------------------------===
# Overlays
#===------------------------------------------------------------------===

@jit
def getitem(obj, idx):
    return obj.__getitem__(idx)

@jit
def setitem(obj, idx, value):
    obj.__setitem__(idx, value)

# We overlay operator.is_ with our own implementation. This works not only
# when operator.is_ is used in user-code, but frontend/translation.py itself
# turns 'is' operations into operator.is_ calls

overlay(operator.is_, is_)
overlay(operator.getitem, getitem)
overlay(operator.setitem, setitem)