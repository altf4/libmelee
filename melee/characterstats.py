"""Static helper functions that provide some data about each characterself.
Note that this is data about the character IN GENERAL, not anything
to do with the current gamestate."""

from melee import enums

def maxjumps(character):
    if character == enums.Character.JIGGLYPUFF:
        return 5
    if character == enums.Character.KIRBY:
        return 5
    return 1
