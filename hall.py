
# hall.py -- digital Hall effect switch (A3144 / 3144E module)
#
# The A3144 is NOT analog. Its output is open-collector: it is released (reads 1)
# with no magnet, and pulled to ground (reads 0) while the SOUTH pole of a magnet
# faces the branded side of the chip, close enough.
#
# Wire the module's S (signal) pin to a GPIO. The internal pull-up below covers
# modules that have no pull-up resistor of their own.
 
from machine import Pin
 
 
class Hall:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
 
    def present(self):
        """True while a magnet is close enough to switch the sensor on."""
        return self.pin.value() == 0
 

