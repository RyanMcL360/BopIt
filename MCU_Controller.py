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
import magnet, IMU          # driver files: for magnetometer and IMU 
import config as C

'''message format: using python's Struct: '<' indicates little endian, B indicates a Byte, H is two bytes
         commands: 1=shield, 2=attack, 3=jump    results: 0=timeout, 1=success, 2=wrong input'''
#CMD_FMT is command format, transmits from hub to controller
CMD_FMT = "<BBH"      # round_id, command, window_ms
#RES_FMT is response format, transmits from controller back to hub
RES_FMT = "<BBH"     # round_id, player_id, reaction_ms

#setup
sta = network.WLAN(network.STA_IF)
sta.active(True)                #WIFI station mode on
print(sta.config("mac"))        # note each board's MAC; the hub's MAC goes in config.py

e = aioespnow.AIOESPNow()
e.active(True)                  #ESP-NOW on
e.add_peer(C.HUB_MAC)           # needed so the controller can reply to the hub

i2c = I2C(0, scl=Pin(C.SCL), sda=Pin(C.SDA), freq=400000)
mag = magnet.LIS3MDL(i2c)
imu = IMU.BMI270(i2c)
button = Pin(C.BTN, Pin.IN, Pin.PULL_UP)     # pressed = 0

audio = I2S(0, sck=Pin(C.BCLK), ws=Pin(C.LRC), sd=Pin(C.DIN),
            mode=I2S.TX, bits=16, format=I2S.MONO, rate=16000, ibuf=8192)
writer = asyncio.StreamWriter(audio)    #lets us await write without freezing other tasks

# Load the clips into RAM at boot so playback starts instantly (skip the 44-byte WAV header)
clips = {n: open(f, "rb").read()[44:] for n, f in C.CLIPS.items()}

'''Shared state dictionary'''
state = {"round": 0, "cmd": None, "deadline": 0, "start": 0, "active": False}


# async def to operate in parallel
''' listener() function receives from hub and starts the countdown'''
async def listener():
    async for mac, msg in e:                                # wakes only when a packet arrives
        rnd, cmd, window = struct.unpack(CMD_FMT, msg)      # unpacks the command struct
        now = time.ticks_ms()                               # start timer
        state.update(round=rnd, cmd=cmd, start=now,
                     deadline=time.ticks_add(now, window), active=True) # update shared state
        asyncio.create_task(play(cmd))

''' inputs() function polls the three different inputs'''
async def inputs():
    mag_base = baseline_mag()            # average a few readings at startup
    while True:
        if state["active"]:              # if we are in active state, pooling starts
            got = None
            if button.value() == 0:      #based on input values, assign got the first user input, no matter correctness
                got = C.JUMP            
            elif abs(mag.magnitude() - mag_base) > C.MAG_THRESH:    #magnetometer threshold
                got = C.SHIELD
            elif abs(imu.accel_magnitude() - 1.0) > C.SHAKE_THRESH: #magnitude of acceleration, orientation doesn't matter
                got = C.ATTACK
            if got is not None:
                finish(1 if got == state["cmd"] else 2)     #correct = 1, incorrect = 2
            elif time.ticks_diff(time.ticks_ms(), state["deadline"]) >= 0:
                finish(0)                # timeout
        await asyncio.sleep_ms(5)

'''finish(result) takes the result from input and packs it to send to hub'''
def finish(result):
    state["active"] = False                                         #make state off
    reaction = time.ticks_diff(time.ticks_ms(), state["start"])     #calculate reaction time

    #don't send result, just negate reaction time is wrong input or timeout 
    if result == 0 | 2: 
        reaction = -reaction
    e.send(C.HUB_MAC, struct.pack(RES_FMT, state["round"], C.PLAYER_ID,  reaction))  #package struct

#audio player
async def play(cmd):
    await writer.awrite(clips[cmd])      # non-blocking, so input polling keeps running


#main
async def main():
    await asyncio.gather(listener(), inputs())

asyncio.run(main())