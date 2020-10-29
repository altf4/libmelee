#!/usr/bin/python3
import melee

console = melee.Console(is_dolphin=False,
                        allow_old_version=False,
                        path="/home/altf4/Slippi/Game_20200707T155649.slp"
                        # path="/home/altf4/Code/smashbot_analysis/training_data/18_46_54 Fox + [OASI] Captain Falcon (BF).slp"
                        )
console.connect()

while True:
    gamestate = console.step()
    # step() returns None when the file ends
    if gamestate is None:
        break
    # print(gamestate.player)
    print(gamestate.frame, gamestate.player[1].stock, gamestate.player[2].stock)
