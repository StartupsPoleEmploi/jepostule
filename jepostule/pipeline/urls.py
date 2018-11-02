from django.urls import path

from . import views

urlpatterns = [
    path('email/application/<int:job_application_id>', views.email_application, name='email_application'),
    path('email/confirmation/<int:job_application_id>', views.email_confirmation, name='email_confirmation'),
    path('reponse/<uuid:answer_uuid>/entretien', views.answer_interview, name='answer_interview'),
]
