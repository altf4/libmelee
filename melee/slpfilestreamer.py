"""SLP File backend for libmelee

Reads Slippi game events from SLP file rather than over network
"""

import ubjson
from enum import Enum
from struct import unpack, error

# pylint: disable=too-few-public-methods
class EventType(Enum):
    """ Replay event types """
    GECKO_CODES = 0x10
    PAYLOADS = 0x35
    GAME_START = 0x36
    PRE_FRAME = 0x37
    POST_FRAME = 0x38
    GAME_END = 0x39
    FRAME_START = 0x3a
    ITEM_UPDATE = 0x3b
    FRAME_BOOKEND = 0x3c

class SLPFileStreamer:
    def __init__(self, path):
        self._path = path
        self._contents = None
        self.eventsize = [0] * 0x100
        self._index = 0

    def shutdown(self):
        pass

    def dispatch(self):
        """Read a single game event off the buffer
        """
        if self._index >= len(self._contents):
            return None

        if EventType(self._contents[self._index]) == EventType.PAYLOADS:
            cursor = 0x2
            payload_size = self._contents[self._index+1]
            num_commands = (payload_size - 1) // 3
            for i in range(0, num_commands):
                command, command_len = unpack(">bH", self._contents[cursor:cursor+3])
                self.eventsize[command] = command_len+1
                cursor += 3

            wrapper = dict()
            wrapper["type"] = "game_event"
            wrapper["payload"] = self._contents[self._index : self._index+payload_size+1]
            self._index += payload_size + 1
            return wrapper

        event_size = self.eventsize[self._contents[self._index]]

        wrapper = dict()
        wrapper["type"] = "game_event"
        wrapper["payload"] = self._contents[self._index : self._index+event_size]
        self._index += event_size

        return wrapper

    def connect(self):
        with open(self._path, mode='rb') as file:
            full = ubjson.loadb(file.read())
            raw = full["raw"]
            self._contents = raw
