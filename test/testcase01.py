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
    """testcase 1

    starts a vm, enters password, opens webbrowser, creates directory
    and saves an image file
    """
    vbox = forgeosi.Vbox(basename=vm, clonename="testrun"+run)
    vbox.start()
    time.sleep(10)
    vbox.keyboard_input("12345\n")
    vbox.create_guest_session()
    vbox.os.open_browser("https://en.wikipedia.org/wiki/Rhinoceros")
    time.sleep(10)
    vbox.take_screenshot(output+"/screenshot.png")
    vbox.os.make_dir()
    vbox.os.download_file(url=
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Diceros_bicornis.jpg/800px-Diceros_bicornis.jpg")
    vbox.stop()
    vbox.log.write_log(output+"/log.xml")
    vbox.export(path=output+"/disk.vdi")
