import os
import sys
import time
import random
import hashlib
import shutil
import uuid
from lxml import etree

from vboxapi import VirtualBoxManager


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

class Process():
    def __init__(self, process):
        self.process = process
        self.readbuffer = ""
        self.writebuffer = ""

        virtualBoxManager = VirtualBoxManager(None, None)
        self.ctx = {'global': virtualBoxManager,
                    'mgr': virtualBoxManager.mgr,
                    'vb': virtualBoxManager.vbox,
                    'const': virtualBoxManager.constants,
                    'remote': virtualBoxManager.remote,
                    'type': virtualBoxManager.type,
        }


    def read(self, handle='stdout'):
        if handle == 'stdin':
            handle = 0
        if handle == 'stdout':
            handle = 1
        if handle == 'stderr':
            handle = 2

        readbuffer = self.process.read(handle, 999999999, 0)
        self.readbuffer += readbuffer
        return readbuffer

    def write(self, writebuffer, handle='stdin', timeout=1000):
        if handle == 'stdin':
            handle = 0
        if handle == 'stdout':
            handle = 1
        if handle == 'stderr':
            handle = 2

        try:
            self.process.write(0, 1, writebuffer, timeout)
        except:
            pass
        self.writebuffer += writebuffer

    def terminate(self):
        try:
            self.process.terminate()
        except:
            pass

class copiedFile():
    """Stores a list of previously, to the VM copied Files
    Depends on toXML
    """
    def __init__(self, source, destination, timeoffset=0, timeRate=100, upTime=0):
        self.source = self.setSource(source)
        self.destination = self.setDestination(destination)
        self.tmp = self.copyToTemp()
        self.md5Sum = self.calcMd5Sum()
        self.sha256sum = self.calcSha256Sum()
        self.filesize = self.getFileSize()
        self.realtime = time.time()
        self.time = time.time() + timeoffset
        self.timeRate = timeRate
        self.upTime = upTime

    def setSource(self, source):
        return source

    def setDestination(self, destination):
        return destination

    def getFileSize(self):
        filesize = os.path.getsize(self.tmp)
        return filesize

    def copyToTemp(self):
        tmp = '/tmp/%s.forensig20' % str(uuid.uuid4())
        shutil.copy(self.source, tmp)
        return tmp

    def calcMd5Sum(self):
        md5 = hashlib.md5(open(self.tmp, 'rb').read()).hexdigest()
        return md5

    def calcSha256Sum(self):
        sha256 = hashlib.sha256(open(self.tmp, 'rb').read()).hexdigest()
        return sha256

    def getFile(self):
        return {'source': self.source, 'destination': self.destination, 'tmp': self.tmp, 'md5sum': self.md5Sum, 'sha256sum': self.sha256sum, 'filesize': self.filesize, 'realtime': self.realtime, 'time': self.time, 'timeRate': self.timeRate, 'upTime': self.upTime}

    def getXML(self):
        return toXML(self, nodeName="copiedFile", ignore=['time'])

class Machine():
    def __init__(self, machine, username="default", password="12345"):
        self.machine = machine
        self.username = username
        self.password = password
        virtualBoxManager = VirtualBoxManager(None, None)
        self.ctx = {'global': virtualBoxManager,
                    'mgr': virtualBoxManager.mgr,
                    'vb': virtualBoxManager.vbox,
                    'const': virtualBoxManager.constants,
                    'remote': virtualBoxManager.remote,
                    'type': virtualBoxManager.type,
        }
        self.vbox = self.ctx['vb']
        self.session = self.ctx['mgr'].getSessionObject(self.vbox)
        #self.machine.lockMachine(self.session, 1)
        self.processes=[]
        self.guestSessionExist = False
        self.copiedFiles = []
        #self.bios = self.session.machine.BIOSSettings

    def stat(self):
        print 'Files:'
        for f in self.copiedFiles:
            print etree.tostring(f.getXML(), pretty_print=True)

    def copyTo(self, source, destination):
        self.copiedFiles.append(copiedFile(source, destination))
        progress = self.guestSession.copyTo(source, destination, [])
        self.__progressBar(progress, 1000)

    def copyFrom(self, source, destination):
        print "copyFrom not implemented correctly"
        progress = self.guestSession.copyFrom(source, destination, [self.ctx['global'].constants.CopyFileFlag_None])
        #self.__progressBar(progress, 1000)

    def directoryCreate(self, path, mode):
        self.guestSession.directoryCreate(path, mode, self.ctx['global'].constants.DirectoryCreateFlag_Parents)

    def directoryRemove(self, path):
        self.guestSession.directoryRemove(path)

    def directoryRemoveRecursive(self, path):
        progress = self.guestSession.directoryRemove(path, [self.ctx['global'].DirectoryRemoveRecFlag_ContentAndDir])
        self.__progressBar(progress, 1000)

    def directoryRename(self, source, destination):
        self.guestSession.directoryRename(source, destination, [self.ctx['global'].constants.PathRenameFlag_Replace])

    def directoryExists(self, path):
        exists = self.guestSession.directoryExists(path)
        return exists

    def fileExists(self, path):
        exists = self.guestSession.fileExists(path)
        return exists

    def fileRemove(self, path):
        self.guestSession.fileRemove(path)

    def fileRename(self, source, destination):
        self.guestSession.fileRename(source, destination, [self.ctx['global'].constants.PathRenameFlag_Replace])

    def lock(self):
        self.session = self.ctx['mgr'].getSessionObject(self.vbox)
        self.machine.lockMachine(self.session, 1)
        self.console = self.session.console
        self.guest = self.session.console.guest
        self.debugger = self.console.debugger
        if not self.guestSessionExist:
            try:
                self.guestSession = self.guest.createSession(self.username, self.password, "", "GuestSession")
                self.guestSessionExist = True
            except:
                print "Guestsession not created"
                pass

    def timeOffset(self, time):
        self.lock()
        self.session.machine.BIOSSettings.timeOffset = time * 1000
        self.session.machine.saveSettings()
        self.unlock()

    def traceNetwork(self):
        self.lock()
        self.network = self.session.machine.getNetworkAdapter(0)
        self.network.traceFile = '/tmp/trace-%s.pcap' % (random.randint(10000, 1000000))
        self.network.traceEnabled = True
        self.session.machine.saveSettings()
        self.unlock()

    def videoCapture(self, path="/tmp/video"):
        self.lock()
        self.session.machine.videoCaptureFile = path
        self.session.machine.videoCaptureEnabled = True
        self.session.machine.saveSettings()
        self.unlock()

    def syntheticCPU(self):
        """Intended to allow live migration from one VM-host to another one"""
        self.lock()
        self.session.machine.setCPUProperty(self.ctx['global'].constants.CPUPropertyType_Synthetic, True)
        self.session.machine.saveSettings()
        self.unlock()

    def virtualTimeRate(self, percent):
        """sets the percentage, with which the time in the VM runs, relative to the host clock (realtime)"""
        self.debugger.virtualTimeRate = percent

    def unlock(self):
        self.session.unlockMachine()

    def delete(self):
        try:
            self.session.unlockMachine()
        except:
            pass

        medium = self.machine.unregister(self.ctx['global'].constants.CleanupMode_Full)
        self.machine.deleteConfig(medium)

    def getMachine(self):
        return self.machine

    def clone(self, nameOrUUIDClone, linked=True, linkedName="Forensig20Linked"):
        self.lock()
        clone = self.__createMachine(nameOrUUIDClone)
        if linked:
            try:
                snap = self.machine.findSnapshot(linkedName)
            except:
                snap = self.takeSnapshot(linkedName, "")

            #self.ctx['global'].constants.CloneOptions_Link,
            progress = snap.machine.cloneTo(clone, self.ctx['global'].constants.CloneMode_MachineState, [self.ctx['global'].constants.CloneOptions_Link])
        else:
            progress = self.machine.cloneTo(clone, self.ctx['global'].constants.CloneMode_MachineState, [])
        self.__progressBar(progress, 1000)
        self.ctx['vb'].registerMachine(clone)
        self.unlock()
        return clone

    def takeSnapshot(self, name, description):
        self.lock()
        progress = self.console.takeSnapshot(name, description)
        self.__progressBar(progress, 1000)
        snap = self.machine.findSnapshot(name)
        self.unlock()
        return snap

    def __createMachine(self, name, osType="Linux26"):
        machine = self.vbox.createMachine("", name, [], osType, "")
        return machine

    def start(self, type="headless", environment=""):
        progress = self.machine.launchVMProcess(self.session, type, environment)
        self.__progressBar(progress, 1000)
        self.lock()
        self.unlock()


    def stop(self):
        self.lock()
        progress = self.console.powerDown()
        self.__progressBar(progress, 1000)
        self.unlock()

    def launchProcess(self, command, options=[], username="default", password="12345"):
        self.lock()
        flag = [self.ctx['global'].constants.ProcessCreateFlag_WaitForStdOut]
#        flag = [self.ctx['global'].constants.ProcessCreateFlag_WaitForProcessStartOnly]
        process = self.guestSession.processCreate(command, options, [], flag, 0)
        process = Process(process)
        self.processes.append(process)
        self.unlock()
        return process

    def __progressBar(self, p, wait=1000, pid=False, retries=3600):
        try:
            old_percent = -1
            while retries > 0 and not p.completed:
                if pid:
                    data = self.session.console.guest.getProcessOutput(pid, 0, wait, 1024)
                    error = self.session.console.guest.getProcessOutput(pid, 1, wait, 1024)
                    (exitcode, flags, reason) = self.session.console.guest.getProcessStatus(pid)
                    if data is not None:
                        sys.stdout.write("STDOUT:\n")
                        for d in data:
                            sys.stdout.write(str(d))
                    if error is not None:
                        sys.stdout.write("\n\nSTDERR:\n")
                        for e in error:
                            sys.stdout.write(str(e))
                    sys.stdout.write(
                        "exitcode: " + str(exitcode) + " flags: " + str(flags) + " reason: " + str(reason) + "\n")
                    sys.stdout.flush()
                if p.percent > old_percent:
                    old_percent = p.percent
                    sys.stdout.write("%s%%..." % (str(p.percent)))
                    sys.stdout.flush()
                p.waitForCompletion(wait)
                retries -= 1
            if retries == 0:
                if p.cancelable:
                    print "Canceling task..."
                    p.cancel()
                raise AutoitDidNotFinishError()
            print "%s %%\r" % (str(p.percent))
            if int(p.resultCode) != 0:
                print p.resultCode
                print p.errorInfo.text
            return 1
        except KeyboardInterrupt:
            print "Interrupted."
            if p.cancelable:
                print "Canceling task..."
                p.cancel()
            raise TaskCanceledError()
            return 0



class VboxControl():
    """Main Class for the VboxControl
    Depends on vboxapi and Machine
    """
    def __init__(self):
        self.api_version = 2
        virtualBoxManager = VirtualBoxManager(None, None)
        self.ctx = {'global': virtualBoxManager,
                    'mgr': virtualBoxManager.mgr,
                    'vb': virtualBoxManager.vbox,
                    'const': virtualBoxManager.constants,
                    'remote': virtualBoxManager.remote,
                    'type': virtualBoxManager.type,
        }
        self.session = self.ctx['mgr'].getSessionObject(self.ctx['vb'])
        self.machines = {}

    def getMachine(self, nameOrUUID):
        vbox = self.ctx['vb']
        machine = vbox.findMachine(nameOrUUID)
        return machine
