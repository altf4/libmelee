#!/usr/bin/python3
import argparse
import signal
import sys
import time
import melee

# This example program demonstrates how to use the Melee API to run a console,
#   setup controllers, and send button presses over to a console (dolphin or Slippi/Wii)

def check_port(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 4:
        raise argparse.ArgumentTypeError("%s is an invalid controller port. \
                                         Must be 1, 2, 3, or 4." % value)
    return ivalue

parser = argparse.ArgumentParser(description='Example of libmelee in action')
parser.add_argument('--port', '-p', type=check_port,
                    help='The controller port (1-4) your AI will play on',
                    default=2)
parser.add_argument('--opponent', '-o', type=check_port,
                    help='The controller port (1-4) the opponent will play on',
                    default=1)
parser.add_argument('--debug', '-d', action='store_true',
                    help='Debug mode. Creates a CSV of all game states')
parser.add_argument('--framerecord', '-r', default=False, action='store_true',
                    help='(DEVELOPMENT ONLY) Records frame data from the match,' \
                    'stores into framedata.csv.')
parser.add_argument('--address', '-a', default="",
                    help='IP address of Slippi/Wii')
parser.add_argument('--dolphin_executable_path', '-e', default=None,
                    help='Manually specify the non-installed directory where dolphin is')
parser.add_argument('--connect_code', '-t', default="",
                    help='Direct connect code to connect to in Slippi Online')

args = parser.parse_args()

# This logger object is useful for retroactively debugging issues in your bot
#   You can write things to it each frame, and it will create a CSV file describing the match
log = None
if args.debug:
    log = melee.Logger()

# This frame data object contains lots of helper functions and values for looking up
#   various Melee stats, hitboxes, and physics calculations
framedata = melee.FrameData(args.framerecord)

# Create our Console object.
#   This will be one of the primary objects that we will interface with.
#   The Console represents the virtual or hardware system Melee is playing on.
#   Through this object, we can get "GameState" objects per-frame so that your
#       bot can actually "see" what's happening in the game
console = melee.Console(path=args.dolphin_executable_path,
                        slippi_address=args.address,
                        logger=log)

# Dolphin has an optional mode to not render the game's visuals
#   This is useful for BotvBot matches
console.render = True

# Create our Controller object
#   The controller is the second primary object your bot will interact with
#   Your controller is your way of sending button presses to the game, whether
#   virtual or physical.
controller = melee.Controller(console=console,
                              port=args.port,
                              type=melee.ControllerType.STANDARD)

controller_opponent = melee.Controller(console=console,
                                       port=args.opponent,
                                       type=melee.ControllerType.GCN_ADAPTER)

# This isn't necessary, but makes it so that Dolphin will get killed when you ^C
def signal_handler(sig, frame):
    console.stop()
    if args.debug:
        log.writelog()
        print("") #because the ^C will be on the terminal
        print("Log file created: " + log.filename)
    print("Shutting down cleanly...")
    if args.framerecord:
        framedata.save_recording()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Run the console
console.run()

# Give the console a second to actually spin up
time.sleep(2)

# Connect to the console
print("Connecting to console...")
if not console.connect():
    print("ERROR: Failed to connect to the console.")
    print("\tIf you're trying to autodiscover, local firewall settings can " +
          "get in the way. Try specifying the address manually.")
    sys.exit(-1)

# Plug our controller in
#   Due to how named pipes work, this has to come AFTER running dolphin
#   NOTE: If you're loading a movie file, don't connect the controller,
#   dolphin will hang waiting for input and never receive it
print("Connecting controller to console...")
if not controller.connect():
    print("ERROR: Failed to connect the controller.")
    sys.exit(-1)
print("Controller connected")

# Main loop
while True:
    # "step" to the next frame
    gamestate = console.step()

    # The console object keeps track of how long your bot is taking to process frames
    #   And can warn you if it's taking too long
    if console.processingtime * 1000 > 12:
        print("WARNING: Last frame took " + str(console.processingtime*1000) + "ms to process.")

    # What menu are we in?
    if gamestate.menu_state in [melee.Menu.IN_GAME, melee.Menu.SUDDEN_DEATH]:

        # Slippi Online matches assign you a random port once you're in game that's different
        #   than the one you're physically plugged into. This helper will autodiscover what
        #   port we actually are.
        discovered_port = melee.gamestate.port_detector(gamestate, controller, melee.Character.FOX)

        if discovered_port > 0:
            if args.framerecord:
                framedata._record_frame(gamestate)
            # NOTE: This is where your AI does all of its stuff!
            # This line will get hit once per frame, so here is where you read
            #   in the gamestate and decide what buttons to push on the controller
            if args.framerecord:
                melee.techskill.upsmashes(ai_state=gamestate.player[discovered_port], controller=controller)
            else:
                melee.techskill.multishine(ai_state=gamestate.player[discovered_port], controller=controller)

    else:
        melee.MenuHelper.menu_helper_simple(gamestate,
                                            controller,
                                            args.port,
                                            melee.Character.FOX,
                                            melee.Stage.POKEMON_STADIUM,
                                            args.connect_code,
                                            autostart=True,
                                            swag=True)
    if log:
        log.logframe(gamestate)
        log.writeframe()
