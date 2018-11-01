from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

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
