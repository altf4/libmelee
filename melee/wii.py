from socket import *
from struct import unpack
import ubjson

from melee.console import Console
from melee.gamestate import GameState
from melee.slippstream import SlippstreamClient, CommType, EventType

class Wii:
    def __init__(self, ai_port, opponent_port, opponent_type, logger=None):
        self.logger = logger
        self.ai_port = ai_port
        self.opponent_port = opponent_port

        self.processingtime = 0
        self.slippi_address = ""
        self.slippi_port = 51441

    def run(self):
        # TODO: Connect to the Slippi networking port
        print("Making SlippstreamClient...")
        self.slippstream = SlippstreamClient(self.slippi_address, self.slippi_port)
        self.slippstream.connect()

    def stop(self):
        # TODO: Disconnect cleanly from Slippi networking port
        pass

    def step(self):
        # TODO: Actually get a real gamestate from the console

        # Keep looping until we get a REPLAY message
        # TODO: This might still not be all we need. Verify the frame ends here
        while True:
            msg = self.slippstream.read_message()
            if msg:
                if (CommType(msg['type']) == CommType.REPLAY):
                    events = msg['payload']['data']
                    self.__handle_slippstream_events(events)
                    # TODO Handle the event here

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

    def __handle_slippstream_events(self, event_bytes):
        """ Handle a series of events, provided sequentially in a byte array """

        while len(event_bytes) > 0:
            if (EventType(event_bytes[0]) == EventType.FRAME_START):
                self.frame_num = unpack(">i", event_bytes[1:5])[0]
                if (self.frame_hook != None):
                    self.frame_hook(self.frame_num)

                event_bytes = event_bytes[0x9:]
            elif (EventType(event_bytes[0]) == EventType.GAME_START):
                event_bytes = event_bytes[0x1A3:]
                continue
            elif (EventType(event_bytes[0]) == EventType.GAME_END):
                event_bytes = event_bytes[0x3:]
                continue
            elif (EventType(event_bytes[0]) == EventType.PAYLOADS):
                cursor = 0x2
                payload_size = event_bytes[1]
                num_commands = (payload_size - 1) // 3
                for i in range(0, num_commands):
                    command, command_len = unpack(">bH", event_bytes[cursor:cursor+3])
                    self.eventsize[command] = command_len
                    cursor += 3
                event_bytes = event_bytes[payload_size + 1:]
            elif (EventType(event_bytes[0]) == EventType.PRE_FRAME):
                event_bytes = event_bytes[0x40:]
                continue
            elif (EventType(event_bytes[0]) == EventType.POST_FRAME):
                if len(event_bytes) < 0x35:
                    print("WARNING: Something went wrong unpacking events. Data is probably missing")
                    print("\tDidn't have enough data for event")
                    return
                print("x", unpack(">f", event_bytes[0xa:0xa+4])[0])
                print("y", unpack(">f", event_bytes[0xe:0xe+4])[0])

                event_bytes = event_bytes[0x35:]

            elif (EventType(event_bytes[0]) == EventType.GECKO_CODES):
                event_bytes = event_bytes[0x5fcb:]
                continue
            elif (EventType(event_bytes[0]) == EventType.FRAME_BOOKEND):
                event_bytes = event_bytes[0x5:]
                continue
            elif (EventType(event_bytes[0]) == EventType.ITEM_UPDATE):
                event_bytes = event_bytes[0x2a:]
                continue
            else:
                print("WARNING: Something went wrong unpacking events. Data is probably missing")
                print("\tGot invalid event type: ", event_bytes[0])
                return


        return GameState(self.ai_port, self.opponent_port)
