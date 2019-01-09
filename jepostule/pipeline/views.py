import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from jepostule.utils import error_response
from . import events
from . import forms
from . import models
from . import application as application_pipeline
from . import answer as answer_pipeline


logger = logging.getLogger(__name__)


@login_required
def email_application(request, job_application_id):
    job_application = get_object_or_404(models.JobApplication, id=job_application_id)
    return HttpResponse(application_pipeline.render_application_email(job_application).encode())


@login_required
def email_confirmation(request, job_application_id):
    job_application = get_object_or_404(models.JobApplication, id=job_application_id)
    return HttpResponse(application_pipeline.render_confirmation_email(job_application).encode())


@login_required
def email_answer(request, answer_id):
    answer = get_object_or_404(models.Answer, id=answer_id)
    return HttpResponse(answer_pipeline.render_answer_email(answer).encode())


@require_http_methods(['GET', 'POST'])
def send_answer(request, answer_uuid, status, is_preview=False, modify_answer=False):
    job_application = get_object_or_404(models.JobApplication, answer_uuid=answer_uuid)
    if models.Answer.objects.filter(job_application=job_application).exists():
        return already_answered_response(request, job_application.id)

    try:
        FormClass = {
            models.Answer.Types.REJECTION: forms.RejectionForm,
            models.Answer.Types.REQUEST_INFO: forms.RequestInfoForm,
            models.Answer.Types.INTERVIEW: forms.InterviewForm,
        }[status]
    except KeyError:
        raise Http404

    template = None
    context = {
        'job_application': job_application,
        'status': status,
        'answer_uuid': answer_uuid,
    }

    if request.method == 'GET':
        form = FormClass(job_application, initial={
            'employer_email': job_application.employer_email,
        })
        template = form.template
    else:
        form = FormClass(job_application, request.POST)
        if form.is_valid() and not modify_answer:
            if is_preview:
                template = 'jepostule/pipeline/answers/preview.html'
                context.update({
                    'subject': answer_pipeline.get_subject(job_application),
                    'message': answer_pipeline.render_answer_details_message(form.instance),
                })
            else:
                try:
                    result = form.save()
                except IntegrityError:
                    return already_answered_response(request, job_application.id)
                answer_pipeline.send(result.job_application.id)
                template = 'jepostule/pipeline/answers/success.html'
        else:
            template = form.template

    context.update({
        'form': form,
    })
    return render(request, template, context)


def already_answered_response(request, job_application_id):
    job_application = models.JobApplication.objects.get(id=job_application_id)
    return render(request, 'jepostule/pipeline/answers/already_answered.html', {
        'subject': answer_pipeline.get_subject(job_application),
        'message': answer_pipeline.render_answer_message(job_application.answer),
    })


@require_POST
@csrf_exempt
def application_event_callback(request):
    """
    Callback endpoint used by Mailjet to monitor event updates
    https://dev.mailjet.com/guides/#events

    The url given to mailjet should include the EVENT_CALLBACK_SECRET setting.
    """
    if request.GET.get('secret') != settings.EVENT_CALLBACK_SECRET:
        return error_response("Invalid secret", 403)
    if request.content_type != 'application/json':
        return error_response("Invalid content type", 400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response("Invalid json content", 400)
    if not isinstance(data, list):
        return error_response("Expected array in json content", 400)
    for event in data:
        # Note that there is no way to make sure we are not flooded with spam events
        events.log(event)
        if event.get('event') == 'spam':
            # For now, we just log an error because spam events occur quite
            # unfrequently. In the future, if more problems occur, we will need
            # to increment a counter and launch a warning whenever this counter
            # exceeds a threshold.
            logger.error("Email spam alert: %s", event.get('email'))
    return JsonResponse({})
