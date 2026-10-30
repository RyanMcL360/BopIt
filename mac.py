# get_mac.py -- print this board's ESP-NOW (Wi-Fi station) MAC address.
#
# Run it once per board and write the result on a piece of tape on the board.
# The MAC is burned into the chip, so it never changes, even after reflashing.

import network

sta = network.WLAN(network.STA_IF)   # newer firmware also accepts network.WLAN.IF_STA
sta.active(True)                     # the radio has to be on to read the MAC

mac = sta.config('mac')              # 6 bytes
print('MAC (for labelling):  ', ':'.join('%02x' % b for b in mac))
print('MAC (paste into code):', mac)