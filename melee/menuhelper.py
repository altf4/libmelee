"""Helper functions for navigating the Melee menus in ways that would be
    cumbersome to do on your own."""
from melee import enums

chipDown = False

"""Choose a character from the character select menu
    Intended to be called each frame while in the character select menu"""
def choosecharacter(character, ai_state, controller):
    global chipDown
    #Figure out where the character is on the select screen
    #NOTE: This assumes you have all characters unlocked
    #Positions will be totally wrong if something is not unlocked
    row = character.value // 9
    column = character.value % 9
    #The random slot pushes the bottom row over a slot, so compensate for that
    if row == 2:
        column = column+1
    #re-order rows so the math is simpler
    row = 2-row
    #Height starts at 1, plus half a box height, plus the number of rows
    target_y = 1 + 3.5 + (row * 7.0)
    #Starts at -32.5, plus half a box width, plus the number of columns
    #NOTE: Technically, each column isn't exactly the same width, but it's close enough
    target_x = -32.5 + 3.5 + (column * 7.0)
    #Wiggle room in positioning character
    wiggleroom = 1.5

    #We want to get to a state where the cursor is NOT over the character,
    # but it's selected. Thus ensuring the token is on the character
    isOverCharacter = abs(ai_state.cursor_x - target_x) < wiggleroom and \
        abs(ai_state.cursor_y - target_y) < wiggleroom
    isFarOutsideCharacter = abs(ai_state.cursor_x - target_x) > wiggleroom * 3 or \
        abs(ai_state.cursor_y - target_y) > wiggleroom * 3
    #TODO: This would be way easier if we just knew the state of the coin from gamestate
    if isFarOutsideCharacter and (ai_state.character != character):
        chipDown = False

    #Don't hold down on B, since we'll quit the menu if we do
    if controller.prev.button[enums.Button.BUTTON_B] == True:
        controller.release_button(enums.Button.BUTTON_B)
        return

    #If character is selected, and we're out of the area, then we're good. Do nothing
    if isFarOutsideCharacter and (ai_state.character == character) and chipDown:
        controller.empty_input()
        return

    #If we're in the right area, select the character
    if isOverCharacter:
        #If we're over the character, but it isn't selected,
        #   then the coin must be somewhere else.
        #   Press B to reclaim the coin
        if chipDown:
            #move away
            controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0)
            return
        else:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, .5)
            if ai_state.character != character:
                controller.press_button(enums.Button.BUTTON_B)
                chipDown = False
                return
            #Press A to select our character
            else:
                if controller.prev.button[enums.Button.BUTTON_A] == False:
                    controller.press_button(enums.Button.BUTTON_A)
                    chipDown = True
                    return
                else:
                    controller.release_button(enums.Button.BUTTON_A)
                    return
    else:
        if not chipDown:
            #If character is NOT selected and we're out of the area, then move in
            controller.release_button(enums.Button.BUTTON_A)
            #Move up if we're too low
            if ai_state.cursor_y < target_y - wiggleroom:
                controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 1)
                return
            #Move downn if we're too high
            if ai_state.cursor_y > target_y + wiggleroom:
                controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0)
                return
            #Move right if we're too left
            if ai_state.cursor_x < target_x - wiggleroom:
                controller.tilt_analog(enums.Button.BUTTON_MAIN, 1, .5)
                return
            #Move left if we're too right
            if ai_state.cursor_x > target_x + wiggleroom:
                controller.tilt_analog(enums.Button.BUTTON_MAIN, 0, .5)
                return
        else:
            #Move away
            controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0)
            return
    controller.empty_input()

"""Spam the start button"""
def skippostgame(controller):
    #Alternate pressing start and letting go
    if controller.prev.button[enums.Button.BUTTON_START] == False:
        controller.press_button(enums.Button.BUTTON_START)
    else:
        controller.release_button(enums.Button.BUTTON_START)
