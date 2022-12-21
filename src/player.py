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

        # connects to the playing area
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
        while True:

            events = self.selector.select(timeout=None)

            #Loops through every event in the selector...
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)

    def service_connection(self, sock):
        print('uwu')

    def handle_input(self, stdin):
        """Receives the typing input"""
        text = format(stdin.read()).strip('\n').upper()

        if text == 'AUTH':
            print('Authenticating...')
            Proto.send_msg(self.sock, Authenticate(self.nickname, 'public_key', 'signature'))
        else:
            print('Invalid input.')
