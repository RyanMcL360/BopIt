# bno055.py -- minimal MicroPython driver for the Bosch BNO055
# Only what the Brawl-It controller needs: linear acceleration (gravity removed).
# Register values are from the BNO055 datasheet. UNTESTED on hardware: if
# something misbehaves, compare against the datasheet register map.

import time
import struct

_CHIP_ID = 0xA0

_REG_ID = 0x00
_REG_ACC = 0x08          # raw accelerometer, X LSB (6 bytes, includes gravity)
_REG_LIA = 0x28          # linear acceleration, X LSB (6 bytes, gravity removed)
_REG_UNIT_SEL = 0x3B
_REG_OPR_MODE = 0x3D
_REG_PWR_MODE = 0x3E
_REG_SYS_TRIGGER = 0x3F

MODE_CONFIG = 0x00
MODE_ACCONLY = 0x01
MODE_IMUPLUS = 0x08      # accel + gyro fusion, magnetometer OFF (good near a speaker)

_G = 9.80665


class BNO055:
    def __init__(self, i2c, addr=0x28):
        self.i2c = i2c
        self.addr = addr

        # The chip can take several hundred ms to boot, so retry for a while
        for _ in range(20):
            try:
                if self._read(_REG_ID, 1)[0] == _CHIP_ID:
                    break
            except OSError:
                pass
            time.sleep_ms(100)
        else:
            raise RuntimeError("BNO055 not found at 0x%02x" % addr)

        self._set_mode(MODE_CONFIG)
        self._write(_REG_PWR_MODE, 0x00)       # normal power
        self._write(_REG_UNIT_SEL, 0x00)       # m/s^2, degrees/s
        self._write(_REG_SYS_TRIGGER, 0x00)    # use internal oscillator
        time.sleep_ms(10)
        self._set_mode(MODE_IMUPLUS)

    # -- low level ------------------------------------------------
    def _read(self, reg, n):
        return self.i2c.readfrom_mem(self.addr, reg, n)

    def _write(self, reg, value):
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))

    def _set_mode(self, mode):
        self._write(_REG_OPR_MODE, mode)
        time.sleep_ms(30)                      # datasheet: 7 ms in, 19 ms to config

    # -- readings -------------------------------------------------
    def accel(self):
        """Raw acceleration (x, y, z) in m/s^2, INCLUDING gravity."""
        x, y, z = struct.unpack("<hhh", self._read(_REG_ACC, 6))
        return (x / 100, y / 100, z / 100)

    def linear_accel(self):
        """Acceleration (x, y, z) in m/s^2 with gravity removed (0 when still)."""
        x, y, z = struct.unpack("<hhh", self._read(_REG_LIA, 6))
        return (x / 100, y / 100, z / 100)

    def shake(self):
        """Size of the motion in g, regardless of orientation. About 0 at rest."""
        x, y, z = self.linear_accel()
        return ((x * x + y * y + z * z) ** 0.5) / _G