#!/usr/bin/python3

import serial
import melee
import argparse
import sys
import signal 

parser = argparse.ArgumentParser(description='TASTM32 test')

parser.add_argument('--address', '-a', default="127.0.0.1",
                    help='IP address of Slippi/Wii')
args = parser.parse_args()

log = melee.Logger()

console = melee.Console(path=None,
                        is_dolphin=False,
                        copy_home_directory=False,
                        slippi_address=args.address,
                        logger=log)

controller = melee.Controller(console=console,
                              port=1,
                              type=melee.ControllerType.STANDARD)

# This isn't necessary, but makes it so that Dolphin will get killed when you ^C
# def signal_handler(sig, frame):
#     log.writelog()
#     print("") #because the ^C will be on the terminal
#     print("Log file created: " + log.filename)
#     print("Shutting down cleanly...")
#     sys.exit(0)

# signal.signal(signal.SIGINT, signal_handler)

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

shinePressedOn = -123

def multishine(gamestate, ai_state, controller):
    """ Frame-perfect Multishines as Fox """
    global shinePressedOn
    #If standing, shine
    if ai_state.action == melee.Action.STANDING:
        controller.press_button(melee.Button.BUTTON_B)
        controller.tilt_analog(melee.Button.BUTTON_MAIN, .5, 0)
        shinePressedOn = gamestate.frame
        # print("shine")
        return

    #Shine on frame 3 of knee bend, else nothing
    if ai_state.action == melee.Action.KNEE_BEND:
        if ai_state.action_frame == 3:
            controller.press_button(melee.Button.BUTTON_B)
            controller.tilt_analog(melee.Button.BUTTON_MAIN, .5, 0)
            shinePressedOn = gamestate.frame
            return
        controller.release_all()
        return

    shine_start = (ai_state.action == melee.Action.DOWN_B_STUN or
                   ai_state.action == melee.Action.DOWN_B_GROUND_START)
    if shine_start and ai_state.action_frame == 1:
        print("frames until shine: ", gamestate.frame - shinePressedOn) 

    #Jump out of shine
    if shine_start and ai_state.action_frame >= 4 and ai_state.on_ground:
        controller.press_button(melee.Button.BUTTON_Y)
        return

    if ai_state.action == melee.Action.DOWN_B_GROUND:
        controller.press_button(melee.Button.BUTTON_Y)
        return

    controller.release_all()

dashedOn = -123

while True:
    # "step" to the next frame
    gamestate = console.step()
    if gamestate is not None:
        print("TICK")
        if 1 in gamestate.players:
            ai_state = gamestate.player[1]

            # if ai_state.action == melee.Action.TURNING and ai_state.action_frame == 1:
            #     print("took this many frames to get to pivot: ", gamestate.frame - dashedOn)
            #     continue
        
            # if ai_state.action == melee.Action.DASHING and ai_state.action_frame >= 11:
            #     controller.tilt_analog(melee.Button.BUTTON_MAIN, int(not ai_state.facing), .5)
            #     continue

            
            # if ai_state.action == melee.Action.DASHING:
            #     dashedOn = gamestate.frame
            # controller.tilt_analog(melee.Button.BUTTON_MAIN, int(ai_state.position.x < 0), .5)
            # continue

            # print(ai_state.action, ai_state.action_frame)
            # if ai_state.action == melee.Action.DOWN_B_GROUND_START and gamestate.player[1].action_frame == 1:
            #     print("frames until shine: ", gamestate.frame - shinePressedOn)
            # # multishine(gamestate, ai_state=gamestate.player[1], controller=controller)
            # if ai_state.action == melee.Action.STANDING:
            #     # Shine
            #     controller.press_button(melee.Button.BUTTON_B)
            #     controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0)
            #     shinePressedOn = gamestate.frame
            # else:
            #     controller.release_all()


            # # JUMPING TEST
            # if ai_state.action == melee.Action.STANDING:
            #     # Shine
            #     controller.press_button(melee.Button.BUTTON_Y)
            #     shinePressedOn = gamestate.frame
            # else: 
            #     controller.empty_input()
            # if ai_state.action == melee.Action.KNEE_BEND and ai_state.action_frame == 1:
            #     print("frames until jump: ", gamestate.frame - shinePressedOn)

            # #Shine on frame 3 of knee bend, else nothing
            # if ai_state.action == melee.Action.KNEE_BEND:
            #     if ai_state.action_frame == 3:
            #         controller.press_button(melee.Button.BUTTON_B)
            #         controller.tilt_analog(melee.Button.BUTTON_MAIN, .5, 0)
            #         print("second shine")
            #         continue
            #     print("wait for second shine")
            #     controller.release_all()
            #     continue

            # shine_start = (ai_state.action == melee.Action.DOWN_B_STUN or
            #             ai_state.action == melee.Action.DOWN_B_GROUND_START)

            # if shine_start:
            #     if ai_state.action_frame >= 4 and ai_state.on_ground:
            #         controller.press_button(melee.Button.BUTTON_Y)  
            #         print("jump shine start")
            #         continue          
            #     else:
            #         # Keep holding down b
            #         controller.press_button(melee.Button.BUTTON_B)
            #         controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0)     

            # if ai_state.action == melee.Action.DOWN_B_GROUND:
            #     controller.press_button(melee.Button.BUTTON_Y)     
            #     print("jump")
            #     continue 

        if log:
            log.logframe(gamestate)
            log.writeframe()
        else:
            print("wat why no 1")
    else:
        print("got a None")


tastm32 = serial.Serial("/dev/ttyACM0", 115200, timeout=None, rtscts=True)
tastm32.reset_input_buffer()

# # Send reset command
# tastm32.write(b'R')
# print("wrote")
# cmd = tastm32.read(2)
# print("got: " + cmd)
# if cmd != b'\x01R':
#     # TODO Better error handling logic here
#     print("ERROR: TAStm32 did not reset properly. Try power cycling it.")


# Set to gamecube mode
tastm32.write(b'SAG\x80\x00')
cmd = tastm32.read(2)
print("cmd: " + cmd)
tastm32.reset_input_buffer()
if cmd != b'\x01S':
    # TODO Better error handling logic here
    print("ERROR: TAStm32 did not set to GCN mode. Try power cycling it.")

