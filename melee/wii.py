from socket import *
from struct import unpack
import time
import ubjson

from melee import enums
from melee.console import Console
from melee.gamestate import GameState, Projectile
from melee.slippstream import SlippstreamClient, CommType, EventType

class Wii:
    def __init__(self, ai_port, opponent_port, opponent_type, logger=None):
        self.logger = logger
        self.ai_port = ai_port
        self.opponent_port = opponent_port

        self.processingtime = 0
        self._frametimestamp = time.time()
        self.slippi_address = ""
        self.slippi_port = 51441

        self.eventsize = [0] * 0x100

    def run(self):
        """ Connects to the Slippi/Wii.

        Returns boolean of success """
        # TODO: Connect to the Slippi networking port
        self.slippstream = SlippstreamClient(self.slippi_address, self.slippi_port)
        return self.slippstream.connect()

    def stop(self):
        # TODO: Disconnect cleanly from Slippi networking port
        pass

    def step(self):
        # TODO: Actually get a real gamestate from the console

        # Keep looping until we get a REPLAY message
        # TODO: This might still not be all we need. Verify the frame ends here
        self.processingtime = time.time() - self._frametimestamp
        gamestate = GameState(self.ai_port, self.opponent_port)
        frame_ended = False
        while not frame_ended:
            msg = self.slippstream.read_message()
            if msg:
                if (CommType(msg['type']) == CommType.REPLAY):
                    events = msg['payload']['data']
                    frame_ended = self.__handle_slippstream_events(events, gamestate)
                    # TODO: Fix frame indexing and iasa
                    # Start the processing timer now that we're done reading messages
                    self._frametimestamp = time.time()
                    continue

                # We can basically just ignore keepalives
                elif (CommType(msg['type']) == CommType.KEEPALIVE):
                    print("Keepalive")
                    continue

                elif (CommType(msg['type']) == CommType.HANDSHAKE):
                    p = msg['payload']
                    print("Connected to console '{}' (Slippi Nintendont {})".format(
                        p['nick'],
                        p['nintendontVersion'],
                    ))
                    continue
        return gamestate

    def __handle_slippstream_events(self, event_bytes, gamestate):
        """ Handle a series of events, provided sequentially in a byte array """
        while len(event_bytes) > 0:
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
                    projectile.subtype = enums.UNKNOWN_PROJECTILE
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
