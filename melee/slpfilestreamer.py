"""SLP File backend for libmelee

Reads Slippi game events from SLP file rather than over network
"""

import ubjson
from enum import Enum
import numpy as np

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
        self._frame = -9999
        self.playedOn = ""
        self.timestamp = ""
        self.consoleNick = ""
        self.players = {}

    def shutdown(self):
        pass

    def _is_new_frame(self, event_bytes):
        """Introspect the bytes of the event to see if it represents a new frame

        This is for supporting older SLP files that don't have frame bookends
        """
        if EventType(event_bytes[0]) in [EventType.POST_FRAME, EventType.PRE_FRAME]:
            frame = np.ndarray((1,), ">i", event_bytes, 0x1)[0]
            if frame > self._frame:
                self._frame = frame
                return True
            self._frame = frame
        return False

    def dispatch(self, dummy):
        """Read a single game event off the buffer
        """
        if self._index >= len(self._contents):
            return None

        if EventType(self._contents[self._index]) == EventType.PAYLOADS:
            cursor = 0x2
            payload_size = self._contents[self._index+1]
            num_commands = (payload_size - 1) // 3
            for i in range(0, num_commands):
                command = np.ndarray((1,), ">B", self._contents, cursor)[0]
                command_len = np.ndarray((1,), ">H", self._contents, cursor + 0x1)[0]
                self.eventsize[command] = command_len+1
                cursor += 3

            wrapper = dict()
            wrapper["type"] = "game_event"
            wrapper["payload"] = self._contents[self._index : self._index+payload_size+1]
            self._index += payload_size + 1
            return wrapper

        event_size = self.eventsize[self._contents[self._index]]

        # Check to see if a new frame has happened for an old file type
        if self._is_new_frame(self._contents[self._index : self._index+event_size]):
            wrapper = dict()
            wrapper["type"] = "frame_end"
            wrapper["payload"] = b""
            return wrapper

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
            try:
                self.playedOn = full["metadata"]["playedOn"]
            except KeyError:
                pass
            try:
                self.timestamp = full["metadata"]["startAt"]
            except KeyError:
                pass
            try:
                self.consoleNick = full["metadata"]["consoleNick"]
            except KeyError:
                pass
            try:
                self.players = full["metadata"]["players"]
            except KeyError:
                pass
            return True
