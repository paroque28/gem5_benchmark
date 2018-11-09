# Generic python libraries
import optparse
import os
import os.path
import sys
import datetime
import json

import Options
"""Retrieve command-line options"""

def create_tests():
    tests = {}
    tests["Cache_size"] = [16, 32, 64]#, 64, 128, 256, 512] #Kb
    tests["Predictor"] = ["local", "tourn", "bi"]
    tests["Matrix_size"] = [{"I": 4, "J": 4 ,"K": 4}, {"I": 6, "J": 6 ,"K": 6}]
    tests["done"] = []
    return tests


def get_options(Options):
    parser = optparse.OptionParser()
    Options.addCommonOptions(parser)
    Options.addSEOptions(parser)

    # base output directory to use.
    #
    # This takes precedence over gem5's built-in outdir option
    parser.add_option("--directory", type="str", default=None)
    parser.add_option("--branch_predictor", type="str", default="local")
    parser.add_option("--test", type="str", default=None)  # options single vs all

    parser.set_defaults(
        # Default to writing to program.out in the current working directory
        # below, we cd to the simulation output directory
        output='./program.out',
        errout='./program.err',

        mem_size=64 * 1024 * 1024,

        caches = True
    )

    (options, args) = parser.parse_args()

    # Always enable caches, DerivO3CPU will not work without it.
    if not options.directory:
        eprint("You must set --directory to the name of an output directory to create")
        sys.exit(1)
    if options.test:
        if not os.path.exists(options.test):
            tests = create_tests()
            with open(options.test, 'w') as outfile:  
                json.dump(tests, outfile)
        else:
            with open(options.test) as json_file:  
                tests = json.load(json_file)

    assert(not options.smt)
    assert(options.num_cpus == 1)
    #assert(not options.fastmem)
    assert(not options.standard_switch)
    assert(not options.repeat_switch)
    assert(not options.take_checkpoints)
    assert(not options.fast_forward)
    assert(not options.maxinsts)
    assert(not options.l2cache)

    if args:
        print ("Error: script doesn't take any positional arguments")
        sys.exit(1)

    return options