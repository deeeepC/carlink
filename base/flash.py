#!/usr/bin/env python3
import os
import subprocess

from link import CarLink

base_path = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
  subprocess.check_call(f"scons -C {base_path}/.. -j$(nproc) {base_path}", shell=True)

  serials = CarLink.list()
  print(f"found {len(serials)} carlink(s) - {serials}")
  for s in serials:
    print("flashing", s)
    with CarLink(serial=s) as c:
      c.flash()
  exit(1 if len(serials) == 0 else 0)