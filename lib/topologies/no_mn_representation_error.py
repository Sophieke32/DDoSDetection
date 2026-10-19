from lib.topologies.network_error import NetworkError

class NoMNRepresentationError(NetworkError):
    """Used when trying to access the MiniNet representation of a network element
    that hasn't yet been created."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)