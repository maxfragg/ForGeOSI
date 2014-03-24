#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]

import forgeosi
import time


def run(vm, output, verbose):
    """testcase 1

    starts a vm, enters password, opens webbrowser, creates directory
    and saves an image file
    """
    vbox = forgeosi(basename=vm)
    vbox.start()
    time.sleep(10)
    vbox.keybord_input("12345\n")
    vbox.create_guestsession()
    vbox.os.open_browser("https://en.wikipedia.org/wiki/Rhinoceros")
    time.sleep(10)
    vbox.take_screenshot(output+"/screenshot.png")
    vbox.os.make_dir()
    vbox.os.download_file(url=
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Diceros_bicornis.jpg/800px-Diceros_bicornis.jpg")
    vbox.stop()
    vbox.log.write_log(output+"/log.xml")
    vbox.export(path=output+"disk.vdi")
