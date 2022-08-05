""" Implementation of a SlippiComm client aka 'Slippstream'
                                                    (I'm calling it that)

This can be used to talk to some server implementing the Slippstream protocol
(i.e. the Project Slippi fork of Nintendont or Slippi Ishiiruka).
"""

import socket
from enum import Enum
import enet
import json
from ubjson.decoder import DecoderException
import ubjson
from struct import pack, unpack
import time

# The null token used for initial SlippiComm handshakes
NULL_TOKEN = b'\x00\x00\x00\x00'

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

class CommType(Enum):
    """ Types of SlippiComm messages """
    HANDSHAKE = 0x01
    REPLAY = 0x02
    KEEPALIVE = 0x03
    MENU = 0x04

class SlippstreamClient():
    """ Container representing a client to some SlippiComm server """

    def __init__(self, address="127.0.0.1", port=51441, gamecube=False):
        """ Constructor for this object """
        self._host = enet.Host(None, 1, 0, 0)
        self._peer = None
        self.buf = bytearray()
        self.gamecube = gamecube
        self.address = address
        self.port = port
        # Not yet supported
        self.playedOn = "dolphin"
        self.timestamp = ""
        self.consoleNick = ""
        self.players = {}
        self.now_frame_time = 0
        self.last_frame_time = 0

    def shutdown(self):
        """ Close down the socket and connection to the console """
        if self._peer:
            self._peer.send(0, enet.Packet())
            self._host.service(100)
            self._peer.disconnect()
            self._peer = None

        if self._host:
            self._host = None

        if self.gamecube:
            self.server.close()

        return False

    def dispatch(self, polling_mode):
        """Dispatch messages with the peer (read and write packets)"""
        event = None
        event_type = 1000
        while event_type not in [enet.EVENT_TYPE_RECEIVE]:
            if self.gamecube:
                wait_time = 1000
                if polling_mode:
                    wait_time = 0
                event = self._host.service(wait_time)
                event_type = event.type

                if event.type == enet.EVENT_TYPE_NONE:
                    if polling_mode:
                        return None
                if event.type == enet.EVENT_TYPE_RECEIVE:
                    try:
                        return json.loads(event.packet.data)
                    except json.JSONDecodeError:
                        # This happens at the end of a game for some reason?
                        if len(event.packet.data) == 0:
                            event_type = 0
                            continue
                        return None
                elif event.type == enet.EVENT_TYPE_CONNECT:
                    handshake = json.dumps({
                        "type" : "connect_request",
                        "cursor" : 0,
                    })
                    self._peer.send(0, enet.Packet(handshake.encode()))
                elif event.type == enet.EVENT_TYPE_DISCONNECT:
                    return None
            else:
                self.buf += self.server.recv(1000)
                # Exclude the the message length in the header
                # msg = ubjson.loadb(self.buf[4:])
                payload = self.buf[:]
                # Clear out the old buffer
                del self.buf
                self.buf = bytearray()
                # event = {}
                # if msg["type"] == 1:
                #     event = {"type": "connect_reply",
                #             "nick": msg["payload"]["nick"],
                #             "version": msg["payload"]["nintendontVersion"],
                #             "cursor": msg["payload"]["pos"]}
                event = {"payload": payload}
                if payload[0] == 0x3E:
                    event["type"] = "menu_event"
                else:
                    event["type"] = "game_event"
                return event

        return None

    def __new_handshake(self, cursor=0, token=NULL_TOKEN):
        """ Returns a new binary handshake message """
        handshake = bytearray()
        handshake_contents = ubjson.dumpb({
            'type': CommType.HANDSHAKE.value,
            'payload': {
                'cursor': cursor,
                'clientToken': token,
                'isRealtime': True,
            }
        })
        handshake += pack(">L", len(handshake_contents))
        handshake += handshake_contents
        return handshake

    def connect(self):
        """ Connect to the server

        Returns True on success, False on failure
        """
        # Try to connect to the server and send a handshake
        if self.gamecube:
            try:
                self._peer = self._host.connect(enet.Address(bytes(self.address, 'utf-8'), int(self.port)), 1)
            except OSError:
                return False
            try:
                for _ in range(4):
                    event = self._host.service(1000)
                    if event.type == enet.EVENT_TYPE_CONNECT:
                        handshake = json.dumps({
                                    "type" : "connect_request",
                                    "cursor" : 0,
                                })
                        self._peer.send(0, enet.Packet(handshake.encode()))
                        return True
                return False
            except OSError:
                return False
        else:
            # There is nothing to connect to on cube
            self.server = socket.socket(socket.AF_INET,
                                socket.SOCK_DGRAM)
            self.server.bind(("0.0.0.0", 55559))
            return True
