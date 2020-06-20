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
