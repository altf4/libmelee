import csv
import os
import math
from melee import enums
from itertools import filterfalse
from collections import defaultdict

class FrameData:
    def __init__(self, write):
        if write:
            self.csvfile = open('framedata.csv', 'a')
            fieldnames = ['character', 'action', 'frame',
                'hitbox_1_status', 'hitbox_1_size', 'hitbox_1_x', 'hitbox_1_y',
                'hitbox_2_status', 'hitbox_2_size', 'hitbox_2_x', 'hitbox_2_y',
                'hitbox_3_status', 'hitbox_3_size', 'hitbox_3_x', 'hitbox_3_y',
                'hitbox_4_status', 'hitbox_4_size', 'hitbox_4_x', 'hitbox_4_y']
            self.writer = csv.DictWriter(self.csvfile, fieldnames=fieldnames)
            self.writer.writeheader()
            self.rows = []
        #Read the existing framedata
        path = os.path.dirname(os.path.realpath(__file__))
        self.framedata = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        with open(path + "/framedata.csv") as csvfile:
            # A list of dicts containing the frame data
            csvreader = list(csv.DictReader(csvfile))
            # Build a series of nested dicts for faster read access
            for frame in csvreader:
                # Pull out the character, action, and frame
                character = enums.Character(int(frame["character"]))
                action = enums.Action(int(frame["action"]))
                action_frame = int(frame["frame"])
                self.framedata[character][action][action_frame] = \
                    {"hitbox_1_status": bool(frame["hitbox_1_status"]), \
                    "hitbox_1_size": float(frame["hitbox_1_size"]), \
                    "hitbox_1_x": float(frame["hitbox_1_x"]), \
                    "hitbox_1_y": float(frame["hitbox_1_y"]), \
                    "hitbox_2_status": bool(frame["hitbox_2_status"]), \
                    "hitbox_2_size": float(frame["hitbox_2_size"]), \
                    "hitbox_2_x": float(frame["hitbox_2_x"]), \
                    "hitbox_2_y": float(frame["hitbox_2_y"]), \
                    "hitbox_3_status": bool(frame["hitbox_3_status"]), \
                    "hitbox_3_size": float(frame["hitbox_3_size"]), \
                    "hitbox_3_x": float(frame["hitbox_3_x"]), \
                    "hitbox_3_y": float(frame["hitbox_3_y"]), \
                    "hitbox_4_status": bool(frame["hitbox_4_status"]), \
                    "hitbox_4_size": float(frame["hitbox_4_size"]), \
                    "hitbox_4_x": float(frame["hitbox_4_x"]), \
                    "hitbox_4_y": float(frame["hitbox_4_y"])}

        #Read the action state data csv
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + "/actiondata.csv") as csvfile:
            # A list of dicts containing the frame data
            self.actiondata = list(csv.DictReader(csvfile))

        #read the character data csv
        self.characterdata = dict()
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + "/characterdata.csv") as csvfile:
            reader = csv.DictReader(csvfile)
            for line in reader:
                del line["Character"]
                #Convert all fields to numbers
                for key, value in line.items():
                    line[key] = float(value)
                self.characterdata[enums.Character(line["CharacterIndex"])] = line

    #Returns boolean on if the given action is a roll
    def isroll(self, character, action):
        for line in self.actiondata:
            if line["action"] == str(action) and line["character"] == str(character) \
                and line["isroll"] == "True":
                return True
        return False

    #Returns boolean on if the given action is an attack (contains a hitbox)
    def isattack(self, character, action):
        if self.framedata[character][action]:
            return True
        return False

    def isshield(self, action):
        out = action == enums.Action.SHIELD \
            or action == enums.Action.SHIELD_START \
            or action == enums.Action.SHIELD_REFLECT \
            or action == enums.Action.SHIELD_STUN \
            or action == enums.Action.SHIELD_RELEASE
        return out

    def maxjumps(character):
        if character == enums.Character.JIGGLYPUFF:
            return 5
        if character == enums.Character.KIRBY:
            return 5
        return 1

    # Returns an attackstate enum
    #    WINDUP
    #    ATTACKING
    #    COOLDOWN
    #    NOT_ATTACKING
    def attackstate_simple(self, player):
        return self.attackstate(player.character, player.action, player.action_frame)

    def attackstate(self, character, action, frame):
        if not self.isattack(character, action):
            return enums.AttackState.NOT_ATTACKING

        if frame < self.firsthitboxframe(character, action):
            return enums.AttackState.WINDUP

        if frame > self.lasthitboxframe(character, action):
            return enums.AttackState.COOLDOWN

        return enums.AttackState.ATTACKING

    # Helper in case you want to use the current character states
    def inrange_simple(self, attacker, defender, future_frames=0):
        return self.inrange(attacker.character, attacker.action, attacker.action_frame + future_frames, \
            attacker.facing, attacker.x, attacker.y, defender.character, defender.x, defender.y)

    # Returns true if the attack specified will hit the defender specified
    # NOTE: This considers the defending character to have a single hurtbox, centered
    #       at the x,y coordinates of the player (adjusted up a little to be centered)
    def inrange(self, attacker_character, attacker_action, attacker_action_frame, \
        attacker_facing, attacker_x, attacker_y, defender_character, defender_x, defender_y):
            attackingframe = self.getframe(attacker_character, attacker_action, attacker_action_frame)
            if attackingframe is None:
                return False
            if self.attackstate(attacker_character, attacker_action, attacker_action_frame) != enums.AttackState.ATTACKING:
                return False
            # Calculate the x and y positions of all 4 hitboxes
            hitbox_1_x = float(attackingframe["hitbox_1_x"])
            hitbox_1_y = float(attackingframe["hitbox_1_y"]) + attacker_y
            hitbox_2_x = float(attackingframe["hitbox_2_x"])
            hitbox_2_y = float(attackingframe["hitbox_2_y"]) + attacker_y
            hitbox_3_x = float(attackingframe["hitbox_3_x"])
            hitbox_3_y = float(attackingframe["hitbox_3_y"]) + attacker_y
            hitbox_4_x = float(attackingframe["hitbox_4_x"])
            hitbox_4_y = float(attackingframe["hitbox_4_y"]) + attacker_y

            if not attacker_facing:
                hitbox_1_x *= -1
                hitbox_2_x *= -1
                hitbox_3_x *= -1
                hitbox_4_x *= -1

            hitbox_1_x += attacker_x
            hitbox_2_x += attacker_x
            hitbox_3_x += attacker_x
            hitbox_4_x += attacker_x

            # Adjust the defender's hurtbox up a little, to be more centered.
            #   the game keeps y coordinates based on the bottom of a character, not
            #   their center. So we need to move up by one radius of the character's size
            defender_size = float(self.characterdata[defender_character]["size"])
            defender_y = defender_y + defender_size

            # Now see if any of the hitboxes are in range
            distance1 = math.sqrt((hitbox_1_x - defender_x)**2 + (hitbox_1_y - defender_y)**2)
            distance2 = math.sqrt((hitbox_2_x - defender_x)**2 + (hitbox_2_y - defender_y)**2)
            distance3 = math.sqrt((hitbox_3_x - defender_x)**2 + (hitbox_3_y - defender_y)**2)
            distance4 = math.sqrt((hitbox_4_x - defender_x)**2 + (hitbox_4_y - defender_y)**2)

            if distance1 < defender_size + float(attackingframe["hitbox_1_size"]):
                return True
            if distance2 < defender_size + float(attackingframe["hitbox_2_size"]):
                return True
            if distance3 < defender_size + float(attackingframe["hitbox_3_size"]):
                return True
            if distance4 < defender_size + float(attackingframe["hitbox_4_size"]):
                return True
            return False

    # Returns a frame dict for the specified frame
    def getframe(self, character, action, action_frame):
        if self.framedata[character][action][action_frame]:
            return self.framedata[character][action][action_frame]
        return None

    #Returns the first frame that a hitbox appears for a given action
    #   returns -1 if no hitboxes (not an attack action)
    def firsthitboxframe(self, character, action):
        # Grab only the subset that have a hitbox
        hitboxes = []
        for action_frame, frame in self.framedata[character][action].items():
            #Does this frame have a hitbox?
            if frame['hitbox_1_status'] or frame['hitbox_2_status'] \
                or frame['hitbox_3_status'] or frame['hitbox_4_status']:
                hitboxes.append(action_frame)
        if not hitboxes:
            return -1
        return min(hitboxes)

    #Returns the last frame that a hitbox appears for a given action
    #   returns -1 if no hitboxes (not an attack action)
    def lasthitboxframe(self, character, action):
        # Grab only the subset that have a hitbox
        hitboxes = []
        for action_frame, frame in self.framedata[character][action].items():
            #Does this frame have a hitbox?
            if frame['hitbox_1_status'] or frame['hitbox_2_status'] \
                or frame['hitbox_3_status'] or frame['hitbox_4_status']:
                hitboxes.append(action_frame)
        if not hitboxes:
            return -1
        return max(hitboxes)

    #This is a helper function to remove all the non-attacking actions
    def cleanupcsv(self):
        #Make a list of all the attacking action names
        attacks = []
        for row in self.rows:
            if row['hitbox_1_status'] == True or row['hitbox_2_status'] == True or \
                row['hitbox_3_status'] == True or row['hitbox_4_status'] == True:
                attacks.append(row['action'])
        #remove duplicates
        attacks = list(set(attacks))
        #rows[:] = filterfalse(determine, somelist)
        #Make a second pass, removing anything not in the list
        for row in list(self.rows):
            if row['action'] not in attacks:
                self.rows.remove(row)

    def recordframe(self, gamestate):
        row = {'character': gamestate.opponent_state.character.value,
            'action': gamestate.opponent_state.action.value,
            'frame': gamestate.opponent_state.action_frame,
            'hitbox_1_status': gamestate.opponent_state.hitbox_1_status,
            'hitbox_1_x': (gamestate.opponent_state.hitbox_1_x - gamestate.opponent_state.x),
            'hitbox_1_y': (gamestate.opponent_state.hitbox_1_y - gamestate.opponent_state.y),
            'hitbox_1_size' : gamestate.opponent_state.hitbox_1_size,
            'hitbox_2_status': gamestate.opponent_state.hitbox_2_status,
            'hitbox_2_x': (gamestate.opponent_state.hitbox_2_x - gamestate.opponent_state.x),
            'hitbox_2_y': (gamestate.opponent_state.hitbox_2_y - gamestate.opponent_state.y),
            'hitbox_2_size' : gamestate.opponent_state.hitbox_2_size,
            'hitbox_3_status': gamestate.opponent_state.hitbox_3_status,
            'hitbox_3_x': (gamestate.opponent_state.hitbox_3_x - gamestate.opponent_state.x),
            'hitbox_3_y': (gamestate.opponent_state.hitbox_3_y - gamestate.opponent_state.y),
            'hitbox_3_size' : gamestate.opponent_state.hitbox_3_size,
            'hitbox_4_status': gamestate.opponent_state.hitbox_4_status,
            'hitbox_4_x': (gamestate.opponent_state.hitbox_4_x - gamestate.opponent_state.x),
            'hitbox_4_y': (gamestate.opponent_state.hitbox_4_y - gamestate.opponent_state.y),
            'hitbox_4_size' : gamestate.opponent_state.hitbox_4_size,
            }

        if not gamestate.opponent_state.hitbox_1_status:
            row['hitbox_1_x'] = 0
            row['hitbox_1_y'] = 0
            row['hitbox_1_size'] = 0
        if not gamestate.opponent_state.hitbox_2_status:
            row['hitbox_2_x'] = 0
            row['hitbox_2_y'] = 0
            row['hitbox_2_size'] = 0
        if not gamestate.opponent_state.hitbox_3_status:
            row['hitbox_3_x'] = 0
            row['hitbox_3_y'] = 0
            row['hitbox_3_size'] = 0
        if not gamestate.opponent_state.hitbox_4_status:
            row['hitbox_4_x'] = 0
            row['hitbox_4_y'] = 0
            row['hitbox_4_size'] = 0

        alreadythere = False
        for i in self.rows:
            if i['character'] == row['character'] and i['action'] == row['action'] and i['frame'] == row['frame']:
                alreadythere = True

        if not alreadythere:
            self.rows.append(row)

    def saverecording(self):
        self.cleanupcsv()
        self.writer.writerows(self.rows)
        self.csvfile.close()
