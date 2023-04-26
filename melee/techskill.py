"""Helper functions for with some techskill examples"""
from melee import enums

def multishine(ai_state, controller):
    """ Frame-perfect Multishines as Fox """
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
        controller.release_all()
        return

    shine_start = (ai_state.action == enums.Action.DOWN_B_STUN or
                   ai_state.action == enums.Action.DOWN_B_GROUND_START)

    #Jump out of shine
    if shine_start and ai_state.action_frame >= 4 and ai_state.on_ground:
        controller.press_button(enums.Button.BUTTON_Y)
        return

    if ai_state.action == enums.Action.DOWN_B_GROUND:
        controller.press_button(enums.Button.BUTTON_Y)
        return

    controller.release_all()

def upsmashes(ai_state, controller):
    """ Spam upsmashes """
    if ai_state.action == enums.Action.STANDING:
        controller.tilt_analog(enums.Button.BUTTON_C, .5, 1)
        return

    controller.release_all()

dashback_frame = -123


def latency_test(gamestate, ai_state, controller):
    """Tests for latency by dash dancing and gradually increasing delay

    Returns number of frames of delay (-1 if not applicable)
    """
    global dashback_frame

    # First, get to center stage
    if abs(ai_state.position.x) > 20:
        dashback_frame = -123
        controller.tilt_analog(enums.Button.BUTTON_MAIN, int(ai_state.position.x < 0), 0.5)
        return -1

    # We're now in center stage

    # Stop runing
    if ai_state.action == enums.Action.RUNNING:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 0.5)
        return -1

    # Start dashing
    if ai_state.action == enums.Action.STANDING:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, int(ai_state.position.x < 0), 0.5)
        return -1

    # Pivot
    if ai_state.action == enums.Action.TURNING and ai_state.action_frame == 1:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, int(not ai_state.facing), 0.5)
        if dashback_frame > 0:
            old_dashback = dashback_frame
            dashback_frame = -123
            return gamestate.frame - old_dashback - 1
        else:
            dashback_frame = -123
            return -1

    # Dash back and record frame we did it
    if ai_state.action == enums.Action.DASHING:
        if ai_state.action_frame > 2:
            # Only record the dashback frame the first time we dash back
            if dashback_frame < 0:
                dashback_frame = gamestate.frame
            controller.tilt_analog(enums.Button.BUTTON_MAIN, int(not ai_state.facing), 0.5)
            return -1
        else:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, int(ai_state.facing), 0.5)
            return -1

    controller.release_all()
    return -1
