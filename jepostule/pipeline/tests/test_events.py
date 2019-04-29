from time import time

from django.test import override_settings

from jepostule.auth.models import ClientPlatform
from jepostule.pipeline import events
from jepostule.pipeline import models
from jepostule.security import blacklist
from jepostule.tests.base import PipelineCacheTestCase


class EventTests(PipelineCacheTestCase):

    def setUp(self):
        super().setUp()
        self.client_platform = ClientPlatform.objects.create(client_id="id")

    def test_dst_email(self):
        job_application = models.JobApplication.objects.create(
            employer_email='boss@company.com',
            candidate_email='candidate@pe.fr',
            client_platform=self.client_platform,
        )
        event1 = job_application.events.create(
            name=models.JobApplicationEvent.SENT_TO_EMPLOYER
        )
        event2 = job_application.events.create(
            name=models.JobApplicationEvent.CONFIRMED_TO_CANDIDATE
        )
        event3 = job_application.events.create(
            name=models.JobApplicationEvent.ANSWERED
        )
        event4 = job_application.events.create(
            name=models.JobApplicationEvent.FORWARDED_TO_MEMO
        )
        self.assertEqual('boss@company.com', event1.to_email)
        self.assertEqual('candidate@pe.fr', event2.to_email)
        self.assertEqual('candidate@pe.fr', event3.to_email)
        self.assertIsNone(event4.to_email)

    def test_large_message_id(self):
        job_application = models.JobApplication.objects.create(
            employer_email='boss@company.com',
            candidate_email='candidate@pe.fr',
            client_platform=self.client_platform,
        )
        event = job_application.events.create(
            name=models.JobApplicationEvent.ANSWERED,
        )
        models.Email.objects.create(
            event=event,
            message_id=576460752697195324,
        )

    def test_open_event(self):
        job_application = models.JobApplication.objects.create(
            employer_email='boss@company.com',
            candidate_email='candidate@pe.fr',
            client_platform=self.client_platform,
        )
        event = job_application.events.create(
            name=models.JobApplicationEvent.SENT_TO_EMPLOYER
        )
        models.Email.objects.create(event=event, status=models.Email.SENT, message_id=123)
        events.receive({
            'event': 'open', 'time': time(),
            'MessageID': 123,
            'email': 'drunk@propaganda.cn',
        })
        events.process.consume()
        self.assertEqual(models.Email.OPENED, models.Email.objects.get().status)
        self.assertFalse(blacklist.is_blacklisted("drunk@propaganda.cn"))

    def test_spam_event(self):
        event = {
            'event': 'spam', 'time': time(),
            'MessageID': 58265320973912910,
            'email': 'drunk@propaganda.cn',
        }
        events.receive(event)
        events.process.consume()
        self.assertTrue(blacklist.is_blacklisted("drunk@propaganda.cn"))

    @override_settings(BLACKLIST_DURATION_SECONDS=1)
    def test_spam_event_in_the_past(self):
        event = {
            'event': 'spam', 'time': time() - 2,
            'MessageID': 58265320973912910,
            'email': 'drunk@propaganda.cn',
        }
        events.receive(event)
        events.process.consume()
        self.assertFalse(blacklist.is_blacklisted("drunk@propaganda.cn"))

    def test_spam_event_incorrect_timestamp(self):
        event = {
            'event': 'spam', 'time': 'wtf',
            'MessageID': 58265320973912910,
            'email': 'drunk@propaganda.cn',
        }
        events.receive(event)
        events.process.consume()
        self.assertTrue(blacklist.is_blacklisted("drunk@propaganda.cn"))

    def test_event_with_incorrect_MessageID(self):
        events.receive({
            'event': 'open', 'time': time(),
            'MessageID': None,
            'email': 'drunk@propaganda.cn',
        })
        events.receive({
            'event': 'open', 'time': time(),
            'MessageID': 'wtf',
            'email': 'drunk@propaganda.cn',
        })
        events.process.consume()

    def test_event_with_incorrect_status(self):
        job_application = models.JobApplication.objects.create(
            employer_email='boss@company.com',
            candidate_email='candidate@pe.fr',
            client_platform=self.client_platform,
        )
        event = job_application.events.create(
            name=models.JobApplicationEvent.SENT_TO_EMPLOYER
        )
        models.Email.objects.create(event=event, status=models.Email.OPENED, message_id=123)

        events.receive({
            'event': None, 'time': time(),
            'MessageID': 123,
            'email': 'drunk@propaganda.cn',
        })
        events.receive({
            'event': 'shutupyouredrunk', 'time': time(),
            'MessageID': 123,
            'email': 'drunk@propaganda.cn',
        })
        events.process.consume()
        self.assertEqual(models.Email.OPENED, models.Email.objects.get().status)
