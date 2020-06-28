""" Implementation of a SlippiComm client aka 'Slippstream'
                                                    (I'm calling it that)

This can be used to talk to some server implementing the Slippstream protocol
(i.e. the Project Slippi fork of Nintendont or Slippi Ishiiruka).
"""

import errno
import socket
from struct import pack, unpack
from enum import Enum
from hexdump import hexdump
from ubjson.decoder import DecoderException
import enet
import ubjson

import melee.slippicomm_pb2

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

    def __init__(self, address="", port=51441, realtime=True):
        """ Constructor for this object """
        self._host = enet.Host(None, 1, 0, 0)
        self._peer = None
        self.buf = bytearray()
        self.realtime = realtime
        self.address = address
        self.port = port

    def shutdown(self):
        """ Close down the socket and connection to the console """
        if self.server is not None:
            self.server.close()
            return True
        return False

    def dispatch(self):
        """Dispatch messages with the peer (read and write packets)"""
        event = self._host.service(1000)
        if event.type == enet.EVENT_TYPE_RECEIVE:
            message = melee.slippicomm_pb2.SlippiMessage()
            message.ParseFromString(event.packet.data)
            return message
        elif event.type == enet.EVENT_TYPE_CONNECT:
            self._peer.send(0, enet.Packet(self.__new_handshake()))
        return None

    def connect(self):
        """ Connect to the server

        Returns True on success, False on failure
        """
        # If we don't have a slippi address, let's autodiscover it
        if not self.address:
            # Slippi broadcasts a UDP message on port
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Slippi sends an advertisement every 10 seconds. So 20 should be enough
            sock.settimeout(20)
            sock.bind(('', 20582))
            try:
                message = sock.recvfrom(1024)
                self.address = message[1][0]
            except socket.timeout:
                return False


        # Try to connect to the server and send a handshake
        self._peer = self._host.connect(enet.Address(bytes(self.address, 'utf-8'), int(self.port)), 1)
        return True

    def __new_handshake(self, cursor=None, token=None):
        """ Returns a new binary handshake message """
        message = melee.slippicomm_pb2.SlippiMessage()
        message.connect_request.cursor = 0
        return bytes(message.SerializeToString())
        # cursor = cursor or [0, 0, 0, 0, 0, 0, 0, 0]
        # token = token or [0, 0, 0, 0, 0, 0, 0, 0]
        #
        # handshake = bytearray()
        # handshake_contents = ubjson.dumpb({
        #     'type': CommType.HANDSHAKE.value,
        #     'payload': {
        #         'cursor': cursor,
        #         'clientToken': token,
        #         'isRealtime': self.realtime,
        #     }
        # })
        # handshake += pack(">L", len(handshake_contents))
        # handshake += handshake_contents
        # return handshake
