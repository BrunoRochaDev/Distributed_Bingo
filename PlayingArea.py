from src.playing_area import PlayingArea # the actual playing area implementation
import argparse # for parsing command line arguments

# parses arguments
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="the secure playing field")

    # card size
    parser.add_argument("card_size", type=int, help="the number of spaces in the players' card")

    # deck size
    parser.add_argument("deck_size", type=int, help="the size of the deck, from 1 to N")

    args = parser.parse_args()

    # restrictions
    if args.card_size <= 0:
        parser.error("the card size must be greater than zero")
    if args.deck_size <= 0:
        parser.error("the deck size must be greater than zero")
    if args.deck_size <= args.card_size:
        parser.error("the card size must be lesser than the deck size")

    # create playing area object
    playing_area = PlayingArea(args.card_size, args.deck_size)
