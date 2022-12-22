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
    PARTY_MAX = 3

    # length of the challenge string for authentication
    CHALLENGE_LENGTH = 14

    # public keys that can be callers
    VALID_CALLERS = set([])

    def __init__(self, card_size : int, deck_size : int):
        self.card_size = card_size
        self.deck_size = deck_size

        self.playing = False # the game has not started

        self.caller = None # tuple of socket, userdata ; data is associated with the socket so that when an user disconnects, we clear the data
        self.players = {} # key is socket, value is userdata ; data is associated with the socket so that when an user disconnects, we clear the data
        self.authorized_keys = {} # set for authorized public keys ; data is associated with the socket so that when an user disconnects, we clear the data
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

        print(f"[NET] Started playing area at port {self.PORT}.")

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
        print(f"[NET] Accepted connection from {address}.")

        self.selector.register(connection, selectors.EVENT_READ, data="")

    def service_connection(self, key):
        sock = key.fileobj
        data = key.data

        msg = Proto.recv_msg(sock)

        # if message is valid
        if msg:
            if msg.header == 'AUTH':
                self.authenticate(sock, msg)

            if msg.header == 'REGISTER':
                self.register(sock, msg)
        else:
            print(f"[NET] Connection with a player has been lost.")
            # remove data associated with the socket
            if sock in self.authorized_keys.keys():
                self.authorized_keys.pop(sock)
            if sock in self.players.keys():
                self.players.pop(sock)
                self.party_changed() # trigger party changed event since someone left

            self.selector.unregister(sock)
            sock.close()

    def authenticate(self, sock : socket, msg : Authenticate):
        """Challenge-response authentication for Portuguese citzens"""

        # don't bother if it's already authorized
        if msg.public_key in self.authorized_keys.values():
            print(f'[AUTH] "{msg.public_key}" is already authorized.')
            # let the user know they are authenticated 
            msg.success = True
            Proto.send_msg(sock, msg)
            return

        # helper function for generating random strings, used for challenges
        def get_random_string(length : int):
            # With combination of lower and upper case
            return ''.join(random.choice(string.ascii_letters) for i in range(length))

        # if the authentication progress has already begun...
        if msg.public_key in self.challenges.keys():
            challenge = self.challenges[msg.public_key]

            # if challenge does not match, player is trying to evade authentication
            if challenge != msg.challenge:
                # TODO: blacklist connection
                return

            # TODO: verify the signature
            if False: # if signature if forged
                # TODO: blacklist connection
                print(f'[AUTH] "{msg.public_key}" has forged it\'s signature. Request denied.')
                return

            # at this point, the user is authenticated as a Portuguese citzen
            print(f'[AUTH] "{msg.public_key}" has passed the challenge and it\'s authenticated.')
            self.challenges.pop(msg.public_key) 
            self.authorized_keys[sock] = msg.public_key

            # let the user know they are authenticated 
            msg.success = True
            Proto.send_msg(sock, msg)

        # if it's starting now...
        else:
            # message is not supposed to have challenge or response yet
            if msg.challenge or msg.response:
                # TODO: blacklist connection
                return

            # create random challenge
            challenge = get_random_string(self.CHALLENGE_LENGTH)

            print(f'[AUTH] Sending "{challenge}" challenge to "{msg.public_key}"...')

            # store in the dict for later steps
            self.challenges[msg.public_key] = challenge

            # update message and send it back. wait for response
            msg.challenge = challenge
            Proto.send_msg(sock, msg)

    def register(self, sock : socket, msg : Register):
        print(f'[REG] Received register request...')

        # users cannot register themselves before they are authorized
        if msg.auth_key not in self.authorized_keys.values():
            # TODO: blacklist connection
            print(f'[REG] ...user was not authorized. Request denied.')
            return

        # nickname cannot be already taken
        if any(player.nickname == msg.nickname for player in self.players.values()):
            # Send it back with success as False to let them know
            print(f'[REG] ...nickname already taken. Request denied.')
            Proto.send_msg(sock, msg)
            return

        # key cannot be already taken
        if any(player.public_key == msg.playing_key for player in self.players.values()):
            # Send it back with success as False to let them know
            print(f'[REG] ...public key already taken. Request denied.')
            Proto.send_msg(sock, msg)
            return

        # signature must be valid
        if False: # signature is not valid
            # TODO: blacklist connection
            print(f'[REG] ...signature forged. Request denied.')
            return

        # is the user a caller...
        if msg.auth_key in self.VALID_CALLERS:
            # there can only be one caller
            if self.caller:
                print(f'[REG] ...users wants to be a caller but there\'s already one. Request denied.')
                Proto.send_msg(sock, msg)
                return

            print(f'[REG] ...Caller "{msg.nickname}" with public key "{msg.playing_key}" registered.')
            caller_data = UserData(sequence = 0, nickname = msg.nickname, public_key = msg.playing_key)
            self.caller = (sock, caller_data)
        # ... or a player
        else:
            print(f'[REG] ...Player "{msg.nickname}" with public key "{msg.playing_key}" registered.')
            player_data = UserData(sequence = len(self.players) + 1, nickname = msg.nickname, public_key = msg.playing_key)
            self.players[sock] = player_data # player data is associated with socket so that when a player disconnects, we clear the player data

        # inform that registration was successful
        msg.success = True
        Proto.send_msg(sock, msg)

        # trigger party changed event since someone joined
        self.party_changed()

    def party_changed(self):
        player_count = len(self.players)
        print(f'[GAME] Party status: {player_count}/{self.PARTY_MAX}')

        # start game if party is full
        if player_count == self.PARTY_MAX:
            print('[GAME] Game starting...')

        # notifies players
        if player_count > 0:
            print('[GAME] Notifying players on party status...')
            for sock in self.players.keys():
                Proto.send_msg(sock, PartyUpdate(player_count, self.PARTY_MAX))

    def poweroff(self):
        """Shutdowns the server"""
        self.sock.close()
        sys.exit()
