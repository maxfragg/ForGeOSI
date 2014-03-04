#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

from enum import Enum
__all__ = ["VboxMode", "SessionType", "RunMethod", "ControllerType"]

class VboxMode(Enum):
	"""Basic operation mode off the VBox class
	"""
	clone = 1
	use = 2


class SessionType(Enum):
	"""Decides, if VirtualBox creates a graphical frontend for the vm or not
	"""
	headless = 1
	gui = 2
	sdl = 3
	emergencystop = 4

class RunMethod(Enum):
	"""Decides, how a program should be started
	"""
	shell = 1
	direct = 2
	start = 3
	run = 4

class ControllerType(Enum):
	"""Mass storage controller
	"""
	SATA = 1
	IDE = 2
