# mimic a python serial port
class CarLinkSerial:
  def __init__(self, carlink, port, baud):
    self.carlink = carlink
    self.port = port
    self.carlink.set_uart_parity(self.port, 0)
    self._baudrate = baud
    self.carlink.set_uart_baud(self.port, baud)
    self.buf = b""

  def read(self, l=1):
    tt = self.carlink.serial_read(self.port)
    if len(tt) > 0:
      self.buf += tt
    ret = self.buf[0:l]
    self.buf = self.buf[l:]
    return ret

  def write(self, dat):
    return self.carlink.serial_write(self.port, dat)

  def close(self):
    pass

  def flush(self):
    pass

  @property
  def baudrate(self):
    return self._baudrate

  @baudrate.setter
  def baudrate(self, value):
    self.carlink.set_uart_baud(self.port, value)
    self._baudrate = value
