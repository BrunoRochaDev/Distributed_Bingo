from src.user import *
import random
from src.crypto import Crypto

class Caller(User):

    def __init__(self, nickname : str):
        print(f'You are a CALLER. Your nickname is "{nickname}".')
        self.CC_public = 'caller_CC'
        self.playing_key = nickname+'_playing_key' # TODO asym key pair, ECC
        self.deck_key = 'deck_key' # TODO sym key, AES128

        self.signed_deck = False

        super().__init__(nickname)

    def handle_input(self, stdin):
        """Receives the typing input"""
        text = format(stdin.read()).upper().strip('\n')

        if text == 'AUTH' and not self.authenticated:
            print('[AUTH] Asking the playing area for a challenge...')
            Proto.send_msg(self.sock, Authenticate(self.CC_public))
        elif text == 'GETUSERS' and self.authenticated:
            print('[SEC] Asking the playing area for the list of registed users...')
            Proto.send_msg(self.sock, GetUsers(self.CC_public, "signature"))
        elif text == 'GETLOG' and self.authenticated:
            print('[SEC] Asking the playing area for the list of logged messages...')
            Proto.send_msg(self.sock, GetLog(self.CC_public, "signature"))
        elif text == 'REGISTER' and not self.registered and self.authenticated:
            print(f'[REG] Registering yourself to the playing area as "{self.nickname}"...')
            Proto.send_msg(self.sock, Register(self.nickname, self.playing_key, self.CC_public, "signature"))
        else:
            print('Invalid input.')

    def generate_deck(self, sock : socket, msg : GenerateCard):
        """Generate the deck"""
        print('[GAME] Generating deck...')
        self.deck = [n for n in range(msg.deck_size)]
        random.shuffle(self.deck)

        # encrypt each number with the sym key
        #encrypted_deck = [Crypto.sym_encrypt(self.deck_key, num) for num in self.deck]
        encrypted_deck = []

        print(f'[GAME] Deck generated : {self.deck}')
        self.signed_deck = True

        # creating the card generation message
        card_msg = GenerateCard(1, encrypted_deck)
        card_msg.signatures.append(card_msg.sign(self.deck_key))

        Proto.send_msg(sock, card_msg)
