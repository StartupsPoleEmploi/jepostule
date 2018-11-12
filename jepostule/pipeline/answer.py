from django.conf import settings
from django.template.loader import get_template

from jepostule.queue import topics
from .utils import send_mail
from . import models


TEMPLATES = [
    ('answerinterview', models.JobApplication.ANSWER_INTERVIEW, 'jepostule/pipeline/emails/interview.html'),
    ('answerrejection', models.JobApplication.ANSWER_REJECTION, 'jepostule/pipeline/emails/rejection.html'),
    ('answerrequestinfo', models.JobApplication.ANSWER_REQUEST_INFO, 'jepostule/pipeline/emails/request_info.html'),
]

# TODO create corresponding events


def send(job_application_id):
    send_answer_to_candidate.run_async(job_application_id)


@topics.subscribe('send-answer')
def send_answer_to_candidate(job_application_id):
    job_application = models.JobApplication.objects.get(id=job_application_id)

    subject = get_subject(job_application)
    template, context = get_answer_message_template(job_application.answer)
    message = get_template(template).render(context)

    reply_to = []
    if hasattr(context['answer'], 'employer_email'):
        reply_to.append(context['answer'].employer_email)

    send_mail(subject, message, settings.JEPOSTULE_NO_REPLY,
              [job_application.candidate_email],
              reply_to=reply_to)


def get_answer_message(answer):
    """
    WARNING: answer is an Answer object
    """
    template, context = get_answer_message_template(answer)
    return get_template(template).render(context)


def get_answer_message_template(answer):
    """
    WARNING: answer is an Answer object
    Return:
        template (str)
        context (dict)
    """
    for attr, _, template in TEMPLATES:
        if hasattr(answer, attr):
            return template, {'answer': getattr(answer, attr)}
    raise ValueError('Undefined answer')


def get_answer_message_from_instance(answer):
    for _, answer_type, template in TEMPLATES:
        if answer.answer_type == answer_type:
            return get_template(template).render({'answer': answer})
    raise ValueError('Undefined answer type')


def get_subject(job_application):
    return "Réponse de l'entreprise {}".format(job_application.employer_description)
