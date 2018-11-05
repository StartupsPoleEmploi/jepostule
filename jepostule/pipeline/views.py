from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, Http404
from django.views.decorators.http import require_http_methods

from . import forms
from . import models


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


@require_http_methods(['GET', 'POST'])
def answer(request, answer_uuid, status):
    job_application = get_object_or_404(models.JobApplication, answer_uuid=answer_uuid)
    if status == models.JobApplication.ANSWER_INTERVIEW:
        FormClass = forms.InterviewForm
        template = 'jepostule/pipeline/answers/interview.html'
    else:
        raise Http404

    if request.method == 'GET':
        # TODO check if answer was already provided
        form = FormClass(initial={
            'employer_email': job_application.employer_email,
        })
    else:
        form = FormClass(request.POST)
        if form.is_valid():
            template = 'jepostule/pipeline/answers/success.html'

    return render(request, template, {
        'job_application': job_application,
        'form': form,
    })
