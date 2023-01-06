import socket # websockets
import sys # for closing the app
import selectors # for multiplexing
import fcntl # For non-blocking stdout
from src.common import UserData, LogEntry
import os

from src.protocol import *

class User:
    """This is a generic class for state and logic common to both players and callers."""

    PLAYING_AREA_PORT = 1024

    # set sys.stdin non-blocking
    orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

    def __init__(self, nickname : str):
        self.nickname = nickname
        self.users = {} # userdata of all players
        self.log = [] # message logs as received from

        self.deck_key = Crypto.sym_gen()[0] # sym key, AES128
        self.encrypted_deck = None

        self.authenticated = False # not authenticated at the start
        self.registered = False # not registered at the start

        # connects to the playing area
        self.running = True
        self.connect()
        self.loop()

    def connect(self):
        """Connects to the playing field"""

        # creates the client's socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((socket.gethostname(), self.PLAYING_AREA_PORT))

        print('[NET] You are now connected to the playing area.')

        # setups up selector for receiving messages
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.sock, selectors.EVENT_READ, self.service_connection)

    def loop(self):
        """Get input and receives messages"""

        print('- To authenticate yourself to the playing area, type "AUTH"')
        self.selector.register(sys.stdin, selectors.EVENT_READ, self.handle_input)
        while self.running:

            events = self.selector.select(timeout=None)

            # loops through every event in the selector...
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)

    def service_connection(self, sock : socket):

        msg = Proto.recv_msg(sock)
        if msg:
            if msg.header == 'AUTH':
                self.authenticate(sock, msg)
            elif msg.header == 'REGISTER':
                self.register(sock, msg)
            elif msg.header == 'GETUSERS':
                self.users = {int(entry['sequence']) : UserData.parse(entry) for entry in msg.response}
                print('[SEC] Registered users:')
                print('\n'.join([str(entry) for entry in self.users.values()]))
            elif msg.header == 'GETLOG':
                self.log = [LogEntry.parse(entry) for entry in msg.response]
                print('[SEC] Logged messages:')
                print('\n'.join([str(entry) for entry in self.log]))
            elif msg.header == 'PARTY':
                print(f'[GAME] Party status: {msg.current}/{msg.maximum} ({"Caller present" if msg.caller else "Caller absent"})')
                if msg.caller and msg.current == msg.maximum:
                    print('[GAME] Game starting shortly...')
            elif msg.header == 'GENDECK':
                self.generate_deck(sock, msg)
            elif msg.header == 'GENCARD':
                self.generate_card(sock, msg)
            elif msg.header == 'DECKKEYREQ':
                self.deck_key_request(sock, msg)
            elif msg.header == 'GAMEOVER':
                print(f'[GAME] {msg}')
        else:
            print(f"[NET] Connection with the playing area is closed.")
            self.selector.unregister(sock)
            sock.close()
            self.running = False

    def authenticate(self, sock : socket, msg : Authenticate):
        # only respond if not authenticated. just in case
        if not self.authenticated:

            # if the playing area has authenticated us...
            if msg.success:
                print('[AUTH] You have passed the challenge and are authenticated.')
                print('- To register yourself, type "REGISTER"')
                print('- Authenticated users can see registed users. type "GETUSERS".')
                print('- Authenticated users can audit the message log. type "GETLOG".')
                self.authenticated = True
                return

            print(f'[AUTH] Received "{msg.challenge}" challenge from the playing area. Responding...')

            # TODO: properly sign the response
            response = 'response'
            msg.response = response

            # send it back to the playing area
            Proto.send_msg(sock, msg)

    def register(self, sock : socket, msg : Register):
        # if the registration was a success
        if msg.success:
            self.registred = True
            print('[REG] ...registration was a success.')
        # was not a success
        else:
            print(f'[REG] ...registration failed. The nickname "{self.nickname}" might be already taken, try another.')
            self.running = False

    def deck_key_request(self, sock : socket, msg : DeckKeyRequest):

        # received a deck key request but have not received commited deck 
        if not self.encrypted_deck:
            print("[ERROR] Deck key request received but don't have commited deck.")
            # TODO disqualify game?
            return

        print('[GAME] Sending my deck key to other players...')
        # TODO deck_key must be sent in a way that the other side can reconstruct
        response = DeckKeyResponse(msg.sequence, str(self.deck_key))
        response.sign(self.playing_key)
        Proto.send_msg(sock, response)
