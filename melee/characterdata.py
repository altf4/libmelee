"""Static helper functions that provide some data about each characterself.
Note that this is data about the character IN GENERAL, not anything
to do with the current gamestate."""

from melee import enums
import csv
import os

class CharacterData():
    def __init__(self):
        #read the character data
        self.data = dict()
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + "/characterdata.csv") as csvfile:
            reader = csv.DictReader(csvfile)
            for line in reader:
                del line["Character"]
                #Convert all fields to numbers
                for key, value in line.items():
                    line[key] = float(value)
                self.data[enums.Character(line["CharacterIndex"])] = line

    def maxjumps(character):
        if character == enums.Character.JIGGLYPUFF:
            return 5
        if character == enums.Character.KIRBY:
            return 5
        return 1
