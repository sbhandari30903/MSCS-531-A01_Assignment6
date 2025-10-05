#!/usr/bin/env bash
set -euo pipefail
GEM5=${GEM5:-"$(pwd)/../gem5/build/X86/gem5.opt"}
CONF=${CONF:-"$(pwd)/../configs/custom_minor_tlp.py"}
BIN=${BIN:-"$(pwd)/../bench/bin/daxpy_mt"}
RUNS=${RUNS:-"$(pwd)/../runs"}
INPUT_SIZE=${INPUT_SIZE:-10000000}
CORES=${CORES:-8} # allow up to 8 cores; threads will be ≤ cores


mkdir -p "$RUNS"


# Sweep pairs and threads
pairs=("1,6" "2,5" "3,4" "4,3" "5,2" "6,1")
threads=(1 2 4 8)


for p in "${pairs[@]}"; do
IFS=',' read -r opl iss <<< "$p"
for t in "${threads[@]}"; do
if (( t > CORES )); then continue; fi
tag="op${opl}_iss${iss}_T${t}"
outdir="$RUNS/$tag"
mkdir -p "$outdir"
echo "[RUN] $tag"
"$GEM5" \
--outdir="$outdir" \
"$CONF" \
--cmd="$BIN" \
--num-cores="$CORES" \
--op-lat="$opl" --issue-lat="$iss" \
--options "$INPUT_SIZE $t" \
>"$outdir/console.log" 2>&1
done
done
