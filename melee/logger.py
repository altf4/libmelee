import csv
import time
import datetime
import os

class Logger:
    def __init__(self):
        timestamp = datetime.datetime.fromtimestamp(time.time())
        #Create the Pipes directory if it doesn't already exist
        if not os.path.exists("Logs/"):
            os.makedirs("Logs/")
        self.csvfile = open('Logs/' + str(timestamp) + '.csv', 'w')
        fieldnames = ['Frame', 'Opponent x',
            'Opponent y', 'AI x', 'AI y', 'Opponent Facing', 'AI Facing',
            'Opponent Action', 'AI Action', 'Opponent Action Frame', 'AI Action Frame',
            'Opponent Jumps Left', 'AI Jumps Left', 'Opponent Stock', 'AI Stock',
            'Opponent Percent', 'AI Percent', 'Buttons Pressed', 'Notes', 'Frame Process Time']
        self.writer = csv.DictWriter(self.csvfile, fieldnames=fieldnames, extrasaction='ignore')
        self.current_row = dict()
        self.rows = []
        self.filename = self.csvfile.name

    def log(self, column, contents, concat=False):
        #Should subsequent logs be cumulative?
        if concat:
            if column in self.current_row:
                self.current_row[column] += contents
            else:
                self.current_row[column] = contents
        else:
            self.current_row[column] = contents

    #Log any common per-frame items
    def logframe(self, gamestate):
        ai_state = gamestate.ai_state
        opponent_state = gamestate.opponent_state

        self.log('Frame', gamestate.frame)
        self.log('Opponent x', str(opponent_state.x))
        self.log('Opponent y', str(opponent_state.y))
        self.log('AI x', str(ai_state.x))
        self.log('AI y', str(ai_state.y))
        self.log('Opponent Facing', str(opponent_state.facing))
        self.log('AI Facing', str(ai_state.facing))
        self.log('Opponent Action', str(opponent_state.action))
        self.log('AI Action', str(ai_state.action))
        self.log('Opponent Action Frame', str(opponent_state.action_frame))
        self.log('AI Action Frame', str(ai_state.action_frame))
        self.log('Opponent Jumps Left', str(opponent_state.jumps_left))
        self.log('AI Jumps Left', str(ai_state.jumps_left))
        self.log('Opponent Stock', str(opponent_state.stock))
        self.log('AI Stock', str(ai_state.stock))
        self.log('Opponent Percent', str(opponent_state.percent))
        self.log('AI Percent', str(ai_state.percent))

    def writeframe(self):
        self.rows.append(self.current_row)
        self.current_row = dict()

    def writelog(self):
        self.writer.writeheader()
        self.writer.writerows(self.rows)
