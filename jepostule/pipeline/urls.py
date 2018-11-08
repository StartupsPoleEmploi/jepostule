from django.urls import path

from . import views

urlpatterns = [
    path('pipeline/email/application/<int:job_application_id>', views.email_application, name='email_application'),
    path('pipeline/email/confirmation/<int:job_application_id>', views.email_confirmation, name='email_confirmation'),
    path('pipeline/email/answer/<int:answer_id>', views.email_answer, name='email_answer'),
    path('candidature/reponse/<uuid:answer_uuid>/<int:status>', views.send_answer, name='answer'),
]
