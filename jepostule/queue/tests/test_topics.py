from unittest import mock

from django.test import TestCase
from django.utils.timezone import now

from jepostule.queue import serialize
from jepostule.queue import topics
from jepostule.queue.models import DelayedMessage, FailedMessage


class TopicsTest(TestCase):

    def setUp(self):
        topics.Processors.clear()

    def test_subscribe_to_topic_twice(self):
        def task1():
            pass

        def task2():
            pass

        topics.subscribe('dummy-topic')(task1)
        self.assertRaises(ValueError, topics.subscribe('dummy-topic'), task2)

    def test_failed_messages_get_stored(self):
        @topics.subscribe('mytopic')
        def task(*args, **kwargs):
            raise ZeroDivisionError

        task.run_async('val1', namedparam='val2')
        self.assertRaises(ZeroDivisionError, topics.consume, 'mytopic')
        self.assertEqual(1, FailedMessage.objects.count())

        failed_message = FailedMessage.objects.first()
        args, kwargs = serialize.loads(failed_message.value_bytes)
        self.assertEqual('mytopic', failed_message.topic)
        self.assertEqual('ZeroDivisionError', failed_message.exception)
        self.assertIn('ZeroDivisionError', failed_message.traceback)
        self.assertEqual(('val1',), args)
        self.assertEqual({'namedparam': 'val2'}, kwargs)

    def test_retry_and_delete(self):
        processor = mock.Mock()
        topics.subscribe('testtopic')(processor)

        failed = FailedMessage.objects.create(
            topic='testtopic',
            value=serialize.dumps(1, 2, key1='val1'),
        )

        topics.retry_and_delete(failed)
        topics.consume('testtopic')

        self.assertEqual(0, FailedMessage.objects.count())
        processor.assert_called_once_with(1, 2, key1='val1')

    def test_retry_and_archive(self):
        processor = mock.Mock()
        topics.subscribe('testtopic')(processor)

        failed = FailedMessage.objects.create(
            topic='testtopic',
            value=serialize.dumps(1, 2, key1='val1'),
        )

        topics.retry_and_archive(failed)
        topics.consume('testtopic')

        self.assertEqual(1, FailedMessage.objects.count())
        processor.assert_called_once_with(1, 2, key1='val1')

    def test_delay(self):
        @topics.subscribe('testtopic')
        def raising(arg1):
            raise topics.exceptions.DelayProcessing(5)

        raising.run_async('val1')
        topics.consume('testtopic')
        delayed_message = DelayedMessage.objects.first()
        self.assertEqual((('val1',), {}), serialize.loads(delayed_message.value_bytes))
        self.assertEqual('testtopic', delayed_message.topic)

    def test_dequeue(self):
        delayed_message = DelayedMessage.objects.create(
            topic='testtopic',
            value=b'value',
            until=now()
        )

        # dequeue works
        with mock.patch.object(topics, 'send') as mock_send:
            topics.dequeue(delayed_message)
            mock_send.assert_called_once_with('testtopic', b'value')

        # object was already deleted, so no message is re-emitted
        with mock.patch.object(topics, 'send', side_effect=ZeroDivisionError):
            topics.dequeue(delayed_message)

    def test_dequeue_picks_correct_value(self):
        DelayedMessage.objects.create(
            topic='testtopic',
            value=b'value',
            until=now()
        )

        with mock.patch.object(topics, 'send') as mock_send:
            topics.dequeue(DelayedMessage.objects.first())
            mock_send.assert_called_once_with('testtopic', b'value')

    def test_dequeue_fails(self):
        until = now()
        delayed_message = DelayedMessage.objects.create(
            topic='testtopic',
            value=b'value',
            until=until
        )

        # When a message cannot be re-emitted, the delayed message is not deleted
        with mock.patch.object(topics, 'send', side_effect=ZeroDivisionError):
            self.assertRaises(ZeroDivisionError, topics.dequeue, delayed_message, 25)

        self.assertEqual(1, DelayedMessage.objects.filter(id=delayed_message.id).count())
        self.assertEqual(25, (DelayedMessage.objects.first().until - until).seconds)
