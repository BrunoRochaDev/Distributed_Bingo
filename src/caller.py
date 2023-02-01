from src.user import *
import random
from src.crypto import Crypto

class Caller(User):

    def __init__(self, nickname : str, pin : str):
        print(f'You are a CALLER. Your nickname is "{nickname}".')
        self.signed_deck = False

        super().__init__(nickname, pin)

    def handle_input(self, stdin):
        """Receives the typing input"""
        text = format(stdin.read()).upper().strip('\n')

        if text == 'AUTH' and not self.authenticated:
            print('[AUTH] Asking the playing area for a challenge...')
            # convert tuple of bytes to tuple of base64 strings
            modulus, pubexp = self.CC_public
            modulus, pubexp = base64.b64encode(modulus).decode('ascii'), base64.b64encode(pubexp).decode('ascii')
            encoded_CC_public = (modulus, pubexp)
            Proto.send_msg(self.sock, Authenticate(encoded_CC_public))
        elif text == 'GETUSERS' and self.authenticated:
            print('[SEC] Asking the playing area for the list of registed users...')
            Proto.send_msg(self.sock, GetUsers(self.CC_public, "signature"))
        elif text == 'GETLOG' and self.authenticated:
            print('[SEC] Asking the playing area for the list of logged messages...')
            Proto.send_msg(self.sock, GetLog(self.CC_public, "signature"))
        elif text == 'REGISTER' and not self.registered and self.authenticated:
            print(f'[REG] Registering yourself to the playing area as "{self.nickname}"...')
            Proto.send_msg(self.sock, Register(self.nickname, self.public_key, self.CC_public, "signature"))
        else:
            print('Invalid input.')

    def generate_deck(self, sock : socket, msg : GenerateCard):
        """Generate the deck"""
        print('[GAME] Generating deck...')
        self.deck = [n for n in range(self.deck_size)]
        random.shuffle(self.deck)

        # encrypt each number with the sym key
        encrypted_deck = self.deck
        encrypted_deck = [Crypto.sym_encrypt(self.deck_key, num) for num in self.deck]

        print(f'[GAME] Deck generated : {self.deck}')
        self.signed_deck = True

        # creating the card generation message
        card_msg = GenerateCard(1, encrypted_deck)
        card_msg.sign(self.private_key) 

        Proto.send_msg(sock, card_msg)

    def generate_card(self, sock : socket, msg : GenerateCard):
        """The deck made all the way back after all players generated their cards"""
        print('[GAME] Received deck after all players made their cards. Validating it...')

        self.encrypted_deck = msg.deck
        self.deck_signatures = msg.signatures

        msg.sign(self.private_key)
        msg.done = True

        # Create dict to hold everyone's deck keys
        self.deck_keys = {key:None for key in self.users.keys()}
        self.deck_keys[0] = self.deck_key
 
        print('[GAME] Comitting deck to all users...')
        Proto.send_msg(self.sock, msg)
        print('[GAME] Waiting for deck keys to decrypt deck...')
