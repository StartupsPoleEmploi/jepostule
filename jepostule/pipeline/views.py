from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, Http404
from django.views.decorators.http import require_http_methods

from . import forms
from . import models
from .answer import send as send_answer


@login_required
def email_application(request, job_application_id):
    job_application = get_object_or_404(models.JobApplication, id=job_application_id)
    return render(request, 'jepostule/pipeline/emails/application.html', {
        'job_application': job_application,
    })


@login_required
def email_confirmation(request, job_application_id):
    job_application = get_object_or_404(models.JobApplication, id=job_application_id)
    return render(request, 'jepostule/pipeline/emails/confirmation.html', {
        'job_application': job_application,
    })


@login_required
def email_answer(request, answer_id):
    return render(request, 'jepostule/pipeline/emails/interview.html', {
        'answer': get_object_or_404(models.Answer, id=answer_id).answerinterview,
    })


@require_http_methods(['GET', 'POST'])
def answer(request, answer_uuid, status):
    job_application = get_object_or_404(models.JobApplication, answer_uuid=answer_uuid)
    if status == models.JobApplication.ANSWER_INTERVIEW:
        FormClass = forms.InterviewForm
        template = 'jepostule/pipeline/answers/interview.html'
    else:
        raise Http404

    # TODO employer needs to previsualize the message sent

    if request.method == 'GET':
        # TODO check if answer was already provided
        form = FormClass(job_application, initial={
            'employer_email': job_application.employer_email,
        })
    else:
        form = FormClass(job_application, request.POST)
        if form.is_valid():
            result = form.save()
            send_answer(result.job_application.id)
            template = 'jepostule/pipeline/answers/success.html'

    return render(request, template, {
        'job_application': job_application,
        'form': form,
    })
