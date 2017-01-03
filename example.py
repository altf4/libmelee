#!/usr/bin/python3
import melee
import argparse
import signal
import sys

#This example program demonstrates how to use the Melee API to run dolphin programatically,
#   setup controllers, and send button presses over to dolphin

def check_port(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 4:
         raise argparse.ArgumentTypeError("%s is an invalid controller port. \
         Must be 1, 2, 3, or 4." % value)
    return ivalue

chain = None

parser = argparse.ArgumentParser(description='Example of libmelee in action')
parser.add_argument('--port', '-p', type=check_port,
                    help='The controller port your AI will play on',
                    default=2)
parser.add_argument('--opponent', '-o', type=check_port,
                    help='The controller port the opponent will play on',
                    default=1)
parser.add_argument('--live', '-l',
                    help='The opponent playing live with a GCN Adapter',
                    default=True)
parser.add_argument('--debug', '-d', action='store_true',
                    help='Debug mode. Creates a CSV of all game state')

args = parser.parse_args()

log = None
if args.debug:
    log = melee.logger.Logger()

#Create our Dolphin object. This will be the primary object that we will interface with
dolphin = melee.dolphin.Dolphin(ai_port=args.port, opponent_port=args.opponent,
    live=args.live, logger=log)
#Create our GameState object for the dolphin instance
gamestate = melee.gamestate.GameState(dolphin)
#Create our Controller object that we can press buttons on
controller = melee.controller.Controller(port=args.port, dolphin=dolphin)

def signal_handler(signal, frame):
    dolphin.terminate()
    if args.debug:
        log.writelog()
        print("") #because the ^C will be on the terminal
        print("Log file created: " + log.filename)
    print("Shutting down cleanly...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#Run dolphin and render the output
dolphin.run(render=True)
#Plug our controller in
#   Due to how named pipes work, this has to come AFTER running dolphin
controller.connect()

#Main loop: process memory updates until the frame has incremented
for mem_update in gamestate:
    #If the frame counter has updated, then process it!
    if gamestate.update(mem_update):
        #What menu are we in?
        if gamestate.menu_state == melee.enums.Menu.IN_GAME:
            #XXX: This is where your AI does all of its stuff!
            #This line will get hit once per frame, so here is where you read
            #   in the gamestate and decide what buttons to push on the controller
            melee.techskill.multishine(ai_state=gamestate.ai_state, controller=controller)
        #If we're at the character select screen, choose our character
        elif gamestate.menu_state == melee.enums.Menu.CHARACTER_SELECT:
            melee.menuhelper.choosecharacter(character=melee.enums.Character.FOX,
                ai_state=gamestate.ai_state, controller=controller)
        #If we're at the postgame scores screen, spam START
        elif gamestate.menu_state == melee.enums.Menu.POSTGAME_SCORES:
            melee.menuhelper.skippostgame(controller=controller)
        #Flush any button presses queued up
        controller.flush()
        if log:
            log.logframe(gamestate)
            log.writeframe()
