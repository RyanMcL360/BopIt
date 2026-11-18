
# test_hall.py -- watch the digital Hall sensor
# Needs hall.py saved on the board. Run from Thonny, stop with the red Stop button.
 
import time
import hall
 
HALL_PIN = 1                      # GPIO the module's S pin is wired to
 
sensor = hall.Hall(HALL_PIN)
print("1 = no magnet, 0 = magnet detected. Bring the magnet close, try BOTH faces.")
 
last = None
while True:
    v = sensor.pin.value()
    if v != last:                 # only print when the state changes
        print("MAGNET DETECTED" if v == 0 else "no magnet", " (pin =", v, ")")
        last = v
    time.sleep_ms(20)
 


