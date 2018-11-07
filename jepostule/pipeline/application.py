from collections import namedtuple

from django.conf import settings
from django.template.loader import get_template

from jepostule.queue import topics
from .models import JobApplication, JobApplicationEvent
from . import ratelimits
from .utils import send_mail


Attachment = namedtuple('Attachment', ['name', 'content'])

def send(job_application_id, attachments=None):
    """
    Entrypoint for the job application pipeline.

    Args:
        job_application_id (int): id of a JobApplication entry
        attachments (list of file-like objects)
    """
    send_application_to_employer.run_async(job_application_id, attachments=attachments)


@topics.subscribe('send-application')
def send_application_to_employer(job_application_id, attachments=None):
    """
    Args:
        job_application_id (int): id of a JobApplication entry
        attachments (list of Attachment objects)
    """
    job_application = JobApplication.objects.get(id=job_application_id)
    topics.delay(ratelimits.Sender.delay(job_application.candidate_email))

    subject = "Candidature spontanée - {}".format(
        job_application.job,
    )
    message = get_template('jepostule/pipeline/emails/application.html').render({
        'job_application': job_application
    })
    send_mail(subject, message,
              settings.JEPOSTULE_NO_REPLY, [job_application.employer_email],
              reply_to=[job_application.candidate_email],
              attachments=attachments)
    job_application.events.create(name=JobApplicationEvent.SENT_TO_EMPLOYER)
    ratelimits.Sender.add(job_application.candidate_email)
    send_confirmation_to_candidate.run_async(job_application_id)


@topics.subscribe('send-confirmation')
def send_confirmation_to_candidate(job_application_id):
    """
    Args:
        job_application_id (int): id of a JobApplication entry
        attachments (list of Attachment objects)
    """
    job_application = JobApplication.objects.get(id=job_application_id)
    # TODO fix subject
    subject = "Votre candidature a bien été envoyée"
    message = get_template('jepostule/pipeline/emails/confirmation.html').render({
        'job_application': job_application
    })
    send_mail(subject, message, settings.JEPOSTULE_NO_REPLY, [job_application.candidate_email])
    job_application.events.create(name=JobApplicationEvent.CONFIRMED_TO_CANDIDATE)
