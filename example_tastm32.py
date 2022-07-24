#!/usr/bin/python3

import melee
import sys
import signal
import melee.serial_helper

log = melee.Logger()

console = melee.Console(path=None,
                        system="gamecube",
                        copy_home_directory=False,
                        logger=log)

tastm32port = melee.serial_helper.get_tastm32_serial_port()
print("Found TAStm32 at: " + tastm32port)

controller = melee.Controller(console=console,
                              port=1,
                              serial_device=tastm32port,
                              type=melee.ControllerType.STANDARD)

# This isn't necessary, but makes it so that Dolphin will get killed when you ^C
def signal_handler(sig, frame):
    log.writelog()
    print("") #because the ^C will be on the terminal
    print("Log file created: " + log.filename)
    print("Shutting down cleanly...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("Connecting controller to console...")
if not controller.connect():
    print("ERROR: Failed to connect the controller.")
    sys.exit(-1)
print("Controller connected")

# Connect to the console
print("Connecting to console...")
if not console.connect():
    print("ERROR: Failed to connect to the console.")
    sys.exit(-1)
print("Console connected")

while True:
    # "step" to the next frame
    gamestate = console.step()
    if gamestate is not None:
        if 1 in gamestate.players:
            ai_state = gamestate.player[1]
            melee.techskill.multishine(ai_state=ai_state, controller=controller)
        if log:
            log.logframe(gamestate)
            log.writeframe()
        else:
            pass
    else:
        print("Not in game")
