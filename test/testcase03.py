#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]

import forgeosi
import time


def run(vm, output, verbose):

    vbox = forgeosi(basename=vm)
    vbox.start()
    time.sleep(10)
    vbox.keybord_input("12345\n")
    vbox.create_guestsession()

    vbox.stop()
    vbox.log.write_log(output+"/log.xml")
    vbox.export(path=output+"disk.vdi")
