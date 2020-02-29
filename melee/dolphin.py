import os, pwd, shutil, subprocess, sys
import configparser
import socket
import time
import csv
from collections import defaultdict
import binascii
from struct import unpack
import math
import copy

from melee import enums, stages
from melee.gamestate import GameState, Projectile
from melee.enums import Action, Character
from melee.console import Console

"""Class for making confuguration and interfacing with the Dolphin emulator easy"""
class Dolphin(Console):

    """Do a some setup of some important dolphin paths"""
    def __init__(self, ai_port, opponent_port, opponent_type, logger=None):
        # Keep a running copy of the last gamestate produced
        #   game info is only produced as diffs, not whole snapshots
        #   so if nothing changes, we need to know what the last value was
        self.memory_watcher = MemoryWatcher()
        self.render = True
        self._prev_gamestate = GameState(ai_port, opponent_port)
        self.ai_port = ai_port
        self.opponent_port = opponent_port
        self.logger = logger
        self.process = None
        config_path = Dolphin.get_dolphin_home_path()
        mem_watcher_path = config_path + "MemoryWatcher/"
        pipes_path = config_path + "Pipes/"
        self.processingtime = 0.0
        self.frametimestamp = 0.0
        #Dict with key of address, and value of (name, player)
        self.locations = dict()
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + "/locations.csv") as csvfile:
            reader = csv.DictReader(csvfile)
            for line in reader:
                self.locations[line["Address"]] = (line["Name"], line["Player"])

        #Create the MemoryWatcher directory if it doesn't already exist
        if not os.path.exists(mem_watcher_path):
            os.makedirs(mem_watcher_path)
            print("WARNING: Had to create a MemoryWatcher directory in Dolphin just now. " \
                "You may need to restart Dolphin and this program in order for this to work. " \
                "(You should only see this warning once)")

        #Copy over Locations.txt that is adjacent to this file
        path = os.path.dirname(os.path.realpath(__file__))
        shutil.copy(path + "/Locations.txt", mem_watcher_path)

        #Create the Pipes directory if it doesn't already exist
        if not os.path.exists(pipes_path):
            os.makedirs(pipes_path)
            print("WARNING: Had to create a Pipes directory in Dolphin just now. " \
                "You may need to restart Dolphin and this program in order for this to work. " \
                "(You should only see this warning once)")

        pipes_path += "Bot" + str(ai_port)
        if not os.path.exists(pipes_path):
            os.mkfifo(pipes_path)

        #setup the controllers specified
        self.setup_controller(ai_port)
        self.setup_controller(opponent_port, opponent_type)

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
        #read the character data csv
        self.characterdata = dict()
        with open(path + "/characterdata.csv") as csvfile:
            reader = csv.DictReader(csvfile)
            for line in reader:
                del line["Character"]
                #Convert all fields to numbers
                for key, value in line.items():
                    line[key] = float(value)
                self.characterdata[Character(line["CharacterIndex"])] = line

    """Setup the necessary files for dolphin to recognize the player at the given
    controller port and type"""
    def setup_controller(self, port, controllertype=enums.ControllerType.STANDARD):
        #Read in dolphin's controller config file
        controller_config_path = self.get_dolphin_config_path() + "GCPadNew.ini"
        config = configparser.SafeConfigParser()
        config.read(controller_config_path)

        #Add a bot standard controller config to the given port
        section = "GCPad" + str(port)
        if not config.has_section(section):
            config.add_section(section)

        if controllertype == enums.ControllerType.STANDARD:
            config.set(section, 'Device', 'Pipe/0/Bot' + str(port))
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
            config.set(section, 'D-Pad/Up', 'T')
            config.set(section, 'D-Pad/Down', 'G')
            config.set(section, 'D-Pad/Left', 'F')
            config.set(section, 'D-Pad/Right', 'H')
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
        dolphinn_config_path = self.get_dolphin_config_path() + "Dolphin.ini"
        config = configparser.SafeConfigParser()
        config.read(dolphinn_config_path)
        #Indexed at 0. "6" means standard controller, "12" means GCN Adapter
        # The enum is scoped to the proper value, here
        config.set("Core", 'SIDevice'+str(port-1), controllertype.value)
        #Enable Cheats
        config.set("Core", 'enablecheats', "True")
        #Turn on background input so we don't need to have window focus on dolphin
        config.set("Input", 'backgroundinput', "True")
        with open(dolphinn_config_path, 'w') as dolphinfile:
            config.write(dolphinfile)

        #Enable the specific cheats we need (Netplay community settings)
        melee_config_path = Dolphin.get_dolphin_home_path() + "/GameSettings/GALE01.ini"
        config = configparser.SafeConfigParser(allow_no_value=True)
        config.optionxform = str
        config.read(melee_config_path)
        if not config.has_section("Gecko_Enabled"):
            config.add_section("Gecko_Enabled")
        config.set("Gecko_Enabled", "$Netplay Community Settings")
        with open(melee_config_path, 'w') as dolphinfile:
            config.write(dolphinfile)

    """Run dolphin-emu"""
    def run(self, iso_path=None, movie_path=None, dolphin_executable_path=None, dolphin_config_path=None):
        if dolphin_executable_path is not None:
            command = [dolphin_executable_path]
        else:
            command = ["dolphin-emu"]
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

    """Terminate the dolphin process"""
    def stop(self):
        if self.process != None:
            self.process.terminate()

    """Return the path to dolphin's home directory"""
    @staticmethod
    def get_dolphin_home_path():
        home_path = pwd.getpwuid(os.getuid()).pw_dir
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

    """ Return the path to dolphin's config directory
            (which is not necessarily the same as the home path)"""
    def get_dolphin_config_path(self):
        home_path = pwd.getpwuid(os.getuid()).pw_dir
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

    """Get the path of the named pipe input file for the given controller port"""
    def get_dolphin_pipes_path(self, port):
        return Dolphin.get_dolphin_home_path() + "/Pipes/Bot" + str(port)

    #Melee's indexing of action frames is wildly inconsistent.
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

    def step(self):
        """Step to the next frame, blocking until it occurs
                returns a gamestate object"""
        # How long did it take to get here from last time?
        gamestate = self._prev_gamestate
        self.processingtime = time.time() - self.frametimestamp
        for mem_update in self.memory_watcher:
            #If the frame counter has updated, then process it!
            if self.__update(mem_update, gamestate):
                # Start the timer, now that we're done waiting for dolphin updates
                self.frametimestamp = time.time()
                self._prev_gamestate = gamestate
                return copy.copy(gamestate)

    def __update(self, mem_update, gamestate):
        """Process one new memory update
           returns True if the frame is finished processing (no more updates this frame)
           Run this in a loop until it returns returns True, then press your buttons,
           wash, rinse, repeat."""

        label = self.locations[mem_update[0]][0]
        player_int = int(self.locations[mem_update[0]][1])
        if label == "frame":
            gamestate.frame = unpack('<I', mem_update[1])[0]
            gamestate.newframe = True
            #Now that the frame is ready, let's calculate some derived information
            #   These are not stored inside Melee anywhere, but are nonetheless
            #   important pieces of information that we don't want to make the
            #   user have to re-calculate on their own
            for i in gamestate.player:
                # Move current x,y over to prev
                gamestate.player[i]._prev_x = gamestate.player[i].x
                gamestate.player[i]._prev_y = gamestate.player[i].y
                # Move future x,y over to current
                gamestate.player[i].x = gamestate.player[i]._next_x
                gamestate.player[i].y = gamestate.player[i]._next_y

                if (abs(gamestate.player[i].x) > stages.edgegroundposition(gamestate.stage) or \
                        gamestate.player[i].y < -6) and not gamestate.player[i].on_ground:
                    gamestate.player[i].off_stage = True
                else:
                    gamestate.player[i].off_stage = False

                # Keep track of a player's invulnerability due to respawn or ledge grab
                gamestate.player[i].invulnerability_left = max(0, gamestate.player[i].invulnerability_left - 1)
                if gamestate.player[i].action == Action.ON_HALO_WAIT:
                    gamestate.player[i].invulnerability_left = 120
                # Don't give invulnerability to the first descent
                if gamestate.player[i].action == Action.ON_HALO_DESCENT and gamestate.frame > 150:
                    gamestate.player[i].invulnerability_left = 120
                if gamestate.player[i].action == Action.EDGE_CATCHING and gamestate.player[i].action_frame == 1:
                    gamestate.player[i].invulnerability_left = 36

                # Which character are we right now?
                if gamestate.player[i].character in [Character.SHEIK, Character.ZELDA]:
                    if gamestate.player[i].transformed == gamestate.player[i].iszelda:
                        gamestate.player[i].character = Character.SHEIK
                    else:
                        gamestate.player[i].character = Character.ZELDA
                # If the player is transformed, then copy over the sub-character attributes
                if gamestate.player[i].transformed:
                    gamestate.player[i].action = gamestate.player[i+4].action
                    gamestate.player[i].action_frame = gamestate.player[i+4].action_frame
                    gamestate.player[i].invulnerable = gamestate.player[i+4].invulnerable
                    gamestate.player[i].hitlag = gamestate.player[i+4].hitlag
                    gamestate.player[i].hitstun_frames_left = gamestate.player[i+4].hitstun_frames_left
                    gamestate.player[i].charging_smash = gamestate.player[i+4].charging_smash
                    gamestate.player[i].jumps_left = gamestate.player[i+4].jumps_left
                    gamestate.player[i].on_ground = gamestate.player[i+4].on_ground
                    gamestate.player[i].speed_air_x_gamestate = gamestate.player[i+4].speed_air_x_self
                    gamestate.player[i].speed_y_self = gamestate.player[i+4].speed_y_self
                    gamestate.player[i].speed_x_attack = gamestate.player[i+4].speed_x_attack
                    gamestate.player[i].speed_y_attack = gamestate.player[i+4].speed_y_attack
                    gamestate.player[i].speed_ground_x_self = gamestate.player[i+4].speed_ground_x_self
                    gamestate.player[i].x = gamestate.player[i+4].x
                    gamestate.player[i].y = gamestate.player[i+4].y
                    gamestate.player[i].percent = gamestate.player[i+4].percent
                    gamestate.player[i].facing = gamestate.player[i+4].facing

                # The pre-warning occurs when we first start a dash dance.
                if gamestate.player[i].action == Action.DASHING and gamestate.player[i].prev_action not in [Action.DASHING, Action.TURNING]:
                    gamestate.player[i].moonwalkwarning = True

                # Take off the warning if the player does an action other than dashing
                if gamestate.player[i].action != Action.DASHING:
                    gamestate.player[i].moonwalkwarning = False

            #TODO: This needs updating in order to support >2 players
            xdist = gamestate.ai_state.x - gamestate.opponent_state.x
            ydist = gamestate.ai_state.y - gamestate.opponent_state.y
            gamestate.distance = math.sqrt( (xdist**2) + (ydist**2) )
            self.__fixiasa(gamestate)
            self.__fixframeindexing(gamestate)
            return True
        if label == "stage":
            gamestate.stage = unpack('<I', mem_update[1])[0]
            gamestate.stage = gamestate.stage >> 16
            gamestate.stage &= 0x000000ff
            try:
                gamestate.stage = enums.Stage(gamestate.stage)
            except ValueError:
                gamestate.stage = enums.Stage.NO_STAGE
            return False
        if label == "menu_state":
            gamestate.menu_state = unpack('<I', mem_update[1])[0]
            gamestate.menu_state &= 0x000000ff
            gamestate.menu_state = enums.Menu(gamestate.menu_state)
            return False
        #Player variables
        if label == "percent":
            if player_int > 4:
                try:
                    gamestate.player[player_int].percent = int(unpack('<f', mem_update[1])[0])
                except ValueError:
                    gamestate.player[player_int].percent = 0
                return False
            gamestate.player[player_int].percent = unpack('<I', mem_update[1])[0]
            gamestate.player[player_int].percent = gamestate.player[player_int].percent >> 16
            return False
        if label == "stock":
            gamestate.player[player_int].stock = unpack('<I', mem_update[1])[0]
            gamestate.player[player_int].stock = gamestate.player[player_int].stock >> 24
            return False
        if label == "facing":
            gamestate.player[player_int].facing = unpack('<I', mem_update[1])[0]
            gamestate.player[player_int].facing = not bool(gamestate.player[player_int].facing >> 31)
            return False
        if label == "x":
            gamestate.player[player_int].next_x = unpack('<f', mem_update[1])[0]
            return False
        if label == "y":
            gamestate.player[player_int]._next_y = unpack('<f', mem_update[1])[0]
            return False
        if label == "character":
            temp = unpack('<I', mem_update[1])[0]
            try:
                gamestate.player[player_int].character = enums.Character(temp)
            except ValueError:
                gamestate.player[player_int].character = enums.Character.UNKNOWN_CHARACTER
            return False
        if label == "character_selected":
            temp = unpack('<I', mem_update[1])[0] >> 24
            try:
                # Convert this character ID to an "internal" character ID
                #   to match with the enum values
                gamestate.player[player_int].character_selected = enums.convertToInternalCharacterID(temp)
            except ValueError:
                gamestate.player[player_int].character_selected = enums.Character.UNKNOWN_CHARACTER
            return False
        if label == "cursor_x":
            gamestate.player[player_int].cursor_x = unpack('<f', mem_update[1])[0]
            return False
        if label == "cursor_y":
            gamestate.player[player_int].cursor_y = unpack('<f', mem_update[1])[0]
            return False
        if label == "action":
            temp = unpack('<I', mem_update[1])[0]
            try:
                # Keep track of old action
                gamestate.player[player_int].prev_action = gamestate.player[player_int].action
                gamestate.player[player_int].action = enums.Action(temp)
            except ValueError:
                gamestate.player[player_int].action = enums.Action.UNKNOWN_ANIMATION
            return False
        if label == "action_frame":
            temp = unpack('<f', mem_update[1])[0]
            try:
                gamestate.player[player_int].action_frame = int(temp)
            except ValueError:
                pass
            return False
        if label == "invulnerable":
            gamestate.player[player_int].invulnerable = unpack('<I', mem_update[1])[0]
            gamestate.player[player_int].invulnerable = gamestate.player[player_int].invulnerable >> 31
            return False
        # We only really care if the character is in hitlag. So convert to bool
        if label == "hitlag":
            temp = unpack('<f', mem_update[1])[0]
            try:
                gamestate.player[player_int].hitlag = int(temp) > 0
            except ValueError:
                pass
            return False
        if label == "hitstun_frames_left":
            temp = unpack('<f', mem_update[1])[0]
            try:
                gamestate.player[player_int].hitstun_frames_left = int(temp)
            except ValueError:
                pass
            return False
        if label == "charging_smash":
            temp = unpack('<I', mem_update[1])[0]
            if temp == 2:
                gamestate.player[player_int].charging_smash = True
            else:
                gamestate.player[player_int].charging_smash = False
            return False
        if label == "jumps_left":
            temp = unpack('<I', mem_update[1])[0]
            temp = temp >> 24
            #This value is actually the number of jumps USED
            #   so we have to do some quick math to turn this into what we want
            try:
                totaljumps = int(self.characterdata[gamestate.player[player_int].character]["Jumps"])
                gamestate.player[player_int].jumps_left = totaljumps - temp + 1
            # Key error will be expected when we first start
            except KeyError:
                gamestate.player[player_int].jumps_left = 1
            return False
        if label == "on_ground":
            temp = unpack('<I', mem_update[1])[0]
            if temp == 0:
                gamestate.player[player_int].on_ground = True
            else:
                gamestate.player[player_int].on_ground = False
            return False
        if label == "speed_air_x_self":
            gamestate.player[player_int].speed_air_x_self = unpack('<f', mem_update[1])[0]
            return False
        if label == "speed_y_self":
            gamestate.player[player_int].speed_y_self = unpack('<f', mem_update[1])[0]
            return False
        if label == "speed_x_attack":
            gamestate.player[player_int].speed_x_attack = unpack('<f', mem_update[1])[0]
            return False
        if label == "speed_y_attack":
            gamestate.player[player_int].speed_y_attack = unpack('<f', mem_update[1])[0]
            return False
        if label == "speed_ground_x_self":
            gamestate.player[player_int].speed_ground_x_self = unpack('<f', mem_update[1])[0]
            return False
        if label == "coin_down":
            temp = unpack('<I', mem_update[1])[0]
            temp = temp & 0x000000ff
            gamestate.player[player_int].coin_down = (temp == 2)
            return False
        if label == "stage_select_cursor_x":
            gamestate.stage_select_cursor_x = unpack('<f', mem_update[1])[0]
            return False
        if label == "stage_select_cursor_y":
            gamestate.stage_select_cursor_y = unpack('<f', mem_update[1])[0]
            return False
        if label == "ready_to_start":
            temp = unpack('>I', mem_update[1])[0]
            temp = temp & 0x000000ff
            gamestate.ready_to_start = not bool(temp)
            return False
        if label == "controller_status":
            temp = unpack('>I', mem_update[1])[0]
            temp = temp & 0x000000ff
            gamestate.player[player_int].controller_status = enums.ControllerStatus(temp)
            return False
        if label == "hitbox_1_size":
            gamestate.player[player_int].hitbox_1_size = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_2_size":
            gamestate.player[player_int].hitbox_2_size = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_3_size":
            gamestate.player[player_int].hitbox_3_size = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_4_size":
            gamestate.player[player_int].hitbox_4_size = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_1_status":
            temp = unpack('<I', mem_update[1])[0]
            status = True
            if temp == 0:
                status = False
            gamestate.player[player_int].hitbox_1_status = status
            return False
        if label == "hitbox_2_status":
            temp = unpack('<I', mem_update[1])[0]
            status = True
            if temp == 0:
                status = False
            gamestate.player[player_int].hitbox_2_status = status
            return False
        if label == "hitbox_3_status":
            temp = unpack('<I', mem_update[1])[0]
            status = True
            if temp == 0:
                status = False
            gamestate.player[player_int].hitbox_3_status = status
            return False
        if label == "hitbox_4_status":
            temp = unpack('<I', mem_update[1])[0]
            status = True
            if temp == 0:
                status = False
            gamestate.player[player_int].hitbox_4_status = status
            return False
        if label == "hitbox_1_x":
            gamestate.player[player_int].hitbox_1_x = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_1_y":
            gamestate.player[player_int].hitbox_1_y = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_2_x":
            gamestate.player[player_int].hitbox_2_x = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_2_y":
            gamestate.player[player_int].hitbox_2_y = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_3_x":
            gamestate.player[player_int].hitbox_3_x = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_3_y":
            gamestate.player[player_int].hitbox_3_y = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_4_x":
            gamestate.player[player_int].hitbox_4_x = unpack('<f', mem_update[1])[0]
            return False
        if label == "hitbox_4_y":
            gamestate.player[player_int].hitbox_4_y = unpack('<f', mem_update[1])[0]
            return False
        if label == "iasa":
            gamestate.player[player_int].iasa = bool(unpack('<I', mem_update[1])[0] >> 31)
            return False
        if label == "transformed":
            temp = unpack('<I', mem_update[1])[0]
            status = False
            if temp == 16777216:
                status = True
            gamestate.player[player_int].transformed = status
            return False
        if label == "iszelda":
            temp = unpack('<I', mem_update[1])[0]
            status = False
            if temp == 18:
                status = True
            gamestate.player[player_int].iszelda = status
            return False
        if label == "projectiles":
            #Only once per new frame that we get a projectile, clear the list out
            if gamestate.newframe:
                gamestate.projectiles.clear()
                gamestate.i = 0
            gamestate.i += 1
            gamestate.newframe = False
            if len(mem_update[1]) < 10:
                gamestate.projectiles.clear()
                return False
            proj = Projectile()
            proj.x = unpack('>f', mem_update[1][0x4c:0x50])[0]
            proj.y = unpack('>f', mem_update[1][0x50:0x54])[0]
            proj.x_speed = unpack('>f', mem_update[1][0x40:0x44])[0]
            proj.y_speed = unpack('>f', mem_update[1][0x44:0x48])[0]
            try:
                proj.subtype = enums.ProjectileSubtype(unpack('>I', mem_update[1][0x10:0x14])[0])
            except ValueError:
                return False
            gamestate.projectiles.append(proj)
        return False

class MemoryWatcher:
    """Reads and parses game memory changes.
    Pass the location of the socket to the constructor, then either manually
    call next() on this class to get a single change, or else use it like a
    normal iterator.
    """
    def __init__(self):
        """Creates the socket if it does not exist, and then opens it."""
        path = self.__get_memory_watcher_socket_path()
        try:
            os.unlink(path)
        except OSError:
            pass
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(path)

    """Iterate over this class in the usual way to get memory changes."""
    def __iter__(self):
        return self

    """Closes the socket."""
    def __del__(self):
        self.sock.close()

    """Returns the next (address, value) tuple, or None on timeout.
    address is the string provided by dolphin, set in Locations.txt.
    value is a four-byte string suitable for interpretation with struct.
    """
    def __next__(self):
        try:
            data = self.sock.recvfrom(9096)[0].decode('utf-8').splitlines()
        except socket.timeout:
            return None
        # Strip the null terminator, pad with zeros, then convert to bytes
        return data[0], binascii.unhexlify(data[1].strip('\x00').zfill(8))

    """Get the MemoryWatcher socket path"""
    def __get_memory_watcher_socket_path(self):
        return Dolphin.get_dolphin_home_path() + "/MemoryWatcher/MemoryWatcher"
