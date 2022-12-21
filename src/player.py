import socket # websockets
import sys # for closing the app
import selectors # for multiplexing

class Player:
    PLAYING_AREA_PORT = 1024

    def __init__(self, nickname : str):
        self.nickname = nickname

        # connects to the playing area
        self.connect()

    def connect(self):
        # creates the client's socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((socket.gethostname(), self.PLAYING_AREA_PORT))

        # setups up selector for receiving messages
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.sock, selectors.EVENT_READ, self.service_connection)

    def service_connection(self, sock):
        print('uwu')
