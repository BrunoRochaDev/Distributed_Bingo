import socket # websockets
import sys # for closing the app
import selectors # for multiplexing
import fcntl # For non-blocking stdout
from src.common import UserData, LogEntry
import random # for shuffling
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
        self.sequence = None # given by the playing area
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
            elif msg.header == 'DECKKEYRES':
                self.deck_key_response(sock, msg)
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
            self.sequence = msg.sequence
            print(f'[REG] ...registration was a success. I am the user of sequence {self.sequence}.')
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

        # sequence must mach
        if msg.sequence != self.sequence:
            print("[ERROR] Deck key request received has incorrect sequence")
            # TODO disqualify?
            return

        print('[SEC] Sending my deck key to other players...')
        # TODO deck_key must be sent in a way that the other side can reconstruct
        response = DeckKeyResponse(msg.sequence, str(self.deck_key))
        response.sign(self.playing_key)
        Proto.send_msg(sock, response)

    def deck_key_response(self, sock : socket, msg : DeckKeyResponse):
        """Verifies and stores deck key response"""

        # TODO verify signature
        if False:
            print('[ERROR] Received a deck key response with invalid signature.')
            # TODO notify caller
            return

        self.deck_keys[msg.sequence] = msg.response

        current = sum([x != None for x in self.deck_keys.values()])
        total = len(self.deck_keys)
        print(f'[SEC] Received a deck key. ({current}/{total})')

        # if got every key, start to decrypt the deck
        if current == total:
            self.decrypt_deck()

    def decrypt_deck(self):
        def get_public_key(sequence : int) -> str:
            return self.users[sequence].public_key

        print('[SEC] Starting to decrypt the deck...')

        # the deck must have been signed by the caller next
        if False: # TODO
            print('[ERROR] Deck was not last signed by the caller')
            return

        # starts unshuffling and decrypting deck to arrive at cards
        total = len(self.deck_keys)
        for seq in reversed(range(total)):
            # check if the signature is valid
            signature = self.deck_signatures.pop()
            if False: # if it's invalid...
                print("[ERROR] There's an invalid signature in the deck. Game should be aborted.")
                # TODO abort game
                return

            # TODO decipher using deck key
            deck_key = self.deck_keys[seq]

            # unshuffle the deck to get to the state of the previous player
            if seq != 0: 
                seed = self.deck_keys[seq]
                self.encrypted_deck = self.deterministic_unshuffle(self.encrypted_deck, seed)


        # now we have the decrypted, unshuffled deck
        self.deck = list(self.encrypted_deck)
        print(f'[GAME] The decrypted deck is: {self.deck}')

        # calculate each player card...
        print('[GAME] The cards are as following:')
        self.cards = {}
        for seq in range(1,total):
            seed = self.deck_keys[seq]
            self.cards[seq] = self.deterministic_shuffle(self.encrypted_deck, seed)[:5] # TODO 5 should not be hardwired
            print(f'{self.users[seq].nickname} {"(You)" if seq == self.sequence else ""} : {self.cards[seq]}')

        # now that the deck and card are known, find the winner
        self.declare_winner()

    def declare_winner(self):
        """Verifies which card gets filled first"""
        fill = {seq : [False for i in range(5)] for seq in self.users.keys() } # TODO 5 should not be hardwired
        
        # sequence of the winners
        winners = []

        # look for winners
        for num_deck in self.deck:
            for seq, card in self.cards.items():
                for idx, num_card in enumerate(card):
                    if num_card == num_deck:
                        fill[seq][idx] = True
                        break
            # if there are winners, stop looking
            winners = [seq for seq, card in fill.items() if all(card)]
            if winners != []:
                break

        print(f'WINNERS {winners}')
        if winners:
            if len(winners) == 1:
                print(f'[GAME] Game over! The winner is {self.users[winners[0]].nickname}.')
            else:
                winner_names = [self.users[seq].nickname for seq in winners]
                print(f'[GAME] Game over! The winners are {", ".join(winner_names[:-1])} and {winner_names[-1]}.')
        else:
            print('[GAME] Game over! There were no winners.')

    # https://crypto.stackexchange.com/q/78309
    def deterministic_shuffle(self, ls, seed : str):
        """Deterministically shuffles a list given a seed""" 
        random.seed(seed)
        random.shuffle(ls)
        return ls

    # https://crypto.stackexchange.com/q/78309
    def deterministic_unshuffle(self, shuffled_ls, seed : str):
        n = len(shuffled_ls)
        # perm is [1, 2, ..., n]
        perm = [i for i in range(1, n + 1)]
        # apply sigma to perm
        shuffled_perm = self.deterministic_shuffle(perm, seed)
        # zip and unshuffle
        zipped_ls = list(zip(shuffled_ls, shuffled_perm))
        zipped_ls.sort(key=lambda x: x[1])
        return [a for (a, b) in zipped_ls]
