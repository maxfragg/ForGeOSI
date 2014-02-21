#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

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

        stdin = '''$ie = new?object ?com "InternetExplorer.Application"
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
            +str(version))
