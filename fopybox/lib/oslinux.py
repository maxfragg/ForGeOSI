#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

from param import RunMethod #local import

class osLinux():
    """Linux specific operations 

    Classes starting with os should all implement the same interface, that offers 
    features, that depend on the opertation system, running in the VM.
    some functions require additional software:
        xdotool
    """

    def __init__(self, vb, term="/usr/bin/xterm", env=[], xdotool_extended=False):
        self.vb = vb
        self.term = term
        self.env = ["DISPLAY=:0", "USER="+vb.username, 
            "HOME=/home/"+vb.username] + env
        self.xdt = "/usr/bin/xdotool"
        self.xdte = xdotool_extended


    def run_shell_cmd(self, command, close_shell=True):
        """runs a command inside the default shell of the user
        """
        if close_shell:
            cmd = command + "\n  exit\n"
        else:
            cmd = command + "\n"

        self.vb.run_process(command=self.term, key_input=cmd, 
            environment=self.env, native_input=True, wait=True)


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
            input - String of characters to be send to the process
            window_class - X-property, usually matching the program name, which 
                can be used to find program. Will be ignored if empty
            name - X-property, might work better than window_class for some 
                usecases
            pid - process id, unique idenifier per process, but not per window, 
                is not allways part of the X-properties. Will be ignored if Zero
        """

        #type will simulate typing and interpret space '\n'
        args = self._build_xdotool_args(window_class, name, pid) + ["type"] 
        
        n = 30 #choose a sane number here, how many keys to send at once

        key_input_split = [key_input[i:i+n] for i in range(0, len(key_input), n)]

        for part in key_input_split:

            self.vb.run_process(command=self.xdt,arguments=args+[part], 
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
        
        self.run_shell_cmd("cp "+source+" "+destination)


    def move_file(self, source, destination):
        
        self.run_shell_cmd("mv "+source+" "+destination)


    def create_user(self, username, password, rootpassword):
        
        self.run_shell_cmd("sudo adduser --group --shell /bin/bash "+username+
        	"\n"+rootpassword+"\nsudo passwd "+username+"\n"+password+"\n")


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


    def open_browser(self, url="www.google.com", method=RunMethod.shell):
        """Opens a firefox browser with the given url

        Arguments:
            method - decide how to run the browser, currently "direct" and 
                "shell" are available 
        """
        if not isinstance(method, RunMethod):
            raise TypeError("method needs to be of type RunMethod")

        if method is RunMethod.direct:
            self.vb.run_process(command="/usr/bin/firefox", 
                arguments=["-new-tab",url], environment=self.env, wait=False)
        elif method is RunMethod.shell:
            self.run_shell_cmd(command="/usr/bin/firefox -new-tab "+url)


    def uninstall_program(self, program):
        """remove a program from the guest system with apt-get

        """
        cmd="sudo apt-get remove {0}\n{1}\n".format(program, self.vb.password)
        self.run_shell_cmd(command=cmd)


    def uninstall_guest_additions():
        """remove the guest additions

        Warning: This can not be undone, since remote running of software is 
        very limited without guest additions!
        """

        self.uninstall_program("virtualbox-guest-*")
