#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

#python 2 compatibility
from __future__ import print_function

import time
import shutil
import uuid
import hashlib
import os
from lxml import etree


IGNORE = ['time', 'up_time', 'time_rate', 'real_time', 'process', 'pid']
"""Ignore time output to enable easier comparison of multiple runs
"""


def object_to_xml(class_element, **kwargs):
    """creates a xml representation of a given object
    """
    if 'nodeName' in kwargs:
        node_name = kwargs['nodeName']
    else:
        node_name = "Node"

    if 'ignore' in kwargs:
        ignore = kwargs['ignore']
    else:
        ignore = []

    node = etree.Element(node_name)
    for i in class_element.__dict__:
        if i not in ignore:
            xml = etree.Element(i)
            xml.text = str(class_element.__dict__[i])
            node.append(xml)
    return node


class LogCopiedFile():
    """Stores data of a single file, copied to the VM
    """
    def __init__(self, source, destination, time_offset=0, time_rate=100,
                 up_time=0):
        self.source = source
        self.destination = destination
        self.tmp = self.copy_to_temp()
        self.md5sum = self.calc_md5sum()
        self.sha256sum = self.calc_sha256sum()
        self.filesize = self.get_file_size()
        self.real_time = time.time()
        self.time = time.time() + time_offset
        self.time_rate = time_rate
        self.up_time = up_time

    def get_file_size(self):
        """local file size to compare to file size in vm
        """
        filesize = os.path.getsize(self.tmp)
        return filesize

    def copy_to_temp(self):
        """copy file to temp for later usage
        """
        tmp = '/tmp/%s.forensig20' % str(uuid.uuid4())
        shutil.copy(self.source, tmp)
        return tmp

    def calc_md5sum(self):
        """calculates md5sum of file
        """
        return hashlib.md5(open(self.tmp, 'rb').read()).hexdigest()

    def calc_sha256sum(self):
        """calculates sha256sum of file
        """
        return hashlib.sha256(open(self.tmp, 'rb').read()).hexdigest()


    def get_entry(self):
        return {'source': self.source, 'destination': self.destination,
                'tmp': self.tmp, 'md5sum': self.md5sum,
                'sha256sum': self.sha256sum, 'filesize': self.filesize,
                'real_time': self.real_time, 'time': self.time,
                'time_rate': self.time_rate, 'up_time': self.up_time}

    def cleanup(self):
        """cleanup copy of file
        """
        return self.tmp

    def to_xml(self):
        return object_to_xml(self, nodeName="copiedFile", ignore=IGNORE)


class LogCdMount():
    """Stores data about a cd mounted to the VM
    """
    def __init__(self, path, delete=False, time_offset=0, time_rate=0,
                 up_time=0):
        self.path = path
        self.delete = delete
        self.real_time = time.time()
        self.time = time.time() + time_offset
        self.time_rate = time_rate
        self.up_time = up_time

    def get_entry(self):
        return {'path': self.path, 'real_time': self.real_time,
                'time': self.time, 'time_rate': self.time_rate,
                'up_time': self.up_time}

    def cleanup(self):
        """clean up only generated cd images
        """
        if self.delete:
            return self.path
        else:
            return False

    def to_xml(self):
        return object_to_xml(self, nodeName="cd", ignore=IGNORE)


class LogEncodedCommand():
    """Stores readable version off the encodedCommand
    """
    def __init__(self, args):
        self.args = args

    def get_entry(self):
        return {'arg': self.args}

    def cleanup(self):
        """return a path on the host, where data needs to be deleted or False
        """
        return False

    def to_xml(self):
        return object_to_xml(self, nodeName="ReadableArg")


class LogProcess():
    """Stores data of a single process, running in the VM
    """
    def __init__(self, process, path, arguments, stdin='', key_input='',
                 stdout='', stderr='', pid=0, time_offset=0, time_rate=0,
                 up_time=0):
        self.process = process
        self.path = path
        self.arguments = arguments
        self.stdin = stdin
        self.key_input = key_input
        self.stdout = stdout
        self.stderr = stderr
        self.pid = pid
        self.real_time = time.time()
        self.time = time.time() + time_offset
        self.time_rate = time_rate
        self.up_time = up_time

    def get_entry(self):
        return {'process': self.process, 'path': self.path,
                'arguments': self.arguments, 'stdin': self.stdin,
                'key_input': self.key_input, 'stdout': self.stdout,
                'stderr': self.stderr, 'pid': self.pid,
                'real_time': self.real_time, 'time': self.time,
                'time_rate': self.time_rate, 'up_time': self.up_time}

    def cleanup(self):
        return False

    def to_xml(self):
        return object_to_xml(self, nodeName="process", ignore=IGNORE)


class LogRawKeyboard():
    """Stores raw keyboard input
    """
    def __init__(self, key_input, time_offset=0, time_rate=0, up_time=0):
        self.key_input = key_input
        self.real_time = time.time()
        self.time = time.time() + time_offset
        self.time_rate = time_rate
        self.up_time = up_time

    def get_entry(self):
        return {'keyboard input': self.key_input, 'real_time': self.real_time,
                'time': self.time, 'time_rate': self.time_rate,
                'up_time': self.up_time}

    def cleanup(self):
        return False

    def to_xml(self):
        return object_to_xml(self, nodeName="keyboard_input", ignore=IGNORE)


class LogMouse():
    """Stores raw mouse input
    """
    def __init__(self, x, y, lmb, mmb, rmb, time_offset=0, time_rate=0,
                 up_time=0):
        self.x = x
        self.y = y
        self.lmb = lmb
        self.mmb = mmb
        self.rmb = rmb
        self.real_time = time.time()
        self.time = time.time() + time_offset
        self.time_rate = time_rate
        self.up_time = up_time

    def get_entry(self):
        return {'x': self.x, 'y': self.y, 'left mouse button': self.lmb,
                'middle mouse button': self.mmb, 'right mouse button': self.rmb,
                'real_time': self.real_time, 'time': self.time,
                'time_rate': self.time_rate, 'up_time': self.up_time}

    def cleanup(self):
        return False

    def to_xml(self):
        return object_to_xml(self, nodeName="mouse_input", ignore=IGNORE)


class LogVM():
    """saves general properties of one VM"""
    def __init__(self, vmname, basename, os_type):
        self.vmname = vmname
        self.basename = basename
        self.os_type = os_type

    def get_entry(self):
        return {'vmname': self.vmname, 'basename': self.basename,
                'os_type': self.os_type}

    def cleanup(self):
        return False

    def to_xml(self):
        return object_to_xml(self, nodeName="vm")


class LogWarning():
    """Generic warnings, be careful, if any of those appear"""
    def __init__(self, warning, verbose=True):
        self.warning = warning
        if verbose:
            print(warning)

    def get_entry(self):
        return {'warning': self.warning}

    def cleanup(self):
        return False

    def to_xml(self):
        return object_to_xml(self, nodeName="warning")


class _LogInterface():
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
        return object_to_xml(self, nodeName="log_interface")


class Logger():
    """A simple logger for ForGeOSI

    This logger creates a protocol of actions performed with pyvbox, that
    altered the virtual machine image. XML-export is available with
    get_xml_log, get_structured_xml_log and write_xml_log.
    """

    def __init__(self):
        self.log = []

    def add_vm(self, *args, **kwargs):
        """Add vm entry to log, required
        """
        self.log.append(LogVM(*args, **kwargs))

    def add_process(self, *args, **kwargs):
        """add process entry to log
        """
        self.log.append(LogProcess(*args, **kwargs))

    def add_file(self, *args, **kwargs):
        """add file entry to log
        """
        self.log.append(LogCopiedFile(*args, **kwargs))

    def add_cd(self, *args, **kwargs):
        """add cd entry to log
        """
        self.log.append(LogCdMount(*args, **kwargs))

    def add_keyboard(self, *args, **kwargs):
        """add keyboard input entry to log
        """
        self.log.append(LogRawKeyboard(*args, **kwargs))

    def add_mouse(self, *args, **kwargs):
        """add mouse input entry to log
        """
        self.log.append(LogMouse(*args, **kwargs))

    def add_encoded_command(self, *args, **kwargs):
        """add readable version of encoded commands entry to log
        """
        self.log.append(LogEncodedCommand(*args, **kwargs))

    def add_warning(self, *args, **kwargs):
        """adds warning entry to the log
        """
        self.log.append(LogWarning(*args, **kwargs))

    def get_pid(self, path=''):
        """Find the PID of a previously started process based on the path

        Returns a list of all found pids matching the path, or all pids, if no
        path was given
        """
        pids = []
        for l in self.log:
            if isinstance(l, LogProcess):
                if path in l.path:
                    pids.append(l.pid)
        return pids


    def get_warnings(self):
        """Fast way to check for warnings
        """
        warn = ''
        for l in self.log:
            if isinstance(l, LogWarning):
                warn += (l.warning)+'\n'
        return warn


    def get_xml_log_by_type(self, logtype):
        """Fast way to check for entry of one type

        Arguments:
            logtype - type of log entry
        """

        partial_log = []
        for l in self.log:
            if isinstance(l, logtype):
                partial_log.append(l.to_xml())
        return partial_log


    def get_log_object_by_type(self, logtype):
        """Gets all log objects of one type

        Arguments:
            logtype - type of log entry
        """
        ret = []
        for l in self.log:
            if isinstance(l, logtype):
                ret.append(l)
        return ret


    def get_xml_log(self):
        """Returns XML representation of the log

        in the original order of actions
        """
        ret = "<log>\n"
        for l in self.log:
            ret += etree.tostring(l.to_xml(), pretty_print=True)
        return ret + "</log>\n"


    def get_pretty_log(self):
        """Returns human readable log
        """
        ret = ""
        for l in self.log:
            ret += l.__class__.__name__+":\n"
            entry = l.get_entry()
            for key in entry:
                ret += "\t"+key+": "+str(entry[key]).encode('string-escape')+"\n"
        return ret


    def get_structured_xml_log(self):
        """Returns XML representation of the log

        actions are grouped by type
        """
        root = self.get_xml_log_by_type(LogVM)[0]

        elements = {'processes': LogProcess, 'cdmounts': LogCdMount,
                    'copiedfile': LogCopiedFile,
                    'encodedcommands': LogEncodedCommand, 'mice': LogMouse,
                    'keyboards': LogRawKeyboard, 'warnings': LogWarning}

        for log_type in elements:
            node = etree.Element(log_type)
            empty = True
            for subnode in self.get_xml_log_by_type(elements[log_type]):
                if subnode is not None:
                    empty = False
                node.append(subnode)
            if not empty:
                root.append(node)

        return etree.tostring(root, pretty_print=True)


    def write_xml_log(self, path):
        """Writes the xml formated log to a file
        """
        f = open(path, 'wb')
        f.write(self.get_xml_log())


    def cleanup(self):
        """Gets one path, to clean up at a time

        Call sequencial untill it returns false to clear the full log
        This destroys the log, so use get_log or write_log first!
        """
        if not self.log:
            return False
        else:
            if len(self.log) is 0:
                return False
            path = self.log.pop().cleanup()
            while path is False and len(self.log) > 0:
                path = self.log.pop().cleanup()
            return path
