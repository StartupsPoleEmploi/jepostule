from urllib.parse import urlencode

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from jepostule.auth import utils as auth_utils
from jepostule.pipeline import application
from .import forms


@require_http_methods(["GET", "POST"])
def candidater(request):
    if request.method == 'GET':
        form_data = request.GET.copy()
        for k, v in forms.JobApplicationForm.defaults.items():
            form_data.setdefault(k, v)
        partial_form = forms.JobApplicationPartialForm(data=form_data)
        if not partial_form.is_valid():
            return render(request, 'jepostule/embed/candidater_invalid.html', {
                'form': partial_form,
            })
        form = forms.JobApplicationForm(data=form_data)
        form.is_valid()
    else:
        form = forms.JobApplicationForm(data=request.POST)
        attachments_form = forms.AttachmentsForm(files=request.FILES)
        if form.is_valid():
            if attachments_form.is_valid():
                job_application = form.save()
                application.send(job_application.id,
                                 attachments_form.cleaned_data['attachments'])
                return render(request, 'jepostule/embed/candidater_success.html')
                # TODO redirect to summary page
                # TODO in case of attachments error, re-display form
                # TODO in case of send error, display 500 error

    return render(request, 'jepostule/embed/candidater.html', {
        'form': form,
    })


@csrf_exempt
@require_http_methods(["POST"])
def validate(request):
    errors = {}
    form = forms.JobApplicationForm()
    for name, value in request.POST.items():
        try:
            error = form.validate_field(name, value)
        except KeyError:
            error = "Unknown field"
        if error is not None:
            errors[name] = error
    return JsonResponse({
        "errors": errors,
    })


def demo(request):
    """
    Demo view to test the embedded application iframe. This requires that a
    demo client id is stored in the settings. Custom from/to addresses can be
    setup by the 'candidate_email' and 'employer_email' querystring parameters.
    """
    client_id = 'democlientid'
    params = {
        'candidate_first_name': 'John',
        'candidate_last_name': 'Doe',
        'candidate_email': 'candidat@example.com',
        'employer_email': 'employeur@example.com',
        'employer_description': """Uniqlo Europe LTD - 75009 Paris""",
        'job': 'Boucher',
    }
    params.update(request.GET)
    token = auth_utils.make_application_token(client_id, params['candidate_email'], params['employer_email'])
    params.update({
        'client_id': client_id,
        'token': token,
    })
    iframe_url = reverse('embed:candidater') + '?' + urlencode(params)
    return render(request, 'jepostule/embed/demo.html', {
        'iframe_url': iframe_url,
    })
