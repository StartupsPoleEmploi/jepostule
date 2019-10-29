from unittest import mock

from django.conf import settings

from jepostule.crypto import encrypt
from jepostule.auth.models import ClientPlatform
from jepostule.queue.exceptions import DelayProcessing
from jepostule.pipeline import application
from jepostule.pipeline import memo, ami
from jepostule.pipeline import models
from jepostule.tests.base import PipelineCacheTestCase


class ApplicationTests(PipelineCacheTestCase):

    def test_application_pipeline(self):
        job_application = models.JobApplication.objects.create(
            message="je suis chaud bouillant pour bosser chez vous",
            siret="82136020300011",
            candidate_first_name="Charles",
            candidate_last_name="Sept",
            candidate_email="candidat@pe.fr",
            candidate_phone="0123456789",
            candidate_address="3 rue du four 75018 Paris",
            candidate_peid="jfljfdkgjfdkgjfdkgjdflkgjkldfgj",
            candidate_rome_code="A1101",
            candidate_peam_access_token=encrypt("01234567890abcdef01234567890abcdef"),
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
            self.assertEqual(settings.JEPOSTULE_NO_REPLY, args[2])
            self.assertEqual(['boss@big.co'], args[3])
            self.assertEqual(1, len(kwargs['attachments']))
            self.assertEqual('moncv.doc', kwargs['attachments'][0].name)
            self.assertEqual(b'', kwargs['attachments'][0].content)
            self.assertEqual(1, job_application.events.filter(name=models.JobApplicationEvent.SENT_TO_EMPLOYER).count())
            event = job_application.events.get(name=models.JobApplicationEvent.SENT_TO_EMPLOYER)
            self.assertEqual(666, event.email.message_id)

        self.assertEqual(0, job_application.events.filter(name=models.JobApplicationEvent.FORWARDED_TO_MEMO).count())
        mocked_response = {'idCandidature': '1161981', 'msg': 'Application saved', 'result': 'ok'}
        with mock.patch.object(memo, 'get_response', return_value=mocked_response) as get_response:
            application.forward_application_to_memo.consume()
            get_response.assert_called_once()
        self.assertEqual(1, job_application.events.filter(name=models.JobApplicationEvent.FORWARDED_TO_MEMO).count())

        self.assertEqual(0, job_application.events.filter(name=models.JobApplicationEvent.FORWARDED_TO_AMI).count())
        mocked_response = {}  # Empty HTTP 204 response anyway.
        with mock.patch.object(ami, 'get_response', return_value=mocked_response) as get_response:
            application.forward_application_to_ami.consume()
            get_response.assert_called_once()
        self.assertEqual(1, job_application.events.filter(name=models.JobApplicationEvent.FORWARDED_TO_AMI).count())

        with mock.patch.object(application, 'send_mail', return_value=[667]) as send_mail:
            application.send_confirmation_to_candidate.consume()
            send_mail.assert_called_once()

            args, kwargs = send_mail.call_args
            self.assertEqual(settings.JEPOSTULE_NO_REPLY, args[2])
            self.assertEqual(['candidat@pe.fr'], args[3])
            self.assertIsNone(kwargs.get('attachments'))
            self.assertEqual(
                1,
                job_application.events.filter(name=models.JobApplicationEvent.CONFIRMED_TO_CANDIDATE).count(),
            )
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
