"""The Console represents the engine running the game.

This can be Dolphin (Slippi's Ishiiruka) or an SLP file. The Console object
is your method to start and stop Dolphin, set configs, and get the latest GameState.
"""

from struct import unpack, error
from collections import defaultdict

import time
import os
import configparser
import csv
import subprocess
import platform
import math
import base64
from pathlib import Path

from melee import enums
from melee.gamestate import GameState, Projectile, Action
from melee.slippstream import SlippstreamClient, CommType, EventType
from melee.slpfilestreamer import SLPFileStreamer
from melee import stages


# pylint: disable=too-many-instance-attributes
class Console:
    """The console object that represents your Dolphin / Wii / SLP file
    """
    def __init__(self,
                 path=None,
                 is_dolphin=True,
                 slippi_address="127.0.0.1",
                 slippi_port=51441,
                 online_delay=2,
                 blocking_input=False,
                 logger=None):
        """Create a Console object

        Args:
            path (str): Path to the directory where your dolphin executable is
                located. (if applicable) None tells console to use the installed copy of the emulator
            slippi_address (str): IP address of the Dolphin / Wii to connect to.
                Empty string will try to autodiscover a nearby SlippiComm server
            slippi_port (int): UDP port that slippi will listen on
            online_delay (int): How many frames of delay to apply in online matches
            blocking_input (bool): Should dolphin block waiting for bot input
                This is only really useful if you're doing ML training.
            logger (logger.Logger): Logger instance to use. None for no logger.
        """
        self.logger = logger
        self.is_dolphin = is_dolphin
        self.path = path
        self.processingtime = 0
        self._frametimestamp = time.time()
        self.slippi_address = slippi_address
        """(str): IP address of the Dolphin / Wii to connect to."""
        self.slippi_port = slippi_port
        """(int): UDP port of slippi server. Default 51441"""
        self.eventsize = [0] * 0x100
        self.render = True
        """(bool): Should dolphin render the game live?"""
        self.connected = False
        self.nick = ""
        """(str): The nickname the console has given itself."""
        self.version = ""
        """(str): The Slippi version of the console"""
        self.cursor = 0
        self.controllers = []
        self._current_stage = enums.Stage.NO_STAGE
        self._frame = 0
        self.slp_version = "unknown"
        """(str): The SLP version this stream/file currently is."""

        # Keep a running copy of the last gamestate produced
        self._prev_gamestate = GameState()
        self._process = None
        if self.is_dolphin:
            self._slippstream = SlippstreamClient(self.slippi_address, self.slippi_port)

            # Setup some dolphin config options
            dolphin_config_path = self._get_dolphin_config_path() + "Dolphin.ini"
            config = configparser.SafeConfigParser()
            config.read(dolphin_config_path)
            config.set("Core", 'slippienablespectator', "True")
            config.set("Core", 'slippispectatorlocalport', str(self.slippi_port))
            # Set online delay
            config.set("Core", 'slippionlinedelay', str(online_delay))
            # Turn on background input so we don't need to have window focus on dolphin
            config.set("Input", 'backgroundinput', "True")
            config.set("Core", 'BlockingPipes', str(blocking_input))
            with open(dolphin_config_path, 'w') as dolphinfile:
                config.write(dolphinfile)
        else:
            self._slippstream = SLPFileStreamer(self.path)

        # Prepare some structures for fixing melee data
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + "/actiondata.csv") as csvfile:
            #A list of dicts containing the frame data
            actiondata = list(csv.DictReader(csvfile))
            #Dict of sets
            self.zero_indices = defaultdict(set)
            for line in actiondata:
                if line["zeroindex"] == "True":
                    self.zero_indices[int(line["character"])].add(int(line["action"]))

        # Read the character data csv
        self.characterdata = dict()
        with open(path + "/characterdata.csv") as csvfile:
            reader = csv.DictReader(csvfile)
            for line in reader:
                del line["Character"]
                #Convert all fields to numbers
                for key, value in line.items():
                    line[key] = float(value)
                self.characterdata[enums.Character(line["CharacterIndex"])] = line

    def connect(self):
        """ Connects to the Slippi server (dolphin or wii).

        Returns:
            True is successful, False otherwise
        """
        # It can take a short amount of time after starting the emulator
        #   for the actual server to start. So try a few times before giving up.
        for _ in range(4):
            if self._slippstream.connect():
                return True
        return False

    def run(self, iso_path=None, dolphin_config_path=None):
        """Run the Dolphin emulator.

        This starts the Dolphin process, so don't run this if you're connecting to an
        already running Dolphin instance.

        Args:
            iso_path (str, optional): Path to Melee ISO for dolphin to read
            dolphin_config_path (str, optional): Alternative config path for dolphin
                if not using the default
        """
        if self.is_dolphin:
            exe_name = "dolphin-emu"
            if platform.system() == "Windows":
                exe_name = "Dolphin.exe"

            exe_path = ""
            if self.path:
                exe_path = self.path
            command = [exe_path + "/" + exe_name]
            if not self.render:
                #Use the "Null" renderer
                command.append("-v")
                command.append("Null")
            if iso_path is not None:
                command.append("-e")
                command.append(iso_path)
            if dolphin_config_path is not None:
                command.append("-u")
                command.append(dolphin_config_path)
            self._process = subprocess.Popen(command)

    def stop(self):
        """ Stop the console.

        For Dolphin instances, this will kill the dolphin process.
        For Wiis and SLP files, it just shuts down our connection
         """
        self.connected = False
        self._slippstream.shutdown()
        # If dolphin, kill the process
        if self._process is not None:
            self._process.terminate()

    def setup_dolphin_controller(self, port, controllertype=enums.ControllerType.STANDARD):
        """Setup the necessary files for dolphin to recognize the player at the given
        controller port and type"""

        pipes_path = self._get_dolphin_home_path() + "Pipes/"
        if platform.system() != "Windows" and controllertype == enums.ControllerType.STANDARD:
            #Create the Pipes directory if it doesn't already exist
            if not os.path.exists(pipes_path):
                os.makedirs(pipes_path)
            pipes_path += "slippibot" + str(port)
            if not os.path.exists(pipes_path):
                os.mkfifo(pipes_path)

        #Read in dolphin's controller config file
        controller_config_path = self._get_dolphin_config_path() + "GCPadNew.ini"
        config = configparser.SafeConfigParser()
        config.read(controller_config_path)

        #Add a bot standard controller config to the given port
        section = "GCPad" + str(port)
        if not config.has_section(section):
            config.add_section(section)

        if controllertype == enums.ControllerType.STANDARD:
            config.set(section, 'Device', 'Pipe/0/slippibot' + str(port))
            config.set(section, 'Buttons/A', 'Button A')
            config.set(section, 'Buttons/B', 'Button B')
            config.set(section, 'Buttons/X', 'Button X')
            config.set(section, 'Buttons/Y', 'Button Y')
            config.set(section, 'Buttons/Z', 'Button Z')
            config.set(section, 'Buttons/L', 'Button L')
            config.set(section, 'Buttons/R', 'Button R')
            config.set(section, 'Main Stick/Up', 'Axis MAIN Y +')
            config.set(section, 'Main Stick/Down', 'Axis MAIN Y -')
            config.set(section, 'Main Stick/Left', 'Axis MAIN X -')
            config.set(section, 'Main Stick/Right', 'Axis MAIN X +')
            config.set(section, 'Triggers/L', 'Button L')
            config.set(section, 'Triggers/R', 'Button R')
            config.set(section, 'Main Stick/Modifier', 'Shift_L')
            config.set(section, 'Main Stick/Modifier/Range', '50.000000000000000')
            config.set(section, 'D-Pad/Up', 'Button D_UP')
            config.set(section, 'D-Pad/Down', 'Button D_DOWN')
            config.set(section, 'D-Pad/Left', 'Button D_LEFT')
            config.set(section, 'D-Pad/Right', 'Button D_RIGHT')
            config.set(section, 'Buttons/Start', 'Button START')
            config.set(section, 'Buttons/A', 'Button A')
            config.set(section, 'C-Stick/Up', 'Axis C Y +')
            config.set(section, 'C-Stick/Down', 'Axis C Y -')
            config.set(section, 'C-Stick/Left', 'Axis C X -')
            config.set(section, 'C-Stick/Right', 'Axis C X +')
            config.set(section, 'Triggers/L-Analog', 'Axis L -+')
            config.set(section, 'Triggers/R-Analog', 'Axis R -+')
        #This section is unused if it's not a standard input (I think...)
        else:
            config.set(section, 'Device', 'XInput2/0/Virtual core pointer')

        with open(controller_config_path, 'w') as configfile:
            config.write(configfile)

        dolphin_config_path = self._get_dolphin_config_path() + "Dolphin.ini"
        config = configparser.SafeConfigParser()
        config.read(dolphin_config_path)
        # Indexed at 0. "6" means standard controller, "12" means GCN Adapter
        #  The enum is scoped to the proper value, here
        config.set("Core", 'SIDevice'+str(port-1), controllertype.value)
        with open(dolphin_config_path, 'w') as dolphinfile:
            config.write(dolphinfile)

    def step(self):
        """ 'step' to the next state of the game and flushes all controllers

        Returns:
            GameState object that represents new current state of the game"""
        # Keep looping until we get a REPLAY message
        self.processingtime = time.time() - self._frametimestamp

        # Flush the controllers
        for controler in self.controllers:
            controler.flush()

        gamestate = GameState()
        frame_ended = False
        while not frame_ended:
            message = self._slippstream.dispatch()
            if message:
                if message["type"] == "connect_reply":
                    self.connected = True
                    self.nick = message["nick"]
                    self.version = message["version"]
                    self.cursor = message["cursor"]

                elif message["type"] == "game_event":
                    if len(message["payload"]) > 0:
                        if self.is_dolphin:
                            frame_ended = self.__handle_slippstream_events(base64.b64decode(message["payload"]), gamestate)
                        else:
                            frame_ended = self.__handle_slippstream_events(message["payload"], gamestate)

                elif message["type"] == "menu_event":
                    if len(message["payload"]) > 0:
                        self.__handle_slippstream_menu_event(base64.b64decode(message["payload"]), gamestate)
                        frame_ended = True
            else:
                return None

        self.__fixframeindexing(gamestate)
        self.__fixiasa(gamestate)
        # Start the processing timer now that we're done reading messages
        self._frametimestamp = time.time()
        return gamestate

    def __handle_slippstream_events(self, event_bytes, gamestate):
        """ Handle a series of events, provided sequentially in a byte array """
        gamestate.menu_state = enums.Menu.IN_GAME
        while len(event_bytes) > 0:
            event_size = self.eventsize[event_bytes[0]]
            if len(event_bytes) < event_size:
                print("WARNING: Something went wrong unpacking events. Data is probably missing")
                print("\tDidn't have enough data for event")
                return False
            if EventType(event_bytes[0]) == EventType.PAYLOADS:
                cursor = 0x2
                payload_size = event_bytes[1]
                num_commands = (payload_size - 1) // 3
                for i in range(0, num_commands):
                    command, command_len = unpack(">bH", event_bytes[cursor:cursor+3])
                    self.eventsize[command] = command_len+1
                    cursor += 3
                event_bytes = event_bytes[payload_size + 1:]

            elif EventType(event_bytes[0]) == EventType.FRAME_START:
                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.GAME_START:
                # event_bytes = event_bytes[event_size:]
                # Need to properly record what stage this is
                self._frame = -10000
                major = unpack(">B", event_bytes[0x01:0x01+1])[0]
                minor = unpack(">B", event_bytes[0x02:0x02+1])[0]
                version = unpack(">B", event_bytes[0x03:0x03+1])[0]
                self.slp_version = str(major) + "." + str(minor) + "." + str(version)
                try:
                    self._current_stage = enums.to_internal_stage(unpack(">H", event_bytes[0x13:0x13+2])[0])
                except ValueError:
                    self._current_stage = enums.Stage.NO_STAGE
                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.GAME_END:
                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.PRE_FRAME:
                # Grab the physical controller state and put that into the controller state
                controller_port = unpack(">B", event_bytes[0x5:0x5+1])[0] + 1
                main_x = unpack(">f", event_bytes[0x19:0x19+4])[0]
                main_y = unpack(">f", event_bytes[0x1D:0x1D+4])[0]
                gamestate.player[controller_port].controller_state.main_stick = (main_x, main_y)

                c_x = unpack(">f", event_bytes[0x21:0x21+4])[0]
                c_y = unpack(">f", event_bytes[0x25:0x25+4])[0]
                gamestate.player[controller_port].controller_state.c_stick = (c_x, c_y)

                buttonbits = unpack(">H", event_bytes[0x31:0x31+2])[0]
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_A] = bool(buttonbits & 0x0100)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_B] = bool(buttonbits & 0x0200)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_X] = bool(buttonbits & 0x0400)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_Y] = bool(buttonbits & 0x0800)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_START] = bool(buttonbits & 0x1000)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_Z] = bool(buttonbits & 0x0010)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_R] = bool(buttonbits & 0x0020)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_L] = bool(buttonbits & 0x0040)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_D_LEFT] = bool(buttonbits & 0x0001)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_D_RIGHT] = bool(buttonbits & 0x0002)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_D_DOWN] = bool(buttonbits & 0x0004)
                gamestate.player[controller_port].controller_state.button[enums.Button.BUTTON_D_UP] = bool(buttonbits & 0x0008)

                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.POST_FRAME:
                gamestate.stage = self._current_stage
                gamestate.frame = unpack(">i", event_bytes[0x1:0x1+4])[0]
                controller_port = unpack(">B", event_bytes[0x5:0x5+1])[0] + 1

                gamestate.player[controller_port].x = unpack(">f", event_bytes[0xa:0xa+4])[0]
                gamestate.player[controller_port].y = unpack(">f", event_bytes[0xe:0xe+4])[0]

                gamestate.player[controller_port].character = enums.Character(unpack(">B", event_bytes[0x7:0x7+1])[0])
                try:
                    gamestate.player[controller_port].action = enums.Action(unpack(">H", event_bytes[0x8:0x8+2])[0])
                except ValueError:
                    gamestate.player[controller_port].action = enums.Action.UNKNOWN_ANIMATION

                # Melee stores this in a float for no good reason. So we have to convert
                facing_float = unpack(">f", event_bytes[0x12:0x12+4])[0]
                gamestate.player[controller_port].facing = facing_float > 0

                gamestate.player[controller_port].percent = int(unpack(">f", event_bytes[0x16:0x16+4])[0])
                gamestate.player[controller_port].shield_strength = unpack(">f", event_bytes[0x1A:0x1A+4])[0]
                gamestate.player[controller_port].stock = unpack(">B", event_bytes[0x21:0x21+1])[0]
                gamestate.player[controller_port].action_frame = int(unpack(">f", event_bytes[0x22:0x22+4])[0])

                # Extract the bit at mask 0x20
                bitflags2 = unpack(">B", event_bytes[0x27:0x27+1])[0]
                gamestate.player[controller_port].hitlag = bool(bitflags2 & 0x20)

                try:
                    gamestate.player[controller_port].hitstun_frames_left = int(unpack(">f", event_bytes[0x2b:0x2b+4])[0])
                except ValueError:
                    gamestate.player[controller_port].hitstun_frames_left = 0
                gamestate.player[controller_port].on_ground = not bool(unpack(">B", event_bytes[0x2f:0x2f+1])[0])
                gamestate.player[controller_port].jumps_left = unpack(">B", event_bytes[0x32:0x32+1])[0]
                gamestate.player[controller_port].invulnerable = int(unpack(">B", event_bytes[0x34:0x34+1])[0]) != 0

                try:
                    gamestate.player[controller_port].speed_air_x_self = unpack(">f", event_bytes[0x35:0x35+4])[0]
                except error:
                    gamestate.player[controller_port].speed_air_x_self = 0

                try:
                    gamestate.player[controller_port].speed_y_self = unpack(">f", event_bytes[0x39:0x39+4])[0]
                except error:
                    gamestate.player[controller_port].speed_y_self = 0

                try:
                    gamestate.player[controller_port].speed_x_attack = unpack(">f", event_bytes[0x3d:0x3d+4])[0]
                except error:
                    gamestate.player[controller_port].speed_x_attack = 0

                try:
                    gamestate.player[controller_port].speed_y_attack = unpack(">f", event_bytes[0x41:0x41+4])[0]
                except error:
                    gamestate.player[controller_port].speed_y_attack = 0

                try:
                    gamestate.player[controller_port].speed_ground_x_self = unpack(">f", event_bytes[0x45:0x45+4])[0]
                except error:
                    gamestate.player[controller_port].speed_ground_x_self = 0

                # Keep track of a player's invulnerability due to respawn or ledge grab
                gamestate.player[controller_port].invulnerability_left = max(0, self._prev_gamestate.player[controller_port].invulnerability_left - 1)
                if gamestate.player[controller_port].action == Action.ON_HALO_WAIT:
                    gamestate.player[controller_port].invulnerability_left = 120
                # Don't give invulnerability to the first descent
                if gamestate.player[controller_port].action == Action.ON_HALO_DESCENT and gamestate.frame > 150:
                    gamestate.player[controller_port].invulnerability_left = 120
                if gamestate.player[controller_port].action == Action.EDGE_CATCHING and gamestate.player[controller_port].action_frame == 1:
                    gamestate.player[controller_port].invulnerability_left = 36

                # The pre-warning occurs when we first start a dash dance.
                if gamestate.player[controller_port].action == Action.DASHING and \
                        self._prev_gamestate.player[controller_port].action not in [Action.DASHING, Action.TURNING]:
                    gamestate.player[controller_port].moonwalkwarning = True

                # Take off the warning if the player does an action other than dashing
                if gamestate.player[controller_port].action != Action.DASHING:
                    gamestate.player[controller_port].moonwalkwarning = False

                # "off_stage" helper
                if (abs(gamestate.player[controller_port].x) > stages.EDGE_GROUND_POSITION[gamestate.stage] or \
                        gamestate.player[controller_port].y < -6) and not gamestate.player[controller_port].on_ground:
                    gamestate.player[controller_port].off_stage = True
                else:
                    gamestate.player[controller_port].off_stage = False

                # ECB top edge, x
                ecb_top_x = 0
                ecb_top_y = 0
                try:
                    ecb_top_x = unpack(">f", event_bytes[0x49:0x49+4])[0]
                except error:
                    ecb_top_x = 0
                # ECB Top edge, y
                try:
                    ecb_top_y = unpack(">f", event_bytes[0x4D:0x4D+4])[0]
                except error:
                    ecb_top_y = 0
                gamestate.player[controller_port].ecb_top = (ecb_top_x, ecb_top_y)

                # ECB bottom edge, x coord
                ecb_bot_x = 0
                ecb_bot_y = 0
                try:
                    ecb_bot_x = unpack(">f", event_bytes[0x51:0x51+4])[0]
                except error:
                    ecb_bot_x = 0
                # ECB Bottom edge, y coord
                try:
                    ecb_bot_y = unpack(">f", event_bytes[0x55:0x55+4])[0]
                except error:
                    ecb_bot_y = 0
                gamestate.player[controller_port].ecb_bottom = (ecb_bot_x, ecb_bot_y)

                # ECB left edge, x coord
                ecb_left_x = 0
                ecb_left_y = 0
                try:
                    ecb_left_x = unpack(">f", event_bytes[0x59:0x59+4])[0]
                except error:
                    ecb_left_x = 0
                # ECB left edge, y coord
                try:
                    ecb_left_y = unpack(">f", event_bytes[0x5D:0x5D+4])[0]
                except error:
                    ecb_left_y = 0
                gamestate.player[controller_port].ecb_left = (ecb_left_x, ecb_left_y)

                # ECB right edge, x coord
                ecb_right_x = 0
                ecb_right_y = 0
                try:
                    ecb_right_x = unpack(">f", event_bytes[0x61:0x61+4])[0]
                except error:
                    ecb_right_x = 0
                # ECB right edge, y coord
                try:
                    ecb_right_y = unpack(">f", event_bytes[0x65:0x65+4])[0]
                except error:
                    ecb_right_y = 0
                gamestate.player[controller_port].ecb_right = (ecb_right_x, ecb_right_y)

                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.GECKO_CODES:
                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.FRAME_BOOKEND:
                self._prev_gamestate = gamestate

                # Calculate helper distance variable
                #   This is a bit kludgey.... :/
                i = 0
                player_one_x, player_one_y, player_two_x, player_two_y = 0, 0, 0, 0
                for _, player_state in gamestate.player.items():
                    if i == 0:
                        player_one_x, player_one_y = player_state.x, player_state.y
                    if i == 1:
                        player_two_x, player_two_y = player_state.x, player_state.y
                    i += 1
                xdist = player_one_x - player_two_x
                ydist = player_one_y - player_two_y
                gamestate.distance = math.sqrt((xdist**2) + (ydist**2))
                event_bytes = event_bytes[event_size:]

                # If this is an old frame, then don't return it.
                if gamestate.frame <= self._frame:
                    return False
                self._frame = gamestate.frame
                return True

            elif EventType(event_bytes[0]) == EventType.ITEM_UPDATE:
                projectile = Projectile()
                projectile.x = unpack(">f", event_bytes[0x14:0x14+4])[0]
                projectile.y = unpack(">f", event_bytes[0x18:0x18+4])[0]
                projectile.x_speed = unpack(">f", event_bytes[0x0c:0x0c+4])[0]
                projectile.y_speed = unpack(">f", event_bytes[0x10:0x10+4])[0]
                try:
                    projectile.owner = unpack(">B", event_bytes[0x2A:0x2A+1])[0] + 1
                    if projectile.owner > 4:
                        projectile.owner = -1
                except error:
                    projectile.owner = -1
                try:
                    projectile.subtype = enums.ProjectileSubtype(unpack(">H", event_bytes[0x05:0x05+2])[0])
                except ValueError:
                    projectile.subtype = enums.ProjectileSubtype.UNKNOWN_PROJECTILE
                # Add the projectile to the gamestate list
                gamestate.projectiles.append(projectile)

                event_bytes = event_bytes[event_size:]

            else:
                print("WARNING: Something went wrong unpacking events. " + \
                    "Data is probably missing")
                print("\tGot invalid event type: ", event_bytes[0])
                return False

        return False

    def __handle_slippstream_menu_event(self, event_bytes, gamestate):
        """ Internal handler for slippstream menu events

        Modifies specified gamestate based on the event bytes
         """
        scene = unpack(">H", event_bytes[0x1:0x1+2])[0]
        if scene == 0x02:
            gamestate.menu_state = enums.Menu.CHARACTER_SELECT
        elif scene == 0x0102:
            gamestate.menu_state = enums.Menu.STAGE_SELECT
        elif scene == 0x0202:
            gamestate.menu_state = enums.Menu.IN_GAME
        elif scene == 0x0001:
            gamestate.menu_state = enums.Menu.MAIN_MENU
        elif scene == 0x0008:
            gamestate.menu_state = enums.Menu.SLIPPI_ONLINE_CSS
        elif scene == 0x0000:
            gamestate.menu_state = enums.Menu.PRESS_START
        else:
            gamestate.menu_state = enums.Menu.UNKNOWN_MENU

        # CSS Cursors
        gamestate.player[1].cursor_x = unpack(">f", event_bytes[0x3:0x3+4])[0]
        gamestate.player[1].cursor_y = unpack(">f", event_bytes[0x7:0x7+4])[0]
        gamestate.player[2].cursor_x = unpack(">f", event_bytes[0xB:0xB+4])[0]
        gamestate.player[2].cursor_y = unpack(">f", event_bytes[0xF:0xF+4])[0]
        gamestate.player[3].cursor_x = unpack(">f", event_bytes[0x13:0x13+4])[0]
        gamestate.player[3].cursor_y = unpack(">f", event_bytes[0x17:0x17+4])[0]
        gamestate.player[4].cursor_x = unpack(">f", event_bytes[0x1B:0x1B+4])[0]
        gamestate.player[4].cursor_y = unpack(">f", event_bytes[0x1F:0x1F+4])[0]

        # Ready to fight banner
        gamestate.ready_to_start = unpack(">B", event_bytes[0x23:0x23+1])[0] == 0

        # Stage
        try:
            gamestate.stage = enums.Stage(unpack(">B", event_bytes[0x24:0x24+1])[0])
        except ValueError:
            gamestate.stage = enums.Stage.NO_STAGE

        # controller port statuses at CSS
        try:
            gamestate.player[1].controller_status = enums.ControllerStatus(unpack(">B", event_bytes[0x25:0x25+1])[0])
        except error:
            gamestate.player[1].controller_status = enums.ControllerStatus.CONTROLLER_UNPLUGGED
        try:
            gamestate.player[2].controller_status = enums.ControllerStatus(unpack(">B", event_bytes[0x26:0x26+1])[0])
        except error:
            gamestate.player[2].controller_status = enums.ControllerStatus.CONTROLLER_UNPLUGGED
        try:
            gamestate.player[3].controller_status = enums.ControllerStatus(unpack(">B", event_bytes[0x27:0x27+1])[0])
        except error:
            gamestate.player[3].controller_status = enums.ControllerStatus.CONTROLLER_UNPLUGGED
        try:
            gamestate.player[4].controller_status = enums.ControllerStatus(unpack(">B", event_bytes[0x28:0x28+1])[0])
        except error:
            gamestate.player[4].controller_status = enums.ControllerStatus.CONTROLLER_UNPLUGGED

        # Character selected
        try:
            tmp = unpack(">B", event_bytes[0x29:0x29+1])[0]
            gamestate.player[1].character_selected = enums.to_internal(tmp)
        except error:
            gamestate.player[1].character_selected = enums.Character.UNKNOWN_CHARACTER
        try:
            tmp = unpack(">B", event_bytes[0x2A:0x2A+1])[0]
            gamestate.player[2].character_selected = enums.to_internal(tmp)
        except error:
            gamestate.player[2].character_selected = enums.Character.UNKNOWN_CHARACTER
        try:
            tmp = unpack(">B", event_bytes[0x2B:0x2B+1])[0]
            gamestate.player[3].character_selected = enums.to_internal(tmp)
        except error:
            gamestate.player[3].character_selected = enums.Character.UNKNOWN_CHARACTER
        try:
            tmp = unpack(">B", event_bytes[0x2C:0x2C+1])[0]
            gamestate.player[4].character_selected = enums.to_internal(tmp)
        except error:
            gamestate.player[4].character_selected = enums.Character.UNKNOWN_CHARACTER

        # Coin down
        try:
            gamestate.player[1].coin_down = unpack(">B", event_bytes[0x2D:0x2D+1])[0] == 2
        except error:
            gamestate.player[1].coin_down = False
        try:
            gamestate.player[2].coin_down = unpack(">B", event_bytes[0x2E:0x2E+1])[0] == 2
        except error:
            gamestate.player[2].coin_down = False
        try:
            gamestate.player[3].coin_down = unpack(">B", event_bytes[0x2F:0x2F+1])[0] == 2
        except error:
            gamestate.player[3].coin_down = False
        try:
            gamestate.player[4].coin_down = unpack(">B", event_bytes[0x30:0x30+1])[0] == 2
        except error:
            gamestate.player[4].coin_down = False

        # Stage Select Cursor X, Y
        gamestate.stage_select_cursor_x = unpack(">f", event_bytes[0x31:0x31+4])[0]
        gamestate.stage_select_cursor_y = unpack(">f", event_bytes[0x35:0x35+4])[0]

        # Frame count
        gamestate.frame = unpack(">i", event_bytes[0x39:0x39+4])[0]

        # Sub-menu
        try:
            gamestate.submenu = enums.SubMenu(unpack(">B", event_bytes[0x3D:0x3D+1])[0])
        except error:
            gamestate.submenu = enums.SubMenu.UNKNOWN_SUBMENU
        except ValueError:
            gamestate.submenu = enums.SubMenu.UNKNOWN_SUBMENU

        # Selected menu
        try:
            gamestate.menu_selection = unpack(">B", event_bytes[0x3E:0x3E+1])[0]
        except error:
            gamestate.menu_selection = 0

    def _get_dolphin_home_path(self):
        """Return the path to dolphin's home directory"""
        if self.path:
            return self.path + "/User/"

        home_path = str(Path.home())
        legacy_config_path = home_path + "/.dolphin-emu/"

        #Are we using a legacy Linux home path directory?
        if os.path.isdir(legacy_config_path):
            return legacy_config_path

        #Are we on OSX?
        osx_path = home_path + "/Library/Application Support/Dolphin/"
        if os.path.isdir(osx_path):
            return osx_path

        #Are we on a new Linux distro?
        linux_path = home_path + "/.local/share/dolphin-emu/"
        if os.path.isdir(linux_path):
            return linux_path

        print("ERROR: Are you sure Dolphin is installed? Make sure it is, and then run again.")
        return ""

    def _get_dolphin_config_path(self):
        """ Return the path to dolphin's config directory
        (which is not necessarily the same as the home path)"""
        if self.path:
            return self.path + "/User/Config/"

        home_path = str(Path.home())

        if platform.system() == "Windows":
            return home_path + "\\Dolphin Emulator\\Config\\"

        legacy_config_path = home_path + "/.dolphin-emu/"

        #Are we using a legacy Linux home path directory?
        if os.path.isdir(legacy_config_path):
            return legacy_config_path

        #Are we on a new Linux distro?
        linux_path = home_path + "/.config/dolphin-emu/"
        if os.path.isdir(linux_path):
            return linux_path

        #Are we on OSX?
        osx_path = home_path + "/Library/Application Support/Dolphin/Config/"
        if os.path.isdir(osx_path):
            return osx_path

        print("ERROR: Are you sure Dolphin is installed? Make sure it is, and then run again.")
        return ""

    def get_dolphin_pipes_path(self, port):
        """Get the path of the named pipe input file for the given controller port
        """
        if platform.system() == "Windows":
            return '\\\\.\\pipe\\slippibot' + str(port)
        return self._get_dolphin_home_path() + "/Pipes/slippibot" + str(port)

    def __fixframeindexing(self, gamestate):
        """ Melee's indexing of action frames is wildly inconsistent.
            Here we adjust all of the frames to be indexed at 1 (so math is easier)"""
        for _, player in gamestate.player.items():
            if player.action.value in self.zero_indices[player.character.value]:
                player.action_frame = player.action_frame + 1

    def __fixiasa(self, gamestate):
        """ The IASA flag doesn't set or reset for special attacks.
            So let's just set IASA to False for all non-A attacks.
        """
        for _, player in gamestate.player.items():
            # Luckily for us, all the A-attacks are in a contiguous place in the enums!
            #   So we don't need to call them out one by one
            if player.action.value < Action.NEUTRAL_ATTACK_1.value or player.action.value > Action.DAIR.value:
                player.iasa = False
