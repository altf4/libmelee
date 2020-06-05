from socket import *
from struct import unpack
from collections import defaultdict

import time
import ubjson
import os
import configparser
import csv
import subprocess
import platform
import sys
from pathlib import Path

from melee import enums
from melee.gamestate import GameState, Projectile, Action
from melee.slippstream import SlippstreamClient, CommType, EventType

class Console:
    def __init__(self, is_dolphin, ai_port, opponent_port, opponent_type,
                 dolphin_executable_path=None, logger=None):
        self.logger = logger
        self.ai_port = ai_port
        self.opponent_port = opponent_port
        self.is_dolphin = is_dolphin
        self.dolphin_executable_path = dolphin_executable_path

        self.processingtime = 0
        self._frametimestamp = time.time()
        self.slippi_address = ""
        self.slippi_port = 51441
        self.eventsize = [0] * 0x100

        # Keep a running copy of the last gamestate produced
        #   game info is only produced as diffs, not whole snapshots
        #   so if nothing changes, we need to know what the last value was
        self.render = True
        self._prev_gamestate = GameState(ai_port, opponent_port)
        self.process = None
        if self.is_dolphin:
            config_path = self._get_dolphin_home_path()
            pipes_path = config_path + "Pipes/"
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

        Returns boolean of success """
        self.slippstream = SlippstreamClient(self.slippi_address, self.slippi_port)
        # It can take a short amount of time after starting the emulator
        #   for the actual server to start. So try a few times before giving up.
        for i in range(4):
            if(self.slippstream.connect()):
                return True
        return False

    def run(self, iso_path=None, movie_path=None, dolphin_config_path=None):
        """Run dolphin-emu"""
        if self.is_dolphin:
            exe_name = "/dolphin-emu"
            if platform.system() == "Windows":
                exe_name = "/Dolphin.exe"
            command = [self.dolphin_executable_path + exe_name]
            if not self.render:
                #Use the "Null" renderer
                command.append("-v")
                command.append("Null")
            if movie_path is not None:
                command.append("-m")
                command.append(movie_path)
            if iso_path is not None:
                command.append("-e")
                command.append(iso_path)
            if dolphin_config_path is not None:
                command.append("-u")
                command.append(dolphin_config_path)
            self.process = subprocess.Popen(command)
            # TODO proper error tracking here
            return True

    def stop(self):
        self.slippstream.shutdown();
        # If dolphin, kill the process
        if self.process != None:
            self.process.terminate()
        pass

    """Setup the necessary files for dolphin to recognize the player at the given
    controller port and type"""
    def setup_dolphin_controller(self, port, controllertype=enums.ControllerType.STANDARD):
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
        config.set("General", 'EnableSlippiNetworkingOutput', "True")
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
        # Keep looping until we get a REPLAY message
        self.processingtime = time.time() - self._frametimestamp
        gamestate = GameState(self.ai_port, self.opponent_port)
        frame_ended = False
        while not frame_ended:
            msg = self.slippstream.read_message()
            if msg:
                if (CommType(msg['type']) == CommType.REPLAY):
                    events = msg['payload']['data']
                    frame_ended = self.__handle_slippstream_events(events, gamestate)
                    # Start the processing timer now that we're done reading messages
                    self._frametimestamp = time.time()
                    continue

                # We can basically just ignore keepalives
                elif (CommType(msg['type']) == CommType.KEEPALIVE):
                    continue

                elif (CommType(msg['type']) == CommType.HANDSHAKE):
                    p = msg['payload']
                    print("Connected to console '{}' (Slippi Nintendont {})".format(
                        p['nick'],
                        p['nintendontVersion'],
                    ))
                    continue

        self.__fixframeindexing(gamestate)
        self.__fixiasa(gamestate)
        return gamestate

    def __handle_slippstream_events(self, event_bytes, gamestate):
        """ Handle a series of events, provided sequentially in a byte array """
        lastmessage = EventType.GAME_START
        while len(event_bytes) > 0:
            lastmessage = EventType(event_bytes[0])
            event_size = self.eventsize[event_bytes[0]]
            if len(event_bytes) < event_size:
                print("WARNING: Something went wrong unpacking events. Data is probably missing")
                print("\tDidn't have enough data for event")
                return False
            if (EventType(event_bytes[0]) == EventType.PAYLOADS):
                cursor = 0x2
                payload_size = event_bytes[1]
                num_commands = (payload_size - 1) // 3
                for i in range(0, num_commands):
                    command, command_len = unpack(">bH", event_bytes[cursor:cursor+3])
                    self.eventsize[command] = command_len+1
                    cursor += 3
                event_bytes = event_bytes[payload_size + 1:]
                continue

            elif (EventType(event_bytes[0]) == EventType.FRAME_START):
                self.frame_num = unpack(">i", event_bytes[1:5])[0]
                event_bytes = event_bytes[event_size:]
                continue

            elif (EventType(event_bytes[0]) == EventType.GAME_START):
                event_bytes = event_bytes[event_size:]
                continue

            elif (EventType(event_bytes[0]) == EventType.GAME_END):
                event_bytes = event_bytes[event_size:]
                continue

            elif (EventType(event_bytes[0]) == EventType.PRE_FRAME):
                event_bytes = event_bytes[event_size:]
                continue

            elif (EventType(event_bytes[0]) == EventType.POST_FRAME):
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

                gamestate.player[controller_port].hitstun_frames_left = int(unpack(">f", event_bytes[0x2b:0x2b+4])[0])
                gamestate.player[controller_port].on_ground = not bool(unpack(">B", event_bytes[0x2f:0x2f+1])[0])
                gamestate.player[controller_port].jumps_left = unpack(">B", event_bytes[0x32:0x32+1])[0]
                gamestate.player[controller_port].invulnerable = int(unpack(">B", event_bytes[0x34:0x34+1])[0]) != 0

                event_bytes = event_bytes[event_size:]
                continue

            elif (EventType(event_bytes[0]) == EventType.GECKO_CODES):
                event_bytes = event_bytes[event_size:]
                continue

            elif (EventType(event_bytes[0]) == EventType.FRAME_BOOKEND):
                event_bytes = event_bytes[event_size:]
                return True

            elif (EventType(event_bytes[0]) == EventType.ITEM_UPDATE):
                # TODO projectiles
                projectile = Projectile()
                projectile.x = unpack(">f", event_bytes[0x14:0x14+4])[0]
                projectile.y = unpack(">f", event_bytes[0x18:0x18+4])[0]
                projectile.x_speed = unpack(">f", event_bytes[0x0c:0x0c+4])[0]
                projectile.y_speed = unpack(">f", event_bytes[0x10:0x10+4])[0]
                try:
                    projectile.subtype = enums.ProjectileSubtype(unpack(">H", event_bytes[0x05:0x05+2])[0])
                except ValueError:
                    projectile.subtype = enums.ProjectileSubtype.UNKNOWN_PROJECTILE
                # Add the projectile to the gamestate list
                gamestate.projectiles.append(projectile)

                event_bytes = event_bytes[event_size:]
                continue

            else:
                print("WARNING: Something went wrong unpacking events. " + \
                    "Data is probably missing")
                print("\tGot invalid event type: ", event_bytes[0])
                return False

        return False

    def _get_dolphin_home_path(self):
        """Return the path to dolphin's home directory"""
        if self.dolphin_executable_path:
            return self.dolphin_executable_path + "/User/"

        home_path = str(Path.home())
        legacy_config_path = home_path + "/.dolphin-emu/";

        #Are we using a legacy Linux home path directory?
        if os.path.isdir(legacy_config_path):
            return legacy_config_path

        #Are we on OSX?
        osx_path = home_path + "/Library/Application Support/Dolphin/";
        if os.path.isdir(osx_path):
            return osx_path

        #Are we on a new Linux distro?
        linux_path = home_path + "/.local/share/dolphin-emu/";
        if os.path.isdir(linux_path):
            return linux_path

        print("ERROR: Are you sure Dolphin is installed? Make sure it is,\
                and then run again.")
        sys.exit(1)
        return ""

    def _get_dolphin_config_path(self):
        """ Return the path to dolphin's config directory
        (which is not necessarily the same as the home path)"""
        if self.dolphin_executable_path:
            return self.dolphin_executable_path + "/User/Config/"

        home_path = str(Path.home())

        if platform.system() == "Windows":
            return home_path + "\\Dolphin Emulator\\Config\\"

        legacy_config_path = home_path + "/.dolphin-emu/";

        #Are we using a legacy Linux home path directory?
        if os.path.isdir(legacy_config_path):
            return legacy_config_path

        #Are we on a new Linux distro?
        linux_path = home_path + "/.config/dolphin-emu/";
        if os.path.isdir(linux_path):
            return linux_path

        #Are we on OSX?
        osx_path = home_path + "/Library/Application Support/Dolphin/Config/";
        if os.path.isdir(osx_path):
            return osx_path

        print("ERROR: Are you sure Dolphin is installed? Make sure it is,\
                and then run again.")
        sys.exit(1)
        return ""

    def get_dolphin_pipes_path(self, port):
        """Get the path of the named pipe input file for the given controller port
        """
        if platform.system() == "Windows":
            return '\\\\.\\pipe\\slippibot' + str(port)
        return self._get_dolphin_home_path() + "/Pipes/slippibot" + str(port)

    # Melee's indexing of action frames is wildly inconsistent.
    #   Here we adjust all of the frames to be indexed at 1 (so math is easier)
    def __fixframeindexing(self, gamestate):
        for _, player in gamestate.player.items():
            if player.action.value in self.zero_indices[player.character.value]:
                player.action_frame = player.action_frame + 1

    # The IASA flag doesn't set or reset for special attacks.
    #   So let's just set IASA to False for all non-A attacks.
    def __fixiasa(self, gamestate):
        for index, player in gamestate.player.items():
            # Luckily for us, all the A-attacks are in a contiguous place in the enums!
            #   So we don't need to call them out one by one
            if player.action.value < Action.NEUTRAL_ATTACK_1.value or player.action.value > Action.DAIR.value:
                player.iasa = False
