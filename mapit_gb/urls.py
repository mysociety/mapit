from django.conf.urls import url

from django.shortcuts import render

urlpatterns = [
    url(r'^changelog$', render, {'template_name': 'mapit/changelog.html'}, 'mapit_changelog'),
]
