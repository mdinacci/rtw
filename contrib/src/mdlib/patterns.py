# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module contains a collection of patterns
"""

import inspect

# Peter Norvig's implementation
def singleton(object, instantiated=[]):
    """
    Raise an exception if an object of this class has been instantiated before.
    Usage:
        class YourClass:
            "A singleton class to do something ..."
            def __init__(self, args):
                singleton(self)
        ...
    """
    assert object.__class__ not in instantiated, \
        "%s is a Singleton class but is already instantiated" % object.__class__
    instantiated.append(object.__class__)


def mixin(cls):
    """
    mixes-in a class (or a module) into another class. must be called from within
    a class definition. `cls` is the class/module to mix-in
    """
    locals = inspect.stack()[1][0].f_locals
    if "__module__" not in locals:
        raise TypeError("mixin() must be called from within a class definition")
    
    # copy the class's dict aside and perform some tweaking
    dict = cls.__dict__.copy()
    dict.pop("__doc__", None)
    dict.pop("__module__", None)
    
    # __slots__ hell
    slots = dict.pop("__slots__", [])
    if slots and "__slots__" not in locals:
        locals["__slots__"] = ["__dict__"]
    for name in slots:
        if name.startswith("__") and not name.endswith("__"):
            name = "_%s%s" % (cls.__name__, name)
        dict.pop(name)
        locals["__slots__"].append(name)
    
    # mix the namesapces
    locals.update(dict)


class SimpleObservable:
    """
    An extremely simple Observable class
    """
    
    observers = []
        
    def __init__(self):
        pass

    def register(self, observer):
        self.observers.append(observer)
        
    def notify(self):
        for observer in self.observers:
            observer.update()
            
    def unregister(self, observer):
        self.observers[observer] = None
        
class Observer:
    def __init__(self):
        pass
    
    def update(self):
        pass
    