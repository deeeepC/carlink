#!/usr/bin/env sh
set -e

DFU_UTIL="dfu-util"

scons -u -j$(nproc)

PYTHONPATH=.. python3 -c "from python import CarLink; CarLink().reset(enter_bootstub=True); CarLink().reset(enter_bootloader=True)" || true
sleep 1
$DFU_UTIL -d 0483:df11 -a 0 -s 0x08004000 -D obj/link.bin.signed
$DFU_UTIL -d 0483:df11 -a 0 -s 0x08000000:leave -D obj/bootstub.link.bin