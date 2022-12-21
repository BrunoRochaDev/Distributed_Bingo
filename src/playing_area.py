from src.common import UserData
import socket # websockets
import sys # for closing the app
import selectors # for multiplexing

class PlayingArea:
    """The secure playing field"""

    # should be >= 1024
    PORT = 1024

    def __init__(self, card_size : int, deck_size : int):
        self.card_size = card_size
        self.deck_size = deck_size

        self.playing = False # the game has not started

        self.users = {} # dict for associating sequence to player data

        # creates and starts the server
        self.server_setup()
        self.run()

    def server_setup(self):
        """Creates a TCP websocket at a predifined port"""

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # adds this line to prevent an error message stating that the previous address was already in use
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # binds the server socket to an interface address and port
        self.sock.bind((socket.gethostname(), self.PORT))

        # starts listening for clients...
        self.sock.listen()

        print(f"Started server at port {self.PORT}.")

        # creates the selector object
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.sock, selectors.EVENT_READ, data=None)

    def run(self):
        """Receives messages as they come"""

        # waits for messages
        try:
            while True:
                events = self.selector.select()

                # Loops through every event in the selector...
                for key, _ in events:
                    # If the data is none, that means that the socket has not yet been accepted
                    if key.data is None:
                        #Accept the connection
                        self.accept_connection(key.fileobj) # key.fileobj is the socket object
                    else:
                        self.service_connection(key)

        # shutdowns if the user interrupts the proccess
        except KeyboardInterrupt:
            self.poweroff()

    def accept_connection(self, sock):
        """Accepts the connection from a client (player)"""

        connection, address = sock.accept()
        print(f"Accepted connection from {address}.")

        self.selector.register(connection, selectors.EVENT_READ, data="")

    def service_connection(self, key):
        sock = key.fileobj
        data = key.data

        #print("Received message")

    def poweroff(self):
        """Shutdowns the server"""

        self.sock.close()
        sys.exit()
