""" Gamestate is a single snapshot in time of the game that represents all necessary information
        to make gameplay decisions
"""
import collections
import melee
from melee import enums
from melee.enums import Action, Character

class GameState(object):
    """Represents the state of a running game of Melee at a given moment in time"""
    __slots__ = ('frame', 'stage', 'menu_state', 'submenu', 'player', 'players', 'projectiles', 'stage_select_cursor_x',
                 'stage_select_cursor_y', 'ready_to_start', 'distance', 'menu_selection', '_newframe')
    def __init__(self):
        self.frame = -10000
        """int: The current frame number. Monotonically increases. Can be negative."""
        self.stage = enums.Stage.FINAL_DESTINATION
        """enums.Stage: The current stage being played on"""
        self.menu_state = enums.Menu.IN_GAME
        """enums.MenuState: The current menu scene, such as IN_GAME, or STAGE_SELECT"""
        self.submenu = enums.SubMenu.UNKNOWN_SUBMENU
        """(enums.SubMenu): The current sub-menu"""
        self.players = dict()
        """(dict of int - gamestate.PlayerState): Dict of PlayerState objects. Key is controller port"""
        self.player = self.players
        """(dict of int - gamestate.PlayerState): WARNING: Deprecated. Will be removed in version 1.0.0. Use `players` instead
                Dict of PlayerState objects. Key is controller port"""
        self.projectiles = []
        """(list of Projectile): All projectiles (items) currently existing"""
        self.stage_select_cursor_x = 0.0
        """(float): DEPRECATED. Use `players[X].cursor` instead. Will be removed in 1.0.0. Stage select cursor's X coordinate. Ranges from -27 to 27"""
        self.stage_select_cursor_y = 0.0
        """(float): DEPRECATED. Use `players[X].cursor` instead. Will be removed in 1.0.0. Stage select cursor's Y coordinate. Ranges from -19 to 19"""
        self.ready_to_start = False
        """(bool): Is the 'ready to start' banner showing at the character select screen?"""
        self.distance = 0.0
        """(float): Euclidian distance between the two players. (or just Popo for climbers)"""
        self.menu_selection = 0
        """(int): The index of the selected menu item for when in menus."""
        self._newframe = True

class PlayerState(object):
    """ Represents the state of a single player """
    __slots__ = ('character', 'character_selected', 'x', 'y', 'percent', 'shield_strength', 'stock', 'facing',
                 'action', 'action_frame', 'invulnerable', 'invulnerability_left', 'hitlag', 'hitstun_frames_left',
                 'jumps_left', 'on_ground', 'speed_air_x_self', 'speed_y_self', 'speed_x_attack', 'speed_y_attack',
                 'speed_ground_x_self', 'cursor_x', 'cursor_y', 'coin_down', 'controller_status', 'off_stage', 'iasa',
                 'moonwalkwarning', 'controller_state', 'ecb_bottom', 'ecb_top', 'ecb_left', 'ecb_right',
                 'costume', 'cpu_level', 'is_holding_cpu_slider', 'nana', 'position', 'cursor', 'ecb')
    def __init__(self):
        # This value is what the character currently is IN GAME
        #   So this will have no meaning while in menus
        #   Also, this will change dynamically if you change characters
        #       IE: Shiek/Zelda
        self.character = enums.Character.UNKNOWN_CHARACTER
        """(enum.Character): The player's current character"""
        # This value is what character is selected at the character select screen
        #   Don't use this value when in-game
        self.character_selected = enums.Character.UNKNOWN_CHARACTER
        self.position = collections.namedtuple("Position", ['x', 'y'])
        """(namedtuple: float, float): x, y character position"""
        self.x = 0
        """(float): DEPRECATED. Use `position` instead. Will be removed in 1.0.0. The character's X position"""
        self.y = 0
        """(float): DEPRECATED. Use `position` instead. Will be removed in 1.0.0. The character's Y position"""
        self.percent = 0
        """(int): The player's damage"""
        self.shield_strength = 60.
        """(float): The player's shield strength (max 60). Shield breaks at 0"""
        self.stock = 0
        """(int): The player's remaining stock count"""
        self.facing = True
        """(bool): Is the character facing right? (left is False). Characters in Melee must always be facing left or right"""
        self.action = enums.Action.UNKNOWN_ANIMATION
        """(enum.Action): The current action (or animation) the character is in"""
        self.action_frame = 0
        """(int): What frame of the Action is the character in? Indexed from 1."""
        self.invulnerable = False
        """(bool): Is the player invulnerable?"""
        self.invulnerability_left = 0
        """(int): How many frames of invulnerability are left."""
        self.hitlag = False
        """(bool): Is the player currently in hitlag?"""
        self.hitstun_frames_left = 0
        """(int): How many more frames of hitstun there is"""
        self.jumps_left = 0
        """(int): Number of jumps available. Including ground jump. Will be 2 for most characters on ground."""
        self.on_ground = True
        """(bool): Is the character on the ground?"""
        self.speed_air_x_self = 0
        """(float): Self-induced horizontal air speed"""
        self.speed_y_self = 0
        """(float): Self-induced vertical speed"""
        self.speed_x_attack = 0
        """(float): Attack-induced horizontal speed"""
        self.speed_y_attack = 0
        """(float): Attack-induced vertical speed"""
        self.speed_ground_x_self = 0
        """(float): Self-induced horizontal ground speed"""
        self.nana = None
        """(enums.PlayerState): Additional player state for Nana, if applicable.
                If the character is not Ice Climbers, Nana will be None.
                Will also be None if this player state is Nana itself.
                Lastly, the secondary climber is called 'Nana' here, regardless of the costume used."""
        self.cursor = collections.namedtuple("Cursor", ['x', 'y'])
        """(namedtuple: float, float): x, y cursor position"""
        self.cursor_x = 0
        """(float): DEPRECATED. Use `cursor` instead. Will be removed in 1.0.0. Cursor X value"""
        self.cursor_y = 0
        """(float): DEPRECATED. Use `position` instead. Will be removed in 1.0.0. Cursor Y value"""
        self.coin_down = False
        """(bool): Is the player's character selection coin placed down? (Does not work in Slippi selection screen)"""
        self.controller_status = enums.ControllerStatus.CONTROLLER_UNPLUGGED
        """(enums.ControllerStatus): Status of the player's controller."""
        self.off_stage = False
        """(bool): Helper variable to say if the character is 'off stage'. """
        self.iasa = 0
        self.moonwalkwarning = False
        """(bool): Helper variable to tell you that if you dash back right now, it'll moon walk"""
        self.controller_state = melee.controller.ControllerState()
        """(controller.ControllerState): What buttons were pressed for this character"""
        self.ecb = collections.namedtuple("ECB", ['right', 'left', 'top', 'bottom'])
        self.ecb_right = (0, 0)
        """(float, float): Right edge of the ECB. (x, y) offset from player's center."""
        self.ecb_left = (0, 0)
        """(float, float): Left edge of the ECB. (x, y) offset from player's center."""
        self.ecb_top = (0, 0)
        """(float, float): Top edge of the ECB. (x, y) offset from player's center."""
        self.ecb_bottom = (0, 0)
        """(float, float): Bottom edge of the ECB. (x, y) offset from player's center."""
        self.costume = 0
        """(int): Index for which costume the player is wearing"""
        self.cpu_level = False
        """(bool): CPU level of player. 0 for a libmelee-controller bot or human player."""
        self.is_holding_cpu_slider = False
        """(bool): Is the player holding the CPU slider in the character select screen?"""

class Projectile:
    """ Represents the state of a projectile (items, lasers, etc...) """
    def __init__(self):
        self.position = collections.namedtuple("Position", ['x', 'y'])
        """(namedtuple: float, float): x, y projectile position"""
        self.x = 0
        """(float): DEPRECATED. Use `position` instead. Will be removed in 1.0.0. Projectile's X position"""
        self.y = 0
        """(float): DEPRECATED. Use `position` instead. Will be removed in 1.0.0. Projectile's Y position"""
        self.speed = collections.namedtuple("Speed", ['x', 'y'])
        """(namedtuple: float, float): x, y projectile speed"""
        self.x_speed = 0
        """(float): DEPRECATED. Use `speed` instead. Will be removed in 1.0.0. Projectile's horizontal speed"""
        self.y_speed = 0
        """(float): DEPRECATED. Use `speed` instead. Will be removed in 1.0.0. Projectile's vertical speed"""
        self.owner = -1
        """(int): Player port of the projectile's owner. -1 for no owner"""
        self.subtype = enums.ProjectileSubtype.UNKNOWN_PROJECTILE
        """(enums.ProjectileSubtype): Which actual projectile type this is"""

def port_detector(gamestate, character, costume):
    """Autodiscover what port the given character is on

    Slippi Online assigns us a random port when playing online. Find out which we are

    Returns:
        [1-4]: The given character belongs to the returned port
        0: We don't know.

    Args:
        gamestate: Current gamestate
        character: The character we know we picked
        costume: Costume index we picked
    """
    detected_port = 0
    for i, player in gamestate.players.items():
        if player.character == character and player.costume == costume:
            if detected_port > 0:
                return 0
            detected_port = i

    return detected_port
