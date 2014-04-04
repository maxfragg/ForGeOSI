#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

# python 2 compatibility
from __future__ import print_function

import virtualbox
import os
import subprocess
from lib import logger  # local import
from lib import oslinux  # local import
from lib import oswindows  # local import
from lib.param import *  # local import
import shutil
import time
from decorator import decorator


__doc__ = """\
This library should simplify automating the control of virtual machines with
VirtualBox, specifically for the use in computer forensics, but it might be
useful else where too.

To work properly, it expects a prepared VirtualBox image to start with. To
create a working image, a correct set os_type is important, since all Vbox.os
functions rely on this to be OS specific. Next, the Guest Additions need to be
installed in the VM and the keyboard layout needs to match the one, of the host
PC, otherwise keyboard input might not match expectations.
The hostname and the VM name of the base-vm also need to match for simplicity
osLinux and osWindows both have special additional requirements, which are
described in Vbox.os. Automatic login of users is strongly encouraged, even
though it is not necessary

The VM host system needs to be a Linux system for some things, since it uses
genisoimage and relies on "/tmp/" being a valid path on the host.

Dependencies:
    fopybox
    decorator
    enum34
    lxml
"""

USERTOKEN = ""
"""this token is added to user-strings to separate users from each other, use
empty string for no separation
"""


class VboxInfo():
    """Helper class, not changing machine state

    Those functions are meant to get information about the whole virtualbox
    state and not limited to a single machine like the Vbox class and need no
    running VM
    """
    def __init__(self):
        self.vb = virtualbox.VirtualBox()


    def list_vms(self):
        """Lists all VMs that are registered in VirtualBox
        """
        return "\n".join([vm.name for vm in self.vb.machines])


    def list_os_types(self):
        """Lists all os_types, that the local VirtualBox accepts
        """
        return "\n".join([os_.id_p for os_ in self.vb.guest_os_types])


class VboxConfig():
    """helper class, changing global state!

    """
    def __init__(self):
        self.vb = virtualbox.VirtualBox()
        self.net = False
        self.network_name = ""


    def get_nat_network(self, network_name="testnet"):
        """creates a nat network, if none of the name exists.

        This is needed to enable networking between different VM instances
        """

        network_name = network_name + USERTOKEN

        try:
            self.net = self.vb.find_nat_network_by_name(network_name)
            self.dhcp = self.vb.find_dhcp_server_by_network_name(network_name)

        except:
            self.net = self.vb.create_nat_network(network_name)
            self.dhcp = self.vb.create_dhcp_server(network_name)

        self.net.enabled = True
        self.dhcp.enabled = True
        self.network_name = network_name
        return self.net


    def get_network_name(self):
        """returns the networkname, that has been created for this instance
        """
        return self.network_name


@decorator
def check_running(func, *args, **kwargs):
    """decorator for use inside Vbox class only!

    ensures that the vm is running
    """
    if not args[0].running:
        print("Machine needs to be running")
        return
    return func(*args, **kwargs)


@decorator
def check_stopped(func, *args, **kwargs):
    """decorator for use inside Vbox class only!

    ensures that the vm is not running
    """
    if args[0].running:
        print("Machine needs to be stopped")
        return
    return func(*args, **kwargs)


@decorator
def check_guestsession(func, *args, **kwargs):
    """decorator for use inside Vbox class only!

    ensures that the vm has a guestsession created
    """
    if not args[0].guestsession:
        args[0].create_guest_session()

    return func(*args, **kwargs)


@decorator
def lock_if_not_running(func, *args, **kwargs):
    """decorator for use inside Vbox class only!

    locks and unlocks vm, if it is not running
    """
    if not args[0].running:
        args[0].lock()
    ret = func(*args, **kwargs)
    if not args[0].running:
        args[0].unlock()
    return ret


class Vbox():
    """base class for controlling VirtualBox

    This implements all operating system independent methods.
    Any method accepting an optional argument "wait" may return a progress
    object, to enable the user to wait, if "wait=False" is passed to it. If this
    happens, the machine might also stay in locked state!
    """

    def __init__(self, basename="ubuntu-lts-base",
                 clonename="testvm", mode=VboxMode.clone,
                 linked_name="Forensig20Linked", wait=True):
        """Initialises a virtualbox instance

        The new instance of this class can either reuse an existing virtual
        machine or create a new one, based on a existing template. The concepts
        of sessions and machines are not exposed to the user

        Arguments:
            basename - must be in VboxInfo.list_vms()
            mode - must be VboxMode.use or VboxMode.clone
            wait - Setting wait to False enables async actions, but might break
                things, use with care!
        """

        if not isinstance(mode, VboxMode):
            raise TypeError("mode must be of type VboxMode")

        self.vb = virtualbox.VirtualBox()

        if mode == VboxMode.clone:

            _orig = self.vb.find_machine(basename)
            _orig_session = _orig.create_session()

            self.vm = self.vb.create_machine("", clonename, [],
                                             _orig.os_type_id, "")

            try:
                _snap = _orig.find_snapshot(linked_name)
            except:

                self.progress = _orig_session.console.take_snapshot(linked_name,
                                                                    "")
                self.progress.wait_for_completion()
                _snap = _orig.find_snapshot(linked_name)

            self.progress = _snap.machine.clone_to(
                    self.vm,virtualbox.library.CloneMode.machine_state,
                    [virtualbox.library.CloneOptions.link])

            if wait:
                self.progress.wait_for_completion()

            self.vb.register_machine(self.vm)
            self.is_clone = True
        elif mode == VboxMode.use:
            self.vm = self.vb.find_machine(basename)
            self.is_clone = False

        self.os_type = self.vm.os_type_id

        self.session = self.vm.create_session()
        self.guestsession = None  # will be created by create_guest_session()
        self.os = None  # will be created by create_guest_session()
        self.basename = basename
        self.running = False
        self.speedup = 100
        self.offset = 0
        self.medium = False
        self.username = ""
        self.password = ""
        self.network = None  # Network will be stored here if needed

        self.log = logger.Logger()
        self.log.add_vm(clonename, basename, self.os_type)


    @check_stopped
    def start(self, session_type=SessionType.headless, wait=True):
        """start a machine

        Arguments:
            session_type - SessionType.headless means, the machine runs without
                any gui, the only sensible way on a remote server. This
                parameter is changeable to SessionType.gui for debugging only
            wait - waits till the machine is initialized, it will not have
                finished booting yet.
        """
        if not isinstance(session_type, SessionType):
            raise TypeError("session_type needs to be of type SessionType")

        self.unlock()

        self.progress = self.vm.launch_vm_process(self.session,
                                                  session_type.name, '')

        self.running = True

        if wait:
            self.progress.wait_for_completion()
            while (self.session.console.guest.additions_run_level < 2):
                time.sleep(5)
        else:
            return self.progress


    @check_running
    def stop(self, stop_mode=StopMode.shutdown, confirm=True, wait=True):
        """Stop a running machine
        Arguments:
            stop_mode - Argument of tpye StopMode, available options are:
                shutdown - will send acpi signal to the machine
                    might take some time for the machine to power down.
                    Can hang, if the OS requires interaction, so try to kill all
                    applications first
                poweroff - will virtually pull the power plug, works reliable
                    and fast, leaves vm in the state aborted
                save_state - freezes the virtual machine in its current state
            confirm - trigger an enter to confirm a shutdown dialog
        """
        if not isinstance(stop_mode, StopMode):
            raise TypeError("stop_mode needs to be of type StopMode")

        if stop_mode is StopMode.shutdown:
            self.session.console.power_button()
            if confirm:
                time.sleep(10)
                self.keyboard_input("\n")
            if wait:
                while (self.vm.state > 1):
                    time.sleep(5)
            self.running = False
            self.guestsession = False
            self.os = False

        elif stop_mode is StopMode.poweroff:
            progress = self.session.console.power_down()
            if wait:
                progress.wait_for_completion()
                self.unlock()
                self.running = False
                self.guestsession = False
                self.os = False
            else:
                self.running = False
                self.guestsession = False
                self.os = False
                return progress

        elif stop_mode is StopMode.save_state:
            progress = self.session.console.save_state()
            if wait:
                progress.wait_for_completion()
                self.running = False
                self.guestsession = False
                self.os = False
            else:
                self.running = False
                self.guestsession = False
                self.os = False
                return progress


    def lock(self):
        """Locks the machine to enable certain operations

        This method should not be needed to be called form outside
        """
        try:
            self.vm.lock_machine(self.session,
                                 virtualbox.library.LockType.shared)
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
    def export(self, path="/tmp/disk.vdi", controller=ControllerType.SATA,
               port=0, disk=0, raw=False, wait=True):
        """Export a VirtualBox hard disk image

        By default, it will export the first disk on the sata controller, which
        is usually the boot device, in the default config of virtualbox.
        This operation will take some time

        Arguments:
            path - path to the exported disk, format .vdi
            controller - controller, where the virtual drive is attached
            port - port number of the controller
            disk - disk number of the controller
            raw - if a raw or a normal vdi file should be created
        """

        if not isinstance(controller, ControllerType):
            raise TypeError("controller must be of type ControllerType")

        self.lock()

        cur_hdd = self.session.machine.get_medium(controller.name, port, disk)

        if raw:
            self.unlock()
            # the clone_to_base function is broken with this parameter
            # so as a workaround we use the shell utility vboxmanage instead
            # variant = virtualbox.library.MediumVariant.vmdk_raw_disk

            subprocess.check_output(['vboxmanage', 'clonehd', '--format',
                                     'RAW', cur_hdd.location, path])

        else:
            clone_hdd = self.vb.create_hard_disk("", path)
            variant = virtualbox.library.MediumVariant.standard
            progress = cur_hdd.clone_to_base(clone_hdd, [variant])
            if wait:
                progress.wait_for_completion()
                clone_hdd.close()
                self.unlock()
            else:
                return progress


    @check_running
    def dump_memory(self, path="/tmp/dump.elf"):
        """Creates a memory dump in 64bit elf format

        Enables analysis of non persistent data

        Arguments:
            path - path to the dump, format .elf
        """
        self.session.console.debugger.dump_guest_core(path, "")


    @check_running
    def take_screenshot(self, path="/tmp/screenshot.png"):
        """Save screenshot to given path

        Arguments:
            path - path, where the png image should be created, format .png
        """

        h, w, _, _, _ = self.session.console.display.get_screen_resolution(0)

        png = self.session.console.display.take_screen_shot_png_to_array(0, h, w)

        f = open(path, 'wb')
        f.write(png)


    @lock_if_not_running
    def start_video(self, path="/tmp/video.webm"):
        """Record video of VM-Screen

        Arguments:
            path - path to the video file on the host, format .webm
        """

        self.session.machine.video_capture_file = path
        self.session.machine.video_capture_enabled = True
        self.session.machine.save_settings()


    @lock_if_not_running
    def stop_video(self):
        """Stop video recording
        """

        self.session.machine.video_capture_enabled = False
        self.session.machine.save_settings()


    @lock_if_not_running
    def set_time_offset(self, offset=0):
        """Sets a time offset in seconds
        Default resets.

        Arguments:
            offset - time in seconds
        """

        self.session.machine.bios_settings.time_offset = offset * 1000L
        self.offset = offset * 1000L


    @check_running
    def set_time_speedup(self, speedup=100):
        """Sets relative speed time runs in the vm

        The speedup is set in percent, valid values go from 2 to 20000 percent.
        Default resets.

        Arguments:
            speedup - relative speedup in percent
        """

        self.session.console.debugger.virtual_time_rate = speedup
        self.speedup = speedup


    @lock_if_not_running
    def start_network_trace(self, path="/tmp/trace.pcap", adapter=0):
        """Trace network traffic on a certain network adapter

        Arguments:
            path - path for saving the pcap file
            adapter - internal number of the network adapter, range 0-
        """

        self.network = self.session.machine.get_network_adapter(adapter)

        self.network.trace_file = path
        self.network.trace_enabled = True
        self.session.machine.save_settings()


    @lock_if_not_running
    def stop_network_trace(self, adapter=0):
        """Stop network trace for one adapter

        Arguments:
            adapter - internal number of the network adapter, range 0-7
        """

        self.network = self.session.machine.get_network_adapter(adapter=0)

        self.network.trace_enabled = False
        self.session.machine.save_settings()


    @check_running
    def create_guest_session(self, username="default", password="12345",
                             home="", wait=True):
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

        if wait:
            while not self.guestsession:
                time.sleep(5)
                try:
                    self.guestsession = self.session.console.guest.create_session(
                        self.username, self.password)
                except:
                    pass
        else:
            self.guestsession = self.session.console.guest.create_session(
                self.username, self.password)

        #use vm property to find systemtype
        #we create the self.os at this point, because it needs a running guest
        #session anyway, this prevents if form being used before this exists
        if self.os_type in ["Linux26", "Linux26_64", "Ubuntu", "Ubuntu_64"]:
            if home:
                self.os = oslinux.OSLinux(self, home=home)
            else:
                self.os = oslinux.OSLinux(self)
        elif self.os_type in ["Windows7", "Windows7_64", "Windows8",
                              "Windows8_64", "Windows81", "Windows81_64"]:
            if home:
                self.os = oswindows.OSWindows(self, home=home)
            else:
                self.os = oswindows.OSWindows(self)


    @check_running
    def mount_folder_as_cd(self, folder_path, iso_path="/tmp/cd.iso",
                           cdlabel="MyCD"):
        """Creates a iso-image based on directory and mounts it to the VM

        If the operating system inside the vm does no automounting, further
        action will be needed. For Ubuntu and Windows, the files should be
        accessible without further action.
        Depends on mkisofs from genisoimage, should be installed by default on
        ubuntu hosts

        Arguments:
            folder_path - path to the folder, which's content should be inside
                the image
            iso_path - path, where the iso image should be created
            cdlabel - label, which will be shown inside the vm
        """

        #basic sanity check
        if not os.path.exists(folder_path):
            print("Error: Path does not exist")
            return

        args = ["-J", "-l", "-R", "-V", cdlabel, "-iso-level", "4", "-o",
                iso_path, folder_path]

        subprocess.check_output(["mkisofs"]+args)

        self.mount_cd(path=iso_path, remove_image=True)


    @check_running
    def mount_cd(self, path, remove_image=False):
        """mounts an iso image to the VM

        Arguments:
            path - path to the iso image
            remove_image - decides, if the image should be deleted on cleanup
        """

        self.medium = self.vb.open_medium(path,
                                          virtualbox.library.DeviceType.dvd,
                                          virtualbox.library.AccessMode.read_only,
                                          False)
        self.session.machine.mount_medium(ControllerType.IDE.name, 1, 0,
                                          self.medium, True)

        self.log.add_cd(path, remove_image, time_offset=self.offset,
                        time_rate=self.speedup)


    @check_running
    def umount_cd(self):
        """Removes a cd from the emulated IDE CD-drive
        """
        self.session.machine.mount_medium(ControllerType.IDE.name, 1, 0,
                                          virtualbox.library.IMedium(), True)
        if self.medium:
            self.medium.close()


    @check_running
    @check_guestsession
    def run_process(self, command, arguments=[], stdin='', key_input='',
                    environment=[], native_input=False, timeout=0, wait_time=10,
                    wait=True):
        """Runs a process with arguments and stdin in the VM

        This method requires the VirtualBox Guest Additions to be installed.

        Arguments:
            command - full path to the binary, that should be executed
            arguments - arguments passed to the binary, passed as an array of
                single arguments
            stdin - this is send to the stdin of the
                process after its creation, NOT WORKING!
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
            wait - selects if the process should be created synchronous with
                input or if this function will return, while the process inside
                the VM is still running

        Returns:
            pid, stdout, stdin
        """

        stdin = ""  # stdin input is broken in pyvbox!

        if wait and not key_input:
            process, stdout, stderr = self.guestsession.execute(command=command,
                arguments=arguments, stdin=stdin, environment=environment,
                timeout_ms=timeout)

        else:
            flags = [virtualbox.library.ProcessCreateFlag.wait_for_process_start_only,
                     virtualbox.library.ProcessCreateFlag.ignore_orphaned_processes]

            process = self.guestsession.process_create(command=command,
                                                       arguments=arguments,
                                                       environment=environment,
                                                       flags=flags,
                                                       timeout_ms=timeout)

            if key_input:
                time.sleep(wait_time)
                if native_input:
                    time.sleep(5)
                    self.os.keyboard_input(key_input=key_input, pid=process.pid)
                else:
                    self.keyboard_input(key_input=key_input)

            if wait:
                process.wait_for(int(virtualbox.library.ProcessWaitForFlag.terminate),
                                 10000)

            stdout = ""
            stderr = ""

        self.log.add_process(process, command, arguments, stdin, key_input,
                             stdout, stderr, process.pid,
                             time_offset=self.offset, time_rate=self.speedup)

        return process.pid, stdout, stderr


    @check_running
    @check_guestsession
    def kill_and_check_output(self, pid=0, timeout=0):
        """Kills a process started with run_process(wait=True)

        collects output written by this process after killing it

        Arguments:
            pid - process-id of the process to kill
            timeout - timeout in milliseconds
        """
        plist = self.log.get_log_object_by_type(logger.LogProcess)

        po = [a for a in plist if a.pid == pid][0]

        po.process.terminate()
        po.stdin += po.process.read(1, 65000, timeout)
        po.stdin += po.process.read(1, 65000, timeout)


    @check_running
    @check_guestsession
    def make_dir(self, directory):
        """Creates a directory and all intermediate ones

        use os specific ones over this command!

        Arguments:
            directory = path to the directory in the vm
        """
        self.guestsession.makedirs(directory)


    @check_running
    @check_guestsession
    def copy_to_vm(self, source, dest, wait=True):
        """Copy a file form outside into the VM

        This leaves no plausible trace for faking, so use with care

        Arguments:
            source - source path on the host
            dest - destination path in the vm
        """

        progress = self.guestsession.copy_to(source, dest, [])

        self.log.add_file(source=source, destination=dest,
                          time_offset=self.offset, time_rate=self.speedup)

        if wait:
            progress.wait_for_completion()
        else:
            return progress


    @check_running
    @check_guestsession
    def copy_from_vm(self, source, dest, wait=True):
        """Copy a file from the VM to the host

        creates no log, since it should not alter the guest

        Arguments:
            source - source path in the vm
            dest - destination path on the host
        """

        progress = self.guestsession.copy_from(source, dest)

        if wait:
            progress.wait_for_completion()
        else:
            return progress


    @check_running
    def keyboard_input(self, key_input):
        """sends raw key-presses to the vm

        avoid this method, as result tends to be unreliable.
        Needs no Guest Additions

        Arguments:
            key_input - string which will be typed on the guest, escapecodes
                will be interpreted
        """

        self.session.console.keyboard.put_keys(key_input)

        self.log.add_keyboard(key_input, time_offset=self.offset,
                              time_rate=self.speedup)


    @check_running
    def keyboard_combination(self, keys=[], make_code=True, break_code=True):
        """sends scancodes to the vm

        avoid this method, as result tends to be unreliable

        uses short names for scancodes as strings or single charakters.
        Example:
            ['win','r'] will send windows+r

        Needs no Guest Additions

        Arguments:
            keys - List of scancodes or chars
            make_code - send the keypress
            break_code - send the keyrelease
        """
        make_codes = {'win': [0xE0, 0x5B], 'esc': [0x01], 'bksp': [0x0E],
                      'ctrl': [0x1D], 'alt': [0x38], 'del': [0xE0, 0x53],
                      'tab': [0x0F], 'enter': [0x1C], 'up': [0xE0, 0x48],
                      'left': [0xE0, 0x4B], 'right': [0xE0, 0x4D],
                      'down': [0xE0, 0x50], 'f1': [0x3B], 'f2': [0x3C],
                      'f3': [0x3D], 'f4': [0x3E], 'f5': [0x3F], 'f6': [0x40],
                      'f7': [0x41], 'f8': [0x42], 'f9': [0x43], 'f10': [0x44],
                      'f11': [0x57], 'f12': [0x58]}

        break_codes = {'win': [0xE0, 0xDB], 'esc': [0x81], 'bksp': [0x8E],
                       'ctrl': [0x9D], 'alt': [0xB8], 'del': [0xE0, 0xD3],
                       'tab': [0x8F], 'enter': [0x9C], 'up': [0xE0, 0xC8],
                       'left': [0xE0, 0xCB], 'right': [0xE0, 0xCD],
                       'down': [0xE0, 0xD0], 'f1': [0xBB], 'f2': [0xBC],
                       'f3': [0xBD], 'f4': [0xBE], 'f5': [0xBF], 'f6': [0xC0],
                       'f7': [0xC1], 'f8': [0xC2], 'f9': [0xC3], 'f10': [0xC4],
                       'f11': [0xD7], 'f12': [0xD8]}

        if make_code:
            for s in keys:
                if s in make_codes:
                    # the api only likes baseintegers, but hex codes are, what
                    # everybody uses for make/break codes, so this conversion is
                    # needed, using int()
                    self.session.console.keyboard.put_scancodes(
                        [int(x) for x in make_codes[s]])
                    self.log.add_keyboard("makecode: "+str(s),
                                          time_offset=self.offset,
                                          time_rate=self.speedup)
                else:
                    # if its not in the list, assume it is a normal char/num
                    self.keyboard_input(s)

        if break_code:
            for s in keys:
                if s in break_codes:
                    self.session.console.keyboard.put_scancodes(
                        [int(x) for x in break_codes[s]])
                    self.log.add_keyboard("breakcode: "+str(s),
                                          time_offset=self.offset,
                                          time_rate=self.speedup)


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

        self.session.console.mouse.put_mouse_event_absolute(x, y, 0, 0,
                                                            buttonstate)
        if release:
            self.session.console.mouse.put_mouse_event_absolute(x, y, 0, 0, 0)

        self.log.add_mouse(x, y, lmb, mmb, rmb, time_offset=self.offset,
            time_rate=self.speedup)


    @check_running
    def add_to_nat_network(self, network_name="test_net", adapter=0):
        """Adds the VM to a NAT-network

        This enables multiple virtual machines to see each other and exchange
        data. The network has to be created first with
        VboxConfig.get_nat_network(). Using adapter 0 will reconfigure the
        default network adapter, use numbers 1-7 for additional adapters.

        Arguments:
            network_name - name of the the network the vm should be added to
            adapter - internal number of the network adapter, range 0-7
        """

        network_name = network_name + USERTOKEN

        self.network = self.session.machine.get_network_adapter(adapter)
        self.network.nat_network = network_name
        self.network.attachment_type = virtualbox.library.NetworkAttachmentType.nat_network
        #allow VMs to see each other
        self.network.promisc_mode_policy = virtualbox.library.NetworkAdapterPromiscModePolicy.allow_network
        self.network.enabled = True
        # to ensure the vm notices the network changes, we remove the cable for
        # 5 seconds
        self.network.cable_connected = False
        time.sleep(5)
        self.network.cable_connected = True
        self.session.machine.save_settings()


    @check_running
    def get_ip(self, adapter=0):
        """returns the IPv4 address of the given adapter

        Needs guest additions installed, not reliable with windows guests
        currently, might be more useful in the future

        Arguments:
            adapter - internal number of the network adapter, range 0-7

        Returns:
            ip-address
        """

        return self.session.machine.get_guest_property_value("/VirtualBox/GuestInfo/Net/"
                                                             + str(adapter)
                                                             + "/V4/IP")


    @lock_if_not_running
    def set_synthetic_cpu(self):
        """Sets the cpu property to make the vm more portable
        """

        self.session.machine.set_cpu_property(
            virtualbox.library.CPUPropertyType.synthetic, True)


    @check_stopped
    def cleanup_and_delete(self, ignore_errors=True, rm_clone=True):
        """clean all data except, what might have been exported

        This should be the last thing to do, just to make sure, we do not
        clutter our VirtualBox, use with care, this deletes files on the host
        system!

        Arguments:
            ignore_errors - ignore errors in removing files
            rm_clone - remove the cloned virtual machine
        """
        path = self.log.cleanup()
        while path:
            shutil.rmtree(path, ignore_errors)
            path = self.log.cleanup()

        #for clones we also remove the vm data of the clone and the
        #hdd, to not clutter
        if self.is_clone and rm_clone:
            self.unlock()

            hdds = []

            for disk in self.vb.hard_disks:
                if self.vm.id_p in disk.machine_ids:
                    hdds.append(disk)

            self.vm.remove()

            #if the hdd is not attached to any other vm, it is save to remove it
            # as well
            for disk in hdds:
                if not disk.machine_ids:
                    disk.delete_storage()
