from django.urls import path

from django.shortcuts import render

urlpatterns = [
    path('changelog', render, {'template_name': 'mapit/changelog.html'}, 'mapit_changelog'),
]
