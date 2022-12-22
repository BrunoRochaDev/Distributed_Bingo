import json # for serializing
import socket # websockets

class Message:
    """Generic message"""
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False)

    def __str__(self):
        return self.to_json()

class Authenticate(Message):
    """Message for players authenticating themselves to the playing area. Uses challenge-response authentication"""
    def __init__(self, public_key : str, challenge : str = None, response : str = None, success : bool = False):
        self.header = 'AUTH'
        self.public_key = public_key
        self.challenge = challenge
        self.response = response
        self.success = success

    @classmethod
    def parse(cls, j : str):
        return Authenticate(j['public_key'], j['challenge'], j['response'], j['success'])

class Register(Message):
    """Message for players registering themselves to the playing area"""
    def __init__(self, nickname : str, playing_key : str, auth_key : str, signature : str, success : bool = False):
        self.header = 'REGISTER'
        self.nickname = nickname
        self.playing_key = playing_key
        self.auth_key = auth_key
        self.signature = signature
        self.success = success

    @classmethod
    def parse(cls, j : str):
        return Register(j['nickname'], j['playing_key'], j['auth_key'], j['signature'], j['success'])

class PartyUpdate(Message):
    """Message for updating registered users on how big the party is"""
    def __init__(self, current : int, maximum : int):
        self.header = "PARTY"
        self.current = current
        self.maximum = maximum

    @classmethod
    def parse(cls, j : str):
        return PartyUpdate(j['current'], j['maximum'])

class Proto:

    HEADER_SIZE = 4

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        try:
            # encodes the string to byte array
            encoded_msg = str.encode(msg.to_json())

            # get the length of the message as a fixed length header header
            header = len(encoded_msg).to_bytes(cls.HEADER_SIZE, byteorder = 'big')
            
            # sends the message + the header
            connection.send(header + encoded_msg)
        except:
            print("An error occurred while sending the message")

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        # get the length of the incoming message
        header = connection.recv(cls.HEADER_SIZE)
        msg_size = int.from_bytes(header, "big")

        msg_encoded = connection.recv(msg_size) 
        msg_str = msg_encoded.decode('UTF-8')

        return cls.parse_msg(msg_str)

    @classmethod
    def parse_msg(self, msg_str: str):
        if not msg_str:
            return None

        j = json.loads(msg_str)

        if j['header'] == 'AUTH':
            return Authenticate.parse(j)
        elif j['header'] == 'REGISTER':
            return Register.parse(j)
        elif j['header'] == 'PARTY':
            return PartyUpdate.parse(j)
        else:
            raise ProtoBadFormat(msg_str)

class ProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: str=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
