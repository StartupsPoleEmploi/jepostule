class BaseProducer:
    def __init__(self):
        pass

    def send(self, topic, value, key=None):
        """
        Send a message in a given topic.
        """
        raise NotImplementedError


class BaseConsumer:
    """
    Message consumer. No special handling of errors is expected.
    """

    def __init__(self, topic):
        self.topic = topic

    def __iter__(self):
        raise NotImplementedError
