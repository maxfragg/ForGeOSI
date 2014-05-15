ForGeOSI
--------
![Image](http://max.fauiwg.de/forgeosi/logo256.png?raw=true)

__ForGeOSI__ is a wrapper for [pyvbox](https://github.com/mjdorma/pyvbox), designed to be used in the education in computer forensics. It simplifies the creation of virtual machines and their automation, while providing a log and reasonable abstraction.
The automation of guest systems supports modern Windows Versions with Powershell 2 or newer, while any modern Linux system should be supported in theory, only Ubuntu 12.04 and Ubuntu 13.10 are tested though.

##Requirements
As host, a Linux system with VirtualBox 4.3 and the VirtualBox API is expected, Python 2.7 is required, while my software in theory should support Python 3 as well, vboxapi has some hiccups, so it is not advised.
Further more, the following Python packets are required:
* pyvbox
* decorator
* enum34
* lxml


The Guest systems should be prepared with Guest Additions installed, further hints are given in the docstring documentation, standalone documentation can be generated with `pydoc forgeosi.py`

##First Steps
Lets start a virtual machine, without cloning it

```python
>ipython
In [1]: import forgeosi

In [2]: print forgeosi.VboxInfo().list_vms()
ubuntu-lts-base
xubuntu-lts-base
windows-8-base

In [3]: vbox = forgeosi.Vbox(mode=forgeosi.VboxMode.use, basename='ubuntu-lts-base')

In [4]: vbox.start(session_type=forgeosi.SessionType.gui)

In [5]: vbox.stop()
```

Generate input, open webbrowser, send keyboard shortcut, get log

```python
In [1]: import forgeosi

In [2]: vbox = forgeosi.Vbox(mode=forgeosi.VboxMode.use, basename='ubuntu-lts-base')

In [3]: vbox.start(session_type=forgeosi.SessionType.gui)
#top secret password
In [4]: vbox.keyboard_input('12345\n')
#needed to access os-specific and Guest Additions functionality
In [5]: vbox.create_guest_session()

In [6]: vbox.os.open_browser('github.com')

In [7]: vbox.keyboard_combination(['alt','f4'])

In [8]: vbox.stop()

In [9]: print vbox.log.get_pretty_log()
LogVM:
	osType: Ubuntu_64
	basename: ubuntu-lts-base
	vmname: testvm
LogRawKeyboard:
	time_rate: 100
	keyboard input: 12345\n
	up_time: 0
	time: 1395224126.58
	real_time: 1395224126.58
LogProcess:
	up_time: 0
	stdout: 
	process: <virtualbox.library.IGuestProcess object at 0x2a95d90>
	time_rate: 100
	pid: 1843
	key_input: 
	path: /bin/bash
	stdin: 
	arguments: [\'-c\', \'/usr/bin/firefox -new-tab github.com\']
	stderr: 
	time: 1395224228.1
	real_time: 1395224228.1
LogRawKeyboard:
	time_rate: 100
	keyboard input: makecode: alt
	up_time: 0
	time: 1395224237.56
	real_time: 1395224237.56
LogRawKeyboard:
	time_rate: 100
	keyboard input: makecode: f4
	up_time: 0
	time: 1395224237.56
	real_time: 1395224237.56
LogRawKeyboard:
	time_rate: 100
	keyboard input: breakcode: alt
	up_time: 0
	time: 1395224237.56
	real_time: 1395224237.56
LogRawKeyboard:
	time_rate: 100
	keyboard input: breakcode: f4
	up_time: 0
	time: 1395224237.56
	real_time: 1395224237.56

```

Export virtual machine
```python
In [1]: import forgeosi

In [2]: vbox = forgeosi.Vbox(mode=forgeosi.VboxMode.us, basename='ubuntu-lts-base')

In [3]: vbox.export(path='/tmp/image.vdi')
```

##Hacking
The basic architecture:
* _forgeosi.py_
	* _VboxInfo_
	  Helper to get info about the VirtualBox instance
	* _VboxConfig_
	  Helper to configure the NAT Network feature
	* _Vbox_
	  Main class containing everything generic to manage virtual machines
* _lib/logger.py_
  Logger to provide a protocol of all actions
* _lib/oslinux.py_
  Linux guest specific code
* _lib/oswindow.py_
  Windows guest specific code
* _lib/param.py_
  Types for typesave parameters

Feel free to extend, I will accept pull requests on a reasonable base, especially additions to support a wider range of guest systems are welcome. 

##Testing
There are testcases to be found __test/__, but they are not portable
and will need fixing to run on other systems. The tests further depend of following tools:
* bash
* Python 3
* The Sleuth Kit ver 4.1 or higher, including fiwalk
* idifference

###Issues
Please report issues on [github](https://github.com/maxfragg/ForgeOSI/issues)

###Documentation
Documentation can be found in __docs/__ after building with `doxygen doxygen.conf` or accessed [here](http://max.fauiwg.de/forgeosi/index.html).
Additionaly, you can find my presentation [here](http://max.fauiwg.de/forgeosi/vortrag.pdf).


###Known bugs and limitations
* Python 3 compatibility needs to be tested
* raw-disk-export in the python API is broken, I'm using vboxmanage instead
* Running programs in Windows guests with '-' in arguments, breaks things, be careful with that.
* limited support for Windows hosts
