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

    subject = "Proposition d'entretien d'embauche - {}".format(
        job_application.employer_description
    )
    template, context = get_answer_template(job_application.answer)
    message = get_template(template).render(context)

    reply_to = []
    if hasattr(context['answer'], 'employer_email'):
        reply_to.append(context['answer'].employer_email)

    send_mail(subject, message, settings.JEPOSTULE_NO_REPLY,
              [job_application.candidate_email],
              reply_to=reply_to)


def get_answer_template(answer):
    """
    Return:
        template (str)
        context (dict)
    """
    if hasattr(answer, 'answerinterview'):
        template = 'jepostule/pipeline/emails/interview.html'
        obj = answer.answerinterview
    elif hasattr(answer, 'answerrejection'):
        template = 'jepostule/pipeline/emails/rejection.html'
        obj = answer.answerrejection
    elif hasattr(answer, 'answerrequestinfo'):
        template = 'jepostule/pipeline/emails/request_info.html'
        obj = answer.answerrequestinfo
    else:
        raise ValueError('Undefined answer')
    return template, {'answer': obj}
