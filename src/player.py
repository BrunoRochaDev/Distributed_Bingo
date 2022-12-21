import socket # websockets
import sys # for closing the app
import selectors # for multiplexing
import fcntl # For non-blocking stdout
import os

from src.protocol import *

class Player:

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

        print('You are now connected to the playing area.')

        # setups up selector for receiving messages
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.sock, selectors.EVENT_READ, self.service_connection)

    def loop(self):
        """Get input and receives messages"""

        print('To authenticate yourself to the playing area, type "AUTH"')
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
                self.handle_authenticate(sock, msg)
        else:
            print(f"Connection with the playing area is closed.")
            self.sel.unregister(sock)
            sock.close()
            self.running = False

    def handle_authenticate(self, sock : socket, msg : Authenticate):
        # only respond if not authenticated. just in case
        if not self.authenticated:

            # if the playing area has authenticated us...
            if msg.success:
                print('[AUTH] You have passed the challenge and are authenticated.')
                self.authenticated = True
                return

            print(f'[AUTH] Received "{msg.challenge}" challenge from the playing area. Responding...')

            # TODO: properly sign the response
            response = 'response'
            msg.response = response

            # send it back to the playing area
            Proto.send_msg(sock, msg)

    def handle_input(self, stdin):
        """Receives the typing input"""
        text = format(stdin.read()).strip('\n').upper()

        if text == 'AUTH' and not self.authenticated:
            print('[AUTH] Asking the playing area for a challenge...')
            Proto.send_msg(self.sock, Authenticate('CC_public'))
        else:
            print('Invalid input.')
