#ForgeOSI

ForgeOSI is a wrapper for [pyvbox](https://github.com/mjdorma/pyvbox), designed to be used in the education in computer forensics. It simplifies the creation of virtual machines and their automation, while providing a log and resonable abstraction.
The automatisation of guest systems supports modern Windows Versions with Powershell 2 or newer, while any modern Linux system should be supported in theory, only Ubuntu 12.04 and Ubuntu 13.10 are tested though.

##Requirements
As host, a Linux system with VirtualBox 4.3 and the VirtualBox API is expected, Python 2.7 is required, while my software in theorie should support Python 3 as well, pyvbox has some hickups, so it is not advised.
Further more, the following Python packets are required:
* pyvbox
* decorator
* enum34

The Guest systems should be prepared with Guest Additions installed, further hints are given in the docstring documentation, standalone documentation can be generated with `pydoc fopybox.py`

##First Steps
Lets start a virtual machine, without cloning it

```
>ipython
In [1]: import fopybox

In [2]: print fopybox.VboxInfo().list_vms()
ubuntu-lts-base
xubuntu-lts-base
windows-8-base

In [3]: vbox = fopybox.Vbox(mode=fopybox.Vbox, basename='ubuntu-lts-base')

In [4]: vbox.start(session_type=fopybox.SessionType.gui)

In [5]: vbox.stop()
```

##Hacking
The basic architecture:
* _fopybox.py_
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

Feel free to extend, i will accept pull requests on a resonable base.

###Issues
Please report issues on github

###Known bugs and limitations
* Python 3 compability needs to be fixed
* Running programs in Windows guests with '-' in arguments, breaks things, be careful with that.
* Windows 
