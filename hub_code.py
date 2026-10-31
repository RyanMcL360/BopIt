# Brawl It Hub code

from machine import Pin
import random
import time
import network
import espnow
import struct

'''
Five steps for the hub
1. Task select
2. Reaction threshold
3. Compare timestamps from players
4. Update values
5. Check for winner
'''

# health and damage
startingHealth = 5
damage = 1

# timing in ms
startThreshold = 3000
thresholdStep = 200
minThreshold = 1000

# pause between each prompt in ms
delayMin = 1500
delayMax = 3500

# initialize button (pin 4 - GPIO)
button = Pin(4, Pin.IN, Pin.PULL_UP)

# ESP NOW setup

# get station
sta = network.WLAN(network.WLAN.IF_STA)

# reset wifi
sta.active(False)

# turn wifi back on
sta.active(True)

# set the channel
sta.config(channel = 1)

# turn on espnow
e = espnow.ESPNow()
e.active(True)

# set to broadcast to all peers
BROADCAST = b'\xff' * 6
e.add_peer(BROADCAST)

# set up signature for both hub and controller
SIG = 0x35

# command sent to controllers format
# signature, round, command, threshold (ms)
CMD_FMT = "<BBBH"

# response from controllers format
# signature, round, playerID, timestamp (ms)
RES_FMT = "<BBBh"

# register MAC addresses of both controllers
CONTROLLER1_MAC = b'\x80\x45\x6b\x2d\x1b\x48'
CONTROLLER2_MAC = b'\x80\x45\x6b\x29\xf0\x9c'

# function to check if controllers are on
def controllersReady(tries = 3, waitMs = 300):
    ready1 = False
    ready2 = False

    PING = 0
    PING_ROUND = 255

    for attempt in range(tries):

        # throw old values away
        while True:
            mac, msg = e.recv(0)
            if mac == None:
                break

        # broadcast to ping controllers
        e.send(BROADCAST, struct.pack(CMD_FMT, SIG, PING_ROUND, PING, 0))
        sentAt = time.ticks_ms()

        # wait for both responses or the deadline
        while((not ready1 or not ready2) and time.ticks_diff(time.ticks_ms(), sentAt) < waitMs):
            # get the mac of sender and msg of sender
            mac, msg = e.recv(50)

            # if the msg is None or not our size, continue
            if (msg == None) or (len(msg) != struct.calcsize(RES_FMT)):
                continue

            # if it is our size, unpack it
            s, rnd, player, t = struct.unpack(RES_FMT, msg)

            # check to make sure it is our signature and right round
            if (s != SIG) or (rnd != PING_ROUND):
                continue

            # set whichever player ready
            if (player == 1) and (mac == CONTROLLER1_MAC):
                ready1 = True
            elif (player == 2) and (mac == CONTROLLER2_MAC):
                ready2 = True

        if ready1 and ready2:
            return True
    return False

# outer loop to always run when the game is turned on
while(True):

    # ret current state of the button
    pressed = button.value()

    # check whether the button is pressed once and then 20 ms later to prevent accidental noise trigger
    if(not pressed):

        # delay
        time.sleep_ms(20)
        pressed = button.value()

        # if the start button still is pressed, start the game
        if(not pressed):

            # make sure players are ready
            if (not controllersReady(3, 500)):
                print("Controllers Not Ready - Game Not Started")
                continue
    
            print("Game is Starting")

            player1Health = startingHealth
            player2Health = startingHealth
            player1Win = False
            player2Win = False
            draw = False
            gameOver = False
            roundNo = 0
            aborted = False
            
            while(not gameOver):
                
                # random delay before task
                delay = random.randint(delayMin, delayMax)
                time.sleep_ms(delay)


                # 1. Task Select
                task = random.randint(1, 3)

                # 2. Reaction threshold
                threshold = startThreshold - (thresholdStep * roundNo)

                if (threshold < minThreshold):
                    threshold = minThreshold
                

                # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # Transmit task to the controllers # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # # # # # # # # # #

                while True:
                    senderMac, senderMsg = e.recv(0)
                    if senderMac is None:
                        break
                packet = struct.pack(CMD_FMT, SIG, roundNo, task, threshold)
                e.send(BROADCAST, packet)
                sentAt = time.ticks_ms()
                print("Sent Task")

                # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
                # # # # # Receive timestamp from the controllers # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

                # clear timestamps and set deadline to get packets back
                timestamp1 = None
                timestamp2 = None
                deadline = threshold + 500

                # wait for both timestamps or the deadline
                while((timestamp1 == None or timestamp2 == None) and time.ticks_diff(time.ticks_ms(), sentAt) < deadline):

                    # get the mac of sender and msg of sender
                    mac, msg = e.recv(50)

                    # if the msg is None or not our size, continue
                    if (msg == None) or (len(msg) != struct.calcsize(RES_FMT)):
                        continue

                    # if it is our size, unpack it
                    s, rnd, player, t = struct.unpack(RES_FMT, msg)

                    # check to make sure it is our signature and right round
                    if (s != SIG) or (rnd != roundNo):
                        continue

                    # check to make sure its actually the players
                    if (player == 1 and mac != CONTROLLER1_MAC) or (player == 2 and mac != CONTROLLER2_MAC):
                        continue

                    if (player == 1) and (timestamp1 == None):
                        timestamp1 = t
                    elif (player == 2) and (timestamp2 == None):
                        timestamp2 = t

                # check to make sure it stopped searching because it got responses
                # if it stopped due to deadline, error and end game
                if (timestamp1 == None) or (timestamp2 == None):
                    print("Controller Connection Error - Game Aborted")
                    aborted = True
                    gameOver = True
                    continue

                print("Packet Received")
                    

                # 3. Compare timestamps from players
                # 4. Update values

                # check if either are wrong or too slow
                if(timestamp1 < 0 or timestamp2 < 0):
                    # decrease health of whoever is wrong and go next
                    if(timestamp1 < 0):
                        print("Player 1 Takes Damage (slow or wrong)")
                        player1Health -= damage
                    
                    if(timestamp2 < 0):
                        print("Player 2 Takes Damage (slow or wrong)")
                        player2Health -= damage
                # if neither are wrong and if neither are too slow, check who was faster
                elif(timestamp1 < timestamp2):
                    # player1 was faster and won
                    print("Player 2 Takes Damage (Player 1 Won)")
                    player2Health -= damage
                
                elif(timestamp2 < timestamp1):
                    # player2 was faster and won
                    print("Player 1 Takes Damage (Player 2 Won)")
                    player1Health -= damage
                    
                else:
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    print("Players Tied - No Damage Dealt")
                
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
                # # # # # Display health and status of each input (wrong, too slow, who won) # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

                # 5. Check for winner
                
                # check to make sure neither player is at 0
                # if at 0, game is over
                if(player1Health <= 0 and player2Health <= 0):
                    print("Both Players Out of Health - Draw")
                    gameOver = True
                    draw = True
                
                elif(player1Health <= 0):
                    print("Player 2 Wins!")
                    player2Win = True
                    gameOver = True
                            
                elif(player2Health <= 0):
                    print("Player 1 Wins!")
                    player1Win = True
                    gameOver = True

                roundNo += 1

            # # # # # # # # # # # # # # # # # # # # # # # # #
            # # # # # # # # # # # # # # # # # # # # # # # # #
            # # # # # Display winner message on hub # # # # # 
            # # # # # # # # # # # # # # # # # # # # # # # # #
            # # # # # # # # # # # # # # # # # # # # # # # # #

            # wait 5 seconds before allowing another game to start
            time.sleep(5)