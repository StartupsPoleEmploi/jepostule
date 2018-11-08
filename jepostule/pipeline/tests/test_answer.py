from django.core import mail
from django.test import TestCase
from django.utils.timezone import now

from jepostule.pipeline import models
from jepostule.pipeline import answer


class AnswerTests(TestCase):

    def test_answer_interview(self):
        job_application = models.JobApplication.objects.create(
            candidate_email='candidate@pe.fr',
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
        )
        models.AnswerRejection.objects.create(
            job_application=job_application,
        )
        answer.send(job_application.id)
        answer.send_answer_to_candidate.consume()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual([], mail.outbox[0].reply_to)
