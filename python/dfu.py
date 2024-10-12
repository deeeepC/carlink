import os
import usb1
import struct
import binascii

from .base import BaseSTBootloaderHandle
from .spi import STBootloaderSPIHandle, CarLinkSpiException
from .usb import STBootloaderUSBHandle
from .constants import FW_PATH, McuType


class CarLinkDFU:
    def __init__(self, dfu_serial: str | None):
        # try USB, then SPI
        handle: BaseSTBootloaderHandle | None
        self._context, handle = CarLinkDFU.usb_connect(dfu_serial)
        if handle is None:
            self._context, handle = CarLinkDFU.spi_connect(dfu_serial)

        if handle is None:
            raise Exception(f"failed to open DFU device {dfu_serial}")

        self._handle: BaseSTBootloaderHandle = handle
        self._mcu_type: McuType = self._handle.get_mcu_type()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if self._handle is not None:
            self._handle.close()
            self._handle = None
            if self._context is not None:
                self._context.close()

    @staticmethod
    def usb_connect(dfu_serial: str | None):
        handle = None
        context = usb1.USBContext()
        context.open()
        for device in context.getDeviceList(skip_on_error=True):
            if device.getVendorID() == 0x0483 and device.getProductID() == 0xdf11:
                try:
                    this_dfu_serial = device.open().getASCIIStringDescriptor(3)
                except Exception:
                    continue

                if this_dfu_serial == dfu_serial or dfu_serial is None:
                    handle = STBootloaderUSBHandle(device, device.open())
                    break

        return context, handle

    @staticmethod
    def spi_connect(dfu_serial: str | None):
        handle = None
        this_dfu_serial = None

        try:
            handle = STBootloaderSPIHandle()
            this_dfu_serial = CarLinkDFU.st_serial_to_dfu_serial(handle.get_uid(), handle.get_mcu_type())
        except CarLinkSpiException:
            handle = None

        if dfu_serial is not None and dfu_serial != this_dfu_serial:
            handle = None

        return None, handle

    @staticmethod
    def usb_list() -> list[str]:
        dfu_serials = []
        try:
            with usb1.USBContext() as context:
                for device in context.getDeviceList(skip_on_error=True):
                    if device.getVendorID() == 0x0483 and device.getProductID() == 0xdf11:
                        try:
                            dfu_serials.append(device.open().getASCIIStringDescriptor(3))
                        except Exception:
                            pass
        except Exception:
            pass
        return dfu_serials

    @staticmethod
    def spi_list() -> list[str]:
        try:
            _, h = CarLinkDFU.spi_connect(None)
            if h is not None:
                dfu_serial = CarLinkDFU.st_serial_to_dfu_serial(h.get_uid(), h.get_mcu_type())
                return [dfu_serial, ]
        except CarLinkSpiException:
            pass
        return []

    @staticmethod
    def st_serial_to_dfu_serial(st: str, mcu_type: McuType = McuType.F4):
        if st is None or st == "none":
            return None
        uid_base = struct.unpack("H" * 6, bytes.fromhex(st))
        return binascii.hexlify(struct.pack("!HHH", uid_base[1] + uid_base[5], uid_base[0] + uid_base[4] + 0xA, uid_base[3])).upper().decode("utf-8")

    def get_mcu_type(self) -> McuType:
        return self._mcu_type

    def reset(self):
        self._handle.jump(self._mcu_type.config.bootstub_address)

    def program_bootstub(self, code_bootstub):
        self._handle.clear_status()

        # erase all sectors
        for i in range(len(self._mcu_type.config.sector_sizes)):
            self._handle.erase_sector(i)

        self._handle.program(self._mcu_type.config.bootstub_address, code_bootstub)

    def recover(self):
        fn = os.path.join(FW_PATH, self._mcu_type.config.bootstub_fn)
        with open(fn, "rb") as f:
            code = f.read()
        self.program_bootstub(code)
        self.reset()

    @staticmethod
    def list() -> list[str]:
        ret = CarLinkDFU.usb_list()
        ret += CarLinkDFU.spi_list()
        return list(set(ret))