from django.conf import settings
from django.template.loader import get_template

from jepostule.queue import topics
from .utils import send_mail
from . import models


TEMPLATES = {
    models.Answer.Types.INTERVIEW: 'jepostule/pipeline/emails/interview.html',
    models.Answer.Types.REJECTION: 'jepostule/pipeline/emails/rejection.html',
    models.Answer.Types.REQUEST_INFO: 'jepostule/pipeline/emails/request_info.html',
}


def send(job_application_id):
    send_answer_to_candidate.run_async(job_application_id)


@topics.subscribe('send-answer')
def send_answer_to_candidate(job_application_id):
    job_application = models.JobApplication.objects.get(id=job_application_id)

    subject = get_subject(job_application)
    template, context = get_answer_message_template(job_application.answer)
    message = get_template(template).render(context)

    reply_to = []
    if hasattr(context['answer_details'], 'employer_email'):
        reply_to.append(context['answer_details'].employer_email)

    send_mail(subject, message, settings.JEPOSTULE_NO_REPLY,
              [job_application.candidate_email],
              reply_to=reply_to)
    job_application.events.create(name=models.JobApplicationEvent.ANSWERED)


def render_answer_email(answer):
    return get_template('jepostule/pipeline/emails/full.html').render({
        'message': render_answer_message(answer),
    })

def render_answer_message(answer):
    """
    Args:
        answer (Answer)
    Return:
        rendered (str)
    """
    return render_answer_details_message(answer.get_details())


def get_answer_message_template(answer):
    """
    Args:
        answer (Answer)
    Return:
        template (str)
        context (dict)
    """
    return get_answer_details_template(answer.get_details())


def render_answer_details_message(answer_details):
    template, context = get_answer_details_template(answer_details)
    return get_template(template).render(context)


def get_answer_details_template(answer_details):
    return TEMPLATES[answer_details.answer_type], {'answer_details': answer_details}


def get_subject(job_application):
    return "Réponse de l'entreprise {}".format(job_application.employer_description)
