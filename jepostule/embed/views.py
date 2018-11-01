from urllib.parse import urlencode

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from jepostule.auth import utils as auth_utils
from jepostule.pipeline import application
from .import forms


@csrf_exempt
@require_http_methods(["GET", "POST"])
def candidater(request):
    response = get_candidater(request) if request.method == 'GET' else post_candidater(request)
    response['X-Frame-Options'] = "allow-from http://localhost:5000"
    return response


def get_candidater(request):
    form_data = request.GET.copy()
    for k, v in forms.JobApplicationForm.defaults.items():
        form_data.setdefault(k, v)
    form = forms.JobApplicationForm(data=form_data)
    # At this point, the form is probably not valid because we need some
    # additional information from the user, but that's ok. We just need to
    # run is_valid() in order to access the cleaned_data attribute in the
    # template.
    form.is_valid()
    form_errors = forms.JobApplicationPartialForm(data=form_data).errors
    attachments_form = forms.AttachmentsForm()
    return render(request, 'jepostule/embed/candidater.html', {
        'form': form,
        'form_errors': form_errors,
        'attachments_form': attachments_form,
    })


def post_candidater(request):
    form = forms.JobApplicationForm(data=request.POST)
    attachments_form = forms.AttachmentsForm(files=request.FILES)
    if form.is_valid() and attachments_form.is_valid():
        job_application = form.save()
        attachments = [
            application.Attachment(name=f.name, content=f.read())
            for f in attachments_form.cleaned_data['attachments']
        ]
        # TODO in case of send error, display 500 error
        application.send(job_application.id, attachments)
        return render(request, 'jepostule/embed/candidater_success.html')
    return render(request, 'jepostule/embed/candidater_invalid.html', {
        'form': form,
        'attachments_form': attachments_form,
    })



@csrf_exempt
@require_http_methods(["POST"])
def validate(request):
    form = forms.JobApplicationForm(request.POST)
    return JsonResponse({
        "errors": form.errors,
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
        'siret': '73345678900023',
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
