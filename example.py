#!/usr/bin/python3
import melee
import argparse
import signal
import os
import sys
import time

# This example program demonstrates how to use the Melee API to run a console,
#   setup controllers, and send button presses over to a console (dolphin or Slippi/Wii)

def check_port(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 4:
         raise argparse.ArgumentTypeError("%s is an invalid controller port. \
         Must be 1, 2, 3, or 4." % value)
    return ivalue

def is_dir(dirname):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname

parser = argparse.ArgumentParser(description='Example of libmelee in action')
parser.add_argument('--port', '-p', type=check_port,
                    help='The controller port (1-4) your AI will play on',
                    default=2)
parser.add_argument('--opponent', '-o', type=check_port,
                    help='The controller port (1-4) the opponent will play on',
                    default=1)
parser.add_argument('--live', '-l',
                    help='The opponent is playing live with a GCN Adapter',
                    default=True)
parser.add_argument('--debug', '-d', action='store_true',
                    help='Debug mode. Creates a CSV of all game states')
parser.add_argument('--framerecord', '-r', default=False, action='store_true',
                    help='(DEVELOPMENT ONLY) Records frame data from the match,' \
                    'stores into framedata.csv.')
parser.add_argument('--console', '-c', default="dolphin",
                    help='Do you want to play on an Emulator (dolphin) or ' \
                    'hardware console (wii)')
parser.add_argument('--address', '-a', default="",
                    help='IP address of Slippi/Wii')
parser.add_argument('--dolphin_executable_path', '-e', default=None,
                    help='Manually specify the non-installed directory where dolphin is')

args = parser.parse_args()

log = None
if args.debug:
    log = melee.logger.Logger()

framedata = melee.framedata.FrameData(args.framerecord)

# Options here are:
#   "Standard" input is what dolphin calls the type of input that we use
#       for named pipe (bot) input
#   GCN_ADAPTER will use your WiiU adapter for live human-controlled play
#   UNPLUGGED is pretty obvious what it means
opponent_type = melee.enums.ControllerType.UNPLUGGED
if args.live:
    opponent_type = melee.enums.ControllerType.GCN_ADAPTER

is_dolphin = True
if args.console == "wii":
    is_dolphin = False
elif args.console != "dolphin":
    print("ERROR: Argument 'console' must be either 'wii' or 'dolphin'")
    sys.exit(-1)

# Create our Console object.
#   This will be one of the primary objects that we will interface with.
#   The Console represents the virtual or hardware system Melee is playing on.
#   Through this object, we can get "GameState" objects per-frame so that your
#       bot can actually "see" what's happening in the game
console = melee.console.Console(ai_port=args.port,
                                is_dolphin=True,
                                opponent_port=args.opponent,
                                opponent_type=opponent_type,
                                dolphin_executable_path=args.dolphin_executable_path,
                                logger=log)

# Dolphin has an optional mode to not render the game's visuals
#   This is useful for BotvBot matches
console.render = True

# If not set by the user, this will be an empty string, which will trigger
#   an autodiscover process
console.slippi_address = args.address

# Create our Controller object
#   The controller is the second primary object your bot will interact with
#   Your controller is your way of sending button presses to the game, whether
#   virtual or physical.
controller = melee.controller.Controller(port=args.port, console=console)

def signal_handler(signal, frame):
    console.stop()
    if args.debug:
        log.writelog()
        print("") #because the ^C will be on the terminal
        print("Log file created: " + log.filename)
    print("Shutting down cleanly...")
    if args.framerecord:
        framedata.saverecording()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Run the console
console.run()

# Give the console a second to actually spin up
time.sleep(1)

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

i = 0
# Main loop
while True:
    i += 1
    # "step" to the next frame
    gamestate = console.step()

    if(console.processingtime * 1000 > 12):
        print("WARNING: Last frame took " +
            str(console.processingtime*1000) + "ms to process.")

    # # What menu are we in?
    # # If this is a Wii, just assume we're in game
    # if args.console == "wii":
    #     # print("\n", gamestate.frame)
    #     # print(gamestate.ai_state.action, gamestate.ai_state.action_frame)
    #     if (gamestate.frame % 20) >= 10:
    #         # print("Go left")
    #         controller.tilt_analog(melee.enums.Button.BUTTON_MAIN, 0.5, 0)
    #     else:
    #         # print("Go right")
    #         controller.tilt_analog(melee.enums.Button.BUTTON_MAIN, 0.5, 1)
    #     # if (gamestate.frame % 8) > 3:
    #     #     controller.tilt_analog(melee.enums.Button.BUTTON_MAIN, 0, 0.5)
    #     # else:
    #     #     controller.tilt_analog(melee.enums.Button.BUTTON_MAIN, 1, 0.5)

    if gamestate.menu_state in [melee.enums.Menu.IN_GAME, melee.enums.Menu.SUDDEN_DEATH]:
        if args.framerecord:
            framedata.recordframe(gamestate)
        # XXX: This is where your AI does all of its stuff!
        # This line will get hit once per frame, so here is where you read
        #   in the gamestate and decide what buttons to push on the controller
        if args.framerecord:
            melee.techskill.upsmashes(ai_state=gamestate.ai_state, controller=controller)
        else:
            melee.techskill.multishine(ai_state=gamestate.ai_state, controller=controller)
    # If we're at the character select screen, choose our character
    elif gamestate.menu_state == melee.enums.Menu.CHARACTER_SELECT:
        melee.menuhelper.choosecharacter(character=melee.enums.Character.FOX,
                                        gamestate=gamestate,
                                        port=args.port,
                                        opponent_port=args.opponent,
                                        controller=controller,
                                        swag=True,
                                        start=False)
    # If we're at the postgame scores screen, spam START
    elif gamestate.menu_state == melee.enums.Menu.POSTGAME_SCORES:
        melee.menuhelper.skippostgame(controller=controller)
    # If we're at the stage select screen, choose a stage
    elif gamestate.menu_state == melee.enums.Menu.STAGE_SELECT:
        melee.menuhelper.choosestage(stage=melee.enums.Stage.POKEMON_STADIUM,
                                    gamestate=gamestate,
                                    controller=controller)
    # Flush any button presses queued up
    controller.flush()
    if log:
        log.logframe(gamestate)
        log.writeframe()
