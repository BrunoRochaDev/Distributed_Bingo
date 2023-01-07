import json # for serializing
import socket # websockets
from src.crypto import Crypto # cryptography
import base64

class Message:
    """Generic message"""
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False)

    def should_log(self) -> bool:
        return True

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
    def parse(cls, j : dict):
        return Authenticate(j['public_key'], j['challenge'], j['response'], j['success'])

class Register(Message): 
     
    """Message for players registering themselves to the playing area"""
    def __init__(self, nickname : str, playing_key : str, auth_key : str, signature : str, success : bool = False, sequence : int = None):
        self.header = 'REGISTER'
        self.nickname = nickname
        self.playing_key = playing_key
        self.auth_key = auth_key
        self.signature = signature
        self.success = success

    @classmethod
    def parse(cls, j : dict):
        return Register(j['nickname'], j['playing_key'], j['auth_key'], j['signature'], j['success'])

class GameInfo(Message):
    """Simple message for letting users know the card and deck size"""
    def __init__(self, sequence : int, card_size : int, deck_size : int):
        self.header = 'GAMEINFO'
        self.sequence = sequence
        self.card_size = card_size
        self.deck_size = deck_size

    def should_log(self) -> bool:
        return False

    @classmethod
    def parse(cls, j : dict):
        return GameInfo(j['sequence'], j['card_size'], j['deck_size'])

class GetUsers(Message):
 
    """Message for getting a list of registered users"""
    def __init__(self, public_key : str, signature : str, response : list = None):
        self.header = 'GETUSERS'
        self.public_key = public_key
        self.signature = signature
        self.response = response

    def should_log(self) -> bool:
        return False

    @classmethod
    def parse(cls, j : dict): 
        return GetUsers( j['public_key'], j['signature'], j['response'])


class GetLog(Message):
    """Message for getting a list of logged messages"""
    def __init__(self, public_key : str, signature : str, response : list = None):
        self.header = 'GETLOG'
        self.public_key = public_key
        self.signature = signature
        self.response = response

    def should_log(self) -> bool:
        return False

    @classmethod
    def parse(cls, j : dict):
        return GetLog(j['public_key'], j['signature'], j['response'])

class PartyUpdate(Message):
    """Message for updating registered users on how big the party is"""
    def __init__(self, current : int, maximum : int, caller : bool):
        self.header = "PARTY"
        self.current = current
        self.maximum = maximum
        self.caller = caller

    def should_log(self) -> bool:
        return False

    @classmethod
    def parse(cls, j : dict):
        return PartyUpdate(j['current'], j['maximum'], j['caller'])

class GenerateDeck(Message):
    """Message telling the caller to generate the deck and initiate the card generation proccess"""
    def __init__(self):
        self.header = "GENDECK"

    @classmethod
    def parse(cls, j : dict):
        return GenerateDeck()

class GenerateCard(Message):
    """Players will pass this message around until everyone has commited their card"""
    def __init__(self, sequence : int, deck : list ,signatures : list = [], done : bool = False):
        self.header = "GENCARD"
        self.sequence = sequence
        self.deck = deck
        self.signatures = signatures
        self.done = done

    def sign(self, private_key : str) -> None: 
        sign = Crypto.sign(private_key, str(self.deck)) # Get signature
        send_format = base64.b64encode(sign).decode('ascii') # Transform to sending format
        self.signatures.append(send_format) # append to signatures list
        
    def verify(self, public_key, signature: str) -> bool:
        signature = base64.b64decode(signature.encode('ascii')) # Transform back to bytes
        return Crypto.verify(public_key, str(self.deck), signature) # Return true if matches false if it doesnt 

    @classmethod
    def parse(cls, j : dict):
        return GenerateCard(j['sequence'], j['deck'], j['signatures'], j['done'])

class DeckKeyRequest(Message):
    """Message requesting that players and caller reveal their symmetric key after the deck is commited"""
    def __init__(self, sequence : int):
        self.header = "DECKKEYREQ"
        self.sequence = sequence

    @classmethod
    def parse(cls, j : dict):
        return DeckKeyRequest(j['sequence'])

class DeckKeyResponse(Message):
    """Response to the deck key request"""
    def __init__(self, sequence : int, response : str, signature : str = None):
        self.header = "DECKKEYRES"
        self.sequence = sequence
        self.response = response
        self.signature = signature

    def sign(self, private_key : str) -> None: 
        sign = Crypto.sign(private_key, str(self.sequence)+self.response) # Get signature
        send_format = base64.b64encode(sign).decode('ascii') # Transform to sending format
        self.signature = send_format

    def verify(self, public_key, signature: str) -> bool:
        signature = base64.b64decode(signature.encode('ascii')) # Transform back to bytes
        return Crypto.verify(public_key, str(self.sequence)+self.response, signature) # Return true if matches false if it doesnt 

    @classmethod
    def parse(cls, j : dict):
        return DeckKeyResponse(j['sequence'], j['response'], j['signature'])

class GameOver(Message):
    """Message for when the game is over / aborted """
    def __init__(self, status : str, detail : any = None):
        self.header = "GAMEOVER"
        self.status = status
        self.detail = detail

    def should_log(self) -> bool:
        return False

    @classmethod
    def parse(cls, j : dict):
        return GameOver(j['status'], j['detail'])

    def __str__(self):
        if self.status == 'player_left':
            return 'Game aborted because a player left.'
        elif self.status == 'player_cheated':
            return f'Game aborted because {self.detail} cheated.'
        else:
            return 'Error :('

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
        except Exception as e:
            print("[PROTO] An error occurred while sending the message")
            raise e

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
        elif j['header'] == 'GAMEINFO':
            return GameInfo.parse(j)
        elif j['header'] == 'GETUSERS':
            return GetUsers.parse(j)
        elif j['header'] == 'GETLOG':
            return GetLog.parse(j)
        elif j['header'] == 'PARTY':
            return PartyUpdate.parse(j)
        elif j['header'] == 'GENDECK':
            return GenerateDeck.parse(j)
        elif j['header'] == 'GENCARD':
            return GenerateCard.parse(j)
        elif j['header'] == 'DECKKEYREQ':
            return DeckKeyRequest.parse(j)
        elif j['header'] == 'DECKKEYRES':
            return DeckKeyResponse.parse(j)
        elif j['header'] == 'GAMEOVER':
            return GameOver.parse(j)
        else:
            raise ProtoBadFormat(msg_str)

class ProtoBadFormat(Exception):
    """Exception when source message is not Proto."""

    def __init__(self, original_msg: str=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
