"""The Console represents the engine running the game.

This can be Dolphin (Ishiiruka), A Nintendont Wii, or an SLP file (TODO). The Console object
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
from melee import stages


# pylint: disable=too-many-instance-attributes
class Console:
    """The console object that represents your Dolphin / Wii / SLP file
    """
    def __init__(self, is_dolphin, ai_port, opponent_port, opponent_type,
                 dolphin_executable_path=None, slippi_address="", logger=None):
        """Create a Console object

        Args:
            is_dolphin (boolean): Is this console a dolphin? (Or a Wii)
            ai_port (int): 1-4 for the controller port your bot will take
            opponent_port (int): 1-4 for the controller port your opponent will take
            opponent_type (:obj:`enums.ControllerType`): Enum of your opponent's controller type
            dolphin_executable_path (str): Path to the directory where your dolphin executable is
                located. (if applicable) None tells console to use the installed copy of the emulator
            slippi_address (str): IP address of the Dolphin / Wii to connect to.
                Empty string will try to autodiscover a nearby SlippiComm server
        """
        self.logger = logger
        self.ai_port = ai_port
        self.opponent_port = opponent_port
        self.is_dolphin = is_dolphin
        self.dolphin_executable_path = dolphin_executable_path
        self.processingtime = 0
        self._frametimestamp = time.time()
        self.slippi_address = slippi_address
        """(str): IP address of the Dolphin / Wii to connect to."""
        self.slippi_port = 51441
        """(int): TCP port of slippi server. Default 51441"""
        self.eventsize = [0] * 0x100
        self.render = True
        self.connected = False
        self.nick = ""
        """(str): The nickname the console has given itself."""
        self.version = ""
        """(str): The Slippi version of the console"""
        self.cursor = 0
        self.controllers = []

        # Keep a running copy of the last gamestate produced
        self._prev_gamestate = GameState(ai_port, opponent_port)
        self._process = None
        if self.is_dolphin:
            pipes_path = self._get_dolphin_home_path() + "Pipes/"
            path = os.path.dirname(os.path.realpath(__file__))

            if platform.system() != "Windows":
                #Create the Pipes directory if it doesn't already exist
                if not os.path.exists(pipes_path):
                    os.makedirs(pipes_path)
                    print("WARNING: Had to create a Pipes directory in Dolphin just now. " \
                          "You may need to restart Dolphin and this program in order for this to work. " \
                          "(You should only see this warning once)")

                pipes_path += "slippibot" + str(ai_port)
                if not os.path.exists(pipes_path):
                    os.mkfifo(pipes_path)

            #setup the controllers specified
            self.setup_dolphin_controller(ai_port)
            self.setup_dolphin_controller(opponent_port, opponent_type)
            self._slippstream = SlippstreamClient(self.slippi_address, self.slippi_port)

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
            if self.dolphin_executable_path:
                exe_path = self.dolphin_executable_path
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

        #Change the bot's controller port to use "standard" input
        dolphin_config_path = self._get_dolphin_config_path() + "Dolphin.ini"
        config = configparser.SafeConfigParser()
        config.read(dolphin_config_path)
        #Indexed at 0. "6" means standard controller, "12" means GCN Adapter
        # The enum is scoped to the proper value, here
        config.set("Core", 'SIDevice'+str(port-1), controllertype.value)
        # Enable networking
        config.set("Core", 'slippienablespectator', "True")
        #Enable Cheats
        config.set("Core", 'enablecheats', "True")
        #Turn on background input so we don't need to have window focus on dolphin
        config.set("Input", 'backgroundinput', "True")
        with open(dolphin_config_path, 'w') as dolphinfile:
            config.write(dolphinfile)

        # #Enable the specific cheats we need (Netplay community settings)
        # melee_config_path = self._get_dolphin_home_path() + "/GameSettings/GALE01.ini"
        # config = configparser.SafeConfigParser(allow_no_value=True)
        # config.optionxform = str
        # config.read(melee_config_path)
        # if not config.has_section("Gecko_Enabled"):
        #     config.add_section("Gecko_Enabled")
        # config.set("Gecko_Enabled", "$Netplay Community Settings")
        # with open(melee_config_path, 'w') as dolphinfile:
        #     config.write(dolphinfile)

    def step(self):
        """ 'step' to the next state of the game and flushes all controllers

        Returns:
            GameState object that represents new current state of the game"""
        # Keep looping until we get a REPLAY message
        self.processingtime = time.time() - self._frametimestamp

        # Flush the controllers
        for controler in self.controllers:
            controler.flush()

        gamestate = GameState(self.ai_port, self.opponent_port)
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
                        frame_ended = self.__handle_slippstream_events(base64.b64decode(message["payload"]), gamestate)
                elif message["type"] == "menu_event":
                    if len(message["payload"]) > 0:
                        self.__handle_slippstream_menu_event(base64.b64decode(message["payload"]), gamestate)
                        frame_ended = True

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
                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.GAME_END:
                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.PRE_FRAME:
                event_bytes = event_bytes[event_size:]

            elif EventType(event_bytes[0]) == EventType.POST_FRAME:
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
        if self.dolphin_executable_path:
            return self.dolphin_executable_path + "/User/"

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
        if self.dolphin_executable_path:
            return self.dolphin_executable_path + "/User/Config/"

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
