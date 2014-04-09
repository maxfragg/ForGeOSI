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
from time import gmtime, strftime
import testcase01linux
import testcase01win
import testcase02
import testcase03


def usage():
    print 'testcase.py -m <virtualmachine> -o <outputdir> -t <testcase>'


def main(argv):
    """Runs a single testcase, wraps argument parsing and checking
    """
    verbose = False
    run = ''
    try:
        opts, args = getopt.getopt(argv, "hvm:o:t:r:", ["machine=", "output=",
                                                        "testcase=", "run="])
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
            testcase = arg
        elif opt in ("-r", "--run"):
            run = arg
        else:
            usage()
            sys.exit()

    if verbose:
        print 'run: '+run
        print '\tvm: '+vm
        print '\tout:'+out
        print '\ttestcase: '+testcase

    if testcase in ("01l", "testcase01linux"):
        tc = testcase01linux
    elif testcase in ("01w", "testcase01win"):
        tc = testcase01win
    elif testcase in ("02", "testcase02"):
        tc = testcase02
    elif testcase in ("03", "testcase03"):
        tc = testcase03

    timestamp = strftime("%Y-%m-%d_%H:%M:%S", gmtime())

    print vm + " " + out + " " + timestamp + "_" + vm + "_" + str(run)

    tc.run(vm=vm, output=out, verbose=verbose,
           run=timestamp+"_"+vm+"_"+str(run))

if __name__ == "__main__":
    main(sys.argv[1:])
