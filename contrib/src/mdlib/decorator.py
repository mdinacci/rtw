# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>

They work better with Python2.5 as we can avoid writing:
newf.__name__ = f.__name__
newf.__dict__.update(f.__dict__)
newf.__doc__ = f.__doc__
newf.__module__ = f.__module__
"""

import time

def Property(func):
    return property(**func())

def deprecated(func):
    """ Decorator to trace method execution """
    def new(*args, **kwds):
        print "The function %s is deprecated" % func.__name__
        func(*args, **kwds)
    return new

def timer(func):
    """ Time the application of func to arguments. Return seconds. """
    def new(*args, **kwds):
        print "Timing %s" % func.__name__
        start = time.clock()
        func(*args)
        print "It took: %d" % (time.clock() - start)
    return new


def traceMethod(func):
    """ Decorator to trace method execution """
    def new(*args, **kwds):
        print "Entering %s " % func.__name__
        func(*args, **kwds)
        print "Exiting %s " % func.__name__
    return new

import warnings

def deprecated(func):
    """
    This is a decorator which can be used to mark functions as deprecated. 
    It will result in a warning being emitted when the function is used.
    """
    def new(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    return new


def dumpArgs(func):
    """ 
    This decorator dumps out the arguments passed to a 
    function before calling it 
    """
    argnames = func.func_code.co_varnames[:func.func_code.co_argcount]
    fname = func.func_name
    def echo(*args,**kwargs):
        print fname, ":", ', '.join(
            '%s=%r' % entry
            for entry in zip(argnames,args) + kwargs.items())
        return func(*args, **kwargs)
    return echo

import sys
import os
import linecache

def trace(f):
    """ 
    This decorator allows decorating individual 
    functions so their lines are traced 
    """
    def globaltrace(frame, why, arg):
        if why == "call":
            return localtrace
        return None

    def localtrace(frame, why, arg):
        if why == "line":
            # record the file name and line number of every trace
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno

            bname = os.path.basename(filename)
            print "%s(%d): %s" % (bname, lineno,
                                  linecache.getline(filename, lineno)),
        return localtrace

    def _f(*args, **kwds):
        sys.settrace(globaltrace)
        result = f(*args, **kwds)
        sys.settrace(None)
        return result

    return _f

def accepts(*types, **kw):
    """ Function decorator. Checks that inputs given to decorated function
    are of the expected type.

    Parameters:
    types -- The expected types of the inputs to the decorated function.
             Must specify type for each parameter.
    kw    -- Optional specification of 'debug' level (this is the only valid
             keyword argument, no other should be given).
             debug = ( 0 | 1 | 2 )

    FIXME: BROKEN !!!
    
    """
    if not kw:
        # default level: MEDIUM
        debug = 1
    else:
        debug = kw['debug']
    try:
        def decorator(f):
            def newf(*args):
                if debug == 0:
                    return f(*args)
                assert len(args) == len(types)
                argtypes = tuple(map(type, args))
                if argtypes != types:
                    msg = info(f.__name__, types, argtypes, 0)
                    if debug == 1:
                        print >> sys.stderr, 'TypeWarning: ', msg
                    elif debug == 2:
                        raise TypeError, msg
                return f(*args)
            newf.__name__ = f.__name__
            return newf
        return decorator
    except KeyError, key:
        raise KeyError, key + "is not a valid keyword argument"
    except TypeError, msg:
        raise TypeError, msg


def returns(ret_type, **kw):
    """ Function decorator. Checks that return value of decorated function
    is of the expected type.

    Parameters:
    ret_type -- The expected type of the decorated function's return value.
                Must specify type for each parameter.
    kw       -- Optional specification of 'debug' level (this is the only valid
                keyword argument, no other should be given).
                debug=(0 | 1 | 2)

    """
    try:
        if not kw:
            # default level: MEDIUM
            debug = 1
        else:
            debug = kw['debug']
        def decorator(f):
            def newf(*args):
                result = f(*args)
                if debug == 0:
                    return result
                res_type = type(result)
                if res_type != ret_type:
                    msg = info(f.__name__, (ret_type,), (res_type,), 1)
                    if debug == 1:
                        print >> sys.stderr, 'TypeWarning: ', msg
                    elif debug == 2:
                        raise TypeError, msg
                return result
            newf.__name__ = f.__name__
            return newf
        return decorator
    except KeyError, key:
        raise KeyError, key + "is not a valid keyword argument"
    except TypeError, msg:
        raise TypeError, msg

def info(fname, expected, actual, flag):
    """ Convenience function returns nicely formatted error/warning msg. """
    format = lambda types: ', '.join([str(t).split("'")[1] for t in types])
    expected, actual = format(expected), format(actual)
    msg = "'%s' method " % fname \
          + ("accepts", "returns")[flag] + " (%s), but " % expected\
          + ("was given", "result is")[flag] + " (%s)" % actual
    return msg
