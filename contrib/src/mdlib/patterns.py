# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module...
"""

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
    