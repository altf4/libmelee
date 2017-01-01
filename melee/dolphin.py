import os, pwd, shutil, subprocess
import configparser

"""Class for making confuguration and interfacing with the Dolphin emulator easy"""
class Dolphin:

    """Do a some setup of some important dolphin paths"""
    def __init__(self, ai_port, opponent_port, live, logger=None):
        self.ai_port = ai_port
        self.opponent_port = opponent_port
        self.logger = logger
        config_path = self.get_dolphin_home_path()
        mem_watcher_path = config_path + "MemoryWatcher/"
        pipes_path = config_path + "Pipes/"

        #Create the MemoryWatcher directory if it doesn't already exist
        if not os.path.exists(mem_watcher_path):
            os.makedirs(mem_watcher_path)
            print("WARNING: Had to create a MemoryWatcher directory in Dolphin just now. " \
                "You may need to restart Dolphin and SmashBot in order for this to work. " \
                "(You should only see this warning once)")

        #Copy over Locations.txt that is adjacent to this file
        path = os.path.dirname(os.path.realpath(__file__))
        shutil.copy(path + "/Locations.txt", mem_watcher_path)

        #Create the Pipes directory if it doesn't already exist
        if not os.path.exists(pipes_path):
            os.makedirs(pipes_path)
            print("WARNING: Had to create a Pipes directory in Dolphin just now. " \
                "You may need to restart Dolphin and SmashBot in order for this to work. " \
                "(You should only see this warning once)")

        pipes_path += "SmashBot" + str(ai_port)
        if not os.path.exists(pipes_path):
            os.mkfifo(pipes_path)

        #setup the controllers specified
        self.setup_controller(ai_port, False)
        self.setup_controller(opponent_port, live)

    """Setup the necessary files for dolphin to recognize the player at the given
    controller port and type"""
    def setup_controller(self, port, gcnadapter):
        #Read in dolphin's controller config file
        controller_config_path = self.get_dolphin_config_path() + "GCPadNew.ini"
        config = configparser.SafeConfigParser()
        config.read(controller_config_path)

        #Add a SmashBot standard controller config to the given port
        section = "GCPad" + str(port)
        if not config.has_section(section):
            config.add_section(section)

        if not gcnadapter:
            config.set(section, 'Device', 'Pipe/0/SmashBot' + str(port))
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
        else:
            config.set(section, 'Device', 'XInput2/0/Virtual core pointer')

        with open(controller_config_path, 'w') as configfile:
            config.write(configfile)

        #Change SmashBot's controller port to use "standard" input
        dolphinn_config_path = self.get_dolphin_config_path() + "Dolphin.ini"
        config = configparser.SafeConfigParser()
        config.read(dolphinn_config_path)
        #Indexed at 0. "6" means standard controller, "12" means GCN Adapter
        if not gcnadapter:
            config.set("Core", 'SIDevice'+str(port-1), "6")
        else:
            config.set("Core", 'SIDevice'+str(port-1), "12")
        #Enable Cheats
        config.set("Core", 'enablecheats', "True")
        #Turn on background input so we don't need to have window focus on dolphin
        config.set("Input", 'backgroundinput', "True")
        with open(dolphinn_config_path, 'w') as dolphinfile:
            config.write(dolphinfile)

        #Enable the cheats we need
        melee_config_path = self.get_dolphin_home_path() + "/GameSettings/GALE01.ini"
        config = configparser.SafeConfigParser(allow_no_value=True)
        config.optionxform = str
        config.read(melee_config_path)
        if not config.has_section("Gecko_Enabled"):
            config.add_section("Gecko_Enabled")
        config.set("Gecko_Enabled", "$Netplay Community Settings")
        with open(melee_config_path, 'w') as dolphinfile:
            config.write(dolphinfile)

    """Run dolphin-emu"""
    def run(self, render = True):
        command = ["dolphin-emu"]
        if not render:
            #Use the "Null" renderer
            command.append("-v Null")
        self.process = subprocess.Popen(command)

    """Terminate the dolphin process"""
    def terminate(self):
        self.process.terminate()

    """Return the path to dolphin's home directory"""
    def get_dolphin_home_path(self):
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
                and then run SmashBot again.")
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
        osx_path = home_path + "/Library/Application Support/Dolphin/";
        if os.path.isdir(osx_path):
            return osx_path

        print("ERROR: Are you sure Dolphin is installed? Make sure it is,\
                and then run SmashBot again.")
        sys.exit(1)
        return ""

    """Get the path of the named pipe input file for the given controller port"""
    def get_dolphin_pipes_path(self, port):
        return self.get_dolphin_home_path() + "/Pipes/SmashBot" + str(port)

    """Get the MemoryWatcher socket path"""
    def get_memory_watcher_socket_path(self):
        return self.get_dolphin_home_path() + "/MemoryWatcher/MemoryWatcher"
