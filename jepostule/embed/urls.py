from django.urls import path

from . import views

urlpatterns = [
    path('candidater/', views.candidater, name='candidater'),
    path('validate/', views.validate, name='validate'),
    path('demo/', views.demo, name='demo'),
]
