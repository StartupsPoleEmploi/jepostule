from collections import namedtuple

from django.conf import settings
from django.template.loader import get_template

from jepostule.email.utils import send_mail
from jepostule.queue import topics
from jepostule.security import ratelimits
from . import models, memo, ami


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

    from_email = job_application.platform_attribute('contact_email')

    # Actually send or not a real email to the employer depending on the platform
    # - lbb - yes (production and local dev)
    # - demo - yes (local dev - so that we can test the whole flow using our backdoor links)
    # - test - yes (production - so that we can test the whole flow using our backdoor links)
    # - lbb-staging - no (applications coming from LBB staging into production JePostule should not send emails to employers for real)
    # - id - yes (test environment)
    if job_application.client_platform.client_id in ['lbb-staging']:
        message_id = None
    elif job_application.client_platform.client_id in ['lbb', 'demo', 'test', 'id']:
        message_id = send_mail(
            f"Candidature spontanée - {job_application.job}",
            render_application_email(job_application),
            from_email,
            [job_application.employer_email],
            from_name=job_application.candidate_name,
            reply_to=job_application.candidate_email,
            attachments=attachments,
            mailjet_template_id=settings.MAILJET_TEMPLATES['SEND_APPLICATION_TO_EMPLOYER'],
            mailjet_template_data=job_application.get_email_template_data(),
            monitoring_category=topics.SEND_APPLICATION,
        )[0]
    else:
        raise ValueError('Unknown client_id.')
    
    event = job_application.events.create(
        name=models.JobApplicationEvent.SENT_TO_EMPLOYER,
    )
    models.Email.objects.create(
        event=event,
        message_id=message_id,
        status=models.Email.SENT,
    )
    ratelimits.Sender.add(job_application.candidate_email)

    forward_application_to_memo.run_async(job_application_id)
    
    # Actually forward or not the application to AMI API for real depending on the platform.
    # - lbb - yes (production and local dev)
    # - demo - no (local dev backdoor links)
    # - test - no (production backdoor links)
    # - lbb-staging - yes (applications coming from LBB staging into production JePostule)
    # - id - yes (test environment)
    if job_application.client_platform.client_id in ['demo', 'test']:
        pass
    elif job_application.client_platform.client_id in ['lbb', 'lbb-staging', 'id']:
        if job_application.candidate_peam_access_token:
            forward_application_to_ami.run_async(job_application_id)
    else:
        raise ValueError('Unknown client_id.')

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


@topics.subscribe(topics.FORWARD_TO_AMI)
def forward_application_to_ami(job_application_id):
    """
    Args:
        job_application_id (int): id of a JobApplication entry
    """
    job_application = models.JobApplication.objects.get(id=job_application_id)
    ami.forward_job_application(job_application_id)
    event = job_application.events.create(
        name=models.JobApplicationEvent.FORWARDED_TO_AMI,
    )


@topics.subscribe(topics.SEND_CONFIRMATION)
def send_confirmation_to_candidate(job_application_id):
    """
    Args:
        job_application_id (int): id of a JobApplication entry
        attachments (list of Attachment objects)
    """
    job_application = models.JobApplication.objects.get(id=job_application_id)
    from_email = job_application.platform_attribute('contact_email')
    message_id = send_mail(
        "Votre candidature a bien été envoyée",
        render_confirmation_email(job_application),
        from_email,
        [job_application.candidate_email],
        from_name=job_application.platform_attribute('name'),
        monitoring_category=topics.SEND_CONFIRMATION,
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
    return get_template('jepostule/pipeline/emails/application.html').render({
        'data': job_application.get_email_template_data(),
        'display_footer': True,
        'jepostule_base_url': settings.JEPOSTULE_BASE_URL,
    })


def render_confirmation_email(job_application):
    return get_template('jepostule/pipeline/emails/application_confirmation.html').render({
        'data': job_application.get_email_template_data(),
        'display_footer': False,
        'jepostule_base_url': settings.JEPOSTULE_BASE_URL,
    })
