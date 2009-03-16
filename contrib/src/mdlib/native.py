# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

import platform, os, ctypes


class UnsupportedSystemException(Exception):
    def __init__(self, system):
        super(UnsupportedSystemException, self).__init__(system)


class SystemInfo(object):
    def checkNetwork(self, protocol, url):
        pass


class WindowsSystemInfo(SystemInfo):
    
    def getSystemDrive(self):
        return os.getenv("SystemDrive")
    
    def checkRam(self, ramNeeded):
        kernel32 = ctypes.windll.kernel32
        c_ulong = ctypes.c_ulong
        
        class MemoryStruct(ctypes.Structure):
            _fields_ = [
                ('dwLength', c_ulong),
                ('dwMemoryLoad', c_ulong),
                ('dwTotalPhys', c_ulong),
                ('dwAvailPhys', c_ulong),
                ('dwTotalPageFile', c_ulong),
                ('dwAvailPageFile', c_ulong),
                ('dwTotalVirtual', c_ulong),
                ('dwAvailVirtual', c_ulong)
            ]
            
        memoryStatus = MemoryStruct()
        memoryStatus.dwLength = ctypes.sizeof(MemoryStruct)
        kernel32.GlobalMemoryStatus(ctypes.byref(memoryStatus))
        
        return memoryStatus.dwAvailPhys > ramNeeded
    

        def checkVRam(self):
            return True
    
        def checkDiskSpace(self, spaceNeeded):
            return True
        
        def checkNetwork(self, protocol, url):
            pass
            
            
class DarwinSystemInfo(SystemInfo):
    
    def getSystemDrive(self):
        return "/"
    
    def checkRam(self, ramNeeded):
        return True
    
    
    def checkVRam(self):
        return True
    
    
    def checkDiskSpace(self, path, spaceNeeded):
        stats = os.statvfs(path)
        
        # F_BSIZE * F_BAVAIL
        return (stats[0] * stats[4] / 1024.0) > spaceNeeded
    
    
    
class LinuxSystemInfo(SystemInfo):
    
    def getSystemDrive(self):
        return "/"
    
    def checkRam(self, ramNeeded):
        f = open("/proc/meminfo")
        
        # skip total memory
        f.readline()
        
        # string format: 'MemTotal:      3111036 kB\n'
        free = f.readline().split(":")[1].strip().split()[0]
        
        f.close()
        
        return free > ramNeeded
    
    
    def checkVRam(self):
        return True
    
    
    def checkDiskSpace(self, path, spaceNeeded):
        stats = os.statvfs(path)
        
        # F_BSIZE * F_BAVAIL
        return (stats[0] * stats[4] / 1024.0) > spaceNeeded
    
    
    def checkNetwork(self, protocol, url):
        pass
    

class SystemManager(object):
    def __init__(self):
        super(SystemManager, self).__init__()
        
        system = platform.system()
        if system == "Linux":
            self._info = LinuxSystemInfo()
        elif system == "Darwin":
            self._info = DarwinSystemInfo()
        elif system == "Windows":
            self._info = WindowsSystemInfo()
        else:
            raise UnsupportedSystemException(system)
    
    def __getattr__(self, attr):
        return getattr( self._info, attr )    
            

