from django import forms


class InterviewForm(forms.Form):
    LOCATION_ONSITE = 'onsite'
    LOCATION_PHONE = 'phone'
    LOCATION_VIDEO = 'video'

    title = "Planifier un entretien d'embauche"
    success_message = "Votre proposition d'entretien a été envoyée avec succès"

    location = forms.ChoiceField(
        label="L'entretien se déroulera",
        choices=(
            (LOCATION_ONSITE, "dans l'entreprise"),
            (LOCATION_PHONE, "par téléphone"),
            (LOCATION_VIDEO, "en visio conférence"),
        ),
        widget=forms.RadioSelect(),
    )
    # TODO render date and time correctly with proper widget
    date = forms.DateField(label="Date de l'entretien")
    time = forms.TimeField(label="Heure de l'entretien")
    employer_name = forms.CharField(label="Nom du recruteur", max_length=128)
    employer_email = forms.EmailField(label="Email du recruteur", max_length=128)
    employer_phone = forms.CharField(
        label="Numéro de téléphone",
        max_length=32,
        widget=forms.TextInput(attrs={
            'placeholder': '01 23 45 67 89'
        }),
    )
    employer_address = forms.CharField(
        label="Adresse de l'entreprise", max_length=256,
        widget=forms.TextInput(attrs={
            'placeholder': '1 avenue de la République 75011 Paris',
        }),
    )
    message = forms.CharField(
        label="Informations complémentaires",
        widget=forms.Textarea(attrs={
            'rows': 10,
            'placeholder': "Questions ? Demande d'information ?",
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, label_suffix='', **kwargs)
