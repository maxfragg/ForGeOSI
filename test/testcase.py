#!/usr/bin/python
# -*- coding: utf8 -*-
#
# By Maximilian Krueger
# [maximilian.krueger@fau.de]
#
# Testcase runner, parses args and runs a single testcase
#


import sys
import getopt
import testcase01
import testcase02
import testcase03


def usage():
    print 'testcase.py -m <virtualmachine> -o <outputdir> -t <testcase>'


def main(argv):
    """Runs a single testcase, wraps argument parsing and checking
    """
    verbose = False
    try:
        opts, args = getopt.getopt(argv,"hvm:o:t:", ["machine=", "output=",
            "testcase="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt == '-v':
            verbose = True
        elif opt in ("-m", "--machine"):
            vm = arg
        elif opt in ("-o", "--output"):
            out = arg
        elif opt in ("-t", "--testcase"):
            testcase = opt
        else:
            usage()
            sys.exit()

    if testcase in ("01", "testcase01"):
        tc = testcase01
    elif testcase in ("02", "testcase02"):
        tc = testcase02
    elif testcase in ("03", "testcase03"):
        tc = testcase03

    tc.run(vm=vm, output=out, verbose=verbose)

if __name__ == "__main__":
    main(sys.argv[1:])
