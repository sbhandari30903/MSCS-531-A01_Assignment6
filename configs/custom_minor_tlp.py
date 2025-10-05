# custom_minor_tlp.py — gem5 v25+ MinorCPU config (SE mode, robust class resolution)
# - Sweeps Float/Simd FU latencies with opLat + issueLat = 7
# - Uses robust resolver for SimObjects that may be exported as modules (e.g., Process, Root, SimpleMemory)
# - Minimal FUs with valid OpClass names for your build

import m5
import m5.objects as mo
from m5.objects import *
import argparse
import importlib
import types

# ---------- robust SimObject class resolver ----------
def resolve_simobject(name: str):
    """
    Return the SimObject class for a given name, even if m5.objects.<name> is a module.
    Tries: m5.objects.<name> (class) -> m5.objects.<name>.<name> (class) -> importlib.
    """
    obj = getattr(mo, name, None)
    if isinstance(obj, type):
        return obj
    if isinstance(obj, types.ModuleType):
        inner = getattr(obj, name, None)
        if isinstance(inner, type):
            return inner
    try:
        mod = importlib.import_module(f"m5.objects.{name}")
        inner = getattr(mod, name, None)
        if isinstance(inner, type):
            return inner
    except Exception:
        pass
    raise TypeError(f"Could not resolve SimObject class for '{name}' (got {type(obj)})")

# ---------- CLI ----------
p = argparse.ArgumentParser()
p.add_argument('--cmd', required=True)
p.add_argument('--options', default='')
p.add_argument('--num-cores', type=int, default=4)
p.add_argument('--sys-clock', default='2GHz')
p.add_argument('--mem-size', default='2GB')
p.add_argument('--op-lat', type=int, default=3)
p.add_argument('--issue-lat', type=int, default=4)
args = p.parse_args()
assert args.op_lat + args.issue_lat == 7, "opLat + issueLat must equal 7"

# ---------- simple caches ----------
class L1ICache(Cache):
    size='32kB'; assoc=2; tag_latency=2; data_latency=2
class L1DCache(Cache):
    size='32kB'; assoc=2; tag_latency=2; data_latency=2
class L2Cache(Cache):
    size='512kB'; assoc=8; tag_latency=12; data_latency=12

# ---------- OpClasses (from your enum list) ----------
IntAluOpClasses = ["IntAlu"]
IntMulOpClasses = ["IntMult"]
IntDivOpClasses = ["IntDiv"]
MemOpClasses    = ["MemRead", "MemWrite"]

FloatSimdOpClasses = [
    "FloatAdd","FloatCmp","FloatCvt","FloatDiv","FloatMult","FloatMisc","FloatSqrt",
    "SimdFloatAdd","SimdFloatAlu","SimdFloatCmp","SimdFloatCvt","SimdFloatDiv",
    "SimdFloatMisc","SimdFloatMult","SimdFloatMultAcc","SimdFloatSqrt"
]

# ---------- Minor FUs (v25 uses opClasses) ----------
class MyIntFU(MinorFU):
    opClasses = minorMakeOpClassSet(IntAluOpClasses)
    opLat = 1; issueLat = 1

class MyIntMulFU(MinorFU):
    opClasses = minorMakeOpClassSet(IntMulOpClasses)
    opLat = 3; issueLat = 3

class MyIntDivFU(MinorFU):
    opClasses = minorMakeOpClassSet(IntDivOpClasses)
    opLat = 12; issueLat = 12

class MyMemFU(MinorFU):
    opClasses = minorMakeOpClassSet(MemOpClasses)
    opLat = 1; issueLat = 1

class MyFloatSimdFU(MinorFU):
    opClasses = minorMakeOpClassSet(FloatSimdOpClasses)
    opLat    = args.op_lat
    issueLat = args.issue_lat

class MyFUPool(MinorFUPool):
    funcUnits = [
        MyIntFU(),
        MyIntMulFU(),
        MyIntDivFU(),
        MyMemFU(),
        MyFloatSimdFU(),  # tunable Float/Simd FU
    ]

# ---------- System ----------
SystemCls       = resolve_simobject('System')
SystemXBarCls   = resolve_simobject('SystemXBar')
SimpleMemoryCls = resolve_simobject('SimpleMemory')
ProcessCls      = resolve_simobject('Process')
RootCls         = resolve_simobject('Root')

system = SystemCls()
system.clk_domain = SrcClockDomain(clock=args.sys_clock, voltage_domain=VoltageDomain())
system.mem_mode   = 'timing'
system.mem_ranges = [AddrRange(args.mem_size)]
system.membus     = SystemXBarCls()

# CPUs
system.cpu = [ MinorCPU() for _ in range(args.num_cores) ]
for cpu in system.cpu:
    cpu.executeFuncUnits = MyFUPool()  # v25 attach point
    cpu.icache = L1ICache(); cpu.dcache = L1DCache()
    cpu.icache.cpu_side = cpu.icache_port; cpu.icache.mem_side = system.membus.slave
    cpu.dcache.cpu_side = cpu.dcache_port; cpu.dcache.mem_side = system.membus.slave
    cpu.createInterruptController()
    cpu.createThreads()

# Shared L2 (simple wiring)
system.l2 = L2Cache()
system.l2.cpu_side = system.membus.master
system.l2.mem_side = system.membus.slave

# Memory (SE): SimpleMemory with robust resolution
system.mem = SimpleMemoryCls(range=system.mem_ranges[0], latency='30ns')
system.mem.port = system.membus.master

# ---------- SE workload ----------
process = ProcessCls()
process.executable = args.cmd
process.cmd = [args.cmd] + (args.options.split() if args.options else [])
for cpu in system.cpu:
    cpu.workload = process

root = RootCls(full_system=False, system=system)
m5.instantiate()
print(f"[INFO] MyFloatSimdFU opLat={args.op_lat}, issueLat={args.issue_lat} (sum=7)")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause()))

