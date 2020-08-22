""" Stages is a collection of helper data for information regarding stages
"""

from melee import enums

"""Get the X coordinate of the edge of the stage, approaching from off_stage
IE: This is your X coordinate when hanging on the edge
NOTE: The left edge is always the same, but negative"""
EDGE_POSITION = {
    enums.Stage.BATTLEFIELD : 71.3078536987,
    enums.Stage.FINAL_DESTINATION : 88.4735488892,
    enums.Stage.DREAMLAND : 80.1791534424,
    enums.Stage.FOUNTAIN_OF_DREAMS : 66.2554016113,
    enums.Stage.POKEMON_STADIUM : 90.657852,
    enums.Stage.YOSHIS_STORY : 58.907848
}

"""Get the X coordinate of the edge of the stage, while standing on the stage
IE: This is your X coordinate when teetering on the edge
NOTE: The left edge is always the same, but negative"""
EDGE_GROUND_POSITION = {
    enums.Stage.BATTLEFIELD : 68.4000015259,
    enums.Stage.FINAL_DESTINATION : 85.5656967163,
    enums.Stage.DREAMLAND : 77.2713012695,
    enums.Stage.FOUNTAIN_OF_DREAMS : 63.3475494385,
    enums.Stage.POKEMON_STADIUM : 87.75,
    enums.Stage.YOSHIS_STORY : 56
}

def top_platform_position(gamestate):
    """Gets the position of the top platform

    Args:
        (gamestate.GameState): The current GameState

    Returns:
        (float, float, float): Tuple of height, left edge, right edge. None if no platform
    """
    if gamestate.stage == enums.Stage.FINAL_DESTINATION:
        return None
    if gamestate.stage == enums.Stage.POKEMON_STADIUM:
        return None
    if gamestate.stage == enums.Stage.BATTLEFIELD:
        return (54.40010070800781, -18.80000114440918, 18.80000114440918)
    if gamestate.stage == enums.Stage.DREAMLAND:
        return (51.42539978027344, -19.01810073852539, 19.017099380493164)
    if gamestate.stage == enums.Stage.FOUNTAIN_OF_DREAMS:
        return (42.750099182128906, -14.25, 14.25)
    if gamestate.stage == enums.Stage.YOSHIS_STORY:
        return (42.000099182128906, -15.75, 15.75)
    return None

def side_platform_position(right_platform, gamestate):
    """Gets the position of the specified side platform

    Args:
        (bool): Is it the right platform?
        (gamestate.GameState): The current GameState

    Returns:
        (float, float, float): Tuple of height, left edge, right edge
    """
    if right_platform:
        return right_platform_position(gamestate)
    else:
        return left_platform_position(gamestate)

def left_platform_position(gamestate):
    """Gets the position of the left platform

    Args:
        (gamestate.GameState): The current GameState

    Returns:
        (float, float, float): Tuple of height, left edge, right edge
    """
    if gamestate.stage == enums.Stage.FINAL_DESTINATION:
        return None
    if gamestate.stage == enums.Stage.POKEMON_STADIUM:
        return (25.000099182128906, -55, -25)
    if gamestate.stage == enums.Stage.BATTLEFIELD:
        return (27.20009994506836, -57.60000228881836, -20)
    if gamestate.stage == enums.Stage.DREAMLAND:
        return (30.14219856262207, -61.39289855957031, -31.725400924682617)
    if gamestate.stage == enums.Stage.FOUNTAIN_OF_DREAMS:
        return None #TODO
    if gamestate.stage == enums.Stage.YOSHIS_STORY:
        return (23.450098037719727, -59.5, -28.0)
    return None

def right_platform_position(gamestate):
    """Gets the position of the right platform

    Args:
        (gamestate.GameState): The current GameState

    Returns:
        (float, float, float): Tuple of height, left edge, right edge
    """
    if gamestate.stage == enums.Stage.FINAL_DESTINATION:
        return None
    if gamestate.stage == enums.Stage.POKEMON_STADIUM:
        return (25.000099182128906, 25, 55)
    if gamestate.stage == enums.Stage.BATTLEFIELD:
        return (27.20009994506836, 20, 57.60000228881836)
    if gamestate.stage == enums.Stage.DREAMLAND:
        return (30.242599487304688, 31.70359992980957, 63.074501037597656)
    if gamestate.stage == enums.Stage.FOUNTAIN_OF_DREAMS:
        return None #TODO
    if gamestate.stage == enums.Stage.YOSHIS_STORY:
        return (23.450098037719727, 28.0, 59.5)
    return None

def randall_position(gamestate):
    """Gets the current position of Randall

    Args:
        (gamestate.GameState): The current gamestate

    Returns:
        (float, float, float): (height, x_left, x_right). None if not on Yoshi's Story
    """
    if gamestate.stage != enums.Stage.YOSHIS_STORY:
        return None
    else:
        frame_count = gamestate.frame % 1200
        randall_width = 11.9

        # Top section
        if 476 < frame_count < 1016:
            start = 101.235443115234
            speed = -0.35484
            frames_in = frame_count - 477
            return (-13.64989, start - randall_width + (speed*frames_in), start + (speed*frames_in))
        # Left section
        if 1022 < frame_count < 1069:
            return (0, -103.6, -91.7) # TODO
        # Bottom section
        if (frame_count > 1075) or (frame_count < 416):
            return (-33.2489, 0, 0) # TODO
        # Right section
        if 423 < frame_count < 469:
            start = -31.160232543945312
            speed = 0.354839325
            frames_in = frame_count - 424
            return (start + (speed*frames_in), 91.35, 103.25)

        return None
        # TODO Corners


# bot right
# (416 -> 423)

# top right
# 469 -> 476
#
# top left
# 1016 -> 1022
#
# bot left
# 1069 -> 1075
