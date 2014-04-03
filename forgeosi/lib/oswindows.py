#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#
# base64_encode_command is straight from
# http://jasagerpwn.googlecode.com/svn/trunk/src/powershellPayload.py


import base64
import time
from param import RunMethod  # local import

__doc__ = """\
Windows specifc code, see class documentation for details
"""


class OSWindows():
    """Windows specific operations

    Classes starting with OS should all implement the same interface, that
    offers features, that depend on the operation system, running in the VM.
    For this class to work, @term needs to be the path to a Windows Powershell.
    Expects the operating system to be a MS Windows 7 (NT6.1) or newer, with
    Powershell 2.0 or newer installed.

    General notes:
        All paths on the guest should be absolute and use 2 backslashes as
        separator, paths with '-' in it will most likely break in any function
        using powershell
    """

    def __init__(self, vb,
            term="C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            home="C:\\Users\\default.windows-8-base\\"):
        """Initializes the osWindows class

        Arguments:
            vb - ForGeOSI.VBox instance
            term - path to the default terminal to be used, should be a
                powershell.exe
            home - home of the default user, used for the guest session
        """

        self.vb = vb
        self.term = term
        self.home = home
        self.cmd = "C:\\Windows\\System32\\cmd.exe"
        self.ie = "C:\\Program Files (x86)\\Internet Explorer\\iexplore.exe"


    def _base64_encode_command(self, command):
        """using base64 encoded commands solves issues with quoting in the
        VirtualBox execute function, needed as a workaround, for pythons
        base64 function not inserting \x00 after each char
        """

        blank_command = ""
        for char in command:
            blank_command += char + "\x00"

        command = blank_command
        command = base64.b64encode(command)
        return command


    def _base64_decode_command(self, command):
        """debugging purpose only, decodes base64 encoded commands
        """

        command = base64.b64decode(command)
        blank_command = ""
        i = 0
        for char in command:
            if (i % 2) == 0:
                blank_command += char
            i = i + 1
        return blank_command


    def _check_path(self, path):
        """check if path parameters contain a '-'
        """
        if '-' in path:
            self.vb.log.add_warning('The path "'+path+
                '" contains a "-", this is know to cause problems')


    def run_shell_cmd(self, command, cmd=False, stop_ps=False):
        """runs a command inside the default shell of the user or in the legacy
        cmd.exe, needs properly split arguments for cmd=True

        Arguments:
            command - command which will be executed
            cmd - run inside a cmd or powershell
            stop_ps - kill the powershell window after running the command
        """
        if cmd:
            return self.vb.run_process(command=self.cmd,
                                       arguments=["/C"]+command)
        else:
            if stop_ps:
                command += "; stop-process powershell"
            self.vb.log.add_encodedCommand(command)
            command = self._base64_encode_command(command)
            return self.vb.run_process(command=self.term,
                                       arguments=["-OutputFormat", "Text",
                                                  "-inputformat", "none",
                                                  "-EncodedCommand", command])


    def keyboard_input(self, key_input, window_class='', name='', pid=0):
        """sends keyboard input using windows powershell and visual basic

        Using more than one identifier is not advised, since they are not
        combined as on Linux, use for plain text only

        Arguments:
            key_input - input send to the program
            window_class - unused, for interface compatibility with osLinux
            name - name of the application to activate
            pid - Process id of the application
        """

        command = """add-type -AssemblyName microsoft.VisualBasic
        add-type -AssemblyName System.Windows.Forms
        start-sleep -Milliseconds 500
        """
        if name:
            command += '''(New-Object -ComObject wscript.shell).AppActivate("'''+name+'''")
            '''

        if pid:
            command += """$mypid ="""+str(pid)+"""
            Set-ForegroundWindow (Get-Process -id $mypid).MainWindowHandle
            """

        command += '''[System.Windows.Forms.SendKeys]::SendWait("'''+key_input+'''")'''

        self.run_shell_cmd(command=command)


    def copy_file(self, source, destination, cmd=True):
        """copy a file on the guest, using the windows cmd copy command

        Arguments:
            source - source to copy from
            destination - destination to copy to
            cmd - use cmd.exe or Powershell
        """
        self._check_path(source)
        self._check_path(destination)

        if cmd:
            self.run_shell_cmd(command=["copy", source, destination], cmd=True)
        else:
            self.run_shell_cmd(command="copy "+source+" "+destination,
                               cmd=False)


    def move_file(self, source, destination, cmd=True):
        """move a file on the guest, using the windows move copy command

        Arguments:
            source - source to move from
            destination - destination to move to
            cmd - use cmd.exe or Powershell
        """
        self._check_path(source)
        self._check_path(destination)

        if cmd:
            self.run_shell_cmd(command=["move", source, destination], cmd=True)
        else:
            self.run_shell_cmd(command="move "+source+" "+destination,
                               cmd=False)


    def make_dir(self, path="C:\\test", cmd=True):
        """Creates a directory on the guest

        Arguments:
            path - path to the directory, missing parent-directories will be
                created as well
            cmd - use cmd.exe or Powershell
        """
        self._check_path(path)

        if cmd:
            self.run_shell_cmd(command=["mkdir", path], cmd=True)
        else:
            self.run_shell_cmd(command="mkdir "+path, cmd=False)


    def create_user(self, username, password):
        """Creates a new user in the guest with default privileges. The
        guestsession needs to belong to a administrator user

        Arguments:
            username - Name for the new user
            password - Password for the new user
        """

        command = """
        [ADSI]$server="WinNT://{0}"
        $user=$server.create("user","{1}")
        $user.setpassword("{2}")
        $user.SetInfo()
        [ADSI]$group="WinNT://{0}/Power Users,Group"
        $group.add($user.path)
        """.format(self.vb.basename, username, password)

        self.run_shell_cmd(command=command)


    def download_file(self, url, path="C:\\test\\image.jpg"):
        """Download a file using powershell

        Arguments:
            url - url to download from
            path - full path, where the file should be saved
        """
        self._check_path(path)

        command = '''(new-object System.Net.WebClient).DownloadFile("{0}", "{1}")'''.format(url, path)

        self.run_shell_cmd(command=command)


    def open_browser(self, url="www.google.com", method=RunMethod.direct,
                     timeout=20000):
        """Opens a Internet Explorer with the given url

        Arguments:
            url - url of the website to open
            method - decide how to run the browser.
                Valid options:
                    RunMethod.direct - VirtualBox-API, doesn't work on Windows 8
                    RunMethod.shell - Windows Powershell
                    RunMethod.run - Windows run dialog
                    RunMethod.start - Startmenu, depends on view on Windows 8
                Note: direct will block, until the browser is closed, if no
                timeout is set!
            timeout - in Milliseconds
        """

        if not isinstance(method, RunMethod):
            raise TypeError("method needs to be of type RunMethod")

        if method is RunMethod.direct:
            self.vb.run_process(command=self.ie, arguments=[url],
                timeout=timeout)

        elif method is RunMethod.shell:
            command = '''$ie = new-object -com "InternetExplorer.Application";$ie.navigate("{0}");$ie.visible = $true'''.format(url)

            self.run_shell_cmd(command=command)

        elif method is RunMethod.run:
            self.vb.keyboard_combination(['win', 'r'])
            time.sleep(5)
            self.vb.keyboard_input('iexplore '+url+'\n')

        elif method is RunMethod.start:
            self.vb.keyboard_combination(['win'])
            time.sleep(5)
            self.vb.keyboard_input('iexplore '+url+'\n')


    def kill_process(self, name='', pid=0):
        """kills the application based on name or pid
        one parameter needs to be given

        Arguments:
            name - name of the program
            pid - process id
        """

        assert(name or pid)

        command = "Stop-Process "
        if name:
            command += "-Name "+name
        if pid:
            command += "-Id "+str(pid)

        self.run_shell_cmd(command=command)


    def uninstall_program(self, program):
        """remove a program from the guest system

        This only works for progams using msi-based installers

        Arguments:
            program - name of the program, as shown in "Installed Software"
        """
        command = '''$app = Get-WmiObject -Class Win32_Product `
                     -Filter "Name = '{0}'"
                $app.Uninstall()
                '''.format(program)

        self.run_shell_cmd(command=command)



    def uninstall_guest_additions(self, version="4.3.8"):
        """remove the guest additions

        Warning: This can not be undone, since remote running of software is
        very limited without guest additions! You need to know the exact version
        installed
        """

        self.uninstall_program("Oracle VM VirtualBox Guest Additions "
                               + str(version))
