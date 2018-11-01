from django.conf import settings
from django import forms

from jepostule.auth import utils as auth_utils
from jepostule.pipeline.models import JobApplication



class JobApplicationPartialForm(forms.ModelForm):
    """
    This form is a bit special: because form-filling happens in multiple
    steps, we need to manually edit the fields with client-side code.
    """

    defaults = {
        "message": """Bonjour,
Votre entreprise suscite tout mon intérêt ; c'est pourquoi je me permets aujourd'hui de vous transmettre ma candidature spontanée.

C'est avec plaisir que je vous rencontrerai lors d'un entretien afin de vous présenter de vive voix mes motivations à rejoindre votre équipe.

Dans l'attente de votre retour, je reste à votre écoute pour tout complément d'information.
"""
    }

    class Meta:
        model = JobApplication
        fields = (
            'candidate_email',
            'candidate_first_name',
            'candidate_last_name',
            'employer_email',
            'employer_description',
            'job',
            'siret',
            'message',
        )
        # All widgets are either read-only or hidden
        widgets = {
            'candidate_email': forms.EmailInput(attrs={'readonly': True}),
            'candidate_first_name': forms.HiddenInput(),
            'candidate_last_name': forms.HiddenInput(),
            'employer_email': forms.EmailInput(attrs={'readonly': True}),
            'employer_description': forms.TextInput(attrs={'readonly': True}),
            'job': forms.TextInput(attrs={'readonly': True}),
            'siret': forms.HiddenInput(),
            # TODO add min_length=100 validation on message?
            'message': forms.Textarea(attrs={'readonly': True}),
        }

    client_id = forms.CharField(
        widget=forms.HiddenInput()
    )
    token = forms.CharField(
        widget=forms.HiddenInput()
    )
    # TODO effectively send application copy to candidate
    receive_copy = forms.BooleanField(
        label="Je souhaite recevoir une copie de ma candidature sur ma boite email",
        initial=True,
        required=False,
    )

    def clean(self):
        """
        Perform client ID/token validation.
        """
        cleaned_data = super().clean()
        try:
            auth_utils.verify_application_token(
                cleaned_data.get('client_id'),
                cleaned_data.get('token'),
                cleaned_data.get('candidate_email'),
                cleaned_data.get('employer_email'),
            )
        except auth_utils.exceptions.ApplicationAuthError:
            raise forms.ValidationError("Jeton d'authentification invalide")
        return cleaned_data


class JobApplicationForm(JobApplicationPartialForm):
    class Meta:
        model = JobApplication
        fields = tuple(list(JobApplicationPartialForm.Meta.fields) + [
            'candidate_phone', 'candidate_address',
        ])
        widgets = JobApplicationPartialForm.Meta.widgets.copy()
        widgets.update({
            'candidate_phone': forms.TextInput(attrs={'readonly': True}),
            'candidate_address': forms.TextInput(attrs={'readonly': True}),
        })


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
                max_size_mb = settings.ATTACHMENTS_MAX_SIZE_BYTES // (1024*1024)
                message = "Pièces jointes trop grosses. La taille maximale autorisée est de %(max_size_mb)s Mo"
                raise forms.ValidationError(message, params={'max_size_mb': max_size_mb})



class AttachmentsForm(forms.Form):
    attachments = AttachmentsField(
        label="Joignez des documents à votre candidature : CV, lettre de motivation...",
        required=False,
    )
