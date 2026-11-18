# test_imu.py -- print live shake values so you can pick SHAKE_THRESH
# Run in Thonny (green Run button) with bno055.py already saved on the board.
# Stop with the red Stop button.

import time
from machine import I2C, Pin
import bno055

i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
print("I2C devices:", [hex(a) for a in i2c.scan()])

imu = bno055.BNO055(i2c, addr=0x28)
print("BNO055 ready. Hold still, then shake it.")

peak = 0.0
while True:
    s = imu.shake()
    peak = max(peak, s)
    print("shake: %.2f g   (peak %.2f g)" % (s, peak))
    time.sleep_ms(50)