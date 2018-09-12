from datetime import timedelta

from django.utils.timezone import now


class DelayProcessing(Exception):
    """
    Exception raised whenever we want to delay the processing of a message.
    """

    def __init__(self, delay_seconds):
        super().__init__(delay_seconds)
        self.delay_seconds = delay_seconds
        self.until = now() + timedelta(seconds=delay_seconds)
