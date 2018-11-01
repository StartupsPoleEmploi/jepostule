from django.urls import path

from . import views

urlpatterns = [
    path('application/token/', views.application_token, name='application_token'),
    path('application/eventcallback/', views.application_event_callback, name='application_event_callback'),
]
