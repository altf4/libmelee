from melee import enums

"""Get the X coordinate of the edge of the stage, approaching from off_stage
IE: This is your X coordinate when hanging on the edge
NOTE: The left edge is always the same, but negative"""
def edgeposition(stage):
    if stage == enums.Stage.BATTLEFIELD:
        return 71.3078536987
    if stage == enums.Stage.FINAL_DESTINATION:
        return 88.4735488892
    if stage == enums.Stage.DREAMLAND:
        return 80.1791534424
    if stage == enums.Stage.FOUNTAIN_OF_DREAMS:
        return 66.2554016113
    if stage == enums.Stage.POKEMON_STADIUM:
        return 90.657852
    if stage == enums.Stage.YOSHI_STORY:
        return 58.907848

    #TODO: Other stages? Do we care?
    return 1000;

"""Get the X coordinate of the edge of the stage, while standing on the stage
IE: This is your X coordinate when teetering on the edge
NOTE: The left edge is always the same, but negative"""
def edgegroundposition(stage):
    if stage == enums.Stage.BATTLEFIELD:
        return 68.4000015259
    if stage == enums.Stage.FINAL_DESTINATION:
        return 85.5656967163
    if stage == enums.Stage.DREAMLAND:
        return 77.2713012695
    if stage == enums.Stage.FOUNTAIN_OF_DREAMS:
        return 63.3475494385
    if stage == enums.Stage.POKEMON_STADIUM:
        return 87.75
    if stage == enums.Stage.YOSHIS_STORY:
        return 56

    #TODO: Other stages? Do we care?
    return 1000;
