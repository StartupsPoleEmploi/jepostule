from urllib.parse import urlencode

from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from jepostule.auth import utils as auth_utils
from jepostule.auth.models import ClientPlatform
from jepostule.pipeline import application
from .import forms


@csrf_exempt
@require_http_methods(["GET", "POST"])
def candidater(request):
    response = get_candidater(request) if request.method == 'GET' else post_candidater(request)
    response.xframe_options_exempt = True
    return response


def get_candidater(request):
    """
    Generate application form and display it.
    """
    form_data = request.GET.copy()
    blacklist_form = forms.BlacklistForm(data=form_data)
    if not blacklist_form.is_valid():
        return render(request, 'jepostule/embed/security.html', {
            'form': blacklist_form,
        })
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
    show_employer_email = form.cleaned_data.get('employer_email') and form.cleaned_data.get('employer_description')
    return render(request, 'jepostule/embed/candidater.html', {
        'form': form,
        'form_errors': form_errors,
        'attachments_form': attachments_form,
        'platform_name': form.instance.platform_attribute('name'),
        'show_employer_email': show_employer_email,
    })


def post_candidater(request):
    """
    Validate application form and save it.
    """
    form = forms.JobApplicationForm(data=request.POST)
    attachments_form = forms.AttachmentsForm(files=request.FILES)
    if form.is_valid() and attachments_form.is_valid():
        job_application = form.save()
        attachments = [
            application.Attachment(name=f.name, content=f.read())
            for f in attachments_form.cleaned_data['attachments']
        ]
        application.send(job_application.id, attachments, send_confirmation=form.cleaned_data['send_confirmation'])
        return render(request, 'jepostule/embed/candidater_success.html', {
            'next_url': form.cleaned_data['next_url'],
        })
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
    Demo view to test the embedded application iframe. This requires either that:
    - a demo client id is stored in the settings.
    - or client_id/client_secret are passed (in clear) as GET parameters

    Custom parameters can also be set in the querystring.
    """
    client_id = request.GET.get('client_id')
    client_secret = request.GET.get('client_secret')
    
    if client_id and client_secret:
        try:
            auth_utils.verify_client_secret(client_id, client_secret)
        except auth_utils.exceptions.AuthError:
            raise Http404
    else:
        client_id = get_object_or_404(ClientPlatform, client_id=ClientPlatform.DEMO_CLIENT_ID).client_id
    
    params = {
        'client_id': client_id,
        'candidate_first_name': 'John',
        'candidate_last_name': 'Doe',
        'candidate_email': 'candidat@example.com',
        'candidate_peid': '123456789',
        'candidate_rome_code': 'A1101',
        'candidate_peam_access_token': None,  # demo applications should not be forwarded to AMI.
        'employer_email': 'employeur@example.com',
        'employer_description': """Uniqlo Europe LTD - 75009 Paris""",
        'siret': '34326262220717',
        'job': 'Boucher',
        'next_url': 'https://example.com?plonk=pfiuut',
    }
    params.update(request.GET.items())
    
    token, timestamp = auth_utils.make_new_application_token(**params)
    params.update({
        'token': token,
        'timestamp': timestamp,
    })
    
    iframe_url = reverse('embed:candidater') + '?' + urlencode(params)
    return render(request, 'jepostule/embed/demo.html', {
        'iframe_url': iframe_url,
    })
