#!/bin/bash
id=`vboxmanage list vms | grep "$@" | awk {'print $2'}`
echo "id: " $id
pid=`ps -ef | grep $id`
echo "pid: " $pid