from dataclasses import dataclass # for structs

class LogEntry:
    """Entry for recording actions and messages"""
    def __init__(self, sequence: int, timestamp, prev_hash : str, text : str):
        self.sequence = sequence
        self.prev_hash = prev_hash
        self.text = text
        self.signature = None

    def sign(self, private_key):
        self.signature = 'signature' # TODO

    def hash(self) -> str:
        return 'hash'

    @classmethod
    def genesis_block(cls):
        return LogEntry(None, None,  None, 'genesis')

@dataclass
class UserData:
    """Object for storing user data"""

    sequence : int
    nickname : str
    public_key : str
