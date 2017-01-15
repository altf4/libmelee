from melee import controller
from melee import enums
from struct import *

class DTMReader():

    def __init__(self, filepath):
        self.filepath = filepath
        self.file = None
        try:
            self.file = open(filepath, "rb")
        except FileNotFoundError:
            print("ERROR: DTM File not found")

        #What controllers are in the replay?
        self.file.seek(0xb)
        raw_data = unpack("<b", self.file.read(1))
        raw_data = raw_data[0]
        self.controllers = []
        for i in range(4):
            temp = raw_data & (1 << i)
            if temp > 0:
                self.controllers.append(temp)

        #Seek to the part of the file where controller data starts
        self.file.seek(0x100)

    """Make iterable"""
    def __iter__(self):
        return self

    """Get the next set of actions out of the DTM file,
    as a list of four ControllerStates"""
    def __next__(self):
        states = dict()
        for i in self.controllers:
            state = controller.ControllerState()
            #Get a 64 bit integer representation of our controller's data
            raw_data = unpack("<q", self.file.read(8))
            raw_data = raw_data[0]

            state.button[enums.Button.BUTTON_START] = bool(raw_data & (1 << 0))
            state.button[enums.Button.BUTTON_A] = bool(raw_data & (1 << 1))
            state.button[enums.Button.BUTTON_B] = bool(raw_data & (1 << 2))
            state.button[enums.Button.BUTTON_X] = bool(raw_data & (1 << 3))
            state.button[enums.Button.BUTTON_Y] = bool(raw_data & (1 << 4))
            state.button[enums.Button.BUTTON_Z] = bool(raw_data & (1 << 5))
            state.button[enums.Button.BUTTON_D_UP] = bool(raw_data & (1 << 6))
            state.button[enums.Button.BUTTON_D_DOWN] = bool(raw_data & (1 << 7))
            state.button[enums.Button.BUTTON_D_LEFT] = bool(raw_data & (1 << 8))
            state.button[enums.Button.BUTTON_D_RIGHT] = bool(raw_data & (1 << 9))
            state.button[enums.Button.BUTTON_L] = bool(raw_data & (1 << 10))
            state.button[enums.Button.BUTTON_R] = bool(raw_data & (1 << 11))

            main_x = (raw_data >> 32) & 0xFF
            main_y = (raw_data >> 40) & 0xFF
            c_x = (raw_data >> 48) & 0xFF
            c_y = (raw_data >> 56) & 0xFF

            #Analog sticks
            state.main_stick = (main_x / 255, main_y / 255)
            state.c_stick = (c_x / 255, c_y / 255)

            #Analog shoulders
            state.l_shoulder = ((raw_data >> 16) & 0xFF) / 255
            state.r_shoulder = ((raw_data >> 24) & 0xFF) / 255

            states[i] = state

        return states
