# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import
import unittest

from pykit.ir import verify, findop
from numba2 import jit, phase, environment
from numba2.types import Function, Bool, Int, Float
from numba2.typing import resolve

class C(object):
    @jit('C -> C -> Bool')
    def __gt__(self, other):
        return True

int32 = Int[32, False]

#===------------------------------------------------------------------===
# Helpers
#===------------------------------------------------------------------===

def get(f, argtypes):
    f = jit(f)
    env = environment.fresh_env(f, argtypes)
    func, env = phase.typing(f, env)
    context = env['numba.typing.context']
    signature = env['numba.typing.signature']
    return func, context, signature

#===------------------------------------------------------------------===
# Tests
#===------------------------------------------------------------------===

class TestInfer(unittest.TestCase):

    def test_simple(self):
        def simple(a, b):
            return 1

        f, context, signature = get(simple, [int32, int32])
        self.assertEqual(signature, Function[int32, int32, int32])

    def test_branch(self):
        def branch(a, b):
            if a > b:
                result = a
            else:
                result = b
            return result

        f, context, signature = get(branch, [int32, int32])
        self.assertEqual(signature, Function[int32, int32, int32])

        # TODO: Make blaze unit types instantiations of generic type constructors
        type = context[findop(f, 'call')]
        type = resolve(type, globals(), {})
        #self.assertEqual(type, set([Bool]))

    def test_loop(self):
        def loop(a, b):
            result = a
            while a > b:
                result = b
            return result

        f, context, signature = get(loop, [int32, int32])
        self.assertEqual(signature, Function[int32, int32, int32])

        # TODO: Make blaze unit types instantiations of generic type constructors
        type = context[findop(f, 'call')]
        type = resolve(type, globals(), {})
        #self.assertEqual(type, set([Bool]))


if __name__ == '__main__':
    #TestInfer('test_simple').debug()
    #TestInfer('test_branch').debug()
    #TestInfer('test_loop').debug()
    unittest.main()