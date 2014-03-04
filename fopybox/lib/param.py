#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

from enum import Enum
__all__ = ["VboxMode", "SessionType", "RunMethod", "ControllerType"]

class VboxMode(Enum):
	clone = 1
	use = 2


class SessionType(Enum):
	headless = 1
	gui = 2

class RunMethod(Enum):
	shell = 1
	direct = 2
	start = 3
	run = 4

class ControllerType(Enum):
	SATA = 1
	IDE = 2
