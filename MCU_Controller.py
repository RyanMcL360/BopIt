'''
Bop-IT Project 2 in Junior Design
Team: Ryan McLister/ Timothy Driscoll/ Chris Wintz
Theme: Brawl-IT

MCU Controller Code : language - python
Using micropython to run trimmed version of python directly on 
    ESP32. 

Save this file onto the board as main.py so it runs at power-up.
'''

'''Libraries live on the board: either built into the firmware, or copied onto its filesystem'''

import asyncio              #asyncio to avoid audio clipping when polling
import network
import struct
import time
from machine import Pin, I2C
import aioespnow            # async wrapper for espnow (mip.install("aioespnow") if missing)
import bno055               # driver file for the IMU
import config as C

# Set to False until the Hall (shield) sensor is wired up and hall.py is on the board
HAVE_HALL = True
if HAVE_HALL:
    import hall             # driver file for the Hall effect shield sensor

# Audio is OFF for now (the DFPlayer isn't available yet). While it's off, play() just
# prints what it would have announced. The I2S code below is the old MAX98357A plan
# and will be replaced when the DFPlayer is added; play() is the only function that
# the rest of the program calls to make sound.
HAVE_AUDIO = False

'''message format: using python's Struct: '<' indicates little endian, B indicates a Byte,
   H is two bytes unsigned, h is two bytes signed. The formats live in config.py so the
   hub and both controllers always agree:
     CMD_FMT (hub -> controller): signature, round_id, command, window_ms
     RES_FMT (controller -> hub): signature, round_id, player_id, reaction_ms
     (reaction_ms is negative when the player failed: wrong input or timeout)
   commands: 1=shield, 2=attack, 3=jump
   connection check: round_id = 255, command = 0, window_ms = 0 -> echo the same bytes back'''

G = 9.80665

NAMES = {C.SHIELD: "SHIELD", C.ATTACK: "ATTACK", C.JUMP: "JUMP"}


def fmt_mac(m):
    return ":".join("%02x" % b for b in m)


#setup
sta = network.WLAN(network.STA_IF)
sta.active(True)                # WIFI station mode on
print("[BOOT] Player", C.PLAYER_ID, "- my MAC:", fmt_mac(sta.config("mac")))
print("[BOOT] hub MAC from config.py:", fmt_mac(C.HUB_MAC))

e = aioespnow.AIOESPNow()
e.active(True)                  # ESP-NOW on
e.add_peer(C.HUB_MAC)           # needed so the controller can reply to the hub

i2c = I2C(0, scl=Pin(C.SCL), sda=Pin(C.SDA), freq=100000)   # 100 kHz is what we tested at
print("[BOOT] I2C devices:", [hex(a) for a in i2c.scan()])
shield_sensor = hall.Hall(C.HALL_PIN) if HAVE_HALL else None
imu = bno055.BNO055(i2c, addr=0x28)
button = Pin(C.BTN, Pin.IN, Pin.PULL_UP)     # pressed = 0

if HAVE_AUDIO:
    from machine import I2S
    audio = I2S(0, sck=Pin(C.BCLK), ws=Pin(C.LRC), sd=Pin(C.DIN),
                mode=I2S.TX, bits=16, format=I2S.MONO, rate=C.SAMPLE_RATE, ibuf=8192)
    writer = asyncio.StreamWriter(audio)    #lets us await write without freezing other tasks
    # Load the clips into RAM at boot so playback starts instantly (skip the 44-byte WAV header)
    clips = {n: open(f, "rb").read()[44:] for n, f in C.CLIPS.items()}

'''Shared state dictionary
   "fresh" is set by listener() when a new round starts, and cleared by inputs()'''
state = {"round": 0, "cmd": None, "deadline": 0, "start": 0, "active": False, "fresh": False}


'''helper functions'''

def attack_detected():
    # True only for a strong push FORWARD along the attack axis that also dominates
    # sideways motion, so swinging the controller toward a shield doesn't count
    lin = imu.linear_accel()                                    # m/s^2, gravity removed
    axis = lin[C.ATTACK_AXIS]
    fwd = C.ATTACK_SIGN * axis / G                              # in g, positive = forward
    side_sq = lin[0] ** 2 + lin[1] ** 2 + lin[2] ** 2 - axis ** 2
    side = (side_sq if side_sq > 0 else 0) ** 0.5 / G           # sideways motion in g
    return fwd > C.ATTACK_THRESH and fwd > C.ATTACK_RATIO * side


def send_to_hub(data, label):
    # send raw bytes to the hub and report whether the hub acknowledged them
    try:
        acked = e.send(C.HUB_MAC, data)
    except OSError as err:
        print("[TX]", label, "FAILED to send:", err)
        return False
    if acked:
        print("[TX]", label, "sent, hub acknowledged")
    else:
        print("[TX]", label, "sent but NO ACK from hub (is the hub on, and does HUB_MAC match it?)")
    return acked


# async def to operate in parallel
''' listener() function receives from hub and starts the countdown'''
async def listener():
    print("[LISTEN] waiting for the hub...")
    async for mac, msg in e:                                # wakes only when a packet arrives
        if len(msg) != struct.calcsize(C.CMD_FMT):
            print("[RX] ignored packet from", fmt_mac(mac), "- wrong size:", len(msg), "bytes")
            continue                                        # not our packet shape, ignore
        sig, rnd, cmd, window = struct.unpack(C.CMD_FMT, msg)   # unpacks the command struct
        if sig != C.SIGNATURE:
            print("[RX] ignored packet from", fmt_mac(mac), "- bad signature:", sig)
            continue                                        # stray ESP-NOW traffic, ignore

        if rnd == C.PING_ROUND:                             # connection check from the hub
            print("[RX] connection check from hub - echoing it back")
            send_to_hub(msg, "echo")                        # echo the exact same bytes
            continue

        if cmd not in NAMES:
            print("[RX] ignored: unknown command", cmd, "in round", rnd)
            continue

        now = time.ticks_ms()                               # start timer
        state.update(round=rnd, cmd=cmd, start=now,
                     deadline=time.ticks_add(now, window),
                     active=True, fresh=True)               # update shared state
        print("[RX] round", rnd, "- command:", NAMES[cmd], "- window:", window, "ms")
        asyncio.create_task(play(cmd))

''' inputs() function polls the three different inputs'''
async def inputs():
    button_ready = False
    while True:
        if state["active"]:              # if we are in active state, polling starts
            now = time.ticks_ms()

            if state["fresh"]:           # a new round just began
                state["fresh"] = False
                button_ready = (button.value() == 1)   # if still held from last round, wait for release
                if not button_ready:
                    print("[INPUT] button is held down at round start - waiting for release")
            if button.value() == 1:
                button_ready = True

            got = None
            if button_ready and button.value() == 0:   # jump, based on first user input, no matter correctness
                got = C.JUMP
            elif time.ticks_diff(now, state["start"]) >= C.GRACE_MS:
                # grace period over: the speaker's magnet and last round's handling have settled
                if HAVE_HALL and shield_sensor.present():                         #Hall sensor switched on by the magnet
                    got = C.SHIELD
                elif state["cmd"] != C.SHIELD and attack_detected():              # IMU ignored during shield rounds
                    got = C.ATTACK

            if got is not None:
                elapsed = time.ticks_diff(now, state["start"])
                print("[INPUT] detected", NAMES[got], "after", elapsed, "ms - expected", NAMES[state["cmd"]])
                finish(C.RESULT_SUCCESS if got == state["cmd"] else C.RESULT_WRONG)
            elif time.ticks_diff(now, state["deadline"]) >= 0:
                print("[INPUT] no input before the deadline")
                finish(C.RESULT_TIMEOUT)
        await asyncio.sleep_ms(C.POLL_MS)

'''finish(result) takes the result from input and packs it to send to hub'''
def finish(result):
    state["active"] = False                                         #make state off
    reaction = time.ticks_diff(time.ticks_ms(), state["start"])     #calculate reaction time

    if result == C.RESULT_SUCCESS:
        print("[RESULT] round", state["round"], "- SUCCESS in", reaction, "ms")
    elif result == C.RESULT_WRONG:
        print("[RESULT] round", state["round"], "- FAIL: wrong input after", reaction, "ms")
    else:
        print("[RESULT] round", state["round"], "- FAIL: timeout after", reaction, "ms")

    #don't send the result code, just negate reaction time for wrong input or timeout
    if result != C.RESULT_SUCCESS:
        reaction = -reaction
    print("[TX] result: round", state["round"], "player", C.PLAYER_ID, "reaction_ms", reaction)
    send_to_hub(struct.pack(C.RES_FMT, C.SIGNATURE, state["round"], C.PLAYER_ID, reaction), "result")

#audio player
async def play(cmd):
    if HAVE_AUDIO:
        await writer.awrite(clips[cmd])      # non-blocking, so input polling keeps running
    else:
        print("[AUDIO] (disabled) would announce:", NAMES[cmd], "IT!")


#main
async def main():
    print("[BOOT] controller ready")
    await asyncio.gather(listener(), inputs())

asyncio.run(main())