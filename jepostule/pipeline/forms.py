from django import forms

from . import models


class BaseAnswerForm(forms.ModelForm):

    def __init__(self, job_application, *args, **kwargs):
        super().__init__(*args, label_suffix='', **kwargs)
        self.job_application = job_application

    def save(self, commit=True):
        self.instance.job_application_id = self.job_application.id
        return super().save(commit=commit)


class InterviewForm(BaseAnswerForm):
    title = "Planifier un entretien d'embauche"
    success_message = "Votre proposition d'entretien a été envoyée avec succès"

    # TODO certains champs ne sont pas requis : il faut spécifier au moins le téléphone ou l'email
    # TODO render date and time correctly with proper widget
    # TODO ensure interview datetime is in the future
    class Meta:
        model = models.AnswerInterview
        fields = (
            'location', 'datetime',
            'employer_name', 'employer_email', 'employer_phone', 'employer_address',
            'message',
        )
        labels = {
            'location': "L'entretien se déroulera",
            'employer_name': "Nom du recruteur",
            'employer_email': "Email du recruteur",
            'employer_phone': "Numéro de téléphone",
            'employer_address': "Adresse de l'entreprise",
            'message': "Informations complémentaires",
        }
        widgets = {
            'location': forms.RadioSelect(),
            'employer_phone': forms.TextInput(attrs={
                'placeholder': '01 23 45 67 89'
            }),
            'employer_address': forms.TextInput(attrs={
                'placeholder': '1 avenue de la République 75011 Paris',
            }),
            'message': forms.Textarea(attrs={
                'rows': 10,
                'placeholder': "Questions ? Demande d'information ?",
            }),
        }

    datetime = forms.DateTimeField(
        label="Date et heure de l'entretien",
    )
