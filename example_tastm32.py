#!/usr/bin/python3

import melee
import sys
import signal
import melee.serial_helper
import time
import argparse

parser = argparse.ArgumentParser(description='Example of libmelee in action')
parser.add_argument('--lagtest', '-l',
                    action='store_true',
                    help='Test end-to-end latency',
                    default=False)
args = parser.parse_args()

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

frame_delays = {}
added_delay = 0

while True:
    # "step" to the next frame
    gamestate = console.step()
    if gamestate is not None:
        # What menu are we in?
        if gamestate.menu_state in [melee.Menu.IN_GAME, melee.Menu.SUDDEN_DEATH]:

            if 1 in gamestate.players:
                ai_state = gamestate.player[1]
                if args.lagtest:
                    # Add one ms delay every minute
                    if (gamestate.frame + 123) % 3600 == 3599:
                        added_delay += .001
                        frame_delays = {}
                        print("Now at ", added_delay * 1000, "ms delay")
                    time.sleep(added_delay)
                    if gamestate.frame % 360 == 0:
                        print(frame_delays)
                    delay = melee.techskill.latency_test(gamestate=gamestate, ai_state=ai_state, controller=controller)
                    if delay >= 0:
                        if delay not in frame_delays:
                            frame_delays[delay] = 1
                        else:
                            frame_delays[delay] += 1
                else:
                    melee.techskill.multishine(ai_state=ai_state, controller=controller)
            if log:
                log.logframe(gamestate)
                log.writeframe()
            else:
                pass
        else:
            melee.MenuHelper.menu_helper_simple(gamestate,
                                                controller,
                                                melee.Character.FOX,
                                                melee.Stage.FINAL_DESTINATION,
                                                "",
                                                costume=1,
                                                autostart=False,
                                                swag=True)
    else:
        print("Not in game")
