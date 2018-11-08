from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, Http404
from django.views.decorators.http import require_http_methods

from . import forms
from . import models
from . import answer as answer_pipeline


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
    answer = get_object_or_404(models.Answer, id=answer_id)
    template, context = answer_pipeline.get_answer_template(answer)
    return render(request, template, context)


@require_http_methods(['GET', 'POST'])
def send_answer(request, answer_uuid, status):
    job_application = get_object_or_404(models.JobApplication, answer_uuid=answer_uuid)
    if models.Answer.objects.filter(job_application=job_application).exists():
        return render(request, 'jepostule/pipeline/answers/already_answered.html')

    try:
        FormClass = {
            models.JobApplication.ANSWER_REJECTION: forms.RejectionForm,
            models.JobApplication.ANSWER_REQUEST_INFO: forms.RequestInfoForm,
            models.JobApplication.ANSWER_INTERVIEW: forms.InterviewForm,
        }[status]
    except KeyError:
        raise Http404

    # TODO employer needs to previsualize the message sent
    if request.method == 'GET':
        form = FormClass(job_application, initial={
            'employer_email': job_application.employer_email,
        })
    else:
        form = FormClass(job_application, request.POST)
        if form.is_valid():
            result = form.save()
            answer_pipeline.send(result.job_application.id)
            return render(request, 'jepostule/pipeline/answers/success.html', {
                'form': form,
            })

    return render(request, form.template, {
        'job_application': job_application,
        'form': form,
    })
