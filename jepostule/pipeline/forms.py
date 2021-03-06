from django import forms
from django.utils.timezone import now

from . import models


class BaseAnswerForm(forms.ModelForm):
    title = ""
    success_message = "Votre réponse a été envoyée avec succès"
    event_label = "undefined"

    def __init__(self, job_application, *args, **kwargs):
        super().__init__(*args, label_suffix='', **kwargs)
        self.instance.job_application = job_application


class MessageWidget(forms.Textarea):
    template_name = 'jepostule/pipeline/emails/widgets/message.html'


class RejectionForm(BaseAnswerForm):
    title = "Refuser la candidature"
    template = 'jepostule/pipeline/answers/rejection.html'
    event_label = "refus"

    class Meta:
        model = models.AnswerRejection
        fields = ('reason',)
        widgets = {
            'reason': forms.RadioSelect(attrs={
                'class': 'bold'
            }),
        }
        labels = {
            'reason': "Précisez le motif",
        }


class RequestInfoForm(BaseAnswerForm):
    title = "Demander des informations complémentaires"
    template = 'jepostule/pipeline/answers/request_info.html'
    event_label = "informations"

    class Meta:
        model = models.AnswerRequestInfo
        fields = (
            'message',
            'employer_name', 'employer_email', 'employer_phone', 'employer_address',
        )
        widgets = {
            'location': forms.RadioSelect(),
            'employer_name': forms.TextInput(attrs={
                'data-localstorage': '',
            }),
            'employer_phone': forms.TextInput(attrs={
                'placeholder': '01 23 45 67 89',
                'data-localstorage': '',
            }),
            'employer_address': forms.TextInput(attrs={
                'placeholder': '1 avenue de la République 75011 Paris',
                'data-localstorage': '',
            }),
            'message': MessageWidget(attrs={
                'rows': 10,
                'placeholder': """Bonjour Madame, Monsieur,

(Formulez votre demande ici).
""",
            }),
        }


class InterviewForm(BaseAnswerForm):
    title = "Planifier un entretien d'embauche"
    success_message = "Votre proposition d'entretien a été envoyée avec succès"
    template = 'jepostule/pipeline/answers/interview.html'
    date_format = '%d/%m/%Y %H:%M'
    date_format_js = 'd/m/Y H:i'
    event_label = "entretien"

    class Meta:
        model = models.AnswerInterview
        fields = (
            'location', 'datetime',
            'employer_name', 'employer_email', 'employer_phone', 'employer_address',
            'message',
        )
        labels = {
            'location': "L'entretien se déroulera",
            'message': "Informations complémentaires",
        }
        widgets = {
            'location': forms.RadioSelect(),
            'employer_name': forms.TextInput(attrs={
                'data-localstorage': '',
            }),
            'employer_phone': forms.TextInput(attrs={
                'placeholder': '01 23 45 67 89',
                'data-localstorage': '',
            }),
            'employer_address': forms.TextInput(attrs={
                'placeholder': '1 avenue de la République 75011 Paris',
                'data-localstorage': '',
            }),
            'message': MessageWidget(attrs={
                'rows': 10,
                'placeholder': "Questions ? Demande d'information ?",
            }),
        }

    datetime = forms.DateTimeField(
        label="Date et heure de l'entretien",
        # Turn off browser's input autocomplete to avoid hiding the JS datepicker.
        widget=forms.DateTimeInput(attrs={'autocomplete': 'off'}),
    )

    def clean_datetime(self):
        value = self.cleaned_data['datetime']
        if value < now():
            raise forms.ValidationError("La date de l'entretien est passée")
        return value

    @property
    def min_datetime_str(self):
        return now().strftime(self.date_format)
