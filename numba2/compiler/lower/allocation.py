# -*- coding: utf-8 -*-

"""
Object allocation. Lower to GC or stack-allocation based on available
information.
"""

from __future__ import print_function, division, absolute_import
import ctypes

from numba2 import is_numba_type, int64, errors
from numba2.compiler.utils import Caller
from numba2.types import Type, Pointer, void
from numba2.representation import stack_allocate
from numba2.runtime import gc

from pykit import types as ptypes
from pykit import ir
from pykit.ir import Builder, OpBuilder, Const

def allocator(func, env):
    context = env['numba.typing.context']
    b = OpBuilder()
    caller = Caller(b, context)
    gcmod = gc.gc_impl(env["numba.gc.impl"])

    for op in func.ops:
        if op.opcode == 'allocate_obj':
            stmts, newop = allocate_object(caller, b, context[op], env)
        elif op.opcode == 'register_finalizer':
            newop = register_finalizer(caller, b, context,
                                       context[op], gcmod, op.args[0])
            stmts = [newop]
        else:
            continue

        if newop is None:
            op.delete()
        elif newop is not None:
            newop.result = op.result
            op.replace(stmts)


def allocate_object(caller, builder, type, env):
    """
    Allocate object of type `type`.
    """
    if stack_allocate(type):
        obj = builder.alloca(ptypes.Pointer(ptypes.Opaque))
        return [obj], obj
    else:
        if env['numba.target'] != 'cpu':
            raise errors.CompileError(
                "Cannot heap allocate object of type %s with target %r" % (
                                                type, env['numba.target']))
        return heap_allocate(caller, builder, type, env)

# TODO: generating calls or typed codes is still messy:
# TODO:     - write "untyped" pykit builder
# TODO:     - write typed numba builder (?)

def heap_allocate(caller, builder, type, env):
    """
    Heap allocate an object of type `type`
    """
    from numba2 import phase

    # TODO: implement untyped pykit builder !

    # Put object on the heap: call gc.gc_alloc(nitems, type)
    gcmod = gc.gc_impl(env["numba.gc.impl"])
    context = env['numba.typing.context']

    # Build arguments for gc_alloc
    n = Const(1, ptypes.Opaque)
    ty = Const(type, ptypes.Opaque)
    context[n] = int64
    context[ty] = Type[type]

    # Type the gc_alloc function
    p = caller.call(phase.typing, gcmod.gc_alloc, [n, ty])
    obj = builder.convert(ptypes.Opaque, p)

    # Update type context
    context[p] = Pointer[void]

    return [p, obj], obj

def register_finalizer(caller, builder, context, type, gcmod, obj):
    """
    Register a finalizer for the object given as pointer `obj`.
    """
    from numba2 import phase

    #(TODO: (indirect) allocation of a new object in __del__ will recurse
    # infinitely)

    if '__del__' in type.fields:
        # Compile __del__
        __del__ = type.fields['__del__']
        lfunc, env = phase.apply_phase(phase.codegen, __del__, (type,))

        # Retrieve function address of __del__
        cfunc = env["codegen.llvm.ctypes"]
        pointerval = ctypes.cast(cfunc, ctypes.c_void_p).value
        ptr = ir.Pointer(pointerval, ptypes.Pointer(ptypes.Void))
        context[ptr] = Pointer[void]

        # Call gc_add_finalizer with (obj, ptr)
        result = caller.call(phase.typing, gcmod.gc_add_finalizer, [obj, ptr])
        context[result] = void

        return result
