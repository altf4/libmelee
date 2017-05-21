import csv
import os
from itertools import filterfalse

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
        with open(path + "/framedata.csv") as csvfile:
            #A list of dicts containing the frame data
            self.data = list(csv.DictReader(csvfile))

        #Read the action state data csv
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + "/actiondata.csv") as csvfile:
            #A list of dicts containing the frame data
            self.actiondata = list(csv.DictReader(csvfile))

    #Returns boolean on if the given action is a roll
    def isroll(self, character, action):
        for line in self.actiondata:
            if line["action"] == str(action) and line["character"] == str(character) \
                and line["isroll"] == "True":
                return True
        return False

    #Returns boolean on if the given action is an attack (contains a hitbox)
    def isattack(self, character, action):
        for line in self.data:
            if line["action"] == str(action) and line["character"] == str(character):
                return True
        return False

    #Returns the first frame that a hitbox appears for a given action
    #   returns -1 if no hitboxes (not an attack action)
    def firsthitboxframe(self, action):
        #Grab a subset of the frames that are relevant to us
        action_frames = [frames for frames in self.data if frames["action"] == str(action)]
        hitboxes = []
        for frame in action_frames:
            #Does this frame have a hitbox?
            hit1 = frame['hitbox_1_status'] == "True"
            hit2 = frame['hitbox_2_status'] == "True"
            hit3 = frame['hitbox_3_status'] == "True"
            hit4 = frame['hitbox_4_status'] == "True"
            if hit1 or hit2 or hit3 or hit4:
                hitboxes.append(int(frame["frame"]))
        if not hitboxes:
            return -1
        return min(hitboxes)

    #Returns the last frame that a hitbox appears for a given action
    #   returns -1 if no hitboxes (not an attack action)
    def lasthitboxframe(self, action):
        #Grab a subset of the frames that are relevant to us
        action_frames = [frames for frames in self.data if frames["action"] == str(action)]
        hitboxes = []
        for frame in action_frames:
            #Does this frame have a hitbox?
            hit1 = frame['hitbox_1_status'] == "True"
            hit2 = frame['hitbox_2_status'] == "True"
            hit3 = frame['hitbox_3_status'] == "True"
            hit4 = frame['hitbox_4_status'] == "True"
            if hit1 or hit2 or hit3 or hit4:
                hitboxes.append(int(frame["frame"]))
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
        row = {'character': gamestate.opponent_state.character,
            'action': gamestate.opponent_state.action,
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
