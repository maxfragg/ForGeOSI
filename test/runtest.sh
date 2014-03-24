#!/bin/bash
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#

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

for i in `seq $RUNS` ; do
	
	mkdir -p "$OUTPUT$i"
	./testcase.py -m "$MACHINE" -t "$TESTCASE" -o "$OUTPUT$i" -r "$i" -v
done