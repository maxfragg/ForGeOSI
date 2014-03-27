#!/bin/bash
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#
# Automated testcase runner and limited preevaluation to save diskspace
# Requires vboxmanage, the sleuth kit including fiwalk and idifference
#


if [[ $1 == '-h' || $1 == '--help' ]]; then
	echo "usage: ./runtest.sh -m <machine> -t <testcase> -o <output dir> -n <number of runs>"
	exit
fi

while [[ $# > 1 ]]
do
key="$1"
shift

case $key in
    -m|--machine)
    MACHINE="$1"
    shift
    ;;
    -n|--runs)
    RUNS="$1"
    shift
    ;;
    -t|--testcase)
    TESTCASE="$1"
    shift
    ;;
    -o|--output)
	OUTPUT="$1"
	shift
	;;
    *)
    echo "unknown option $1"
    exit
    ;;
esac
done

if [ -d "$OUTPUT" ]; then
  echo "$OUTPUT already exists, please choose new directory"
  #exit
fi

mkdir -p "$OUTPUT"

BASE_DISK_UUID=`vboxmanage showvminfo $MACHINE | grep "SATA (0, 0)" | cut -d'{' -f2 | cut -d'}' -f1`

vboxmanage clonehd --format RAW "$BASE_DISK_UUID" "$OUTPUT/base.img"

for i in `seq $RUNS` ; do
	
	mkdir -p "$OUTPUT/$i"
	./testcase.py -m "$MACHINE" -t "$TESTCASE" -o "$OUTPUT/$i" -r "$i" -v

	python3 ~/git/dfxml/python/idifference.py --noatime "$OUTPUT/base.img" "$OUTPUT/$i/disk.img" > "$OUTPUT/$i/idiff.log"

	rm "$OUTPUT/$i/disk.img"
done