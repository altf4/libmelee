import csv
import os
import math
from melee.enums import Action, Character
from melee import stages
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
                'hitbox_4_status', 'hitbox_4_size', 'hitbox_4_x', 'hitbox_4_y',
                'locomotion_x', 'locomotion_y']
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
                character = Character(int(frame["character"]))
                action = Action(int(frame["action"]))
                action_frame = int(frame["frame"])
                self.framedata[character][action][action_frame] = \
                    {"hitbox_1_status": frame["hitbox_1_status"] == "True", \
                    "hitbox_1_size": float(frame["hitbox_1_size"]), \
                    "hitbox_1_x": float(frame["hitbox_1_x"]), \
                    "hitbox_1_y": float(frame["hitbox_1_y"]), \
                    "hitbox_2_status": frame["hitbox_2_status"] == "True", \
                    "hitbox_2_size": float(frame["hitbox_2_size"]), \
                    "hitbox_2_x": float(frame["hitbox_2_x"]), \
                    "hitbox_2_y": float(frame["hitbox_2_y"]), \
                    "hitbox_3_status": frame["hitbox_3_status"] == "True", \
                    "hitbox_3_size": float(frame["hitbox_3_size"]), \
                    "hitbox_3_x": float(frame["hitbox_3_x"]), \
                    "hitbox_3_y": float(frame["hitbox_3_y"]), \
                    "hitbox_4_status": frame["hitbox_4_status"] == "True", \
                    "hitbox_4_size": float(frame["hitbox_4_size"]), \
                    "hitbox_4_x": float(frame["hitbox_4_x"]), \
                    "hitbox_4_y": float(frame["hitbox_4_y"]), \
                    "locomotion_x": float(frame["locomotion_x"]), \
                    "locomotion_y": float(frame["locomotion_y"])}

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
                self.characterdata[Character(line["CharacterIndex"])] = line

    #Returns boolean on if the given action is a roll
    def isroll(self, character, action):
        # Marth counter
        if character == Character.MARTH and action == Action.MARTH_COUNTER:
            return True
        if character == Character.MARTH and action == Action.MARTH_COUNTER_FALLING:
            return True

        # Turns out that the actions we'd call a "roll" are fairly few. Let's just
        # hardcode them since it's just more cumbersome to do otherwise
        rolls = [Action.SPOTDODGE, Action.ROLL_FORWARD, Action.ROLL_BACKWARD, \
            Action.NEUTRAL_TECH, Action.FORWARD_TECH, Action.BACKWARD_TECH, \
            Action.GROUND_GETUP, Action.TECH_MISS_UP, Action.TECH_MISS_DOWN, \
            Action.EDGE_GETUP_SLOW, Action.EDGE_GETUP_QUICK, Action.EDGE_ROLL_SLOW, \
            Action.EDGE_ROLL_QUICK, Action.GROUND_ROLL_FORWARD_UP, Action.GROUND_ROLL_BACKWARD_UP, \
            Action.GROUND_ROLL_FORWARD_DOWN, Action.GROUND_ROLL_BACKWARD_DOWN, Action.SHIELD_BREAK_FLY, \
            Action.SHIELD_BREAK_FALL, Action.SHIELD_BREAK_DOWN_U, Action.SHIELD_BREAK_DOWN_D, \
            Action.SHIELD_BREAK_STAND_U, Action.SHIELD_BREAK_STAND_D, Action.TAUNT_RIGHT, Action.TAUNT_LEFT]
        return action in rolls

    #Returns boolean on if the given action is an attack (contains a hitbox)
    def isattack(self, character, action):
        if self.framedata[character][action]:
            return True
        return False

    def isshield(self, action):
        out = action == Action.SHIELD \
            or action == Action.SHIELD_START \
            or action == Action.SHIELD_REFLECT \
            or action == Action.SHIELD_STUN \
            or action == Action.SHIELD_RELEASE
        return out

    def maxjumps(character):
        if character == Character.JIGGLYPUFF:
            return 5
        if character == Character.KIRBY:
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
            return AttackState.NOT_ATTACKING

        if frame < self.firsthitboxframe(character, action):
            return AttackState.WINDUP

        if frame > self.lasthitboxframe(character, action):
            return AttackState.COOLDOWN

        return AttackState.ATTACKING

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
            if self.attackstate(attacker_character, attacker_action, attacker_action_frame) != AttackState.ATTACKING:
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

    # Returns the last frame of the roll
    # -1 if not a roll
    def lastrollframe(self, character, action):
        if not self.isroll(character, action):
            return -1
        frames = []
        for action_frame in self.framedata[character][action]:
            frames.append(action_frame)
        return max(frames)

    # Returns the x coordinate that the current roll will end in
    def endrollposition(self, character_state, stage):
        distance = 0
        #TODO: Take current momentum into account
        # Loop through each frame in the attack
        for action_frame in self.framedata[character_state.character][character_state.action]:
            # Only care about frames that haven't happened yet
            if action_frame > character_state.action_frame:
                distance += self.framedata[character_state.character][character_state.action][action_frame]["locomotion_x"]
        # Do we need to flip around the distance?
        #   I'm PRETTY sure that there aren't any rolls that start moving in one direction
        #   and then go the other, with the exception on ledge rolls.
        #   So let's use the initial self speed as a heuristic
        #   for the direction the roll is going
        isedgeroll = character_state.action in [Action.EDGE_GETUP_SLOW, \
            Action.EDGE_GETUP_QUICK, Action.EDGE_ROLL_SLOW, Action.EDGE_ROLL_QUICK]
        if isedgeroll and not character_state.facing:
            distance = -distance
        elif character_state.speed_ground_x_self < 0:
            distance = -distance
        position = character_state.x + distance

        # Adjust the position to account for the fact that we can't roll off the stage
        position = min(position, stages.edgegroundposition(stage))
        position = max(position, -stages.edgegroundposition(stage))
        return position

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

    #This is a helper function to remove all the non-attacking, non-rolling actions
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
            if row['action'] not in attacks and not self.isroll(Character(row['character']), Action(row['action'])):
                self.rows.remove(row)

    def recordframe(self, gamestate):
        # So here's the deal... We don't want to count horizontal momentum for almost
        #   all air moves. Except a few. So let's just enumerate those. It's ugly,
        #   but whatever, you're not my boss
        xspeed = 0
        airmoves = gamestate.opponent_state.action in [Action.EDGE_ROLL_SLOW, Action.EDGE_ROLL_QUICK, Action.EDGE_GETUP_SLOW, \
            Action.EDGE_GETUP_QUICK, Action. EDGE_ATTACK_SLOW, Action.EDGE_ATTACK_QUICK, \
            Action.EDGE_JUMP_1_SLOW, Action.EDGE_JUMP_1_QUICK, Action.EDGE_JUMP_2_SLOW, Action.EDGE_JUMP_2_QUICK]

        if gamestate.opponent_state.on_ground or airmoves:
            xspeed = gamestate.opponent_state.x - gamestate.opponent_state.prev_x

        # This is a bit strange, but here's why:
        #   The vast majority of actions don't actually affect vertical speed
        #   For most, the character just moves according to their normal momentum
        #   Any exceptions can be manually edited in
        #  However, there's plenty of attacks that make the character fly upward at a set
        #   distance, like up-b's. So keep those around
        yspeed = max(gamestate.opponent_state.y - gamestate.opponent_state.prev_y, 0)

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
            'locomotion_x' : xspeed,
            'locomotion_y' : yspeed,
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
