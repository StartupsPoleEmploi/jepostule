from django.test import TestCase
from django.utils.timezone import now

from jepostule.pipeline import models
from jepostule.pipeline import answer
from jepostule.queue import topics


class AnswerTests(TestCase):

    def test_answer_interview(self):
        job_application = models.JobApplication.objects.create()
        models.AnswerInterview.objects.create(
            job_application=job_application,
            datetime=now(),
        )
        answer.send(job_application.id)
        topics.consume(answer.send_answer_to_candidate.topic)
