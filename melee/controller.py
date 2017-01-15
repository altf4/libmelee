from melee import enums, logger
import copy

"""A snapshot of the state of a virtual controller"""
class ControllerState:
    def __init__(self):
        self.button = dict()
        #Boolean buttons
        self.button[enums.Button.BUTTON_A] = False
        self.button[enums.Button.BUTTON_B] = False
        self.button[enums.Button.BUTTON_X] = False
        self.button[enums.Button.BUTTON_Y] = False
        self.button[enums.Button.BUTTON_Z] = False
        self.button[enums.Button.BUTTON_L] = False
        self.button[enums.Button.BUTTON_R] = False
        self.button[enums.Button.BUTTON_START] = False
        self.button[enums.Button.BUTTON_D_UP] = False
        self.button[enums.Button.BUTTON_D_DOWN] = False
        self.button[enums.Button.BUTTON_D_LEFT] = False
        self.button[enums.Button.BUTTON_D_RIGHT] = False
        #Analog sticks
        self.main_stick = (.5, .5)
        self.c_stick = (.5, .5)
        #Analog shoulders
        self.l_shoulder = 0
        self.r_shoulder = 0

    def __str__(self):
        string = ""
        for val in self.button:
            string += str(val) + ": " + str(self.button[val])
            string += "\n"
        string += "MAIN_STICK: " + str(self.main_stick) + "\n"
        string += "C_STICK: " + str(self.c_stick) + "\n"
        string += "L_SHOULDER: " + str(self.l_shoulder) + "\n"
        string += "R_SHOULDER: " + str(self.r_shoulder) + "\n"
        return string

"""Utility class that manages virtual controller state and button presses"""
class Controller:
    def __init__(self, dolphin, port):
        self.pipe_path = dolphin.get_dolphin_pipes_path(port)
        self.pipe = None
        self.prev = ControllerState()
        self.current = ControllerState()
        self.logger = dolphin.logger

    """Connect the controller to dolphin
    TODO: returns True if connection was successful """
    def connect(self):
        self.pipe = open(self.pipe_path, "w")

    def disconnect(self):
        if self.pipe:
            self.pipe.close()
            self.pipe = None

    """Here is a simpler representation of a button press, in case
        you don't want to bother with the tedium of manually doing everything.
        It isn't capable of doing everything the normal controller press functions
        can, but probably covers most scenarios.
        Notably, a difference here is that doing a button press releases all
        other buttons pressed previously.
        Don't call this function twice in the same frame
            x = 0 (left) to 1 (right) on the main stick
            y = 0 (down) to 1 (up) on the main stick
            button = the button to press. Enter None for no button"""
    def simple_press(self, x, y, button):
        if not self.pipe:
            return
        #Tilt the main stick
        self.tilt_analog(enums.Button.BUTTON_MAIN, x, y)
        #Release the shoulders
        self.press_shoulder(enums.Button.BUTTON_L, 0)
        self.press_shoulder(enums.Button.BUTTON_R, 0)
        #Press the right button
        for item in enums.Button:
            #Don't do anything for the main or c-stick
            if item == enums.Button.BUTTON_MAIN:
                continue
            if item == enums.Button.BUTTON_C:
                continue
            #Press our button, release all others
            if item == button:
                self.press_button(item)
            else:
                self.release_button(item)

    def press_button(self, button):
        if not self.pipe:
            return
        command = "PRESS " + str(button.value) + "\n"
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        self.current.button[button] = True
        self.pipe.write(command)

    def release_button(self, button):
        if not self.pipe:
            return
        command = "RELEASE " + str(button.value) + "\n"
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        self.current.button[button] = False
        self.pipe.write(command)

    def press_shoulder(self, button, amount):
        if not self.pipe:
            return
        command = "SET " + str(button.value) + " " + str(amount) + "\n"
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        if button == enums.Button.BUTTON_L:
            self.current.l_shoulder = amount
        elif button == enums.Button.BUTTON_R:
            self.current.r_shoulder = amount
        self.pipe.write(command)

    def tilt_analog(self, button, x, y):
        if not self.pipe:
            return
        command = "SET " + str(button.value) + " " + str(x) + " " + str(y) + "\n"
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        self.pipe.write(command)

    def empty_input(self):
        if not self.pipe:
            return
        command = "RELEASE A" + "\n"
        command += "RELEASE B" + "\n"
        command += "RELEASE X" + "\n"
        command += "RELEASE Y" + "\n"
        command += "RELEASE Z" + "\n"
        command += "RELEASE L" + "\n"
        command += "RELEASE R" + "\n"
        command += "RELEASE START" + "\n"
        command += "RELEASE D_UP" + "\n"
        command += "RELEASE D_DOWN" + "\n"
        command += "RELEASE D_LEFT" + "\n"
        command += "RELEASE D_RIGHT" + "\n"
        command += "SET MAIN .5 .5" + "\n"
        command += "SET C .5 .5" + "\n"
        command += "SET L 0" + "\n"
        command += "SET R 0" + "\n"
        #Set the internal state back to neutral
        self.current.button[enums.Button.BUTTON_A] = False
        self.current.button[enums.Button.BUTTON_B] = False
        self.current.button[enums.Button.BUTTON_X] = False
        self.current.button[enums.Button.BUTTON_Y] = False
        self.current.button[enums.Button.BUTTON_Z] = False
        self.current.button[enums.Button.BUTTON_L] = False
        self.current.button[enums.Button.BUTTON_R] = False
        self.current.button[enums.Button.BUTTON_START] = False
        self.current.button[enums.Button.BUTTON_D_UP] = False
        self.current.button[enums.Button.BUTTON_D_DOWN] = False
        self.current.button[enums.Button.BUTTON_D_LEFT] = False
        self.current.button[enums.Button.BUTTON_D_RIGHT] = False
        self.current.main_stick = (.5, .5)
        self.current.c_stick = (.5, .5)
        self.current.l_shoulder = 0
        self.current.r_shoulder = 0
        #Send the presses to dolphin
        self.pipe.write(command)
        if self.logger:
            self.logger.log("Buttons Pressed", "Empty Input", concat=True)

    def flush(self):
        if not self.pipe:
            return
        self.pipe.flush()
        #Move the current controller state into the previous one
        self.prev = copy.copy(self.current)
