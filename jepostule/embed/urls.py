from django.urls import path

from . import views

urlpatterns = [
    path('candidater/', views.candidater, name='candidater'),
    path('demo/', views.demo, name='demo'),
]
