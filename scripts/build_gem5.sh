#!/usr/bin/env bash
set -euo pipefail
# Adjust JOBS as you wish
JOBS=${JOBS:-$(nproc || sysctl -n hw.ncpu || echo 4)}


# Enter your gem5 source directory
GEM5_DIR=${GEM5_DIR:-"$(pwd)/../gem5"}


cd "$GEM5_DIR"
# Optional: pick a known-good tag
# git fetch --all --tags
# git checkout v23.2.1.0


# Build X86 SE binary
scons -j"$JOBS" build/X86/gem5.opt


echo "Built: $GEM5_DIR/build/X86/gem5.opt"
