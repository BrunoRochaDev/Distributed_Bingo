from src.common import UserData, LogEntry
import socket # websockets
import sys # for closing the app
import selectors # for multiplexing
import time # for sleeping

# for generating random challenges
import random
import string

from src.protocol import *

class PlayingArea:
    """The secure playing field"""

    # should be >= 1024
    PORT = 1024

    # the number of players needed for a game to start
    PARTY_MAX = 2

    # countdown to start the game
    GAME_COUNTDOWN = 1

    # length of the challenge string for authentication
    CHALLENGE_LENGTH = 14

    # public keys that can be callers
    VALID_CALLERS = set(['caller_CC'])

    def __init__(self, card_size : int, deck_size : int):
        self.card_size = card_size
        self.deck_size = deck_size

        self.running = True
        self.playing = False # the game has not started

        self.caller = None # tuple of socket, userdata ; data is associated with the socket so that when an user disconnects, we clear the data
        self.players = {} # key is socket, value is userdata ; data is associated with the socket so that when an user disconnects, we clear the data
        self.authorized_keys = {} # key is socket, value is a public key ; data is associated with the socket so that when an user disconnects, we clear the data
        self.challenges = {} # dict for associating public key to the challenge for users not yet authenticated

        # Sets Up Private/Public key
        (self.private_key, self.public_key) = Crypto.asym_gen()

        # Log for every command given to the playing area
        self.log = [LogEntry.genesis_block()]

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
            while self.running:
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

        # only accepts connection if game has not yet started
        if self.playing:
            print(f"[NET] Refused a connection because the game has already begun.")
            connection.close()
            return

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
            elif msg.header == 'REGISTER':
                self.register(sock, msg)
            elif msg.header == 'GETUSERS':
                self.get_user_list(sock, msg)
            elif msg.header == 'GETLOG':
                self.get_audit_log(sock, msg)
            elif msg.header == 'GENCARD':
                self.gen_card(sock, msg)
            elif msg.header == 'DECKKEYRES':
                self.deck_key_response(sock, msg)

            # log the message
            if msg.should_log():
                self.log_message(msg)
        else:
            print(f"[NET] Connection with a user has been lost.")

            # if a user disconnected midgame, abort it
            if self.playing:
                print('[GAME] Aborting game since we lost a player.')
                print('[GAME] Notifying players that the game has been aborted...')
                for sock in self.players.keys():
                    Proto.send_msg(sock, GameOver('player_left'))
                if self.caller:
                    Proto.send_msg(self.caller[0], GameOver('player_left'))
                # stop
                self.running = False

            # if not, no biggie
            else:
                # remove data associated with the socket
                if self.caller and self.caller[0] == sock:
                    self.caller = None
                if sock in self.authorized_keys.keys():
                    self.authorized_keys.pop(sock)
                if sock in self.players.keys():
                    self.players.pop(sock)
                    self.party_changed() # trigger party changed event since someone left

            self.selector.unregister(sock)
            sock.close()

    def log_message(self, msg : Message):

        sequence = 0 # TODO

        timestamp = 'now' # TODO

        last_entry = self.log[-1]
        last_hash = last_entry.hash()

        text = str(msg) # the text for now will be the message as a json

        # creates the log entry from the message
        entry = LogEntry(sequence, timestamp, last_hash, text)

        # TODO : playing area should sign this
        entry.sign(self.private_key)

        self.log.append(entry)

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
            caller_data = UserData(0, msg.nickname, msg.playing_key)
            self.caller = (sock, caller_data)
            msg.sequence = 0
        # ... or a player
        else:
            print(f'[REG] ...Player "{msg.nickname}" with public key "{msg.playing_key}" registered.')
            player_data = UserData(len(self.players) + 1, msg.nickname, msg.playing_key)
            self.players[sock] = player_data # player data is associated with socket so that when a player disconnects, we clear the player data
            msg.sequence = len(self.players)

        # inform that registration was successful
        msg.success = True
        Proto.send_msg(sock, msg)

        # let them know of the card size used for the game
        Proto.send_msg(sock, GameInfo(self.card_size, self.deck_size))

        # trigger party changed event since someone joined
        self.party_changed()

    def get_audit_log(self, sock : socket, msg : GetLog):
        """Returns to the user the list of logged messages"""

        print('[SEC] Received request to audit the message log. Sending the list...')

        msg.response = self.log
        Proto.send_msg(sock, msg)

    def get_user_list(self, sock : socket, msg : GetUsers):
        """Returns to the user the list of connected users"""

        print('[SEC] Received request to see registed users. Sending the list...')

        # add the players
        res = list(self.players.values())

        # add the caller if exists
        if self.caller:
            res.append(self.caller[1])

        msg.response = res

        print("\n Public key; \n" + str(msg.response[0]) + "\n\n")

        Proto.send_msg(sock, msg)

    def party_changed(self):
        player_count = len(self.players)
        print(f'[GAME] Party status: {player_count}/{self.PARTY_MAX} ({"(Caller present)" if self.caller else "Caller absent"})')

        # notifies players
        if player_count > 0:
            print('[GAME] Notifying players on party status...')
            for sock in self.players.keys():
                Proto.send_msg(sock, PartyUpdate(player_count, self.PARTY_MAX, self.caller != None))

            if self.caller:
                Proto.send_msg(self.caller[0], PartyUpdate(player_count, self.PARTY_MAX, True))

        # start game if party is full and there's a caller
        if player_count == self.PARTY_MAX and self.caller:
            self.start_game()

    def start_game(self):
        print(f'[GAME] Game starting in {self.GAME_COUNTDOWN} second(s)...')
        print('[SEC] Sending everyone the list of all the participants.')
        self.get_user_list(self.caller[0], GetUsers("",""))
        for sock in self.players.keys():
            self.get_user_list(sock, GetUsers("",""))

        time.sleep(self.GAME_COUNTDOWN)
        print('[GAME] Game started.')
        self.playing = True

        # deck generation
        print('[GAME] Initiating deck generation.')
        print('[GAME] Asking Caller to generate the deck...')
        Proto.send_msg(self.caller[0], GenerateDeck())

    def gen_card(self, sock : socket, msg : GenerateCard):
        def find_user_by_sequence(sequence : id):
            for socket, player in self.players.items():
                if player.sequence == sequence:
                    return socket, player
            return None, None

        # if the card generation has made all the way back to the caller...
        if msg.done:
            # ... distribute it to every player
            for _sock in self.players.keys():
                Proto.send_msg(_sock, msg)

            # and ask for the deck key
            Proto.send_msg(self.caller[0], DeckKeyRequest(0))
            for seq in range(1,len(self.players)+1):
                _sock, _ = find_user_by_sequence(seq)
                Proto.send_msg(_sock, DeckKeyRequest(seq))
            return

        next_socket, next_player = find_user_by_sequence(msg.sequence)

        # If there's no next player, send it back to the caller
        if not next_socket:
            next_socket, next_player = self.caller

        print(f'[NET] Forwarding deck to {next_player.nickname}... ({msg.sequence}/{len(self.players) + 1})')
        Proto.send_msg(next_socket, msg)

    def deck_key_response(self, sock : socket, msg : DeckKeyResponse):
        """Verifies and distribute deck keys to all users"""

        print('[NET] Forwarding deck key around...')
        for _sock in [i for i in self.players.keys()] + [self.caller[0]]:
            if _sock == sock: # don't need to send it back
                continue
            Proto.send_msg(_sock, msg) 

    def poweroff(self):
        """Shutdowns the server"""
        self.sock.close()
        sys.exit()
