#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

from lib.param import RunMethod #local import
import time


class osLinux():
    """Linux specific operations 

    Classes starting with os should all implement the same interface, that offers 
    features, that depend on the opertation system, running in the VM.
    some functions require additional software:
        xdotool

    Known limitations:
        xdotool_extended=True only works, if the the windowmanager confirms X11
        specifications, which Unity in Ubuntu 12.04 does not.
    """

    def __init__(self, vb, term="/usr/bin/xterm", home="/home/default/",
            env=[], xdotool_extended=False):
        self.vb = vb
        self.term = term
        self.home = home
        self.shell = "/bin/bash"
        self.env = ["DISPLAY=:0", "USER="+vb.username, 
            "HOME=/home/"+vb.username] + env
        self.xdt = "/usr/bin/xdotool"
        self.xdte = xdotool_extended


    def run_shell_cmd(self, command, gui=False ,close_shell=False):
        """runs a command inside the default shell of the user

        Arguments:
            gui - decides if a x-terminal should be created, or the scripts 
                should run in a naked bash without terminal emulator
            close_shell - if a x-terminal is created, this is needed to make the
                window close again 
        """
        if gui:
            if close_shell:
                cmd = command + "\n  exit\n"
            else:
                cmd = command + "&\n"

            self.vb.run_process(command=self.term, key_input=cmd, 
                environment=self.env, native_input=True, wait=True)
        else:
            self.vb.run_process(command=self.shell, arguments=['-c',command],
                environment=self.env, wait=True)


    def _build_xdotool_args(self, window_class, name, pid):
        """helper to get the arguments for xdotool

        note that none of the options are really reliable, since they all depend
        on the windows having the correct fields set
        Additional, Unity in Ubuntu 12.04 is not working properly with xdotool
        """
        args = []

        #turn this function into a noop if we do not want to use it (like on unity)
        if not self.xdte:
            return args

        if window_class or name or pid:
            #sync makes it hang, until a window is found with the propery
            args = ["search", "--sync"]
        if window_class:
            args = args + ["--class", window_class]
        if name:
            args = args + ["--name", name]
        if pid:
            args = args + ["--pid", str(pid)]
        return args


    def keyboard_input(self, key_input, window_class='', name='', pid=0):
        """Sends keyboard input to a running gui process.

        Arguments
            input - String of characters to be send to the process, magic for 
                sleeping during input, put a 'sleep_hack\n' in the string to 
                sleep at this position, for example to wait for sudo to ask for 
                a password
            window_class - X-property, usually matching the program name, which 
                can be used to find program. Will be ignored if empty
            name - X-property, might work better than window_class for some 
                usecases
            pid - process id, unique idenifier per process, but not per window, 
                is not allways part of the X-properties. Will be ignored if Zero
        """

        #type will simulate typing and interpret space '\n'
        args = self._build_xdotool_args(window_class, name, pid) + ["type","--delay","30"] 
        

        #send input line by line, to prevent to long argument
        key_input_split = str.splitlines(str(key_input))

        for part in key_input_split:
            if part is "sleep_hack":
                time.sleep(10)
            else:
                #reinsert '\n' since we lost that with the splitlines
                self.vb.run_process(command=self.xdt,arguments=args+[part+'\n'], 
                    environment=self.env)



    def keyboard_specialkey(self, key, window_class='', name='', pid=0):
        """Sends a special key or key combination to a running gui process.

        Arguments
            key - X name of the key to be send as a string, names like "alt", 
                "ctrl", combinations like "ctl+alt+backspace" also work
            window_class - X-property, usually matching the program name, which 
                can be used to find program. Will be ignored if empty
            name - X-property, might work better than window_class for some 
                usecases
            pid - process id, unique idenifier per process, but not per window, 
                is not allways part of the X-properties. Will be ignored if Zero
        """

        #key uses keynames in oposite to type
        args = self._build_xdotool_args(window_class, name, pid) + ["key"]

        self.vb.run_process(command=self.xdt,arguments=args+[key],
                environment=self.env)


    def copy_file(self, source, destination):
        """Copy file within the guest

        Arguments:
            source - source path
            destination - destination path
        """
        self.run_shell_cmd("cp "+source+" "+destination)


    def move_file(self, source, destination):
        """Move file within the guest

        Arguments:
            source - source path
            destination - destination path
        """
        self.run_shell_cmd("mv "+source+" "+destination)

    def make_dir(self, path):
        """Creates a directory on the guest

        Arguments:
            path - path to the directory, missing parent-directories will be 
                created as well
        """
        self.run_shell_cmd("mkdir -p "+path)

    def create_user(self, username, password, sudopassword):
        """Creates a new user in the VM

        Arguments:
            username - username of the new user
            password - password of the new user
            sudopassword - password of the existing sudo user
        """
        self.run_shell_cmd("sudo useradd "+username+
            "\n"+rootpassword+"\nsudo passwd "+username+"\nsleep_hack\n"
            +sudopassword+"\nsleep_hack\n"+password+"\n")


    def download_file(self, url, destination):
        """Download file using wget

        Arguments:
            url - url to download from
            destination - path where the file should be saved
        """
        self.run_shell_cmd("wget -O "+destination+" "+url)


    def serve_directory(self, directory="~", port=8080):
        """creates a simple webserver, serving a directory on a given port

        uses python SimpleHTTPServer, since it is installed by default and acts
        as a propper webserver, unlike netcat.

        Arguments:
            directory - a directory to be served, including subdirectories, 
                default is ~
            port - needs to be over 1000, default is 8080
        """
        self.run_shell_cmd("cd "+directory+" ; python -m SimpleHTTPServer "
            +str(port))


    def open_browser(self, url="www.google.com", method=RunMethod.direct):
        """Opens a firefox browser with the given url

        Arguments:
            url - url which should be opened in the browser
            method - decide how to run the browser, must be of type RunMethod
        """
        if not isinstance(method, RunMethod):
            raise TypeError("method needs to be of type RunMethod")

        if method is RunMethod.direct:
            self.vb.run_process(command="/usr/bin/firefox", 
                arguments=["-new-tab",url], environment=self.env, wait=False)
        elif method is RunMethod.shell:
            self.run_shell_cmd(command="/usr/bin/firefox -new-tab "+url)
        else:
            self.vb.log.add_warning("RunMethod: "+method.name+
                " is not implemented on Linux")


    def uninstall_program(self, program):
        """remove a program from the guest system with apt-get

        Arguments:
            program - name of the program to remove
        """
        cmd="sudo apt-get remove {0}\nsleep_hack\n{1}\n".format(program, 
            self.vb.password)
        self.run_shell_cmd(command=cmd)


    def uninstall_guest_additions():
        """remove the guest additions

        Warning: This can not be undone, since remote running of software is 
        very limited without guest additions!
        """

        self.uninstall_program("virtualbox-guest-*")
