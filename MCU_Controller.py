'''
Bop-IT Project 2 in Junior Design
Team: Ryan McLister/ Timothy Driscoll/ Chris Wintz
Theme: Brawl-IT

MCU Controller Code : language - python
Using micropython to run trimmed version of python directly on 
    ESP32. 
'''

'''Libraries live on the firmware, when flashed, the ESP-32 will access these libraries'''

import asyncio              #asyncio to avoid audio clipping when polling
import network
import struct
import time
from machine import Pin, I2C, I2S
import aioespnow            # async wrapper for espnow (mip.install("aioespnow") if missing)
import bno055               # driver files: for magnetometer and IMU 
import config as C

G = 9.80665     #gravity value for IMU

# Set to False until the LIS3MDL magnetometer is wired up and its driver is on the board
HAVE_MAG = True
if HAVE_MAG:
    import magnet           # driver file for the magnetometer

#setup
sta = network.WLAN(network.STA_IF)
sta.active(True)                # WIFI station mode on
print(sta.config("mac"))        # hub mac in config

e = aioespnow.AIOESPNow()
e.active(True)                  # ESP-NOW on
e.add_peer(C.HUB_MAC)           # needed so the controller can reply to the hub

i2c = I2C(0, scl=Pin(C.SCL), sda=Pin(C.SDA), freq=100000)
mag = magnet.LIS3MDL(i2c) if HAVE_MAG else None
bno055.BNO055(i2c, addr=0x28)
button = Pin(C.BTN, Pin.IN, Pin.PULL_UP)     # pressed = 0

audio = I2S(0, sck=Pin(C.BCLK), ws=Pin(C.LRC), sd=Pin(C.DIN),
            mode=I2S.TX, bits=16, format=I2S.MONO, rate=C.SAMPLE_RATE, ibuf=8192)
writer = asyncio.StreamWriter(audio)    #lets us await write without freezing other tasks

# Load the clips into RAM at boot so playback starts instantly (skip the 44-byte WAV header)
clips = {n: open(f, "rb").read()[44:] for n, f in C.CLIPS.items()}

'''Shared state dictionary
   "fresh" is set by listener() when a new round starts, and cleared by inputs()'''
state = {"round": 0, "cmd": None, "deadline": 0, "start": 0, "active": False, "fresh": False}


'''helper functions'''
 
def baseline_mag():
    # average several readings at boot: the controller's own magnetic background
    total = 0
    for _ in range(C.BASELINE_SAMPLES):
        total += mag.magnitude()
        time.sleep_ms(20)
    return total / C.BASELINE_SAMPLES
 
def attack_detected():
    # True only for a strong push FORWARD along the attack axis that also dominates
    # sideways motion, so swinging the controller toward a shield doesn't count
    lin = imu.linear_accel()                                    # m/s^2, gravity removed
    axis = lin[C.ATTACK_AXIS]
    fwd = C.ATTACK_SIGN * axis / G                              # in g, positive = forward
    side_sq = lin[0] ** 2 + lin[1] ** 2 + lin[2] ** 2 - axis ** 2
    side = (side_sq if side_sq > 0 else 0) ** 0.5 / G           # sideways motion in g
    return fwd > C.ATTACK_THRESH and fwd > C.ATTACK_RATIO * side
 
 
# async def to operate in parallel
''' listener() function receives from hub and starts the countdown'''
async def listener():
    async for mac, msg in e:                                # wakes only when a packet arrives
        if len(msg) != struct.calcsize(C.CMD_FMT):
            continue                                        # not our packet shape, ignore
        sig, rnd, cmd, window = struct.unpack(C.CMD_FMT, msg)   # unpacks the command struct
        if sig != C.SIGNATURE:
            continue                                        # stray ESP-NOW traffic, ignore
        now = time.ticks_ms()                               # start timer
        state.update(round=rnd, cmd=cmd, start=now,
                     deadline=time.ticks_add(now, window),
                     active=True, fresh=True)               # update shared state
        asyncio.create_task(play(cmd))
 
''' inputs() function polls the three different inputs'''
async def inputs():
    mag_base = baseline_mag() if HAVE_MAG else 0    # average a few readings at startup
    button_ready = False
    while True:
        if state["active"]:              # if we are in active state, polling starts
            now = time.ticks_ms()
 
            if state["fresh"]:           # a new round just began
                state["fresh"] = False
                button_ready = (button.value() == 1)   # if still held from last round, wait for release
            if button.value() == 1:
                button_ready = True
 
            got = None
            if button_ready and button.value() == 0:   # jump, based on first user input, no matter correctness
                got = C.JUMP
            elif time.ticks_diff(now, state["start"]) >= C.GRACE_MS:
                # grace period over: the speaker's magnet and last round's handling have settled
                if HAVE_MAG and abs(mag.magnitude() - mag_base) > C.MAG_THRESH:   #magnetometer threshold
                    got = C.SHIELD
                elif state["cmd"] != C.SHIELD and attack_detected():              # IMU ignored during shield rounds
                    got = C.ATTACK
 
            if got is not None:
                finish(C.RESULT_SUCCESS if got == state["cmd"] else C.RESULT_WRONG)
            elif time.ticks_diff(now, state["deadline"]) >= 0:
                finish(C.RESULT_TIMEOUT)
        await asyncio.sleep_ms(C.POLL_MS)
 
'''finish(result) takes the result from input and packs it to send to hub'''
def finish(result):
    state["active"] = False                                         #make state off
    reaction = time.ticks_diff(time.ticks_ms(), state["start"])     #calculate reaction time
 
    #don't send the result code, just negate reaction time for wrong input or timeout
    if result != C.RESULT_SUCCESS:
        reaction = -reaction
    e.send(C.HUB_MAC, struct.pack(C.RES_FMT, C.SIGNATURE, state["round"], C.PLAYER_ID, reaction))
 
#audio player
async def play(cmd):
    await writer.awrite(clips[cmd])      # non-blocking, so input polling keeps running
 
 
#main
async def main():
    await asyncio.gather(listener(), inputs())
 
asyncio.run(main())
