from datetime import timedelta
import logging
import traceback

from django.conf import settings

from jepostule.utils import import_object
from .models import FailedMessage, DelayedMessage
from . import exceptions
from . import serialize


logger = logging.getLogger(__name__)


# TODO we need a different mechanism to register processors: this requires the
# __name__ attribute, which is clunky with mock objects (see test_topics).
# Also, I'm not sure this object is cleaned between two test runs.
TOPIC_PROCESSORS = {}


def all_topics():
    """
    Return a list of all defined topics.
    """
    return sorted(TOPIC_PROCESSORS.keys())


def subscribe(topic):
    """
    Decorator for asynchronous tasks. This adds utility methods to decorated functions:

        run_async(*args, **kwargs): delay execution of function
        consume(): execute pending tasks

    Usage:

        @subscribe('topicname')
        def my_func(arg1, arg2, kwarg1=None):
            # do some lengthy stuff
            ....

        my_func.run_async("val1", "val2", kwarg1="k1")
    """
    def decorator(func):
        if topic in TOPIC_PROCESSORS:
            # TODO this is fragile. For instance, we cannot differentiate two
            # lambda functions. Yet, we need this because django make multiple
            # imports at runtime. Maybe we need a cleaner way to associate
            # topics to functions...
            path = '{func.__module__}.{func.__name__}'
            existing_processor = path.format(func=TOPIC_PROCESSORS[topic])
            new_processor = path.format(func=func)
            if new_processor != existing_processor:
                raise ValueError("Cannot replace {} with {} as processor of topic {}".format(
                    existing_processor, new_processor, topic
                ))

        def run_async(*args, **kwargs):
            produce(topic, *args, **kwargs)
        def consume_topic():
            consume(topic)
        func.run_async = run_async
        func.consume = consume_topic
        TOPIC_PROCESSORS[topic] = func
        return func
    return decorator


def produce(topic, *args, **kwargs):
    """
    Produce a message in a given topic.
    """
    send(topic, serialize.dumps(*args, **kwargs))


def send(topic, value):
    """
    Like `produce` but with raw bytes.

    Args:
        topic (str)
        value (bytes)
    """
    ProducerClass = import_object(settings.QUEUE_PRODUCER)
    ProducerClass().send(topic, value)
    logger.info("produced=%s", value)


def consume(topic):
    """
    Consume a topic. This function is *not* resilient to errors and keyboard
    interrupts! For long running tasks, where you want to be sure that a task
    has finished executing before killing it, and more generally for handling
    tasks that may trigger errors in production you need to call the `consume`
    function from the `threads` module.
    """
    for value in iter_values(topic):
        if value is not None:
            process(topic, value)


def iter_values(topic):
    """
    Iterate over values stored in topic. This may yield None values whenever
    the inner consumer times out.
    """
    ConsumerClass = import_object(settings.QUEUE_CONSUMER)
    consumer = ConsumerClass(topic)
    for value in consumer:
        yield value


def process(topic, value):
    """
    Process a message, e.g: the result of iter_values. Processing does *not*
    operate in a safe way: exceptions are not caught, so it is the
    responsibility of the caller to process them. However, all errors lead to
    the creation of a FailedMessage object, which make it possible to retry
    later the tasks that failed.

    Args:
        topic (str)
        value (bytes): must be parsable by serialize.loads.
    """
    try:
        args, kwargs = serialize.loads(value)
        func = TOPIC_PROCESSORS[topic]
        return func(*args, **kwargs)
    except exceptions.DelayProcessing as e:
        DelayedMessage.objects.create(
            topic=topic,
            value=value,
            until=e.until,
        )
    except Exception as e:
        FailedMessage.objects.create(
            topic=topic,
            value=value,
            exception=e.__class__.__name__,
            traceback=traceback.format_exc(),
        )
        raise
    finally:
        logger.info("consumed=%s", value)


def delay(delay_seconds):
    """
    Commodity function to delay the processing of an asynchronous function.

    Usage:

        @subscribe('mytopic')
        def async_func():
            if should_wait:
                delay(30)
            ...

    Note that this raises an exception that will *not* be caught whenever the
    function is run synchronously.

    Args:
        delay_seconds (int)
    """
    if delay_seconds > 0:
        raise exceptions.DelayProcessing(delay_seconds)


def retry_and_delete(failed_message):
    """
    Retry a failed message, then delete it.

    Args:
        failed_message (FailedMessage)
    """
    send(failed_message.topic, failed_message.value_bytes)
    failed_message.delete()


def retry_and_archive(failed_message):
    """
    Retry a failed message, then archive it.

    Args:
        failed_message (FailedMessage)
    """
    send(failed_message.topic, failed_message.value_bytes)
    failed_message.archive()


def dequeue(delayed_message, fail_delay=36000):
    """
    Re-send to corresponding topic a delayed message.

    Args:
        delayed_message (DelayedMessage)
        fail_delay (int): in case of dequeue failure, this is the delay, in
        seconds, that we should apply to the re-delayed message.
    """
    count, _ = DelayedMessage.objects.filter(id=delayed_message.id).delete()
    if count > 0:
        try:
            send(delayed_message.topic, delayed_message.value_bytes)
        except:
            # On failure, we need to recreate the message
            delayed_message.until += timedelta(seconds=fail_delay)
            delayed_message.save()
            raise
