""" Defines a Clontroller class that manages pressing buttons for your console"""

from cmath import e
import platform
import sys
import copy
import time
import serial
from struct import pack

try:
    import win32file
    import pywintypes
except ImportError:
    pass

from melee import enums


class ControllerState:
    """A snapshot of the state of a virtual controller"""

    def __init__(self):
        __slots__ = ("button", "main_stick", "c_stick", "l_shoulder", "r_shoulder")
        self.button = dict()
        """(dict of enums.Button to bool): For the each Button as key, tells you if the button is pressed."""
        # Boolean buttons
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
        # Analog sticks
        self.main_stick = (0.5, 0.5)
        """(pair of floats): The main stick's x,y position. Ranges from 0->1, 0.5 is neutral"""
        self.c_stick = (0.5, 0.5)
        """(pair of floats): The C stick's x,y position. Ranges from 0->1, 0.5 is neutral"""
        self.raw_main_stick = (0, 0)
        """(pair of ints): The raw unprocessed main stick coordinates. Ranges from -128 -> 127. 0 is neural. """
        # Analog shoulders
        self.l_shoulder = 0
        """(float): L shoulder analog press. Ranges from 0 (not pressed) to 1 (fully pressed)"""
        self.r_shoulder = 0
        """(float): R shoulder analog press. Ranges from 0 (not pressed) to 1 (fully pressed)"""

    def toBytes(self):
        """Serialize the controller state into an 8 byte sequence that the Gamecube uses"""
        buttons_total = 0x0080
        if self.button[enums.Button.BUTTON_A]:
            buttons_total += 0x0100
        if self.button[enums.Button.BUTTON_B]:
            buttons_total += 0x0200
        if self.button[enums.Button.BUTTON_X]:
            buttons_total += 0x0400
        if self.button[enums.Button.BUTTON_Y]:
            buttons_total += 0x0800
        if self.button[enums.Button.BUTTON_Z]:
            buttons_total += 0x0010
        if self.button[enums.Button.BUTTON_L]:
            buttons_total += 0x0040
        if self.button[enums.Button.BUTTON_R]:
            buttons_total += 0x0020
        if self.button[enums.Button.BUTTON_START]:
            buttons_total += 0x1000

        buffer = pack(">H", buttons_total)

        # Convert from a float 0-1 to int 1-255
        val = pack(">B", (int((max(min(self.main_stick[0], 1), 0) * 254)) + 1))
        buffer += val
        val = pack(">B", (int((max(min(self.main_stick[1], 1), 0) * 254)) + 1))
        buffer += val
        val = pack(">B", (int((max(min(self.c_stick[0], 1), 0) * 254)) + 1))
        buffer += val
        val = pack(">B", (int((max(min(self.c_stick[1], 1), 0) * 254)) + 1))
        buffer += val

        # Convert from a float 0-1 to int 0-255
        #   The max/min thing just ensures the value is between 0 and 1
        val = pack(">B", int(max(min(self.l_shoulder, 1), 0) * 255))
        buffer += val
        val = pack(">B", int(max(min(self.r_shoulder, 1), 0) * 255))
        buffer += val
        return buffer

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


class Controller:
    """Manages virtual controller state and button presses

    The Controller object is your primary input mechanism for a bot. It's used for pressing
    buttons programatically, but also automatically configuring the controller with dolphin
    """

    def __init__(
        self,
        console,
        port,
        type=enums.ControllerType.STANDARD,
        serial_device="/dev/ttyACM0",
    ):
        """Create a new virtual controller

        Args:
            console (console.Console): A console object to attach the controller to
            port (int): Which controller port to plug into. Must be 1-4.
            type (enums.ControllerType): The type of controller this is
        """
        self._is_dolphin = console.system == "dolphin"
        if self._is_dolphin:
            self.pipe_path = console.get_dolphin_pipes_path(port)
            self.pipe = None
        else:
            try:
                self.tastm32 = serial.Serial(
                    serial_device, 115200, timeout=None, rtscts=True
                )
            except serial.serialutil.SerialException:
                print(
                    "TAStm32 was not ready. It might be booting up. "
                    + "Wait a few seconds and try again"
                )
                sys.exit(-1)

        self.port = port
        self.prev = ControllerState()
        self.current = ControllerState()
        self.logger = console.logger
        self._console = console
        self._type = type

        # Configure our controller with the console
        if self._is_dolphin:
            self._console.setup_dolphin_controller(port, type)

    def __del__(self):
        """Clean up any resources held by the controller object"""
        self.disconnect()

    def connect(self):
        """Connect the controller to the console

        Note:
            Blocks until the other side is ready
        """
        if self._type == enums.ControllerType.STANDARD:
            # Add ourselves to the console's controller list
            self._console.controllers.append(self)

            if self._is_dolphin:
                if platform.system() == "Windows":
                    # Windows can take a little while to actually make the pipes
                    #   So keep trying a few times to connect to it
                    for _ in range(5):
                        try:
                            # "Create File" in windows is what you use to open a file. Not
                            #   create one. Because the windows API is stupid.
                            self.pipe = win32file.CreateFile(
                                self.pipe_path,
                                win32file.GENERIC_WRITE,
                                0,
                                None,
                                win32file.OPEN_EXISTING,
                                0,
                                None,
                            )
                            return True
                        except pywintypes.error:
                            time.sleep(1)
                else:
                    self.pipe = open(self.pipe_path, "w")
                return True
            else:
                # Remove any extra garbage that might have accumulated in the buffer
                self.tastm32.reset_input_buffer()

                # Send reset command
                self.tastm32.write(b"R")  # reset
                cmd = self.tastm32.read(2)
                if cmd != b"\x01R":
                    # TODO Better error handling logic here
                    print(
                        "ERROR: TAStm32 did not reset properly. Try power cycling it."
                    )
                    return False
                # controller mode
                self.tastm32.write(b"C1")
                # Set to gamecube mode
                self.tastm32.write(b"SAG\x80\x00")
                # no bulk transfer
                self.tastm32.write(b"QA0")
                cmd = self.tastm32.read(2)
                self.tastm32.reset_input_buffer()
                if cmd != b"\x01S":
                    # TODO Better error handling logic here
                    print(
                        "ERROR: TAStm32 did not set to GCN mode. Try power cycling it."
                    )
                    return False
                return True
        else:
            return True

    def disconnect(self):
        """Disconnects the controller from the console"""
        if self._is_dolphin:
            if self.pipe:
                self.pipe.close()
                self.pipe = None

    def simple_press(self, x, y, button):
        """Here is a simpler representation of a button press, in case
        you don't want to bother with the tedium of manually doing everything.
        It isn't capable of doing everything the normal controller press functions
        can, but probably covers most scenarios.
        Notably, a difference here is that doing a button press releases all
        other buttons pressed previously.

        Note:
            Don't call this function twice in the same frame
                x = 0 (left) to 1 (right) on the main stick
                y = 0 (down) to 1 (up) on the main stick
                button = the button to press. Enter None for no button"""
        if self._is_dolphin:
            if not self.pipe:
                return
            # Tilt the main stick
            self.tilt_analog(enums.Button.BUTTON_MAIN, x, y)
            # Release the shoulders
            self.press_shoulder(enums.Button.BUTTON_L, 0)
            self.press_shoulder(enums.Button.BUTTON_R, 0)
            # Press the right button
            for item in enums.Button:
                # Don't do anything for the main or c-stick
                if item == enums.Button.BUTTON_MAIN:
                    continue
                if item == enums.Button.BUTTON_C:
                    continue
                # Press our button, release all others
                if item == button:
                    self.press_button(item)
                else:
                    self.release_button(item)

    def press_button(self, button):
        """Press a single button

        If already pressed, this has no effect

        Args:
            button (enums.Button): Button to press
        """
        self.current.button[button] = True
        command = "PRESS " + str(button.value) + "\n"
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        if self._is_dolphin:
            if not self.pipe:
                return
            self._write(command)

    def release_button(self, button):
        """Release a single button

        If already released, this has no effect

        Args:
            button (enums.Button): Button to release
        """
        self.current.button[button] = False
        command = "RELEASE " + str(button.value) + "\n"
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        if self._is_dolphin:
            if not self.pipe:
                return
            self._write(command)

    def press_shoulder(self, button, amount):
        """Press the analog shoulder buttons to a given amount

        Args:
            button (enums.Button): Has to be L or R
            amount (float): Ranges from 0 (not pressed at all) and 1 (Fully pressed in)

        Note:
            The 'digital' button press of L or R are handled separately
            as normal button presses. Pressing the shoulder all the way in
            will not cause the digital button to press
        """
        if button == enums.Button.BUTTON_L:
            self.current.l_shoulder = amount
        elif button == enums.Button.BUTTON_R:
            self.current.r_shoulder = amount
        command = "SET " + str(button.value) + " " + str(amount) + "\n"
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        if self._is_dolphin:
            if not self.pipe:
                return
            self._write(command)

    def tilt_analog(self, button, x, y):
        """Tilt one of the analog sticks to a given (x,y) value

        Args:
            button (enums.Button): Must be main stick or C stick
            x (float): Ranges between 0 (left) and 1 (right)
            y (float): Ranges between 0 (down) and 1 (up)
        """
        if button == enums.Button.BUTTON_MAIN:
            self.current.main_stick = (x, y)
        else:
            self.current.c_stick = (x, y)
        command = "SET " + str(button.value) + " " + str(x) + " " + str(y) + "\n"
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        if self._is_dolphin:
            if not self.pipe:
                return
            self._write(command)

    def tilt_analog_unit(self, button, x, y):
        """Tilt one of the analog sticks to a given (x,y) value, normalized to a unit vector

        This mean the values range from -1 -> 1 (with 0 center) rather than 0 -> 1 (with 0.5 center)
        This doesn't press the stick any further than the tilt_analog(), it's just a compat helper

        Args:
            button (enums.Button): Must be main stick or C stick
            x (float): Ranges between -1 (left) and 1 (right)
            y (float): Ranges between -1 (down) and 1 (up)
        """
        if button == enums.Button.BUTTON_MAIN:
            self.current.main_stick = (x, y)
        else:
            self.current.c_stick = (x, y)
        command = (
            "SET "
            + str(button.value)
            + " "
            + str((x / 2) + 0.5)
            + " "
            + str((y / 2) + 0.5)
            + "\n"
        )
        if self.logger:
            self.logger.log("Buttons Pressed", command, concat=True)
        if self._is_dolphin:
            if not self.pipe:
                return
            self._write(command)

    # Left around for compat reasons. Might disappear at any time
    #   left undocumented. Just use release_all()
    def empty_input(self):
        self.release_all()

    def release_all(self):
        """Resets the controller to a resting state

        All buttons are released, all sticks set to 0.5, all shoulders set to 0
        """
        # Set the internal state back to neutral
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
        self.current.main_stick = (0.5, 0.5)
        self.current.c_stick = (0.5, 0.5)
        self.current.l_shoulder = 0
        self.current.r_shoulder = 0
        if self._is_dolphin:
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
            # Send the presses to dolphin
            self._write(command)
        if self.logger:
            self.logger.log("Buttons Pressed", "Empty Input", concat=True)

    def _write(self, command):
        """Platform independent button write function."""
        if platform.system() == "Windows":
            try:
                win32file.WriteFile(self.pipe, command.encode())
            except pywintypes.error:
                pass
        else:
            self.pipe.write(command)

    def flush(self):
        """Actually send the button presses to the console

        Up until this point, any buttons you 'press' are just queued in a pipe.
        It doesn't get sent to the console until you flush
        """
        # Move the current controller state into the previous one
        self.prev = copy.copy(self.current)

        if self._is_dolphin:
            self._write("FLUSH\n")
            if platform.system() != "Windows":
                if not self.pipe:
                    return
                self.pipe.flush()
        else:
            # Command for "send single controller poll" is 'A'
            # Serialize controller state into bytes and send
            self.tastm32.write(b"A" + self.current.toBytes())
            cmd = self.tastm32.read(1)

            if cmd != b"A":
                print("Got error response: ", bytes(cmd))
