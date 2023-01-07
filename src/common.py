import json # for serializing

class LogEntry:
    """Entry for recording actions and messages"""
    def __init__(self, sequence: int, timestamp, prev_hash : str, text : str, signature : str = None):
        self.sequence = sequence
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.text = text
        self.signature = signature

    @classmethod
    def parse(cls, j):
        return LogEntry(j['sequence'], j['timestamp'], j['prev_hash'], j['text'], j['signature'])

    def sign(self, private_key):
        self.signature = 'signature' # TODO

    def hash(self) -> str:
        return 'hash'

    @classmethod
    def genesis_block(cls):
        return LogEntry(None, None,  None, 'genesis')

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False)

class UserData:
    """Object for storing user data"""
    def __init__(self, sequence : int, nickname : str, public_key : str):
        self.sequence = sequence
        self.nickname = nickname
        self.public_key = public_key

    @classmethod
    def parse(cls, j):
        return UserData(j['sequence'], j['nickname'], j['public_key'])

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False)

