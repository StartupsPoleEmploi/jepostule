from unittest import mock

from django.conf import settings

from jepostule.auth.models import ClientPlatform
from jepostule.queue.exceptions import DelayProcessing
from jepostule.pipeline import application
from jepostule.pipeline import models
from jepostule.tests.base import CacheTestCase


class ApplicationTests(CacheTestCase):

    def test_application_pipeline(self):
        job_application = models.JobApplication.objects.create(
            message="message",
            candidate_first_name="Charles",
            candidate_last_name="Sept",
            candidate_email="candidat@pe.fr",
            employer_email="boss@big.co",
            client_platform=ClientPlatform.objects.create(client_id="id"),
        )
        attachment = application.Attachment(
            content=b'',
            name='moncv.doc'
        )

        application.send(job_application.id, [attachment])

        with mock.patch.object(application, 'send_mail', return_value=[666]) as send_mail:
            application.send_application_to_employer.consume()
            send_mail.assert_called_once()

            args, kwargs = send_mail.call_args
            self.assertEqual("Charles Sept <{}>".format(settings.JEPOSTULE_NO_REPLY), args[2])
            self.assertEqual(['boss@big.co'], args[3])
            self.assertEqual(1, len(kwargs['attachments']))
            self.assertEqual('moncv.doc', kwargs['attachments'][0].name)
            self.assertEqual(b'', kwargs['attachments'][0].content)
            self.assertEqual(1, job_application.events.filter(name=models.JobApplicationEvent.SENT_TO_EMPLOYER).count())
            event = job_application.events.get(name=models.JobApplicationEvent.SENT_TO_EMPLOYER)
            self.assertEqual(666, event.email.message_id)

        with mock.patch.object(application, 'send_mail', return_value=[667]) as send_mail:
            application.send_confirmation_to_candidate.consume()
            send_mail.assert_called_once()

            args, kwargs = send_mail.call_args
            self.assertEqual("La Bonne Boite <{}>".format(settings.JEPOSTULE_NO_REPLY), args[2])
            self.assertEqual(['candidat@pe.fr'], args[3])
            self.assertIsNone(kwargs.get('attachments'))
            self.assertEqual(1, job_application.events.filter(name=models.JobApplicationEvent.CONFIRMED_TO_CANDIDATE).count())
            event = job_application.events.get(name=models.JobApplicationEvent.CONFIRMED_TO_CANDIDATE)
            self.assertEqual(667, event.email.message_id)

    def test_application_rate_limits(self):
        job_application = models.JobApplication.objects.create(
            message="message",
            candidate_email="candidat@pe.fr",
            employer_email="boss@big.co",
            client_platform=ClientPlatform.objects.create(client_id="id"),
        )
        application.send_application_to_employer(job_application.id)
        self.assertRaises(
            DelayProcessing,
            application.send_application_to_employer, job_application.id
        )
