#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import time
import shutil
import uuid
import hashlib
from lxml import etree


def toXML(classElement, **kwargs):
    if kwargs.has_key('nodeName'):
        nodeName = kwargs['nodeName']
    else:
        nodeName = "Node"

    if kwargs.has_key('ignore'):
        ignore = kwargs['ignore']
    else:
        ignore = []

    node = etree.Element(nodeName)
    for i in classElement.__dict__:
        if i not in ignore:
            xml = etree.Element(i)
            xml.text = str(classElement.__dict__[i])
            node.append(xml)
    return node

class LogCopiedFile():
    """Stores data of a single file, copyed to the VM

    """
    def __init__(self, source, destination, timeoffset=0, timeRate=100, upTime=0):
        self.source = source
        self.destination = destination
        self.tmp = self.copy_to_temp()
        self.md5Sum = self.calc_md5sum()
        self.sha256sum = self.calc_sha256sum()
        self.filesize = self.get_file_size()
        self.realtime = time.time()
        self.time = time.time() + timeoffset
        self.timeRate = timeRate
        self.upTime = upTime

    def get_file_size(self):
        filesize = os.path.getsize(self.tmp)
        return filesize

    def copy_to_temp(self):
        tmp = '/tmp/%s.forensig20' % str(uuid.uuid4())
        shutil.copy(self.source, tmp)
        return tmp

    def calc_md5sum(self):
        md5 = hashlib.md5(open(self.tmp, 'rb').read()).hexdigest()
        return md5

    def calc_sha256sum(self):
        sha256 = hashlib.sha256(open(self.tmp, 'rb').read()).hexdigest()
        return sha256

    def get_entry(self):
        return {'source': self.source,
            'destination': self.destination, 'tmp': self.tmp, 
            'md5sum': self.md5Sum, 'sha256sum': self.sha256sum, 
            'filesize': self.filesize, 'realtime': self.realtime, 
            'time': self.time, 'timeRate': self.timeRate, 'upTime': self.upTime}

    def cleanup(self):
        return self.tmp

    def to_xml(self):
        return toXML(self, nodeName="copiedFile", ignore=['time'])

class LogCdMount():
    """Stores data about a cd mounted to the VM

    """
    def __init__(self, path, timeoffset=0, timeRate=0, upTime=0):
        self.path = path
        self.realtime = time.time()
        self.time = time.time() + timeoffset
        self.timeRate = timeRate
        self.upTime = upTime

    def get_entry(self):
        return {'path': self.path, 'realtime': self.realtime, 'time': self.time, 
            'timeRate': self.timeRate, 'upTime': self.upTime}

    def cleanup(self):
        return self.path

    def to_xml(self):
        return toXML(self, nodeName="cd", ignore=['time'])

class LogProcess():
    """Stores data of a single process, running in the VM

    """
    def __init__(self, process, arguments, stdin='', stdout='', stderr='', 
            timeoffset=0, timeRate=0, upTime=0):
        self.process = process
        self.arguments = arguments
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.realtime = time.time()
        self.time = time.time() + timeoffset
        self.timeRate = timeRate
        self.upTime = upTime

    def get_entry(self):
        return {'process': self.process, 'arguments': self.arguments,
            'stdin': self.stdin, 'stdout': self.stdout, 'stderr': self.stderr, 
            'realtime': self.realtime, 'time': self.time, 
            'timeRate': self.timeRate, 'upTime': self.upTime}

    def cleanup(self):
        return False

    def to_xml(self):
        return toXML(self, nodeName="process", ignore=['time'])

class LogRawKeyboard():
    """Stores raw keyboard input
    """
    def __init__(self, key_input, timeoffset=0, timeRate=0, upTime=0):
        self.key_input = key_input
        self.realtime = time.time()
        self.time = time.time() + timeoffset
        self.timeRate = timeRate
        self.upTime = upTime

    def get_entry(self):
        return {'keyboard input': self.key_input, 'realtime': self.realtime, 
            'time': self.time, 'timeRate': self.timeRate, 'upTime': self.upTime}

    def cleanup(self):
        return False

    def to_xml(self):
        return toXML(self, nodeName="keyboard input", ignore=['time'])

class LogVM():
    """saves general properties of one VM"""
    def __init__(self, vmname, basename, osType, username, password):  
        self.vmname = vmname
        self.basename = basename
        self.osType = osType
        self.username = username
        self.password = password

    def get_entry(self):
        return {'vmname': self.vmname, 'basename': self.basename, 
            'osType': self.osType, 'username': self.username, 
            'password': password}

    def cleanup(self):
        return False

    def to_xml(self):
        return toXML(self, nodeName="VM Properties")

class LogInterface():
    """This is just an example, of the logging class interface

    every logger needs to implement this interface"""
    def __init__(self, arg):
        self.arg = arg

    def get_entry(self):
        return {'arg': self.arg}

    def cleanup(self):
        """return a path on the host, where data needs to be deleted or False
        """
        return False

    def to_xml(self):
        return toXML(self, nodeName="LogInterface")
        

class Logger():
    """A simple logger for fopybox

    This logger creates a protocol of actions performed with pyvbox, that altered
    the virtual machine image. If wished, a xml-export is available with get_log

    """

    def __init__(self):
        self.log = []

    def add_vm(self, *args):
        self.log.append(LogVM(*args))

    def add_process(self, *args):
        self.log.append(LogProcess(*args))

    def add_file(self, *args):
        self.log.append(LogCopiedFile(*args))

    def add_cd(self, *args):
        self.log.append(LogCdMount(*args))

    def add_keyboard(self, *args):
        self.log.append(LogRawKeyboard(*args))

    def get_log(self):
        for l in self.log:
            print etree.tostring(l.getXML(), pretty_print=True)

    def cleanup(self):
        """Gets one path, to clean up at a time

        This destroys the log, so use get_log first!
        """
        if not self.log:
            return False
        else:
            path = self.log.pop().cleanup()
            while path is False:
                path = self.log.pop().cleanup()
            return return path

        