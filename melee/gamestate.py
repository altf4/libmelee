from melee import enums, stages
from melee.enums import Action, Character

"""Represents the state of a running game of Melee at a given moment in time"""
class GameState:
    def __init__(self, ai_port, opponent_port):
        self.frame = 0
        self.stage = enums.Stage.FINAL_DESTINATION
        self.menu_state = enums.Menu.CHARACTER_SELECT
        self.player = dict()
        self.projectiles = []
        self.stage_select_cursor_x = 0.0
        self.stage_select_cursor_y = 0.0
        self.ready_to_start = False
        self.distance = 0.0
        self.sock = None
        self.player[1] = PlayerState()
        self.player[2] = PlayerState()
        self.player[3] = PlayerState()
        self.player[4] = PlayerState()
        self.player[5] = PlayerState()
        self.player[6] = PlayerState()
        self.player[7] = PlayerState()
        self.player[8] = PlayerState()
        self.newframe = True
        #Helper names to keep track of us and our opponent
        self.ai_state = self.player[ai_port]
        self.opponent_state = self.player[opponent_port]

    """Return a list representation of the current gamestate
    Only caring about in-game things, not menus and such"""
    def tolist(self):
        thelist = []
        #I don't think that the frame is really relevant here...
        #thelist.append(self.frame)
        thelist.append(self.distance)
        thelist.append(self.stage.value)
        thelist = thelist + self.ai_state.tolist()
        thelist = thelist + self.opponent_state.tolist()
        #TODO: Figure out the best way to add projectiles to the list
        #thelist = thelist + self.projectiles.tolist()
        return thelist

"""Represents the state of a single player"""
class PlayerState:
    def __init__(self):
        # This value is what the character currently is IN GAME
        #   So this will have no meaning while in menus
        #   Also, this will change dynamically if you change characters
        #       IE: Shiek/Zelda
        self.character = enums.Character.UNKNOWN_CHARACTER
        # This value is what character is selected at the character select screen
        #   Don't use this value when in-game
        self.character_selected = enums.Character.UNKNOWN_CHARACTER
        self.x = 0
        self.y = 0
        self.percent = 0
        self.stock = 0
        # Facingis a bool here for convenience.
        #   True -> Facing right
        #   False -> Facing left
        self.facing = True
        self.action = enums.Action.UNKNOWN_ANIMATION
        self.action_frame = 0
        self.invulnerable = False
        self.invulnerability_left = 0
        self.hitlag = False
        self.hitstun_frames_left = 0
        self.jumps_left = 0
        self.on_ground = True
        self.speed_air_x_self = 0
        self.speed_y_self = 0
        self.speed_x_attack = 0
        self.speed_y_attack = 0
        self.speed_ground_x_self = 0
        self.cursor_x = 0
        self.cursor_y = 0
        self.coin_down = False
        self.controller_status = enums.ControllerStatus.CONTROLLER_UNPLUGGED
        self.off_stage = False
        self.transformed = False
        self.iasa = 0
        self.moonwalkwarning = False
        self.hitbox_1_size = 0
        self.hitbox_2_size = 0
        self.hitbox_3_size = 0
        self.hitbox_4_size = 0
        self.hitbox_1_status = False
        self.hitbox_2_status = False
        self.hitbox_3_status = False
        self.hitbox_4_status = False
        self.hitbox_1_x = 0
        self.hitbox_1_y = 0
        self.hitbox_2_x = 0
        self.hitbox_2_y = 0
        self.hitbox_3_x = 0
        self.hitbox_3_y = 0
        self.hitbox_4_x = 0
        self.hitbox_4_y = 0
        self.prev_action = Action.UNKNOWN_ANIMATION

        # For internal use only, ignore these
        self._next_x = 0
        self._next_y = 0
        self._prev_x = 0
        self._prev_x = 0


    """Produces a list representation of the player's state"""
    def tolist(self):
        thelist = []
        thelist.append(self.x)
        thelist.append(self.y)
        thelist.append(self.percent)
        thelist.append(self.stock)
        thelist.append(int(self.facing))
        thelist.append(self.action.value)
        thelist.append(self.action_frame)
        thelist.append(int(self.invulnerable))
        thelist.append(self.hitlag)
        thelist.append(self.hitstun_frames_left)
        thelist.append(self.jumps_left)
        thelist.append(int(self.on_ground))
        #We're combining speeds here for simplicity's sake
        thelist.append(self.speed_air_x_self + self.speed_x_attack + self.speed_ground_x_self)
        thelist.append(self.speed_y_self + self.speed_y_attack)
        thelist.append(int(self.off_stage))
        return thelist

"""Represents the state of a projectile (items, lasers, etc...)"""
class Projectile:
    def __init(self):
        self.x = 0
        self.y = 0
        self.x_speed = 0
        self.y_speed = 0
        self.opponent_owned = True
        self.subtype = enums.ProjectileSubtype.UNKNOWN_PROJECTILE

    """Produces a list representation of the projectile"""
    def tolist(self):
        thelist = []
        thelist.append(self.x)
        thelist.append(self.y)
        thelist.append(self.x_speed)
        thelist.append(self.y_speed)
        thelist.append(int(self.opponent_owned))
        thelist.append(self.subtype.value)
        return thelist
