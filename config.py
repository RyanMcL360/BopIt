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
# Run this on the hub board to find its MAC:
#   import network; w = network.WLAN(network.STA_IF); w.active(True); print(w.config("mac"))
# It prints something like b'\xa0v\x4e...'. Paste those 6 bytes below.
# ---------------------------------------------------------------
HUB_MAC = b"\x80\x45\x66\x29\x99\x30"   # PLACEHOLDER, replace with the hub's real MAC

# ---------------------------------------------------------------
# Pins (ESP32-S3-DevKitC-1 N8R8)
# Avoid GPIO 26-37 (flash/PSRAM), 19/20 (USB), and strapping pins 0, 3, 45, 46.
# ---------------------------------------------------------------
# I2C bus shared by the LIS3MDL and BMI270
SDA = 8
SCL = 9

# Jump button: wire one side to the pin, the other to GND (internal pull-up used)
BTN = 23

# I2S to MAX98357A amplifier
BCLK = 5               # amp pin BCLK
LRC = 6                # amp pin LRC (word select)
DIN = 7                # amp pin DIN

# ---------------------------------------------------------------
# Commands (what the hub asks for)
# ---------------------------------------------------------------
SHIELD = 1
ATTACK = 2
JUMP = 3

# ---------------------------------------------------------------
# Results (what the controller reports back)
# ---------------------------------------------------------------
RESULT_TIMEOUT = 0
RESULT_SUCCESS = 1
RESULT_WRONG = 2

# ---------------------------------------------------------------
# Message formats (must match the hub exactly)
# ---------------------------------------------------------------
CMD_FMT = "<BBH"       # hub -> controllers: round_id, command, window_ms
RES_FMT = "<BBH"      # controller -> hub: round_id, player_id, result, reaction_ms

# ---------------------------------------------------------------
# Audio
# WAV files must be 16-bit mono PCM at 16 kHz.
# ---------------------------------------------------------------
SAMPLE_RATE = 16000

SND_SUCCESS = 10
SND_FAIL = 11

CLIPS = {
    SHIELD: "shield.wav",
    ATTACK: "attack.wav",
    JUMP: "jump.wav",
    SND_SUCCESS: "success.wav",
    SND_FAIL: "fail.wav",
}

# ---------------------------------------------------------------
# Input tuning (STARTING GUESSES, adjust by experiment)
# ---------------------------------------------------------------
POLL_MS = 5            # how often inputs are checked
GRACE_MS = 150         # ignore IMU/magnetometer this long after a round starts

MAG_THRESH = 300       # change in field magnitude that counts as "shield"
                       # (units depend on your driver; print real values to tune)
SHAKE_THRESH = 1.5     # deviation from 1 g that counts as "attack"

BASELINE_SAMPLES = 20  # readings averaged at boot for the magnetometer baseline
