from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from jepostule.auth import utils as auth_utils
from jepostule.pipeline import application
from .forms import JobApplicationForm


@require_http_methods(["GET", "POST"])
def candidater(request):
    if request.method == 'GET':
        default_message = """Madame, Monsieur,
Vous cherchez sûrement du renfort au sein de votre société. C'est donc tout naturellement que je vous adresse ma candidature.

Je serais très heureux de vous rencontrer afin de vous présenter de vive voix mes motivations à rejoindre votre équipe.

Dans cette attente, je reste à votre disposition pour tout autre complément d'information.
"""
        form_data = request.GET.copy()
        form_data.setdefault('message', default_message)
        form = JobApplicationForm(data=form_data)
    else:
        form = JobApplicationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            job_application = form.save()
            application.send(job_application.id, form.cleaned_data['attachments'])

    return render(request, 'jepostule/embed/candidater.html', {
        'form': form,
    })


def demo(request):
    """
    Demo view to test the embedded application iframe. This requires that a
    demo client id is stored in the settings. Custom from/to addresses can be
    setup by the 'candidate_email' and 'employer_email' querystring parameters.
    """
    client_id = 'democlientid'
    candidate_email = request.GET.get('candidate_email', 'candidat@example.com')
    employer_email = request.GET.get('employer_email', 'employeur@example.com')
    token = auth_utils.make_application_token(client_id, candidate_email, employer_email)
    iframe_url = reverse('embed:candidater') + '?' + urlencode({
        'client_id': client_id,
        'token': token,
        'candidate_email': candidate_email,
        'employer_email': employer_email,
        'job': 'Boucher',
        'coordinates': 'Tel: 0612345678',
        'message': """Bonjour,

Je vous prie de bien vouloir considérer ma candidature dans votre boucherie.

Cordialement,

Ernest Loyal"""
    })
    return render(request, 'jepostule/embed/demo.html', {
        'iframe_url': iframe_url,
    })
