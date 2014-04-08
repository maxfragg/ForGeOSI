#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]

import sys
import time

sys.path.append('../')

import forgeosi

source_path = '/media/MyCD'
dest_path = '/home/default/test'


def run(vm, output, verbose, run):
    """testcase 2

    Tests mount cd and copying of files from this cd and copying files from and
    the vm and cleanup
    """
    vbox = forgeosi.Vbox(basename=vm, clonename="testrun"+run)
    vbox.start(session_type=forgeosi.SessionType.gui)
    time.sleep(10)
    vbox.create_guest_session()
    vbox.umount_cd()
    vbox.mount_folder_as_cd(folder_path="/home/maxfragg/images")
    time.sleep(20)
    vbox.os.make_dir(dest_path)
    vbox.os.copy_file(source=source_path+'/*', destination=dest_path+'/')
    time.sleep(10)
    vbox.umount_cd()
    if verbose:
        print "copy file from vm"
    vbox.copy_from_vm(source=dest_path+'/nashorn_baby_01.jpg',
                      dest=output+'/nashorn_baby_01.jpg')
    time.sleep(30)
    vbox.stop()
    if verbose:
        print "machine stopped"
    vbox.log.write_xml_log(output+"/log.xml")
    vbox.export(path=output+"/disk.img", raw=True)
    if verbose:
        print "cleanup"
    vbox.cleanup_and_delete()
