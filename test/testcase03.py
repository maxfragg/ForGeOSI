#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]

import sys
import time

sys.path.append('../')

import forgeosi


def run(vm, output, verbose, run):
    """testcase 3


    """
    vbox = forgeosi.Vbox(basename=vm, clonename="testrun"+run)
    vbox.start()
    time.sleep(10)
    vbox.keybord_input("12345\n")
    vbox.create_guest_session()

    vbox.stop()
    if verbose:
        print "machine stopped"
    vbox.log.write_log(output+"/log.xml")
    vbox.export(path=output+"/disk.img", raw=True)
