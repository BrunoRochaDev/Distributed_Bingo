import socket # websockets
import sys # for closing the app
import selectors # for multiplexing
import fcntl # For non-blocking stdout
import os

from src.protocol import *

class User:
    """This is a generic class for state and logic common to both players and callers."""

    PLAYING_AREA_PORT = 1024

    # set sys.stdin non-blocking
    orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

    def __init__(self, nickname : str):
        print(f'Your nickname is "{nickname}".')
        self.nickname = nickname

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
                print(f'[SEC] Registered users: {msg.response}')
            elif msg.header == 'GETLOG':
                print(f'[SEC] Logged messages: {msg.response}')
            elif msg.header == 'PARTY':
                print(f'[GAME] Party status: {msg.current}/{msg.maximum}')
                if msg.current == msg.maximum:
                    print('[GAME] Game starting...')
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
            pass
