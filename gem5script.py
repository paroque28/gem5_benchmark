"""
This script executes a program with gem5's system call emulation mode.

Basic usage:
    path/to/gem5.opt ./gem5script.py --cmd=./path/to/executable 
            --directory=output-directory

After running the above command, output from the simulation will be placed in
output-directory including these files:
    config.ini, config.json --- the full configuration of all the internal components of
                                the simulation.

    program.out, program.err --- the output of the executable program

    stats.txt --- statistics from the simulation, such as the number of instructions
                  executed, the cache hit ratios, etc., etc.

"""

# Generic python libraries
import optparse
import os
import os.path
import sys
import datetime
import json
import shutil
# Interface to m5 simulation, implementing in gem5/src
import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import addToPath, fatal

addToPath(os.path.join('configs/common'))
addToPath(os.path.join('configs'))

# Utilities included with m5 for configuring common simulations
# from gem5/configs/common
import Options
import Simulation
from Caches import *
import MemConfig

## local functions
from options  import *
from utils import eprint


"""
Main function. This is called once at the very bottom of the script.
"""
def main(options): 
    if not options.test:
        process = create_process(options)
        run_one_simulation(options, process)
    else:
        run_all_simulations(options)

"""
Create multiple forks for all the tests
"""
def run_all_simulations(options):
    # keep track of tests that were ran
    with open(options.test) as json_file:
        tests = json.load(json_file)
    total_tests = len(tests["Cache_size"]) * len(tests["Predictor"]) * len(tests["Matrix_size"])
    current  = 0
    for c in tests["Cache_size"]:
        for p in tests["Predictor"]:
            for  m in tests["Matrix_size"]:
                current += 1
                UUID = "l1d:" + str(c)+ " BP:" + p + " M:" +str(m["I"]) + "," + str(m["J"]) + "," + str(m["K"])
                if not (UUID) in tests["done"]: 
                    options.l1d_size = str(c) +"kB"
                    options.branch_predictor = p
                    options.options = ""+ str(m["I"]) + " " + str(m["J"]) + " " + str(m["K"])
                    process = create_process(options)
                    res = run_one_simulation(options, process)
                    tests["done"].append(UUID)
                    print(UUID,  "  done!")
                    with open(options.test, 'w') as outfile:  
                        json.dump(tests, outfile) 
                else:
                    print(UUID,  "  exists!")
                print("######### TEST ", current, " of ", total_tests, " ###############" )
                


"""
Create a virtual CPU for the simulation.

To see the list of parameters you can set on the CPU, look in
gem5/src/cpu/o3/O3CPU.py.
"""
def create_cpu(options, cpu_id):
    # DerivO3CPU is the configurable out-of-order CPU model supplied by gem5
    the_cpu = DerivO3CPU(cpu_id=cpu_id)
    icache = L1_ICache(size=options.l1i_size, assoc=options.l1i_assoc)
    dcache = L1_DCache(size=options.l1d_size, assoc=options.l1d_assoc)
    if options.branch_predictor:
        if (options.branch_predictor == "tourn"):
            the_cpu.branchPred = TournamentBP()
        elif (options.branch_predictor == "bi"):
            the_cpu.branchPred =  BiModeBP()
        elif (options.branch_predictor == "local"):
            the_cpu.branchPred =  LocalBP()

    the_cpu[cpu_id].addPrivateSplitL1Caches(icache, dcache, None, None)
    the_cpu[cpu_id].createInterruptController()
    return the_cpu

"""
Create a representation of the program to run for gem5. The
supplied version expects you to run this script with --cmd
specifying the executable to run and --options specifying
the command line arguments it will receive via argv.
"""
def create_process(options):
    process = Process()
    # use realpath to change something like ./naive-matmul into
    # something like /if22/cr4bd/naive-matmul
    process.executable = os.path.realpath(options.cmd)
    if options.options != "":
        process.cmd = [options.cmd] + options.options.split()
    else:
        process.cmd = [options.cmd]

    if options.input != "":
        process.input = options.input
    if options.output != "":
        process.output = options.output
    if options.errout != "":
        process.errout = options.errout
    
    return process



"""
Based on options, fork a child process and run one simulation in it.
Uses the create_cpu function above.
"""
def run_one_simulation(options, process):
    the_dir = os.path.join(options.directory + "/l1d-" 
                        + options.l1d_size+ "_BP-" + options.branch_predictor + "_M-" + options.options.replace(" ", ",") + "_" +
                        datetime.datetime.now().strftime("%m-%d-%Hh%Mm%Ss") )
    if not os.path.exists(the_dir):
        os.makedirs(the_dir)
    pid = os.fork()
    if pid == 0:
        # in child
        os.chdir(the_dir)
        run_system_with_cpu(process, options, os.path.realpath("."),
            real_cpu_create_function=lambda cpu_id: create_cpu(options, cpu_id)
        )
        sys.exit(0)
    else:
        # in parent
        exited_pid, exit_status = os.waitpid(pid, 0)
        # Check whether child reached exit(0)
        if os.WIFEXITED(exit_status) and os.WEXITSTATUS(exit_status) != 0:
            eprint("Child did not exit normally")
            sys.exit(1)

"""
Setup a simulation to run the specified program, writing output to the specified output directory.

Optionally supports running with a different (faster) CPU for the first instrunctions.
"""
def run_system_with_cpu(
        process, options, output_dir,
        warmup_cpu_class=None,
        warmup_instructions=0,
        real_cpu_create_function=lambda cpu_id: DerivO3CPU(cpu_id=cpu_id)):
    m5.options.outdir = output_dir
    m5.core.setOutputDir(m5.options.outdir)

    m5.stats.reset()

    max_tick = options.abs_max_tick
    if options.rel_max_tick:
        max_tick = options.rel_max_tick
    elif options.maxtime:
        max_tick = int(options.maxtime * 1000 * 1000 * 1000 * 1000)

    eprint("Simulating until tick=%s" %  (max_tick))

    real_cpus = [real_cpu_create_function(0)]
    mem_mode = real_cpus[0].memory_mode()

    if warmup_cpu_class:
        warmup_cpus = [warmup_cpu_class(cpu_id=0)]
        warmup_cpus[0].max_insts_any_thread = warmup_instructions
    else:
        warmup_cpus = real_cpus

    system = System(cpu = warmup_cpus,
                    mem_mode = mem_mode,
                    mem_ranges = [AddrRange(options.mem_size)],
                    cache_line_size = options.cacheline_size)
    system.multi_thread = False
    system.voltage_domain = VoltageDomain(voltage = options.sys_voltage)
    system.clk_domain = SrcClockDomain(clock =  options.sys_clock,
                                       voltage_domain = system.voltage_domain)
    system.cpu_voltage_domain = VoltageDomain()
    system.cpu_clk_domain = SrcClockDomain(clock = options.cpu_clock,
                                           voltage_domain =
                                           system.cpu_voltage_domain)
    system.cache_line_size = options.cacheline_size
    if warmup_cpu_class:
        for cpu in real_cpus:
            cpu.clk_domain = system.cpu_clk_domain
            cpu.workload = process
            cpu.system = system
            cpu.switched_out = True
            cpu.createThreads()
        system.switch_cpus = real_cpus

    for cpu in system.cpu:
        cpu.clk_domain = system.cpu_clk_domain
        cpu.workload = process
        if options.prog_interval:
            cpu.progress_interval = options.prog_interval
        cpu.createThreads();

    MemClass = Simulation.setMemClass(options)
    system.membus = SystemXBar()
    system.system_port = system.membus.slave
    system.cpu[0].connectAllPorts(system.membus)
    MemConfig.config_mem(options, system)
    root = Root(full_system = False, system = system)

    m5.options.outdir = output_dir
    m5.instantiate(None) # None == no checkpoint
    if warmup_cpu_class:
        eprint("Running warmup with warmup CPU class (%d instrs.)" % (warmup_instructions))
    eprint("Starting simulation")
    exit_event = m5.simulate(max_tick)
    if warmup_cpu_class:
        max_tick -= m5.curTick()
        m5.stats.reset()
        # debug_print("Finished warmup; running real simulation")
        m5.switchCpus(system, real_cpus)
        exit_event = m5.simulate(max_tick)
    eprint("Done simulation @ tick = %s: %s  with exit code %d." % (m5.curTick(), exit_event.getCause(), exit_event.getCode()))
    print("#####Finished %s %s", options.cmd, options.options)
    if (exit_event.getCode() != 0):
        shutil.rmtree(m5.options.outdir)
        sys.exit(1)
    m5.stats.dump()

main(get_options(Options))
