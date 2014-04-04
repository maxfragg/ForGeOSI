#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]

import sys
import time

sys.path.append('../')

import forgeosi

rhino1 = "http://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Diceros_bicornis.jpg/800px-Diceros_bicornis.jpg"
rhino2 = "https://upload.wikimedia.org/wikipedia/commons/b/b9/D%C3%BCrer_-_Rhinoceros.jpg"
vm2 = "windows-7-base"
vm1 = "ubuntu-lts-base"

def run(vm, output, verbose, run):
    """testcase 3

    Runs 3 virtual machines, using one as server and 2 as clients, interacting
    via networt. Works only with linux systems
    """
    vboxcfg = forgeosi.VboxConfig()
    vboxcfg.get_nat_network(run)
    vbox_c1 = forgeosi.Vbox(basename=vm1, clonename="testrun"+run+"client1")
    vbox_c2 = forgeosi.Vbox(basename=vm1, clonename="testrun"+run+"client2")
    vbox_c3 = forgeosi.Vbox(basename=vm2, clonename="testrun"+run+"client3")
    vbox_s = forgeosi.Vbox(basename=vm1, clonename="testrun"+run+"server")
    p_c1 = vbox_c1.start(wait=False)
    p_c2 = vbox_c2.start(wait=False)
    p_c3 = vbox_c3.start(wait=False)
    p_s = vbox_s.start(wait=False)

    p_c1.wait_for_completion()
    p_c2.wait_for_completion()
    p_c3.wait_for_completion()
    p_s.wait_for_completion()

    time.sleep(10)

    vbox_c1.create_guest_session()
    vbox_c2.create_guest_session()
    vbox_c3.create_guest_session()
    vbox_s.create_guest_session()

    vbox_c1.add_to_nat_network(run)
    vbox_c2.add_to_nat_network(run)
    vbox_c3.add_to_nat_network(run)
    vbox_s.add_to_nat_network(run)
    vbox_s.start_network_trace(path=output+"/server.pcap")
    vbox_c1.start_network_trace(path=output+"/client1.pcap")

    ip_server = vbox_s.get_ip()
    ip_client1 = vbox_c1.get_ip()
    vbox_s.make_dir("~/server")

    if verbose:
        print "downloading files to server"
    time.sleep(10)
    vbox_s.os.download_file(rhino1, "~/server/rhino1.jpg")
    time.sleep(10)
    vbox_s.os.download_file(rhino2, "~/server/rhino2.jpg")
    time.sleep(10)

    if verbose:
        print "starting webserver"
    vbox_s.os.serve_directory("~/server", port=8080)
    time.sleep(10)

    vbox_c1.os.open_browser(ip_server+":8080/rhino1.jpg")
    vbox_c2.os.open_browser(ip_server+":8080/rhino2.jpg")
    vbox_c3.os.open_browser(ip_server+":8080/rhino2.jpg",
                            method=forgeosi.RunMethod.run)

    time.sleep(30)
    vbox_c1.os.make_dir("~/rhinopix")
    time.sleep(10)
    vbox_c1.os.download_file(ip_server+":8080/rhino1.jpg",
                             "~/rhinopix/rhino1.jpg")
    time.sleep(30)
    vbox_c2.os.run_shell_cmd("""scp """+ip_client1+""":~/rhinopix/rhino1.jpg .
        sleep_hack
        12345
        """, gui=True)

    vbox_s.stop_network_trace()
    vbox_s.stop()
    vbox_c1.stop_network_trace()
    vbox_c1.stop()
    vbox_c2.stop()
    vbox_c3.stop()

    if verbose:
        print "machines stopped"
    vbox_c1.log.write_xml_log(output+"/log_c1.xml")
    vbox_c2.log.write_xml_log(output+"/log_c2.xml")
    vbox_c3.log.write_xml_log(output+"/log_c3.xml")
    vbox_s.log.write_xml_log(output+"/log_s.xml")
    vbox_c1.export(path=output+"/disk_c1.img", raw=True)
    vbox_c1.export(path=output+"/disk_c2.img", raw=True)
    vbox_c1.export(path=output+"/disk_c3.img", raw=True)
    vbox_c1.export(path=output+"/disk_s.img", raw=True)
