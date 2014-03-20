#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

from enum import Enum
__all__ = ["VboxMode", "SessionType", "RunMethod", "ControllerType"]

__doc__ = """\
Collection of enums used for parameters, meant for type safety in parameters, 
to detect invalid parameters.  
"""

class VboxMode(Enum):
    """Basic operation mode off the VBox class

    Members:
        clone
        use
    """
    clone = 1
    use = 2


class SessionType(Enum):
    """Decides, if VirtualBox creates a graphical frontend for the vm or not

    Members:
        headless
        gui
        sdl
        emergencystop
    """
    headless = 1
    gui = 2
    sdl = 3
    emergencystop = 4

class RunMethod(Enum):
    """Decides, how a program should be started

    Members:
        shell
        direct
        start
        run
    """
    shell = 1
    direct = 2
    start = 3
    run = 4

class ControllerType(Enum):
    """Mass storage controller types

    Members:
        SATA
        IDE
    """
    SATA = 1
    IDE = 2

class StopMode(Enum):
    """Modes of stopping the virtual machine

    Members:
        poweroff
        shutdown
        save_state
    """
    poweroff = 1
    shutdown = 2
    save_state = 3
    