class TopologyError(Exception):
    """Used when something goes wrong with the topology."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)