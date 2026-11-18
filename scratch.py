''' scratch file to poke at hardware and generate responses to physical input'''


#First command running in REPL: 
from machine import Pin
b = Pin(23, Pin.IN, Pin.PULL_UP)
b.value()

#command to comfirm I2C connections work and grab addresses from IMU and 
from machine import I2C, Pin
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
print([hex(a) for a in i2c.scan()])