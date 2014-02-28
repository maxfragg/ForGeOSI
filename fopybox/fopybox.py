#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

import virtualbox #pyvbox
import os
import subprocess
import logger #local import
import oslinux #local import
import oswindows #local import
import shutil
import time
#needs python-decorator, needed for signature preserving decorators
from decorator import decorator 

__doc__ = """\
This library should simplify automating the control of virtual machines with
VirtualBox, specifically for the use in computer forensics, but it might be useful
else where too.

To work properly, it expects a prepared VirtualBox image to start with. To 
create a working image, a correct set osType is important, since all Vbox.os 
functions rely on this to be OS specific. Next, the Guest Additions need to be 
installed in the VM and the keyboard layout needs to match the one, of the host 
PC, otherwise keyboard input might not match expectations.
osLinux and osWindows both have special additional requirements, which are 
described in Vbox.os

The VM host system needs to be a Linux system for some things, since it uses 
genisoimage and relies on "/tmp/" being a valid path on the host.

"""

usertoken=""
"""this token is added to user-strings to separate users from each other, use 
empty string for no separation
"""

class VboxInfo():
    """Helper class, not changing machine state

    Those functions are meant to get information about the whole virtualbox state
    and not limited to a single machine like the Vbox class and need no running VM
    """
    def __init__(self):
        self.vb = virtualbox.VirtualBox()


    def list_vms(self):
        """Lists all VMs that are registered in VirtualBox
        """
        return "\n".join([vm.name for vm in self.vb.machines])


    def list_ostypes(self):
        """Lists all osTypes, that the local VirtualBox accepts
        """
        return "\n".join([os.id_p for os in self.vb.guest_os_types])


class VboxConfig():
    """helper class, changing global state!

    """
    def __init__(self):
        self.vb = virtualbox.VirtualBox()
        self.net = False
        self.network_name = ""


    def get_nat_network(self, network_name="testnet"):
        """creates a nat network, if none of the name exists.
        
        This is needed to enabled networking between different VM instances
        """

        network_name = network_name + usertoken

        try:
            self.net = self.vb.find_nat_network_by_name(network_name)
            self.dhcp = self.vb.find_dhcp_server_by_network_name(network_name)
                
        except:
            self.net = vb.create_nat_network(network_name)
            self.dhcp = vb.create_dhcp_server(network_name)

        self.net.enabled = True
        self.network_name = network_name
        return self.net


    def get_network_name(self):
        return self.network_name


@decorator
def check_running(func, *args, **kwargs):
    """decorator for use inside Vbox class only!
    """
    if not args[0].running:
        print "Machine needs to be running"
        return
    func(*args, **kwargs)


@decorator
def check_stopped(func, *args, **kwargs):
    """decorator for use inside Vbox class only!
    """
    if args[0].running:
        print "Machine needs to be stopped"
        return
    func(*args, **kwargs)


@decorator
def check_guestsession(func, *args, **kwargs):
    """decorator for use inside Vbox class only!
    """
    if not args[0].guestsession:
        print "needs guestsession"
        return
    func(*args, **kwargs)   


class Vbox():
    """base class for controlling VirtualBox

    This implements all operating system independent methods.
    Any method accepting an optional argument "wait" may return a progress object, 
    to enable the user to wait, if "wait=False" is passed to it. If this happens,
    the machine might also stay in locked state!
    """
    
    def __init__(self, basename="ubuntu-lts-base",
            clonename="testvm", mode="clone", linkedName="Forensig20Linked",
            wait=True):
        """Initialises a virtualbox instance

        The new instance of this class can either reuse an existing virtual 
        machine or create a new one, based on a existing template. The concepts
        of sessions and machines are not exposed to the user

        Arguments:
            basename - must be in VboxInfo.list_vms()
            mode - must be "use" or "clone"
            wait - Setting wait to False enables async actions, but might break 
                things, use with care!
        """

        self.vb = virtualbox.VirtualBox()

        if mode=="clone":

            _orig = self.vb.find_machine(basename)
            _orig_session = _orig.create_session()

            self.vm = self.vb.create_machine("",clonename,[], _orig.os_type_id,"")

            try:
                _snap = _orig.find_snapshot(linkedName)
            except:
                #_orig.lock_machine(_orig_session,virtualbox.library.LockType.shared)

                self.progress = _orig_session.console.take_snapshot(linkedName, "")
                self.progress.wait_for_completion()
                _snap = _orig.find_snapshot(linkedName)
                #_orig_session.unlock_machine()    

            self.progress =  _snap.machine.clone_to(
                    self.vm,virtualbox.library.CloneMode.machine_state,
                    [virtualbox.library.CloneOptions.link])
            
            if wait:
                self.progress.wait_for_completion()

            self.vb.register_machine(self.vm)
            self.is_clone=True
        elif mode=="use":
            self.vm = self.vb.find_machine(basename)
            self.osType = self.vm.os_type_id

        self.session = self.vm.create_session()
        self.guestsession = False
        self.basename = basename
        self.running = False

        self.log = logger.Logger()
        self.log.add_vm(clonename, basename, self.osType)


    @check_stopped  
    def start(self, type="headless", wait=True):
        """start a machine

        Arguments:
            type - "headless" means, the machine runs without any gui, the only 
                sensible way on a remote server. This parameter is changeable to 
                "gui" for debugging only
            wait - waits till the machine is initialized, it will not have 
                finished booting yet. 
        """

        self.unlock()

        self.progress = self.vm.launch_vm_process(self.session, type, '')

        self.running = True

        if wait:
            self.progress.wait_for_completion()
            while (self.session.console.guest.additions_run_level < 2):
                time.sleep(5)
        else:
            return self.progress


    @check_running
    def stop(self, shutdown=True, wait=True):
        """Stop a running machine
        Arguments:
            shutdown - will send acpi signal to the machine
                might take some time for the machine to power down.
                Otherwise the machine will just be turned off, and its state in
                VirtualBox will be "aborted"
                Can hang, if the OS requires interaction, so try to kill all 
                applications first
        """  

        if shutdown:
            self.session.console.power_button()
            if wait:
                while (self.vm.state > 1):
                    time.sleep(5)
            self.running = False
            self.guestsession = False

        else:
            self.progress = self.session.console.power_down()
            if wait:
                self.progress.wait_for_completion()
                self.unlock()
                self.running = False
                self.guestsession = False
            else:
                self.running = False
                self.guestsession = False
                return self.progress
        


    def lock(self):
        """Locks the machine to enable certain operations

        This method should not be needed to be called form outside
        """
        try:
            self.vm.lock_machine(self.session,virtualbox.library.LockType.shared)
        except:
            pass 


    def unlock(self):
        """Unlocks the machine

        This method should not be needed to be called form outside
        """
        try:
            self.session.unlock_machine()
        except:
            pass


    @check_stopped
    def export(self, path="/tmp/disk.vdi", wait=True, controller="SATA", port=0, 
        disk=0):
        """Export a VirtualBox hard disk image

        By default, it will export the first disk on the sata controller, which 
        is usually the boot device, in the default config of virtualbox
        """

        self.lock()

        clone_hdd = self.vb.create_hard_disk("",path)
        cur_hdd = self.session.machine.get_medium(controller,port,disk)
        #TODO: support vmdk_raw_disk as well?
        progress = cur_hdd.clone_to_base(clone_hdd,
            [virtualbox.library.MediumVariant.standard])

        if wait:
            progress.wait_for_completion()
            clone_hdd.close()
            self.unlock()
        else:
            return progress


    @check_running
    def take_screenshot(self, path="/tmp/screenshot.png"):
        """Save screenshot to given path
        Arguments:
            path - path, where the png image should be created
        """

        h, w, _, _, _ = self.session.console.display.get_screen_resolution(0)

        png = self.session.console.display.take_screen_shot_png_to_array(0, h, w)

        f = open(path, 'wb')
        f.write(png)


    @check_running
    def start_video(self, path="/tmp/video"):
        """Record video of VM-Screen
        """
        self.session.machine.video_capture_file = path
        self.session.machine.video_capture_enabled = True
        self.session.machine.save_settings()


    @check_running
    def stop_video(self):
        """Stop video recording
        """
        self.session.machine.video_capture_enabled = False
        self.session.machine.save_settings()


    @check_running
    def time_offset(self,offset=0):
        """Sets a time offset in seconds
        Default resets.

        Arguments:
            offset - time in seconds
        """

        self.session.machine.bios_settings.time_offset = offset * 1000


    @check_running
    def time_speedup(self,speedup=100):
        """Sets relative speed time runs in the vm

        The speedup is set in percent, valid values go from 2 to 20000 percent.
        Default resets.

        Arguments:
            speedup - relative speedup in percent
        """

        self.session.console.debugger.virtual_time_rate = speedup


    @check_running
    def start_network_trace(self, path="/tmp/trace.pcap", adapter=0):
        """Trace network traffic on a certain network adapter
        """

        self.network = session.machine.get_network_adapter(adapter)

        self.network.trace_file = path
        self.network.trace_enabled = True
        self.session.machine.save_settings()


    @check_running
    def stop_network_trace(self, adapter=0):
        """Stop network trace for one adapter
        """

        self.network = session.machine.get_network_adapter(adapter=0)

        self.network.trace_enabled = False
        self.session.machine.save_settings()


    @check_running
    def create_guest_session(self, username="default", password="12345"):
        """creates a guest session for issuing commands to the guest system

        While the VirtualBox API would support up to 256 simultaneous guest 
        sessions, here only one simultaneous guestsession is supported, if more 
        than one guestsession are needed, they need to be manged by hand.

        Arguments:
            username - username for the vm user, the session should belong to
            password - password for the vm user, the session should belong to
        """

        self.username = username
        self.password = password

        self.guestsession = self.session.console.guest.create_session(self.username,self.password)

        #use vm property to find systemtype
        #we create the self.os at this point, because it needs a running guest
        #session anyway, this prevents if form being used before this exists
        if self.osType in ["Linux26","Linux26_64","Ubuntu","Ubuntu_64"]:
            self.os = oslinux.osLinux(self)
        elif self.osType in  ["Windows7","Windows7_64","Windows8","Windows8_64"
                ,"Windows81","Windows81_64"]:
            self.os = oswindows.osWindows(self)


    @check_running
    def mount_folder_as_cd(self, folder_path, iso_path="/tmp/cd.iso" ,cdlabel="MyCD"):
        """Creates a iso-image based on directory and mounts it to the VM

        If the operating system inside the vm does no automounting, further 
        action will be needed. For Ubuntu and Windows, the files should be 
        accessible without further action.
        Depends on mkisofs from genisoimage, should be installed by default on 
        ubuntu hosts

        Arguments
            folder_path - path to the folder, which's content should be inside the 
                image
            iso_path - path, where the iso image should be created
            cdlabel - label, which will be shown inside the vm
        """

        #basic sanity check
        if os.path.exists(iso_path) == False:
            return

        args = ["-J", "-l", "-R", "-V", cdlabel, "-iso-level", "4" ,"-o ",
            folder_path, iso_path]

        subprocess.call(["mkisofs"]+args)

        self.session.machine.mount_medium("IDE",0,0,iso_path,False)

        self.log.add_cd(iso_path,True)


    @check_running
    def mount_cd(self,path):
        """mounts an iso image to the VM
        """

        self.session.machine.mount_medium("IDE",0,0,path,False)
        self.log.add_cd(path)


    @check_running
    def umount_cd(self):
        """Removes a cd from the emulated IDE CD-drive
        """

        self.session.machine.mount_medium("IDE",0,0,"",False)


    @check_running
    @check_guestsession
    def run_process(self, command, arguments=[], stdin='', key_input='',
            environment=[], native_input=False,
            timeout=0, wait_time=10, wait=True):
        """Runs a process with arguments and stdin in the VM

        This method requires the VirtualBox Guest Additions to be installed.

        Arguments:
            command - full path to the binary, that should be executed
            arguments - arguments passed to the binary, passed as an array of 
                single arguments
            stdin - this is send to the stdin of the 
                process after its creation
            key_input - this is send to the process as keyboard input
            environment - user environment for the program, important on linux, 
                because otherwise user processes have the environment of root
            native_input - decides, if the virtualbox keyboard input or 
                alternative methods will be used. If available, OS native input
                methods should be preferred, and virtualbox should only be used, 
                if no alternative is available 
            timeout - This is a timeout in milliseconds, which determines, when 
                the process will be killed, 0 will disable the timeout
            wait_time - time to wait, until input is send via keyboard, only 
                relevant in combination with wait=False/keyinput
            wait - selects if the process should be created synchronous with input 
                or if this function will return, while the process inside the VM
                is still running
        """

        #since stdin is broken:
        stdin=""

        if wait and not key_input:
            process, stdout, stderr = self.guestsession.execute(command=command, 
            arguments=arguments, stdin=stdin, environment=environment, 
            timeout_ms=timeout)

        else:
            flags=[virtualbox.library.ProcessCreateFlag.wait_for_process_start_only,
                   virtualbox.library.ProcessCreateFlag.ignore_orphaned_processes]

            process = self.guestsession.process_create(command=command, 
                arguments=arguments, environment=environment, flags=flags,
                timeout_ms = timeout)

            if key_input:
                time.sleep(wait_time)
                if native_input:
                    time.sleep(5)
                    self.os.keyboard_input(key_input=key_input, pid=process.pid)
                else:
                    self.keyboard_input(key_input=key_input)

            if wait:
                process.wait_for(2, 10000) #virtualbox.library.ProcessWaitForFlag.terminate

            stdout = ""
            stderr = ""


        self.log.add_process(process, command ,arguments, stdin, key_input, stdout, stderr, process.pid)

        return stdout, stderr


    @check_running
    @check_guestsession
    def make_dir(self,directory):
        """Creates a directory and all intermediate ones

        use os specific ones over this command!
        """
        self.guestsession.makedirs(directory)


    @check_running
    @check_guestsession
    def copy_to_vm(self, source, dest, wait=True):
        """Copy a file form outside into the VM

        This leaves no plausible trace for faking, so use with care
        """

        progress = self.guestsession.copy_to_vm(source, destination, [])

        self.log.add_file(source=source, destination=dest)

        if wait:
            progress.wait_for_completion()
        else:
            return progress

    def copy_from_vm(self, source, dest, wait=True):
        """Copy a file from the VM to the host, creates no log, since it should
        not alter the guest
        """

        progress = self.guestsession.copy_from(source, destination)

        if wait:
            progress.wait_for_completion()
        else:
            return progress

    @check_running
    def keyboard_input(self, key_input):
        """sends raw keypresses to the vm

        avoid this method, as result tends to be unreliable.
        Needs no Guest Additions
        """

        self.session.console.keyboard.put_keys(key_input)

        self.log.add_keyboard(key_input)


    @check_running
    def keyboard_scancodes(self, scancode=[], make_code=True, break_code=True):
        """sends scancodes to the vm

        avoid this method, as result tends to be unreliable

        uses short names for scancodes as strings or single charakters.
        Example:
            ['win','r'] will send windows+r 

        Needs no Guest Additions

        Arguments:
            scancode - List of scancodes or chars
            make_code - send the keypress
            break_code - send the keyrelease
        """
        make_codes={'win': [0xE0, 0x5B], 'esc': [0x01], 'bksp': [0x0E], 
            'ctrl': [0x1D], 'alt': [0x38], 'del': [0xE0, 0x53], 'tab': [0x0F], 
            'enter': [0x1C], 'up': [0xE0, 0x48], 'left':[0xE0, 0x4B],
            'right': [0xE0 ,0x4D], 'down': [0xE0, 0x50],
            'F1': [0x3B], 'F2': [0x3C], 'F3': [0x3D], 'F4': [0x3E], 'F5': [0x3F],
            'F6': [0x40], 'F7': [0x41], 'F8': [0x42], 'F9': [0x43], 
            'F10': [0x44], 'F11': [0x57], 'F12': 0x58}

        break_codes={'win': [0xE0, 0xDB], 'esc': [0x81], 'bksp': [0x8E], 
            'ctrl': [0x9D], 'alt': [0xB8],'del': [ 0xE0, 0xD3], 'tab': [0x8F], 
            'enter': [0x9C], 'up': [0xE0, 0xC8], 'left':[0xE0, 0xCB],
            'right': [0xE0 ,0xCD], 'down': [0xE0, 0xD0],
            'F1': [0xBB], 'F2': [0xBC], 'F3': [0xBD], 'F4': [0xBE], 'F5': [0xBF],
            'F6': [0xC0], 'F7': [0xC1], 'F8': [0xC2], 'F9': [0xC3], 
            'F10': [0xC4], 'F11': [0xD7], 'F12': 0xD8}

        if make_code:
            for s in scancode:
                if s in make_codes:
                    #the api only likes baseintegers, but hex codes are, what everybody
                    #uses for make/break codes
                    self.session.console.keyboard.put_scancodes([int(x) for x in make_codes[s]])
                    self.log.add_keyboard("makecode: "+str(s))
                else:
                    #if its not in the list, assume, that it is a normal char/num
                    self.keyboard_input(s)

        if break_code:
            for s in scancode:
                if s in break_codes:
                    self.session.console.keyboard.put_scancodes([int(x) for x in break_codes[s]])
                    self.log.add_keyboard("breakcode: "+str(s))


    @check_running
    def mouse_input(self, x, y, lmb=1, mmb=0, rmb=0, release=True):
        """sends raw mouse movements and clicks to the vm

        avoid this method, as result tends to be unreliable

        Arguments:
            x - absolute x-Coordinate starting form the left
            y - absolute y-Coordinate starting form the top
            lmb - state of the left mouse button, 1 pressed, 0 unpressed
            mmb - state of the middle mouse button, 1 pressed, 0 unpressed
            rmb - state of the right mouse button, 1 pressed, 0 unpressed
            release - releases the mouse button, only triggering one click
        """

        buttonstate = lmb + (2 * rmb) + (4 * mmb)

        self.session.console.mouse.put_mouse_event_absolute(x,y,0,0,buttonstate)
        if release:
            self.session.console.mouse.put_mouse_event_absolute(x,y,0,0,0)

        self.log.add_mouse(x, y, lmb, mmb, rmb)


    @check_running
    def add_to_nat_network(self, network_name="test_net", adapter=0):
        """Adds the vm to a nat-network

        This enables multiple virtual machines to see each other and exchange 
        data. The network has to be created first with 
        VboxConfig.get_nat_network(). Using adapter 0 will reconfigure the 
        default network adapter, use numbers 2-7 for additional adapters.
        """

        network_name = network_name + usertoken

        self.network = self.session.machine.get_network_adapter(adapter)
        self.network.nat_network = network_name
        self.network.attachment_type = virtualbox.library.NetworkAttachmentType.nat_network
        #allow VMs to see each other
        self.network.promisc_mode_policy = virtualbox.library.NetworkAdapterPromiscModePolicy.allow_network
        self.network.enabled = True
        self.session.machine.save_settings()


    @check_running
    def get_ip(self, adapter=0):
        """returns the IPv4 address of the given adapter

        Needs guest additions installed
        """

        return self.session.machine.get_guest_property_value("/VirtualBox/GuestInfo/Net/"
            +str(adapter)+"/V4/IP")


    @check_stopped
    def cleanup_and_delete(self, ignore_errors=True, rm_clone=True):
        """clean all data except, what might have been exported

        This should be the last thing to do, just to make sure, we do not clutter
        our VirtualBox.
        """
        path = self.log.cleanup()
        while path is not False:
            shutil.rmtree(path, ignore_errors)
            path = self.log.cleanup()

        #for clones we also remove the vm data of the clone and the
        #hdd, to not clutter
        if self.is_clone and rm_clone:
            hdd = self.vm.remove()
            #if the hdd is not attached to any other vm, its save to remove it as well
            if not hdd.machine_ids:
                hdd.delete_storage()


