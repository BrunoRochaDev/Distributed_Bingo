from src.user import *
from src.crypto import Crypto

class Player(User):

    def __init__(self, nickname : str):
        print(f'You are a PLAYER. Your nickname is "{nickname}".')
        self.CC_public = nickname+'_CC' 
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
            Proto.send_msg(self.sock, Register(self.nickname, self.private_key, self.CC_public, "signature"))
        else:
            print('Invalid input.')

    def generate_card(self, sock : socket, msg : GenerateCard):
        """Generate the card for this player"""
        if msg.done:
            print('[GAME] Received commtied deck. Waiting for deck keys to decrypt it.')
            self.encrypted_deck = msg.deck
            self.deck_signatures = msg.signatures
            return

        # sequence must match
        if msg.sequence != self.sequence:
            print('[ERROR] Sequence from the card does not match your own.')
            # TODO tell caller
            return

        # message must have deck
        if not msg.deck:
            print('[ERROR] Generate card message does not contain a deck')
            return

        print('[GAME] Generating card...')

        # Shuffle the deck deterministically
        msg.deck = self.deterministic_shuffle(msg.deck, str(self.deck_key))

        msg.sign(self.private_key)

        msg.sequence += 1

        print('[GAME] Card generated. Passing it forward...')
        Proto.send_msg(self.sock, msg)

        # Create dict to hold everyone's deck keys
        self.deck_keys = {key:None for key in self.users.keys()}
        self.deck_keys[self.sequence] = str(self.deck_key)
