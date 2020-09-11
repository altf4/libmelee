""" Stages is a collection of helper data for information regarding stages
"""

from melee import enums

"""Get the 4 blast zone boundaries for a given stage.  Values are tuples in 
order of (left x boundary, right x boundary, upper y boundary, lower y boundary).
Source:  Magus420 -
https://smashboards.com/threads/official-ask-anyone-frame-things-thread.313889/page-20#post-18643652"""
BLASTZONES = {
    enums.Stage.BATTLEFIELD : (-224, 224, 200, -108.8)
    enums.Stage.FINAL_DESTINATION : (-246, 246, 188, -140)
    enums.Stage.DREAMLAND : (-255, 255, 250, -123)
    enums.Stage.FOUNTAIN_OF_DREAMS : (-198.75, 198.75, 202.5, -146.25)
    enums.Stage.POKEMON_STADIUM : (-230, 230, 180, -111)
    enums.Stage.YOSHIS_STORY : (-175.7, 173.6, 168, -91)
}

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

_RANDALL_CORNER_POSITIONS = {
    416: (-33.184478759765625, 89.75263977050781),
    417: (-33.04470443725586, 90.07878112792969),
    418: (-32.904930114746094, 90.40492248535156),
    419: (-32.76515197753906, 90.73107147216797),
    420: (-32.49260711669922, 90.92455291748047),
    421: (-32.16635513305664, 91.06437683105469),
    422: (-31.840103149414062, 91.20419311523438),
    423: (-31.513851165771484, 91.3440170288086),
    469: (-15.1948881149292, 91.3371353149414),
    470: (-14.868742942810059, 91.1973648071289),
    471: (-14.542601585388184, 91.05758666992188),
    472: (-14.216456413269043, 90.91781616210938),
    473: (-13.967143058776855, 90.71036529541016),
    474: (-13.869664192199707, 90.36917877197266),
    475: (-13.772183418273926, 90.02799224853516),
    476: (-13.674698829650879, 89.68680572509766),
    1069: (-31.590042114257812, -103.554931640625),
    1070: (-31.907413482666016, -103.39625549316406),
    1071: (-32.22478485107422, -103.23756408691406),
    1072: (-32.54215621948242, -103.07887268066406),
    1073: (-32.7216796875, -102.77439880371094),
    1074: (-32.89775085449219, -102.46626281738281),
    1075: (-33.07382583618164, -102.15814208984375),
    1016: (-13.679760932922363, -101.919677734375),
    1017: (-13.819535255432129, -102.24581909179688),
    1018: (-13.959305763244629, -102.57196044921875),
    1019: (-14.099089622497559, -102.89810180664062),
    1020: (-14.320136070251465, -103.14761352539062),
    1021: (-14.6375150680542, -103.30630493164062),
    1022: (-14.954894065856934, -103.46499633789062)
}

def randall_position(frame):
    """Gets the current position of Randall

    Args:
        (int): The frame you'd like to know position for

    Note:
        The values returned here are not EXACT. But they're at most off by .001 in practice
        The reason is that Randall's location is not easily read from in-game memory. So we
        have to exprapolate it on our own. But unfortunately, it doesn't move very regularly.

    Returns:
        (float, float, float): (height, x_left, x_right)
    """
    frame_count = frame % 1200
    randall_width = 11.9

    # Top section
    if 476 < frame_count < 1016:
        start = 101.235443115234
        speed = -0.35484
        frames_in = frame_count - 477
        return (-13.64989, start - randall_width + (speed*frames_in), start + (speed*frames_in))
    # Left section
    if 1022 < frame_count < 1069:
        start = -15.2778692245483
        speed = -0.354839325
        frames_in = frame_count - 1023
        return (start + (speed*frames_in), -103.6, -91.7)
    # Bottom section
    if (frame_count > 1075) or (frame_count < 416):
        start = -101.850006103516
        speed = 0.35484
        frames_in = frame_count - 1076
        if frame_count < 416:
            frames_in = 125 + frame_count
        return (-33.2489, start + (speed*frames_in), start + randall_width + (speed*frames_in))
    # Right section
    if 423 < frame_count < 469:
        start = -31.160232543945312
        speed = 0.354839325
        frames_in = frame_count - 424
        return (start + (speed*frames_in), 91.35, 103.25)

    # Here's an ugly section. But I don't know a better way to do it
    # It just hardcodes the rounded corners of Randall's location
    position = _RANDALL_CORNER_POSITIONS[frame_count]
    return (position[0], position[1], position[1]+randall_width)
