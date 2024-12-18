import os
import enum
from typing import NamedTuple

# Update BASEDIR to point to the main carlink folder
BASEDIR = '/Volumes/rpalmr/deepC/carlink/'
FW_PATH = os.path.join(BASEDIR, "base/obj/")

USBPACKET_MAX_SIZE = 0x40

class McuConfig(NamedTuple):
    mcu: str
    mcu_idcode: int
    sector_sizes: list[int]
    sector_count: int  # total sector count, used for MCU identification in DFU mode
    uid_address: int
    block_size: int
    serial_number_address: int
    app_address: int
    app_fn: str
    bootstub_address: int
    bootstub_fn: str

    def sector_address(self, i):
        # assume bootstub is in sector 0
        return self.bootstub_address + sum(self.sector_sizes[:i])

F4Config = McuConfig(
    "STM32F4",
    0x463,
    [0x4000 for _ in range(4)] + [0x10000] + [0x20000 for _ in range(11)],
    16,
    0x1FFF7A10,
    0x800,
    0x1FFF79C0,
    0x8004000,
    "link.bin.signed",
    0x8000000,
    "bootstub.link.bin",
)


@enum.unique
class McuType(enum.Enum):
    F4 = F4Config

    @property
    def config(self):
        return self.value

MCU_TYPE_BY_IDCODE = {m.config.mcu_idcode: m for m in McuType}
