#!/bin/bash
set -e
cd "$(dirname "$0")"
export VITASDK="${VITASDK:-$(cd ../ext/vitasdk && pwd)}"
export PATH="$VITASDK/bin:$PATH"
arm-vita-eabi-gcc -Wl,-q -O2 -ffreestanding -fno-tree-loop-distribute-patterns -nostartfiles -nostdlib -o mgs3ru.elf main.c -ltaihen_stub -lSceLibKernel_stub -lSceKernelModulemgr_stub
vita-elf-create -e exports.yml mgs3ru.elf mgs3ru.velf
vita-make-fself -c mgs3ru.velf mgs3ru.suprx
ls -l mgs3ru.suprx
