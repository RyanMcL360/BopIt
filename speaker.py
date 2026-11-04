from machine import Pin, UART
import time

# setup pins
DF_UART = 1
DF_TX = 5             # ESP32 TX -> DFPlayer RX (through a 1k resistor)
DF_RX = 6             # ESP32 RX <- DFPlayer TX

df_uart = UART(DF_UART, baudrate = 9600, tx = Pin(DF_TX), rx = Pin(DF_RX))

TRACKS = {
    "shield" : 1,
    "attack" : 2,
    "jump" : 3,
    "start" : 4,
    "game" : 5,
    "player1" : 6,
    "player2" : 7,
    "tie" : 8
}

def df_send(cmd, param = 0):

    # split the parameter into two bytes (high and low)
    paramHigh = (param >> 8) & 0xFF
    paramLow = param & 0xFF

    # get the total of the packet without check, start, or end
    total = 0xFF + 0x06 + cmd + 0x00 + paramHigh + paramLow

    # get checksum
    checksum = (0x10000 - total) & 0xFFFF

    # write the byte packet
    # start, version, length (6), cmd, ack, param high, param low, checksum bits, end
    df_uart.write(bytes([0x7E, 0xFF, 0x06, cmd, 0x00, paramHigh, paramLow, checksum >> 8, checksum & 0xFF, 0xEF]))

def play(sound):
    # get track from track dictionary
    track = TRACKS.get(sound)

    # if track is none, error
    if track is None:
        print("No track found!")
        return
    
    # play the audio track
    df_send(0x12, track)
    print("Audio playing!")
    return