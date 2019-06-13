from collections import namedtuple

from django.conf import settings
from django.template.loader import get_template

from jepostule.email.utils import send_mail
from jepostule.queue import topics
from jepostule.security import ratelimits
from . import models, memo


Attachment = namedtuple('Attachment', ['name', 'content'])

def send(job_application_id, attachments=None, send_confirmation=True):
    """
    Entrypoint for the job application pipeline.

    Args:
        job_application_id (int): id of a JobApplication entry
        attachments (list of file-like objects)
        send_confirmation (bool)
    """
    send_application_to_employer.run_async(
        job_application_id, attachments=attachments,
        send_confirmation=send_confirmation
    )


@topics.subscribe(topics.SEND_APPLICATION)
def send_application_to_employer(job_application_id, attachments=None, send_confirmation=True):
    """
    Args:
        job_application_id (int): id of a JobApplication entry
        attachments (list of Attachment objects)
        send_confirmation (bool)
    """
    job_application = models.JobApplication.objects.get(id=job_application_id)
    topics.delay(ratelimits.Sender.delay(job_application.candidate_email))

    subject = "Candidature spontanée - {}".format(
        job_application.job,
    )
    from_email = job_application.platform_attribute('contact_email')  # The sender email should be validated in Mailjet.
    message_id = send_mail(
        subject, render_application_email(job_application),
        from_email, [job_application.employer_email],
        from_name=job_application.candidate_name,
        reply_to=[job_application.candidate_email],
        attachments=attachments
    )
    event = job_application.events.create(
        name=models.JobApplicationEvent.SENT_TO_EMPLOYER,
    )
    models.Email.objects.create(
        event=event,
        message_id=message_id[0],
        status=models.Email.SENT,
    )
    ratelimits.Sender.add(job_application.candidate_email)

    forward_application_to_memo.run_async(job_application_id)
    if send_confirmation:
        send_confirmation_to_candidate.run_async(job_application_id)


@topics.subscribe(topics.FORWARD_TO_MEMO)
def forward_application_to_memo(job_application_id):
    """
    Args:
        job_application_id (int): id of a JobApplication entry
    """
    job_application = models.JobApplication.objects.get(id=job_application_id)
    memo.forward_job_application(job_application_id)
    event = job_application.events.create(
        name=models.JobApplicationEvent.FORWARDED_TO_MEMO,
    )


@topics.subscribe(topics.SEND_CONFIRMATION)
def send_confirmation_to_candidate(job_application_id):
    """
    Args:
        job_application_id (int): id of a JobApplication entry
        attachments (list of Attachment objects)
    """
    job_application = models.JobApplication.objects.get(id=job_application_id)
    subject = "Votre candidature a bien été envoyée"
    from_email = job_application.platform_attribute('contact_email')
    message = get_template('jepostule/pipeline/emails/full.html').render({
        'message': render_confirmation_message(job_application),
    })
    message_id = send_mail(
        subject, message, from_email, [job_application.candidate_email],
        from_name=job_application.platform_attribute('name')
    )
    event = job_application.events.create(
        name=models.JobApplicationEvent.CONFIRMED_TO_CANDIDATE,
    )
    models.Email.objects.create(
        event=event,
        message_id=message_id[0],
        status=models.Email.SENT,
    )


def render_application_email(job_application):
    footer = get_template('jepostule/pipeline/emails/footer.html').render({
        'jepostule_base_url': settings.JEPOSTULE_BASE_URL,
    })
    return get_template('jepostule/pipeline/emails/full.html').render({
        'message': render_application_message(job_application),
        'footer': footer,
    })


def render_application_message(job_application):
    return get_template('jepostule/pipeline/emails/application.html').render({
        'job_application': job_application,
        'jepostule_base_url': settings.JEPOSTULE_BASE_URL,
    })


def render_confirmation_email(job_application):
    return get_template('jepostule/pipeline/emails/full.html').render({
        'message': render_confirmation_message(job_application),
    })


def render_confirmation_message(job_application):
    return get_template('jepostule/pipeline/emails/confirmation.html').render({
        'job_application': job_application
    })
