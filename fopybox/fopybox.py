#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import virtualbox #pyvbox
import os
import subprocess
import logger #local import
import shutil
import time
#needs python-decorator, needed for signature preserving decorators
from decorator import decorator 

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
        """creates a natnetwork, if none of the name exists.
        
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
    """baseclass for controlling virtualbox

    This implements all operating system independent methods.
    Any method accepting an optional argument "wait" may return a progress object, 
    to enable the user to wait, if "wait=False" is passed to it. If this happens,
    the machine might also stay in locked state!
    """
    
    def __init__(self, basename="ubuntu-lts-base",
            clonename="testvm", mode="clone", linkedName="Forensig20Linked",
            osType="Linux26", username="default", password="12345", wait=True):
        """Initialises a virtualbox instance

        The new instance of this class can either reuse an existing virtual 
        machine or create a new one, based on a existing template. The concepts
        of sessions and machines are not exposed to the user

        Arguments:
            osType - must be in VboxInfo.list_ostypes()
            basename - must be in VboxInfo.list_vms()
            mode - must be "use" or "clone"
            wait - Setting wait to False enables async actions, but might break 
                things, use with care!
        """

        self.vb = virtualbox.VirtualBox()

        if mode=="clone":
            self.vm = self.vb.create_machine("",clonename,[], osType,"")

            _orig = self.vb.find_machine(basename)
            _orig_session = _orig.create_session()

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

        self.session = self.vm.create_session()
        self.guestsession = False
        self.username = username
        self.password = password

        #use vm property to find systemtype
        if osType in ["Linux26","Linux26_64","Ubuntu","Ubuntu_64"]:
            self.os = osLinux(self)
        elif osType in  ["Windows7","Windows7_64","Windows8","Windows8_64"
                ,"Windows81","Windows81_64"]:
            self.os = osWindows(self)

        self.running = False

        self.log = logger.Logger()
        self.log.add_vm(clonename, basename, osType, username, password)


    @check_stopped  
    def start(self, type="headless", wait=True):
        """start a machine

        Arguments:
            type - "headless" means, the machine runs without any gui, the only 
                sensible way on a remote server. This parameter is changable to 
                "gui" for debugging only
            wait - waits till the machine is initialised, it will not have 
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
            shutdown - will send acpi signal to the machine and 
                might take some time for the machine to power down.
                Otherwise the machine will just be turned off, and its state in
                virtualbox will be "aborted"
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

        clone_hdd = self.vb.create_hard_disk("",path)
        cur_hdd = self.session.machine.get_medium(controller,port,disk)
        #TODO: support vmdk_raw_disk as well?
        progress = clone_hdd.copy_to(clone_hdd,
            virtualbox.library.MediumVariant.standard,None)

        if wait:
            progress.wait_for_completion()
            self.unlock()
        else:
            return progress


    @check_running
    def take_screenshot(self, path="/tmp/screenshot.png"):
        """Save screenshot to given path
        Arguments:
            path - path, where the png image should be created
        """

        h, w, d, x, y = self.session.console.display.get_screen_resolution(0)

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
    def create_guest_session(self):
        """creates a guest session for issuing commands to the guest system

        While the VirtualBox API would support up to 256 simultanious guest 
        sessions, here only one simultanious guestsession is supported
        """

        self.guestsession = self.session.console.guest.create_session(self.username,self.password)


    @check_running
    def mount_folder_as_cd(self, folder_path, iso_path="/tmp/cd.iso" ,cdlabel="MyCD"):
        """Creates a iso-image based on directory and mounts it to the VM

        If the operating system inside the vm does no automounting, further action
        will be needed. For Ubuntu and Windows, the files should be accessible without
        further action
        Depends on mkisofs form genisoimage, should be installed by default on ubuntu
        """

        #basic sanity check
        if os.path.exists(iso_path) == False:
            return

        args = "-J -l -R -V"+cdlabel+"-iso-level 4 -o"+iso_path+" "+folder_path

        subprocess.call(["mkisofs", args])

        self.session.machine.mount_medium("IDE",0,0,iso_path,False)
        self.iso = iso_path

        self.log.add_cd(iso_path)


    @check_running
    def umount_cd(self):
        """Removes a cd from the emulated IDE CD-drive
        """

        self.session.machine.mount_medium("IDE",0,0,"",False)


    @check_running
    @check_guestsession
    def run_process(self, command, arguments=[], stdin='', environment=[],
             timeout=0, wait=True):
        """Runs a process with arguments and stdin in the VM

        This method requires the VirtualBox Guest Additions to be installed.

        Arguments:
            stdin - only used, if wait=True, this is send to the stdin of the 
                process after its creation
            timeout - This is a timeout in miliseconds, which determines, when 
                the process will be killed, 0 will disable the timeout
            wait - selects if the process should be created syncronous with input 
                or if this function will return, while the porcess inside the VM
                is still running
        """

        if wait:
            process, stdout, stderr = self.guestsession.execute(command=command, 
            arguments=arguments, stdin=stdin, environment=environment, 
            timeout_ms=timeout)

        else:
            flags=[virtualbox.library.ProcessCreateFlag.wait_for_process_start_only,
                   virtualbox.library.ProcessCreateFlag.ignore_orphaned_processes]

            process = self.guestsession.process_create(command=command, 
                arguments=arguments, environment=environment, flags=flags,
                timeout_ms = timeout)

            stdout = ""
            stderr = ""


        self.log.add_process(process, arguments, stdin, stdout, stderr)

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

        This leaves no plausible trace for fakeing, so use with care
        """

        progress = self.guestsession.copy_to_vm(source, destination, [])

        self.log.add_file(source=source, destination=dest)

        if wait:
            progress.wait_for_completion()
        else:
            return progress


    @check_running
    def keyboard_input(self, key_input):
        """sends raw keypresses to the vm

        avoid this method, as result tends to be unreliable
        """

        self.session.console.keyboard.put_keys(key_input)

        self.log.add_keyboard(key_input)


    @check_running
    def keyboard_scancodes(self, scancode=[]):
        """sends scancodes to the vm

        avoid this method, as result tends to be unreliable

        Usefull scancodes might be:
             1 - escape
            14 - backspace
            28 - enter
            224, 91 - super/windows
        """
        for s in scancode:
            self.session.console.keyboard.put_scancode(s)
            self.log.add_keyboard("scancode: "+s)

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
            release - releases the mousebutton, only triggering one click
        """

        buttonstate = lmb + (2 * rmb) + (4 * mmb)

        session.console.mouse.put_mouse_event_absolute(x,y,0,0,buttonstate)
        if release:
            session.console.mouse.put_mouse_event_absolute(x,y,0,0,0)

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
        """clean all data exept, what might have been exported

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


class osLinux():
    """Linux specific operations 

    Classes starting with os should all implement the same interface, that offers 
    features, that depend on the opertation system, running in the VM
    """

    def __init__(self, vb, term="/usr/bin/xterm", env=[]):
        self.vb = vb
        self.term = term
        self.env = ["DISPLAY=:0", "USER="+vb.username, 
            "HOME=/home/"+vb.username] + env


    def run_shell_cmd(self, command, close_shell=True):
        """runs a command inside the default shell of the user
        """
        if close_shell:
            cmd = command + "\n  exit\n"
        else:
            cmd = command + "\n"

        self.vb.run_process(command=self.term, stdin=cmd, 
            environment=self.env, wait=True)


    def copy_file(self, source, destination):
        
        self.run_shell_cmd("cp "+source+" "+destination)


    def move_file(self, source, destination):
        
        self.run_shell_cmd("mv "+source+" "+destination)


    def create_user(self, username, password):
        pass


    def download_file(self, url, destination):

        self.run_shell_cmd("wget -O "+destination+" "+url)


    def serve_directory(self, directory="~", port=8080):
        """creates a simple webserver, serving a directory on a given port

        uses python SimpleHTTPServer, since it is installed by default and acts
        as a propper webserver, unlike netcat.

        Arguments:
            port - needs to be over 1000, default is 8080
            directory - a directory to be served, including subdirectories, 
                default is ~
        """
        self.run_shell_cmd("cd "+directory+" ; python -m SimpleHTTPServer "
            +str(port))


    def open_browser(self, url="www.google.com", method="shell"):
        """Opens a firefox browser with the given url

        Arguments:
            method - decide how to run the browser, currently "direct" and 
                "shell" are available 
        """

        if method == "direct":
            self.vb.run_process(command="/usr/bin/firefox", 
                arguments=["-new-tab",url], environment=self.env, wait=False)
        elif method == "shell":
            self.run_shell_cmd(command="/usr/bin/firefox -new-tab"+url)


    def uninstall_program(self, program):
        """remove a program from the guest system with apt-get

        """
        stdin="sudo apt-get remove {0}\n{1}\n".format(program, self.vb.password)
        self.vb.run_process(command=self.term, stdin=stdin, environment=self.env,)


    def uninstall_guest_additions():
        """remove the guest additions

        Warning: This can not be undone, since remote running of software is 
        very limited without guest additions!
        """

        self.uninstall_program("virtualbox-guest-*")


class osWindows():
    """Windows specific operations

    Classes starting with os should all implement the same interface, that offers 
    features, that depend on the opertation system, running in the VM.
    For this class to work, @term needs to be the path to a windows powershell!
    Expects the operating system to be a MS Windows 7 or newer 
    """

    def __init__(self,vb,
            term="%%SystemRoot%%\\system32\\WindowsPowerShell\\v.1.0\powershell.exe"):
        self.vb = vb
        self.term = term
        self.cmd ="%%SystemRoot%%\\system32\\cmd.exe" 


    def run_shell_cmd(self, command, cmd=True):
        """runs a command inside the default shell of the user or in the legacy
        cmd.exe
        """
        if cmd:
            return self.vb.run_process(command=self.cmd, arguments=['/C', command])
        else:
            return self.vb.run_process(command=self.term, stdin=command+"\n")


    def copy_file(self, source, destination):
        """copy a file on the guest, using the windows cmd copy command
        """
        self.run_shell_cmd(command="copy "+source+" "+destination, cmd=True)


    def move_file(self, source, destination):
        """move a file on the guest, using the windows move copy command
        """
        self.run_shell_cmd(command="move "+source+" "+destination, cmd=True)


    def create_user(self, username, password):
        
        stdin = """$objOu = [ADSI]"WinNT://$computer"
        $objUser = $objOU.Create("User", {0})
        $objUser.setpassword({1})
        $objUser.SetInfo()

        """.format(username, password)

        self.vb.run_process(command=self.term, stdin=stdin)


    def download_file(self, url, destination):

        stdin = '''$source = "{0}"
        $destination = "{1}"
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile($source, $destination)

        '''.format(url,destination)

        self.vb.run_process(command=self.term, stdin=stdin)


    def open_browser(self, url="www.google.com"):

        stdin = '''$ie = new­object ­com "InternetExplorer.Application"
        $ie.navigate("{0}")
        $ie.visible = $true

        '''.format(url)

        self.vb.run_process(command=self.term, stdin=stdin)


    def uninstall_program(self, program):
        """remove a program from the guest system

        This only works for progams using msi-based installers
        """
        stdin = """$app = Get-WmiObject -Class Win32_Product `
                     -Filter "Name = '{0}'"
                $app.Uninstall()

                """.format(program)

        self.vb.run_process(command=self.term, stdin=stdin)


    def uninstall_guest_additions(self, version="4.3.6"):
        """remove the guest additions

        Warning: This can not be undone, since remote running of software is 
        very limited without guest additions! You need to know the exact version
        installed
        """

        self.uninstall_program("Oracle VM VirtualBox Guest Additions"
            +str(version)
