import virtualbox
import os
import subprocess
import logger
import shutil
from functools import wraps



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



def check_running(func, errrormsg="Machine needs to be running"):
    """decorator for use inside Vbox only!
    """
    def checked(self):
        if not self.running:
            print errrormsg
            return
        func(self)
    return checked

def check_stopped(func, errrormsg="Machine needs to be stopped"):
    """decorator for use inside Vbox only!
    """
    def checked(self):
        if self.running:
            print errrormsg
            return
        func(self)
    return checked


class Vbox():
    """baseclass for controlling virtualbox

    This implements all operating system independent methods.
    Any method accepting an optional argument "wait" may return a progress object, 
    to enable the user to wait, if "wait=False" is passed to it. If this happens,
    the machine might also stay in locked state!
    """
    
    def __init__(self, basename="ubuntu-lts-base",
            clonename="testvm", mode="clone", linkedName="Forensig20Linked",
            osType="Linux26", wait=True):
        """Initialises a virtualbox instance

        The new instance of this class can either reuse an existing virtual 
        machine or create a new one, based on a existing template. The concepts
        of sessions and machines are not exposed to the user

        @osType - must be in >VboxInfo.list_ostypes()

        @basename - must be in >VboxInfo.list_vms()
        """

        self.vb = virtualbox.VirtualBox()

        if mode=="clone":
            self.vm = self.vb.create_machine("",clonename,[], osType,"")

            _orig = self.vb.find_machine(basename)
            _orig_session = _orig.create_session()

            try:
                _snap = _orig.findSnapshot(linkedName)
            except:
                _orig.lock_machine(_orig_session,virtualbox.library.LockType.shared)

                _orig_session.console.take_snapshot(linkedName, "")
                _snap = _orig.findSnapshot(linkedName)
                _orig_session.unlock_machine()    

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


        #use vm property to find systemtype
        if osType in ["Linux26","Linux26_64","Ubuntu","Ubuntu_64"]:
            self.os = osLinux(self)
        elif osType in  ["Windows7","Windows7_64","Windows8","Windows8_64"
                ,"Windows81","Windows81_64"]:
            self.os = osWindows(self)

        self.running = False

        self.log = logger.Logger()


    @check_stopped  
    def start(self, type="headless", wait=True):
        """start a machine

        The @type "headless" means, the machine runs without any gui, the only 
        sensible way on a remote server. This parameter is changable for 
        debugging only
        """

        self.progress = self.vm.launch_vm_process(self.session, type, '')

        self.running = True

        if wait:
            self.progress.wait_for_completion()
        else:
            return self.progress

    @check_running
    def stop(self, wait=True):
        """Stop a running machine

        """

        self.lock()
        self.progress = self.session.console.power_down()

        self.running = False

        if wait:
            self.progress.wait_for_completion()
            self.unlock()
        else:
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
    def export(self, path="/tmp/disk.vdi", wait=True):
        """Export a VirtualBox hard disk image

        Currently, this will always export the first hard disk
        on the virtual SATA controller
        """

        self.lock()

        clone_hdd = self.vb.create_hard_disk("",path)
        cur_hdd = self.session.machine.get_medium("SATA",0,0)
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

        @path - path, where the png image should be created
        """

        h, w, d, x, y = self.session.console.display.get_screen_resolution(0)

        png = self.session.console.display.take_screen_shot_png_to_array(0, h, w)

        f = open(path, 'wb')
        f.write(png)


    @check_running
    def start_video(self, path="/tmp/video"):

        self.session.machine.video_capture_file = "/tmp/video"
        self.session.machine.video_capture_enabled = True
        self.session.machine.save_settings()


    @check_running
    def stop_video(self):

        self.session.machine.video_capture_enabled = False
        self.session.machine.save_settings()


    @check_running
    def time_offset(self,offset=0):
        """Sets a time offset in seconds

        The @offset is set in the bios clock of the virtual machine, multiplied 
        by 1000 because the default miliseconds are not usefull for our usecase.
        Default resets.

        @offset - time in miliseconds
        """

        self.session.machine.bios_settings.time_offset = offset * 1000


    @check_running
    def time_speedup(self,speedup=100):
        """Sets relative speed time runs in the vm

        The speedup is set in percent, valid values go from 2 to 20000 percent.
        Default resets.

        @speedup - relative speedup in percent
        """

        self.session.console.debugger.virtual_time_rate = speedup


    @check_running
    def start_network_trace(self, path="/tmp/trace.pcap"):


        self.network = session.machine.get_network_adapter(0)

        self.network.trace_file = path
        self.network.traceEnabled = True
        self.session.machine.saveSettings()


    @check_running
    def stop_network_trace(self):

        self.network = session.machine.get_network_adapter(0)

        self.network.traceEnabled = False
        self.session.machine.saveSettings()


    @check_running
    def create_guest_session(self, username="default", password="12345"):
        """creates a guest session for issuing commands to the guest system

        While the VirtualBox API would support up to 256 simultanious guest 
        sessions, here only one simultanious guestsession is supported
        """
        self.username = username
        self.password = password
        self.guestsession = self.session.console.guest.create_session(username,password)


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

        #TODO: maybe remove self.iso afterwards


    @check_running
    def run_process(self, command, arguments=[], stdin='', wait=True):
        """Runs a process with arguments and stdin in the VM

        This method requires the VirtualBox Guest Additions to be installed.
        @flags
        """

        if wait:
            flags=[virtualbox.library.ProcessCreateFlag.wait_for_std_err,
                   virtualbox.library.ProcessCreateFlag.wait_for_std_out,
                   virtualbox.library.ProcessCreateFlag.ignore_orphaned_processes]
        else:
            flags=[virtualbox.library.ProcessCreateFlag.wait_for_process_start_only,
                   virtualbox.library.ProcessCreateFlag.ignore_orphaned_processes] 


        process, stdout, stderr = self.guestsession.execute(command, arguments, 
            stdin, flags=flags)


        self.log.add_process(process, arguments, stdin, stdout, stderr)

        return stdout, stderr



    @check_running
    def copy_to_vm(self, source, dest, wait=True):
        """Copy a file form outside into the VM

        This leaves no plausible trace for fakeing, so use with care
        """

        self.progress = self.guestSession.copy_to(source, destination, [])

        self.log.add_file(source=source, destination=dest)

        if wait:
            self.progress.wait_for_completion()
        else:
            return progress


    @check_running
    def keyboard_input(self, key_input):
        """sends raw keypresses to the vm
        """
        session.console.keyboard.put_keys(key_input)

        self.log.add_keyboard(key_input)


    @check_running
    def mouse_input(self, x, y, pressed=True):
        pass


    @check_stopped
    def cleanup_and_delete(self, ignore_errors=True, rm_clone=True):
        """clean all data exept, what might have been exported

        This should be the last thing to do, just to make sure, we do not clutter
        our VirtualBox. Since this
        """

        while (path = self.log.cleanup()) is not False:
            shutil.rmtree(path, ignore_errors)

        #for clones we also remove the vm data of the clone and the
        #hdd, to not clutter
        if self.is_clone and rm_clone:
            hdd = self.vm.remove()
            #if the hdd is not attached to any other vm, its save to remove it as well
            if not hdd.machine_ids():
                hdd.delete_storage()


class osLinux():
    """Linux specific operations 

    Classes starting with os should all implement the same interface, that offers 
    features, that depend on the opertation system, running in the VM
    """

    def __init__(self, vb, term="/usr/bin/xterm"):
        self.vb = vb
        self.term = term

    def create_user(self, username, password):
        pass

    def open_browser(self, url="www.google.com"):

        vb.run_process(command="/usr/bin/firefox", arguments=["-new-tab",url], wait=False)

    def uninstall_program(self, program):
        """remove a program from the guest system with apt-get

        """
        stdin="sudo apt-get remove {0}\n{1}\n".format(program, self.vb.password)
        self.vb.run_process(command=self.term, stdin=stdin)

    def uninstall_guest_additions():
        """remove the guest additions

        Warning: This can not be undone, since remote running of software is 
        very limited without guest additions! You need to know the exact version
        installed
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

    def create_user(self, username, password):
        
        stdin = """$objOu = [ADSI]"WinNT://$computer"
                $objUser = $objOU.Create("User", {0})
                $objUser.setpassword({1})
                $objUser.SetInfo()

                """.format(username, password)

    def open_browser(self, url="www.google.com"):

        stdin = """$ie = new­object ­com "InternetExplorer.Application"
                $ie.navigate("{0}")
                $ie.visible = $true

                """.format(url)

        vb.run_process(command=self.term, stdin=stdin)

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

        self.uninstall_program("Oracle VM VirtualBox Guest Additions"+version)
