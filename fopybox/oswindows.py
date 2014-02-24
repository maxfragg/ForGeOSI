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
    Expects the operating system to be a MS Windows 7 (NT6.1) or newer, with 
    powershell 2.0 or newer 
    """

    def __init__(self,vb,
            term="C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"):
        self.vb = vb
        self.term = term
        self.cmd ="C:\\Windows\\System32\\cmd.exe"
        self.ie ="C:\\Program Files (x86)\\Internet Explorer\iexplore.exe"


    def run_shell_cmd(self, command, cmd=False):
        """runs a command inside the default shell of the user or in the legacy
        cmd.exe
        """
        if cmd:
            return self.vb.run_process(command=self.cmd, arguments=['/C', command])
        else:
            return self.vb.run_process(command=self.term, arguments=["'"+command+"; stop-process powershell'")


    def keyboard_input(self, key_input, window_class='', name='', pid=0):
        """sends keyboard input using windows powershell and visual basic

        Using more than one identifier is not advised, since they are not 
        combined as on Linux

        Arguments:
            key_input - input send to the program
            window_class - unused, for interface compatibility with osLinux
            name - name of the application to activate
            pid - Process id of the application
        """

        command ="""add-type -AssemblyName microsoft.VisualBasic
        add-type -AssemblyName System.Windows.Forms
        start-sleep -Milliseconds 500
        """
        if name:
            command = command + """[Microsoft.VisualBasic.Interaction]::AppActivate(\\\""""+name+"""\\\")
            """
        
        if pid:
            command = command + """$mypid ="""+pid+"""
            Set-ForegroundWindow (Get-Process -id $mypid).MainWindowHandle
            """

        command = command + """[System.Windows.Forms.SendKeys]::SendWait(\\\""""+key_input+"""\\\")
        """

        self.run_shell_cmd(command=command)


    def copy_file(self, source, destination):
        """copy a file on the guest, using the windows cmd copy command
        """
        self.run_shell_cmd(command="copy "+source+" "+destination)


    def move_file(self, source, destination):
        """move a file on the guest, using the windows move copy command
        """
        self.run_shell_cmd(command="move "+source+" "+destination)


    def create_user(self, username, password):
        
        command = """$objOu = [ADSI]\\"WinNT://$computer\\"
        $objUser = $objOU.Create("User", {0})
        $objUser.setpassword({1})
        $objUser.SetInfo()

        """.format(username, password)

        self.run_shell_cmd(command=command)


    def download_file(self, url, destination):

        command = '''$source = \\"{0}\\"
        $destination = \\"{1}\\"
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile($source, $destination)

        '''.format(url,destination)

        self.run_shell_cmd(command=command)




    def open_browser(self, url="www.google.com", method="direct"):
        """Opens a Internet Explorer with the given url

        Arguments:
            url - url of the website to open
            method - decide how to run the browser, currently "direct" and 
                "shell" are available 
        """
        if method is "direct":
            self.vb.run_process(command=self.ie, arguments=[url])
        
        elif method is "shell":
            command = '''$ie = new-object -com "InternetExplorer.Application"
            $ie.navigate(\\"{0}\\")
            $ie.visible = $true

            '''.format(url)

            self.run_shell_cmd(command=command)


    def kill_process(self, name='', pid=0):
        """kills the application based on name or pid
        one parameter needs to be given
        """

        assert(name and pid)

        command = "Stop-Process"
        if name:
            command = command + "-Name "+name
        if pid:
            command = command + "-Id "+pid

        self.run_shell_cmd(command=command)


    def uninstall_program(self, program):
        """remove a program from the guest system

        This only works for progams using msi-based installers
        """
        command = """$app = Get-WmiObject -Class Win32_Product `
                     -Filter \\"Name = '{0}'\\"
                $app.Uninstall()

                """.format(program)

        self.run_shell_cmd(command=command)



    def uninstall_guest_additions(self, version="4.3.6"):
        """remove the guest additions

        Warning: This can not be undone, since remote running of software is 
        very limited without guest additions! You need to know the exact version
        installed
        """

        self.uninstall_program("Oracle VM VirtualBox Guest Additions"
            +str(version))
