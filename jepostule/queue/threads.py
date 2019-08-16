import logging
import sys
import threading
from time import sleep

from .topics import iter_values, process

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ThreadedConsumer:
    """
    Consume messages in a separate thread. This makes it possible to be
    resilient to keyboard interrupts. Don't use this class directly. Instead,
    use the `consume(topic)` function.

    If a specific thread fails, it will *not* be restarted. For instance, this
    may happen when trying to process an unknown topic.
    When all threads have finished processing (which should normally never
    happen), this consumer returns. So, for safe, production-ready topic
    consumption, you should process one thread at a time, and under
    supervision.
    """

    def __init__(self, *topics, stdout=sys.stdout):
        self.terminate = False
        self.stdout = stdout
        self.threads = [
            threading.Thread(name=topic, target=self.run, args=(topic,))
            for topic in topics
        ]

        for thread in self.threads:
            thread.start()

    def run(self, topic):
        for value in iter_values(topic):
            if value is not None:
                try:
                    process(topic, value)
                except Exception as e:# pylint: disable=broad-except
                    # We need to log an error in addition to an exception. This
                    # is because exception stacktraces that contain attachments
                    # are very large, and they may not reach sentry.
                    logger.error("Error processing value in topic %s. Please "
                                 "check failed messages at "
                                 "/admin/queue/failedmessage/. %s", topic, e)
                    logger.exception(e)
            if self.terminate:
                return

    def wait(self):
        while True:
            try:
                if not any([thread.is_alive for thread in self.threads]):
                    return
                sleep(1)
            except KeyboardInterrupt:
                self.stdout.write("Gracefully stopping running consumer... (you can press Ctrl+C again to force but please don't do that)\n")
                self.terminate = True
                for thread in self.threads:
                    # Join the main thread and
                    # wait for all child threads to finish.
                    # Also, kill the thread.
                    thread.join()
                return


def consume(*topics):
    """
    Consume messages, just like `topics.consume`, but with resiliency to
    keyboard interrupts (ctrl+c)
    """
    ThreadedConsumer(*topics).wait()
