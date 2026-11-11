'''
Bop-IT Project 2 in Junior Design
Team: Ryan McLister/ Timothy Driscoll/ Chris Wintz
Theme: Brawl-IT

MCU Controller Code : language - python
Using micropython to run trimmed version of python directly on 
    ESP32. 
'''

'''
Configuration file to personalize constants/ configure GPIO/ I2C/ I2S
'''

''' identity of player, only constant that needs to be changed between two ESP's'''
PLAYER_ID = 1          # 1 for controller one, 2 for controller two

# ---------------------------------------------------------------
# Hub address
# and controller addresses
# ---------------------------------------------------------------
HUB_MAC = b"\x80\x45\x6b\x29\x99\x30"   
P1_MAC = b"\x80\x45\x6b\x2d\x1b\x48"
P2_MAC = b"\x80\x45\x6b\x29\xf0\x9c"
# ---------------------------------------------------------------
# Pins (ESP32-S3-DevKitC-1 N8R8)
# Avoid GPIO 26-37 (flash/PSRAM), 19/20 (USB), and strapping pins 0, 3, 45, 46.
# ---------------------------------------------------------------
# I2C bus shared by the LIS3MDL and BMI270
SDA = 8
SCL = 9

# Jump button: wire one side to the pin, the other to GND (internal pull-up used)
BTN = 4

# ---------------------------------------------------------------
# Commands 
# ---------------------------------------------------------------
SHIELD = 1
ATTACK = 2
JUMP = 3

# ---------------------------------------------------------------
# Results 
# ---------------------------------------------------------------
RESULT_TIMEOUT = 0
RESULT_SUCCESS = 1
RESULT_WRONG = 2

# ---------------------------------------------------------------
# Message formats
# ---------------------------------------------------------------
'''message format: using python's Struct: '<' indicates little endian, B indicates a Byte, H is two bytes
         commands: 1=shield, 2=attack, 3=jump    results: 0=timeout, 1=success, 2=wrong input'''
#CMD_FMT is command format, transmits from hub to controller
CMD_FMT = "<BBBH"      # signature, round_id, command, window_ms
#RES_FMT is response format, transmits from controller back to hub
RES_FMT = "<BBBh"     # signature, round_id, player_id, reaction_ms


ATTACK_AXIS = 1        # 0=x, 1=y, 2=z (found with the axis test script)
ATTACK_SIGN = 1        # 1 or -1 so a forward thrust is positive
ATTACK_THRESH = 1.0    # forward acceleration in g, start from your tuned value
ATTACK_RATIO = 2.0     # forward must beat sideways motion by this factor

# ---------------------------------------------------------------
# Audio
# WAV files must be 16-bit mono PCM at 16 kHz.
# ---------------------------------------------------------------
SAMPLE_RATE = 16000

# Command codes - task field in package receieved
PING_CMD = 0        # 0 is ping, echo back to start game
CMD_START = 4       # cmd = 4
CMD_END = 5         # cmd = 5

# DFPlayer Mini (UART, binary frames)
DF_UART = 1
DF_TX = 5           # ESP32 TX -> DFPlayer RX (through 1k resistor)
DF_RX = 6           # ESP32 RX <- DFPlayer TX
DF_BAUD = 9600
DF_VOLUME = 20      # 0-30

TRACKS = {          # must match the hub-side numbering / SD card file order
    "shield": 1, "attack": 2, "jump": 3, "start": 4,
    "game": 5, "player1": 6, "player2": 7, "tie": 8,
}
GAME_AUDIO_MS = 8000   # TODO: set to the real length of your "game" track

# ---------------------------------------------------------------
# Input tuning 
# ---------------------------------------------------------------
POLL_MS = 5            # how often inputs are checked
GRACE_MS = 150         # ignore IMU/magnetometer this long after a round starts

# ---------------------------------------------------------------
# Hall (shield) sensor: output wired to this GPIO (ADC1 range, away from I2C/I2S/button)
# ---------------------------------------------------------------
HALL_PIN = 1

# ---------------------------------------------------------------
# Message signature and connection check ("ping")
# Every packet starts with SIGNATURE so stray ESP-NOW traffic is ignored.
# SIGNATURE MUST be the same byte the hub uses -- confirm with whoever wrote the hub.
#
# Connection check: the hub sends a normal command packet with
#   round_id = PING_ROUND, command = PING_CMD, window_ms = PING_WINDOW
# and the controller echoes the same bytes back. That is why the hub must never
# use 255 as a real round number (wrap rounds 0..254).
# ---------------------------------------------------------------
SIGNATURE = 0x35
PING_ROUND = 255
PING_CMD = 0
PING_WINDOW = 0