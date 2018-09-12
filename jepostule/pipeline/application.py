from django.conf import settings
from django.core import mail

from jepostule.queue import topics
from .models import JobApplication, JobApplicationEvent
from . import ratelimits


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
    job_application = JobApplication.objects.get(id=job_application_id)
    topics.delay(ratelimits.Sender.delay(job_application.candidate_email))

    # TODO Fix subject and use message template
    subject = "Candidature spontanée au poste de {}".format(job_application.job)
    send_mail(subject, job_application.message,
              settings.JEPOSTULE_NO_REPLY, [job_application.employer_email],
              reply_to=[job_application.candidate_email],
              attachments=attachments)
    job_application.events.create(name=JobApplicationEvent.NAME_SENT_TO_EMPLOYER)
    ratelimits.Sender.add(job_application.candidate_email)
    send_confirmation_to_candidate.run_async(job_application_id)


@topics.subscribe('send-confirmation')
def send_confirmation_to_candidate(job_application_id):
    job_application = JobApplication.objects.get(id=job_application_id)
    # TODO Fix subject and use message template
    # TODO remove useless arguments
    subject = "Votre candidature a bien été envoyée"
    message = "Votre message ci-dessous"
    send_mail(subject, message, settings.JEPOSTULE_NO_REPLY, [job_application.candidate_email])
    job_application.events.create(name=JobApplicationEvent.NAME_CONFIRMED_TO_CANDIDATE)


# pylint: disable=too-many-arguments
def send_mail(subject, message, from_email, recipient_list,
              reply_to=None, attachments=None, html_message=None):
    """
    We don't rely on django.core.mail.send_mail function, because it does not
    let us override the 'reply-to' field.

    Note that `reply_to` must be a list or tuple.
    """
    connection = mail.get_connection()
    message = mail.EmailMultiAlternatives(
        subject, message, from_email, recipient_list,
        connection=connection,
        reply_to=reply_to,
        attachments=attachments,
    )
    if html_message:
        message.attach_alternative(html_message, 'text/html')

    return message.send()
