import logging

from django.conf import settings
from django import forms

from jepostule.auth import utils as auth_utils
from jepostule.pipeline.models import JobApplication, Email
from jepostule.security import blacklist


logger = logging.getLogger(__name__)

class BlacklistForm(forms.Form):

    candidate_email = forms.EmailField()
    employer_email = forms.EmailField()

    def clean_candidate_email(self):
        details = blacklist.details(self.cleaned_data['candidate_email'])
        if details.is_blacklisted:
            message = "La raison du problème est malheureusement inconnue :-("
            if details.reason == Email.SPAM:
                message = (
                    "Votre hébergeur de mail considère nos messages "
                    "comme des spams. Nous ne pouvons donc vous contacter "
                    "par email. Si vous pensez qu'il s'agit d'une erreur, "
                    "veuillez contacter votre hébergeur de mail directement. "
                )
            elif details.reason == Email.BLOCKED:
                message = (
                    "Nos messages sont bloqués et ne peuvent pas vous être "
                    "délivrés. Le problème peut venir d'une adresse email "
                    "incorrecte ou d'une boite email pleine."
                )
            else:
                logger.error("Unknown blacklisting reason: %s", details.reason)
            raise forms.ValidationError(message)
        return self.cleaned_data['candidate_email']

    def clean_employer_email(self):
        details = blacklist.details(self.cleaned_data['employer_email'])
        if details.is_blacklisted:
            raise forms.ValidationError(
                "Les emails que nous essayons d'envoyer à cette entreprise ne"
                "sont pas correctement reçus, pour des raisons indépendantes de"
                "notre volonté :-( Nous ne pouvons donc pas envoyer de"
                "candidature de votre part."
            )
        return self.cleaned_data['employer_email']


class JobApplicationPartialForm(forms.ModelForm):
    """
    This form is a bit special: because form-filling happens in multiple
    steps, we need to manually edit the fields with client-side code.
    """

    class Meta:
        model = JobApplication
        fields = (
            'candidate_email',
            'candidate_first_name',
            'candidate_last_name',
            'candidate_peid',
            'candidate_rome_code',
            'candidate_peam_access_token',
            'employer_email',
            'employer_description',
            'siret',
            'message',
        )
        # All widgets are either read-only or hidden
        widgets = {
            'candidate_email': forms.EmailInput(attrs={'readonly': True}),
            'candidate_first_name': forms.HiddenInput(),
            'candidate_last_name': forms.HiddenInput(),
            'candidate_peid': forms.HiddenInput(),
            'candidate_rome_code': forms.HiddenInput(),
            'candidate_peam_access_token': forms.HiddenInput(),
            'employer_email': forms.EmailInput(attrs={'readonly': True}),
            'employer_description': forms.TextInput(attrs={'readonly': True}),
            'siret': forms.HiddenInput(),
            'message': forms.Textarea(attrs={'readonly': True}),
        }

    client_id = forms.CharField(
        widget=forms.HiddenInput()
    )
    token = forms.CharField(
        widget=forms.HiddenInput()
    )
    timestamp = forms.FloatField(
        widget=forms.HiddenInput()
    )

    def clean(self):
        """
        Perform client ID/token validation.
        """
        cleaned_data = super().clean()
        try:
            auth_utils.verify_application_token(**cleaned_data)
            self.instance.client_platform = auth_utils.get_client_platform(cleaned_data['client_id'])
        except auth_utils.exceptions.AuthError as e:
            raise forms.ValidationError(e.message)
        return cleaned_data


class JobApplicationForm(JobApplicationPartialForm):
    SEND_CONFIRMATION_EMAIL_DEFAULT = False
    defaults = {
        'message': """Bonjour,

Votre entreprise suscite tout mon intérêt ; c'est pourquoi je me permets aujourd'hui de vous transmettre ma candidature spontanée.

C'est avec plaisir que je vous rencontrerai lors d'un entretien afin de vous présenter de vive voix mes motivations à rejoindre votre équipe.

Dans l'attente de votre retour, je reste à votre écoute pour tout complément d'information.
""",
        'send_confirmation': SEND_CONFIRMATION_EMAIL_DEFAULT,
    }

    class Meta(JobApplicationPartialForm.Meta):
        model = JobApplication
        fields = JobApplicationPartialForm.Meta.fields + (
            'job',
            'candidate_phone',
            'candidate_address',
            'send_confirmation',
        )
        JobApplicationPartialForm.Meta.widgets.update({
            'job': forms.TextInput(attrs={'readonly': True}),
            'candidate_phone': forms.TextInput(attrs={'readonly': True}),
            'candidate_address': forms.TextInput(attrs={'readonly': True}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, label_suffix='', **kwargs)

    send_confirmation = forms.BooleanField(
        label="Je souhaite recevoir une copie de ma candidature sur ma boite mail",
        initial=SEND_CONFIRMATION_EMAIL_DEFAULT,
        required=False,
    )
    next_url = forms.URLField(
        widget=forms.HiddenInput(),
        required=False,
    )


class MultipleFileInput(forms.FileInput):
    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class AttachmentsField(forms.FileField):
    widget = MultipleFileInput

    def to_python(self, data):
        attachments = []
        data = data or []
        for d in data:
            attachment = super().to_python(d)
            if attachment:
                attachments.append(attachment)
        return attachments

    def validate(self, value):
        """
        Check that attachments total size is equal or less than setting.
        """
        super().validate(value)
        total_size = 0
        for attachment in value:
            total_size += attachment.size
            if total_size > settings.ATTACHMENTS_MAX_SIZE_BYTES:
                max_size_mb = settings.ATTACHMENTS_MAX_SIZE_BYTES // (1024 * 1024)
                message = "Pièces jointes trop grosses. La taille maximale autorisée est de %(max_size_mb)s Mo"
                raise forms.ValidationError(message, params={'max_size_mb': max_size_mb})


class AttachmentsForm(forms.Form):
    attachments = AttachmentsField(
        label="Joignez des documents à votre candidature : CV, lettre de motivation...",
        required=False,
    )
