from src.caller import Caller # the actual player implementation
import argparse # for parsing command line arguments

# parses arguments
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="the caller")

    # nickname
    parser.add_argument("nickname", type=str, help="the nickname of the caller")

    # pin
    parser.add_argument("pin", type=str, help="the PIN of the smartcard")

    args = parser.parse_args()

    # create playing area object
    caller = Caller(args.nickname, args.pin)
