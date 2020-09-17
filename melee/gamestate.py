""" Gamestate is a single snapshot in time of the game that represents all necessary information
        to make gameplay decisions
"""
import melee
from melee import enums
from melee.enums import Action, Character

class GameState(object):
    """Represents the state of a running game of Melee at a given moment in time"""
    __slots__ = ('frame', 'stage', 'menu_state', 'submenu', 'player', 'projectiles', 'stage_select_cursor_x',
                 'stage_select_cursor_y', 'ready_to_start', 'distance', 'menu_selection', '_newframe')
    def __init__(self):
        self.frame = -9999
        """int: The current frame number. Monotonically increases. Can be negative."""
        self.stage = enums.Stage.FINAL_DESTINATION
        """enums.Stage: The current stage being played on"""
        self.menu_state = enums.Menu.IN_GAME
        """enums.MenuState: The current menu scene, such as IN_GAME, or STAGE_SELECT"""
        self.submenu = enums.SubMenu.UNKNOWN_SUBMENU
        """(enums.SubMenu): The current sub-menu"""
        self.player = dict()
        """(dict of int - gamestate.PlayerState): Dict of PlayerState objects. Key is controller port"""
        self.projectiles = []
        """(list of Projectile): All projectiles (items) currently existing"""
        self.stage_select_cursor_x = 0.0
        """(float): Stage select cursor's X coordinate. Ranges from -27 to 27"""
        self.stage_select_cursor_y = 0.0
        """(float): Stage select cursor's Y coordinate. Ranges from -19 to 19"""
        self.ready_to_start = False
        """(bool): Is the 'ready to start' banner showing at the character select screen?"""
        self.distance = 0.0
        """(float): Euclidian distance between the two players. (or closest one for climbers)"""
        self.menu_selection = 0
        """(int): The index of the selected menu item for when in menus."""
        self._newframe = True

class PlayerState(object):
    """ Represents the state of a single player """
    __slots__ = ('character', 'character_selected', 'x', 'y', 'percent', 'shield_strength', 'stock', 'facing',
                 'action', 'action_frame', 'invulnerable', 'invulnerability_left', 'hitlag', 'hitstun_frames_left',
                 'jumps_left', 'on_ground', 'speed_air_x_self', 'speed_y_self', 'speed_x_attack', 'speed_y_attack',
                 'speed_ground_x_self', 'cursor_x', 'cursor_y', 'coin_down', 'controller_status', 'off_stage', 'iasa',
                 'moonwalkwarning', 'controller_state', 'ecb_bottom', 'ecb_top', 'ecb_left', 'ecb_right', 'prev_action',
                 '_next_x', '_next_y', '_prev_x', '_prev_y')
    def __init__(self):
        # This value is what the character currently is IN GAME
        #   So this will have no meaning while in menus'speed_y_self'
        #   Also, this will change dynamically if you change characters
        #       IE: Shiek/Zelda
        self.character = enums.Character.UNKNOWN_CHARACTER
        """(enum.Character): The player's current character"""
        # This value is what character is selected at the character select screen
        #   Don't use this value when in-game
        #TODO Remove this and just use character
        self.character_selected = enums.Character.UNKNOWN_CHARACTER
        self.x = 0
        """(float): The character's X position"""
        self.y = 0
        """(float): The character's Y position"""
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
        self.cursor_x = 0
        """(float): Cursor X value"""
        self.cursor_y = 0
        """(float): Cursor Y value"""
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
        self.ecb_right = (0, 0)
        """(float, float): Right edge of the ECB. (x, y) offset from player's center."""
        self.ecb_left = (0, 0)
        """(float, float): Left edge of the ECB. (x, y) offset from player's center."""
        self.ecb_top = (0, 0)
        """(float, float): Top edge of the ECB. (x, y) offset from player's center."""
        self.ecb_bottom = (0, 0)
        """(float, float): Bottom edge of the ECB. (x, y) offset from player's center."""
        # self.hitbox_1_size = 0
        # self.hitbox_2_size = 0
        # self.hitbox_3_size = 0
        # self.hitbox_4_size = 0
        # self.hitbox_1_status = False
        # self.hitbox_2_status = False
        # self.hitbox_3_status = False
        # self.hitbox_4_status = False
        # self.hitbox_1_x = 0
        # self.hitbox_1_y = 0
        # self.hitbox_2_x = 0
        # self.hitbox_2_y = 0
        # self.hitbox_3_x = 0
        # self.hitbox_3_y = 0
        # self.hitbox_4_x = 0
        # self.hitbox_4_y = 0
        self.prev_action = Action.UNKNOWN_ANIMATION

        # For internal use only, ignore these
        self._next_x = 0
        self._next_y = 0
        self._prev_x = 0
        self._prev_y = 0

class Projectile:
    """ Represents the state of a projectile (items, lasers, etc...) """
    def __init(self):
        self.x = 0
        """(float): Projectile's X position"""
        self.y = 0
        """(float): Projectile's Y position"""
        self.x_speed = 0
        """(float): Projectile's horizontal speed"""
        self.y_speed = 0
        """(float): Projectile's vertical speed"""
        self.owner = -1
        """(int): Player port of the projectile's owner. -1 for no owner"""
        self.subtype = enums.ProjectileSubtype.UNKNOWN_PROJECTILE
        """(enums.ProjectileSubtype): Which actual projectile type this is"""

def port_detector(gamestate, controller, character):
    """Autodiscover what port the given controller is on

    Slippi Online assigns us a random port when playing online. Find out which we are

    Returns:
        [1-4]: The given controller belongs to the returned port
        0: We don't know yet, and we pressed a button to discover. Don't press
        any other buttons this frame or it'll mess this up!!

    Args:
        gamestate: Current gamestate
        controller: The controller we want to test
        character: The character we know we picked
    """
    for i, player in gamestate.player.items():
        if player.character == character:
            return i

    # TODO Do some movement

    return 1
