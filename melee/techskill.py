"""Helper functions for with some techskill examples"""
from melee import enums

"""Frame-perfect Multishines as Fox"""
def multishine(ai_state, controller):
    #If standing, shine
    if ai_state.action == enums.Action.STANDING:
        controller.press_button(enums.Button.BUTTON_B)
        controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0)
        return

    #Shine on frame 3 of knee bend, else nothing
    if ai_state.action == enums.Action.KNEE_BEND:
        if ai_state.action_frame == 3:
            controller.press_button(enums.Button.BUTTON_B)
            controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0)
            return
        else:
            controller.empty_input()
            return

    isInShineStart = (ai_state.action == enums.Action.DOWN_B_STUN or
            ai_state.action == enums.Action.DOWN_B_GROUND_START)

    #Jump out of shine
    if isInShineStart and ai_state.action_frame >= 4 and ai_state.on_ground:
        controller.press_button(enums.Button.BUTTON_Y)
        return

    if ai_state.action == enums.Action.DOWN_B_GROUND:
        controller.press_button(enums.Button.BUTTON_Y)
        return

    controller.empty_input()

"""Spam upsmashes"""
def upsmashes(ai_state, controller):
    if ai_state.action == enums.Action.STANDING:
        controller.tilt_analog(enums.Button.BUTTON_C, .5, 1)
        return

    controller.empty_input()
