#!/usr/bin/env python3
import os
import time
import subprocess

from link import CarLink, CarLinkDFU

board_path = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
  subprocess.check_call(f"scons -C {board_path}/.. -j$(nproc) {board_path}", shell=True)

  for s in CarLink.list():
    print("putting", s, "in DFU mode")
    with CarLink(serial=s) as p:
      p.reset(enter_bootstub=True)
      p.reset(enter_bootloader=True)

  # wait for reset carlinks to come back up
  time.sleep(1)

  dfu_serials = CarLinkDFU.list()
  print(f"found {len(dfu_serials)} carlink(s) in DFU - {dfu_serials}")
  for s in dfu_serials:
    print("flashing", s)
    CarLinkDFU(s).recover()
  exit(1 if len(dfu_serials) == 0 else 0)