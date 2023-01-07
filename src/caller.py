from src.user import *
import random
from src.crypto import Crypto

class Caller(User):

    def __init__(self, nickname : str):
        print(f'You are a CALLER. Your nickname is "{nickname}".')
        self.CC_private = """-----BEGIN ENCRYPTED PRIVATE KEY-----
MIIFLTBXBgkqhkiG9w0BBQ0wSjApBgkqhkiG9w0BBQwwHAQI18O7AM4nA8ICAggA
MAwGCCqGSIb3DQIJBQAwHQYJYIZIAWUDBAEqBBCGbc0edFnAF/HVrGQkXkgxBIIE
0JkdMgx1kZdi0ZkD1gWUNlQ/DPW8sfp9fqIoeBNQ28bG/7ogx3Ey3oiJ1dACRPir
AjNnDV1NbJltZUr+vi4VFf73MccVjVtxnxTVvZizOcsMHJ7vKTdP64Bfm9vr45+B
d9yY1jeU3KcWt5rXwLtUlmpSogupLRqGXeqhtEyyjk/Kt9p0yu1drOSNUc3+ujm/
I15cvgH1t4efUXtsBqT3RhzxZD6vrXhnk/YTF3f7XM9VNOsMPtjxCy+3nVQAuiGq
SR8Ie3ZtSOlw9ZdTqCxMaiwfz3pkLahpXy2mzxjjPgncg+WGJc39WP7vr/TDoCQb
BFuwhMxZ/UNFO5rB9z1IcVirvM5cGd1CAV9s0A9aDTVAZcn5K7u6S3+kEvtUitTd
a2DnsGvdsvmuEnd2C+fL9gX6h0DQcI5Zm9rvj2G18UYbbqvTh0nURfxZdrB6P2gq
NR7FOrbuc7DmuH7FlWPB2WxIlfZZYuX/IFPCtTo8nI9g54B9cyNebzFYWTxaaywg
YHvm31yiNcFG16Molbhmj9R8K3Je91fT8oaq7LcooNROudMuJ3NFWMTyqfbghrJ2
oFx3th6rcb1lFu2wZJBtZJCfY258jEIDLA+IoFecB2Q/v1EPW4Nj/7cH5C1EG+hD
3h5lBgTDeH6GqHVevC3cBHxDZ0tHRgECwTqqrvwNbgJR2LWu3/bf7lZAXcWHniu6
9RMsr5RV3nZxzh2Y/armKpI6XEWkf5mDqdYZpPSCRQIOCvum77zA6qasRL8wVDMW
5/lD6KHMHmkOxGdKVSsEcye4hUZgqOOu75kq7gxKM3HBYodkjOeDBbv/awMrimpZ
rJTWWkP6SiUCT+bLQF8BSfhablLScQBbFHUEY6CwGhZMJsBvDhpTvVfxnJ9Bbejf
X/X1ZOblUZtXfl5EAMK/Vz33PY/knr7mErTKZ4GNbHUIY9XmzaiHC382EjAn0iLp
5ZjfjUpHCw/kS9UthAVajdQsfTCBlwxJay9bcLZLLJ43ykQ7ztoTxQkUxzJrOpIF
bx8Kc10JLI94XJoTCZ4ICB4LRULad2flRZ6EOIW3DIkAeHXjLf3a/oukQNQUDxRI
e2d4QwZX9abG/xUj1TXv3oTIYkIjBIA2fdFQ59BW7o8Sgc+gXJX+RC7ley1Q3RQo
lMkmnsQtwUpy8mgWBgYfHbTktTM/N2mxGfK5n6QmefQ0SDvYbumsZn0Z7QO4ksKH
lX10UAJEKTo3rb/AkvaawWgT3auVbg6EcgEkHX0fxoY9MCNP91C0M2KDBlavyve2
VQo2HcFcl+Xjxr3CKKRCwjFRbEn9404SUFXzLzByDPQXzkrna/JQVOiq7ZeAx3xW
53ykNs2TURsOd1MjGjHGae3q3KnKuB1WP/fIceb+moK2s1osDDcNJGk2/E69hTeX
3GAe3lzdcWf89zl2Z51M4HXHGSr8j74nBFRGIG+v7TVGQWFN+ebrcqnLRGBMXLnW
YUO2I0bECvuGPLWe2LdZ3GSacz3xGNVw4tj3tnplxBT+Q0sMJyzxBLFAwLcRkq35
0Ft6v8g5zfEuyyAT5etotRigsQFTauvgOI1qzfOKsjJk97hYAWFb7w7xWzmUcWX9
uEJK31tg1Yj96noyWIiI6/pt4pBCT36O47dzse8bHLBi
-----END ENCRYPTED PRIVATE KEY-----"""
        self.CC_public = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtoqIL+zjU69K159wo/E2
odAje0eTFG9jB09E9wdrg3rzjS4oZGaKb6aNgv0lxJHQzCTXeHNSujEkQPLuJMCc
v2nYmi6E/3FJb/mBgCU9HIlphqz5QQEMTS7SO8orpGR2mZxnM9KXygHXG2NP1w/N
0+ZTQmEW79cJnNlDndWjFnIjNj4RQBPDfWnQGtfNOVy6Y6nqLEROU/QsjGHR+Baj
KstAjJWI5H5mIIEiIWidEYlmGNvd+An5bjW+cYZr5wft0//lxp9gD4jOyWeuISCw
JTrNKygmMLmLZUKNN5VRp+PnGJvzUzYSwiYtaAVJqvWtcUTSlFTgjv12gb/MZfS2
XwIDAQAB
-----END PUBLIC KEY-----"""

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
