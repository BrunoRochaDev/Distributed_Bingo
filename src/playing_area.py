from src.common import UserData
import socket # websockets
import sys # for closing the app
import selectors # for multiplexing

# for generating random challenges
import random
import string

from src.protocol import *

class PlayingArea:
    """The secure playing field"""

    # should be >= 1024
    PORT = 1024

    # the number of players needed for a game to start
    PLAYER_NUM = 3

    # length of the challenge string for authentication
    CHALLENGE_LENGTH = 14

    def __init__(self, card_size : int, deck_size : int):
        self.card_size = card_size
        self.deck_size = deck_size

        self.playing = False # the game has not started

        self.users = {} # dict for associating sequence to player data
        self.authorized_keys = set() # set for authorized public keys
        self.challenges= {} # dict for assoaciating public key to the challenge for users not yet authenticated

        # creates and starts the server
        self.server_setup()
        self.run()

    def server_setup(self):
        """Creates a TCP websocket at a predifined port"""

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # adds this line to prevent an error message stating that the previous address was already in use
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # binds the server socket to an interface address and port
        self.sock.bind((socket.gethostname(), self.PORT))

        # starts listening for clients...
        self.sock.listen()

        print(f"Started playing area at port {self.PORT}.")

        # creates the selector object
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.sock, selectors.EVENT_READ, data=None)

    def run(self):
        """Receives messages as they come"""

        # waits for messages
        try:
            while True:
                events = self.selector.select()

                # loops through every event in the selector...
                for key, _ in events:
                    # if the data is none, that means that the socket has not yet been accepted
                    if key.data is None:
                        # accept the connection
                        self.accept_connection(key.fileobj) # key.fileobj is the socket object
                    else:
                        self.service_connection(key)

        # shutdowns if the user interrupts the proccess
        except KeyboardInterrupt:
            self.poweroff()

    def accept_connection(self, sock):
        """Accepts the connection from a client (player)"""

        connection, address = sock.accept()
        print(f"Accepted connection from {address}.")

        self.selector.register(connection, selectors.EVENT_READ, data="")

    def service_connection(self, key):
        sock = key.fileobj
        data = key.data

        msg = Proto.recv_msg(sock)
        #print('msg :', msg)

        if msg.header == 'AUTH':
            self.authenticate(sock, msg)

    def authenticate(self, sock : socket, msg : Authenticate):
        """Challenge-response authentication for Portuguese citzens"""

        # helper function for generating random strings, used for challenges
        def get_random_string(length : int):
            # With combination of lower and upper case
            return ''.join(random.choice(string.ascii_letters) for i in range(length))

        public_key = msg.public_key

        # if the authentication progress has already begun...
        if public_key in self.challenges.keys():
            challenge = self.challenges[public_key]

            # if challenge does not match, player is trying to evade authentication
            if challenge != msg.challenge:
                # TODO: blacklist connection
                return

            response = msg.response

            # TODO: verify the signature
            if False: # if signature if forged
                # TODO: blacklist connection
                return

            # at this point, the user is authenticated as a Portuguese citzen
            print(f'[AUTH] "{public_key}" has passed the challenge and it\'s authenticated.')
            self.challenges.pop(public_key) 
            self.authorized_keys.add(public_key)

            # let the user know they are authenticated 
            msg.success = True
            Proto.send_msg(sock, msg)

        # if it's starting now...
        else:
            print(f'[AUTH] Sending challenge to "{public_key}"...')

            # message is not supposed to have challenge or response yet
            if msg.challenge or msg.response:
                # TODO: blacklist connection
                return

            # create random challenge
            challenge = get_random_string(self.CHALLENGE_LENGTH)

            # store in the dict for later steps
            self.challenges[public_key] = challenge

            # update message and send it back. wait for response
            msg.challenge = challenge
            Proto.send_msg(sock, msg)

    def poweroff(self):
        """Shutdowns the server"""
        self.sock.close()
        sys.exit()
