from django.conf import settings
from django import forms

from jepostule.auth import utils as auth_utils
from jepostule.pipeline.models import JobApplication



class AttachmentsInput(forms.FileInput):
    template_name = 'jepostule/embed/forms/widgets/attachments.html'
    class Media:
        js = ('js/attachments.js',)


class AttachmentsField(forms.FileField):
    widget = AttachmentsInput

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



class JobApplicationForm(forms.ModelForm):
    class Meta:
        # TODO min length for message? We can add one with a simple validator
        model = JobApplication
        fields = ('candidate_email', 'employer_email', 'job', 'message', 'coordinates')
        labels = {
            'candidate_email': "De :",
            'employer_email': "À :",
            'job': "Poste :",
            'message': "Votre message :",
            'coordinates': "Vos coordonnées :",
        }
        widgets = {
            'candidate_email': forms.EmailInput(attrs={'readonly': True}),
            'employer_email': forms.EmailInput(attrs={'readonly': True}),
            'message': forms.Textarea(),
            'coordinates': forms.Textarea(attrs={'rows': 4}),
        }

    attachments = AttachmentsField(
        label="Joignez des documents à votre candidature : CV, lettre de motivation...",
        required=False,
        widget=AttachmentsInput(attrs={
            'multiple': True,
            'accept': (
                "video/*,image/*,application/pdf,"
                "application/msword,application/vnd.ms-excel,application/vnd.ms-powerpoint,"
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        })
    )

    client_id = forms.CharField(
        widget=forms.HiddenInput()
    )
    token = forms.CharField(
        widget=forms.HiddenInput()
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
