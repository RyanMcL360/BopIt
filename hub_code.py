# Brawl It Hub code

from machine import Pin
import random
import time

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

            player1Health = startingHealth
            player2Health = startingHealth
            player1Win = False
            player2Win = False
            draw = False
            gameOver = False
            rounds = 0
            
            while(not gameOver):
                
                # random delay before task
                delay = random.randint(delayMin, delayMax)
                time.sleep_ms(delay)


                # 1. Task Select

                tasks = ["attack", "shield", "jump"]

                taskint = random.randint(0, 2)

                task = tasks[taskint]

                # 2. Reaction threshold
                threshold = startThreshold - (thresholdStep * rounds)

                if (threshold < minThreshold):
                    threshold = minThreshold
                

                # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # Transmit task to the controllers # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # # # # # # # # # #


                # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
                # # # # # Receive timestamp from the controllers # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                timestamp1 = 0
                timestamp2 = 0

                # 3. Compare timestamps from players
                # 4. Update values

                # check if either are wrong or too slow
                if(timestamp1 < 0 or timestamp2 < 0):
                    # decrease health of whoever is wrong and go next
                    if(timestamp1 < 0):
                        player1Health -= damage
                    
                    if(timestamp2 < 0):
                        player2Health -= damage
                # if neither are wrong and if neither are too slow, check who was faster
                elif(timestamp1 < timestamp2):
                    # player1 was faster and won
                    player2Health -= damage
                
                elif(timestamp2 < timestamp1):
                    # player2 was faster and won
                    player1Health -= damage
                    
                else:
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
                    # Tie
                    pass
                
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
                # # # # # Display health and status of each input (wrong, too slow, who won) # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
                # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

                # 5. Check for winner
                
                # check to make sure neither player is at 0
                # if at 0, game is over
                if(player1Health <= 0 and player2Health <= 0):
                    gameOver = True
                    draw = True
                
                elif(player1Health <= 0):
                    player2Win = True
                    gameOver = True
                            
                elif(player2Health <= 0):
                    player1Win = True
                    gameOver = True

                rounds += 1
                            
            
        
