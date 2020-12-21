""" A custom logger for a console. Writes the gametstate out to a CSV file
        so you can retroactively view the game frame-by-frame"""

import csv
import os
from datetime import datetime
from pathlib import Path

class Logger():
    """A custom logger for a console. Writes the gametstate out to a CSV file each frame
            so you can retroactively view the game frame-by-frame"""
    def __init__(self):
        timestamp = Path(str(datetime.now()).replace(" ", "-").replace(":", "-") + ".csv")
        #Create the Logs directory if it doesn't already exist
        if not os.path.exists(Path("Logs")):
            os.makedirs(Path("Logs"))
        self.csvfile = open("Logs" / timestamp, 'w')
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
        """Write 'contents' to the log at given 'column'

        Args:
            column (str): The column to write the log message at
            contents (str): The thing to write to the log
            concat (bool): Should we concatenate the contents to the existing log at that column
                (or replace it)
        """
        #Should subsequent logs be cumulative?
        if concat:
            if column in self.current_row:
                self.current_row[column] += contents
            else:
                self.current_row[column] = contents
        else:
            self.current_row[column] = contents

    def logframe(self, gamestate):
        """Log any common per-frame things

        Args:
            gamestate (gamestate.GameState): A gamestate object to log
        """
        opponent_state = None
        ai_state = None
        count = 0
        for i, player in gamestate.players.items():
            if count == 0:
                ai_state = player
                count += 1
            elif count == 1:
                opponent_state = player
                count += 1

        if not opponent_state or not ai_state:
            return
        self.log('Frame', gamestate.frame)
        self.log('Opponent x', str(opponent_state.position.x))
        self.log('Opponent y', str(opponent_state.position.y))
        self.log('AI x', str(ai_state.position.x))
        self.log('AI y', str(ai_state.position.y))
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
        """Write the current frame to the log and move to a new frame"""
        self.rows.append(self.current_row)
        self.current_row = dict()

    def writelog(self):
        """Write the log to file """
        self.writer.writeheader()
        self.writer.writerows(self.rows)
