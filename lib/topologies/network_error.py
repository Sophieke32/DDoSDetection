class NetworkError(Exception):
    """Used when something goes wrong with the network."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)