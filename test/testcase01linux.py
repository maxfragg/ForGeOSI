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
    """testcase 1 for linux

    starts a vm, enters password, opens webbrowser, creates directory
    and saves an image file
    """
    vbox = forgeosi.Vbox(basename=vm, clonename="testrun"+run)
    vbox.start(session_type=forgeosi.SessionType.headless)
    time.sleep(10)
    if verbose:
        print "creating guest session"
    vbox.create_guest_session()
    if verbose:
        print "opening webbrowser"
    vbox.os.open_browser("https://en.wikipedia.org/wiki/Rhinoceros")
    time.sleep(20)
    vbox.take_screenshot(output+"/screenshot.png")
    vbox.os.make_dir()
    if verbose:
        print "downloading picture"    
    vbox.os.download_file(url=
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Diceros_bicornis.jpg/800px-Diceros_bicornis.jpg")
    time.sleep(30)
    vbox.stop(stop_mode=forgeosi.StopMode.poweroff)
    if verbose:
        print "machine stopped"
    vbox.log.write_xml_log(output+"/log.xml")
    vbox.export(path=output+"/disk.img", raw=True)
