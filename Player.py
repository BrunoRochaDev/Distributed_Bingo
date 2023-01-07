from src.player import Player # the actual player implementation
import argparse # for parsing command line arguments

# parses arguments
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="the player")

    # nickname
    parser.add_argument("nickname", type=str, help="the nickname of the player")

    args = parser.parse_args()

    # create playing area object
    player = Player(args.nickname)
