from src.user import *
import random

class Player(User):

    def __init__(self, nickname : str):
        print(f'You are a PLAYER. Your nickname is "{nickname}".')
        self.CC_public = nickname+'_CC'
        self.playing_key = nickname+'_playing_key' 
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

    def generate_card(self, sock : socket, msg : GenerateCard):
        """Generate the card for this player"""
        print('[GAME] Generating card...')
        self.card = set() # card is a set of M numbers ranging from 0 to N

        # get M random numbers from 0 to N
        deck = [n for n in range(msg.deck_size)]
        random.shuffle(deck)
        for m in range(msg.card_size):
            self.card.add(deck[m])
        print(f'[GAME] Card generated : {self.card}')
