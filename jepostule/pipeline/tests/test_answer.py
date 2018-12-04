from django.core import mail
from django.test import TestCase
from django.utils.timezone import now

from jepostule.auth.models import ClientPlatform
from jepostule.pipeline import models
from jepostule.pipeline import answer


class AnswerTests(TestCase):

    def test_answer_interview(self):
        job_application = models.JobApplication.objects.create(
            candidate_email='candidate@pe.fr',
            client_platform=ClientPlatform.objects.create(client_id="id"),
        )
        models.AnswerInterview.objects.create(
            job_application=job_application,
            datetime=now(),
            employer_email='boss@bigco.com',
        )
        answer.send(job_application.id)
        answer.send_answer_to_candidate.consume()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(['boss@bigco.com'], mail.outbox[0].reply_to)

    def test_rejection(self):
        job_application = models.JobApplication.objects.create(
            candidate_email='candidate@pe.fr',
            client_platform=ClientPlatform.objects.create(client_id="id"),
        )
        models.AnswerRejection.objects.create(
            job_application=job_application,
        )
        answer.send(job_application.id)
        answer.send_answer_to_candidate.consume()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual([], mail.outbox[0].reply_to)

    def test_get_details(self):
        job_application = models.JobApplication.objects.create(
            candidate_email='candidate@pe.fr',
            client_platform=ClientPlatform.objects.create(client_id="id"),
        )
        models.AnswerInterview.objects.create(
            job_application=job_application,
            datetime=now(),
        )
        self.assertEqual(models.JobApplication.ANSWER_INTERVIEW, job_application.answer.get_details().answer_type)

    def test_get_answer_message(self):
        job_application = models.JobApplication.objects.create(
            candidate_email='candidate@pe.fr',
            client_platform=ClientPlatform.objects.create(client_id="id"),
        )
        models.AnswerInterview.objects.create(
            job_application=job_application,
            datetime=now(),
        )
        with self.settings(TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'string_if_invalid': 'INVALID__%s',
                    },
                },
        ]):
            rendered = answer.get_answer_message(job_application.answer)
        self.assertIn("Proposition d'entretien d'embauche", rendered)
        self.assertNotIn("INVALID__", rendered)

    def test_get_answer_details_message(self):
        job_application = models.JobApplication.objects.create(
            candidate_email='candidate@pe.fr',
            client_platform=ClientPlatform.objects.create(client_id="id"),
        )
        answer_request_info = models.AnswerRequestInfo.objects.create(
            job_application=job_application,
        )
        with self.settings(TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'string_if_invalid': 'INVALID__%s',
                    },
                },
        ]):
            rendered = answer.get_answer_details_message(answer_request_info)
        self.assertIn("informations supplémentaires", rendered)
        self.assertNotIn("INVALID__", rendered)
