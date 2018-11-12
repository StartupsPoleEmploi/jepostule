from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, Http404
from django.views.decorators.http import require_http_methods

from . import forms
from . import models
from . import application as application_pipeline
from . import answer as answer_pipeline


@login_required
def email_application(request, job_application_id):
    job_application = get_object_or_404(models.JobApplication, id=job_application_id)
    return view_email_response(request, application_pipeline.get_application_message(job_application))


@login_required
def email_confirmation(request, job_application_id):
    job_application = get_object_or_404(models.JobApplication, id=job_application_id)
    return view_email_response(request, application_pipeline.get_confirmation_message(job_application))


@login_required
def email_answer(request, answer_id):
    answer = get_object_or_404(models.Answer, id=answer_id)
    message = answer_pipeline.get_answer_message(answer)
    return view_email_response(request, message)


def view_email_response(request, message):
    return render(request, 'jepostule/pipeline/emails/full.html', {
        'message': message,
    })


@require_http_methods(['GET', 'POST'])
def send_answer(request, answer_uuid, status, is_preview=False, modify_answer=False):
    job_application = get_object_or_404(models.JobApplication, answer_uuid=answer_uuid)
    if models.Answer.objects.filter(job_application=job_application).exists():
        answer = models.Answer.objects.get(job_application=job_application)
        return render(request, 'jepostule/pipeline/answers/already_answered.html', {
            'subject': answer_pipeline.get_subject(job_application),
            'message': answer_pipeline.get_answer_message(answer),
        })

    try:
        FormClass = {
            models.JobApplication.ANSWER_REJECTION: forms.RejectionForm,
            models.JobApplication.ANSWER_REQUEST_INFO: forms.RequestInfoForm,
            models.JobApplication.ANSWER_INTERVIEW: forms.InterviewForm,
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
                    'message': answer_pipeline.get_answer_message_from_instance(form.instance),
                })
            else:
                result = form.save()
                answer_pipeline.send(result.job_application.id)
                template = 'jepostule/pipeline/answers/success.html'
        else:
            template = form.template

    context.update({
        'form': form,
    })
    return render(request, template, context)
