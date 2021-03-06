from django.urls import path

from . import views

urlpatterns = [
    path('application/token/', views.application_token, name='application_token'),
    path('application/token/refresh/', views.application_token_refresh, name='application_token_refresh'),
]
