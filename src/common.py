from dataclasses import dataclass # for structs

@dataclass
class LogEntry:
    """Entry for recording actions and messages"""

    sequence: int
    timestamp: int
    prev_hash : str
    text : str
    signature : str

@dataclass
class UserData:
    """Object for storing user data"""

    sequence : int
    nickname : str
    public_key : str
