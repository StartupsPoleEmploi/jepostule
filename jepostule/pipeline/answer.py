from django.conf import settings
from django.template.loader import get_template

from jepostule.queue import topics
from .utils import send_mail
from . import models


def send(job_application_id):
    send_answer_to_candidate.run_async(job_application_id)


@topics.subscribe('send-answer')
def send_answer_to_candidate(job_application_id):
    job_application = models.JobApplication.objects.get(id=job_application_id)

    answer = job_application.answer.answerinterview
    subject = "Proposition d'entretien d'embauche - {}".format(
        job_application.employer_description
    )
    message = get_template('jepostule/pipeline/emails/interview.html').render({
        'answer': answer,
    })
    send_mail(subject, message, settings.JEPOSTULE_NO_REPLY,
              [job_application.candidate_email],
              reply_to=[answer.employer_email])
