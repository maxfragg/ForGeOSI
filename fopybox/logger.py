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

    def to_xml(self):
        return toXML(self, nodeName="copiedFile", ignore=['time'])



class LogProcess():
	"""Stores data of a single process, running in the VM

	"""
	def __init__(self, process, arguments, timeoffset=0, timeRate=0, upTime=0):
		self.process = process
		self.arguments = arguments
		self.realtime = time.time()
		self.time = time.time() + timeoffset
		self.timeRate = timeRate
		self.upTime = upTime

	def get_entry(self):
		return {'process': self.process, 'arguments': self.arguments, 
			'realtime': self.realtime, 'time': self.time, 
			'timeRate': self.timeRate, 'upTime': self.upTime}

	def to_xml(self):
		return toXML(self, nodeName="process",ignore=['time'])

class Logger():
	"""A simple logger for fopybox

	This logger creates a protocol of actions performed with pyvbox, that altered
	the virtual machine image. If wished, a xml-export is available.

	"""

	def __init__(self):
		self.log = []

	def append_process(self, *args):
		self.log.append(LogProcess(*args))

	def append_file(self, *args):
		self.log.append(LogCopiedFile(*args))

	def get_log(self):
	 	for l in self.log:
            print etree.tostring(l.getXML(), pretty_print=True)

		