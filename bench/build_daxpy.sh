#!/usr/bin/env bash
set -euo pipefail
CC=${CC:-gcc}
CFLAGS="-O3 -march=x86-64 -mtune=native -pthread"
mkdir -p ../bench/bin
$CC $CFLAGS daxpy_mt.c -o ../bench/bin/daxpy_mt
echo "Built: $(realpath ../bench/bin/daxpy_mt)"

