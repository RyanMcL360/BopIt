# test_tone.py -- play three test beeps through the MAX98357A amplifier
# Run from Thonny with the green Run button. No other files are needed on the board.
# Uses the same I2S settings as main.py, so if this works, WAV playback will too.

import math
import struct
import time
from machine import Pin, I2S

# GPIO numbers on the ESP32 (these match config.py)
BCLK = 5          # amp pin BCLK
LRC = 6           # amp pin LRC (word select)
DIN = 7           # amp pin DIN

RATE = 16000      # samples per second (same as the game's WAV files)
VOLUME = 0.2      # 0.0 to 1.0. Start low; raise it once you hear something.

audio = I2S(0, sck=Pin(BCLK), ws=Pin(LRC), sd=Pin(DIN),
            mode=I2S.TX, bits=16, format=I2S.MONO, rate=RATE, ibuf=8192)


def make_tone(freq):
    """A buffer holding about 0.1 s of a sine wave at roughly `freq` Hz."""
    n = RATE // freq                          # samples in one cycle
    amp = int(32767 * VOLUME)
    cycle = struct.pack("<%dh" % n,
                        *[int(amp * math.sin(2 * math.pi * i / n)) for i in range(n)])
    return cycle * max(1, (RATE // 10) // n)


def beep(freq, ms):
    buf = make_tone(freq)
    end = time.ticks_add(time.ticks_ms(), ms)
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        audio.write(buf)                      # blocks until the data is queued


def silence(ms):
    audio.write(bytes(RATE * 2 * ms // 1000))  # zeros, 2 bytes per sample


print("Playing three beeps: low, medium, high")
for f in (400, 600, 800):
    beep(f, 400)
    silence(150)
time.sleep_ms(300)                            # let the last buffer finish playing
audio.deinit()
print("Done. Run again to repeat.")