from django.conf.urls import url

from mapit.shortcuts import render

urlpatterns = [
    url(r'^changelog$', render, {'template_name': 'mapit/changelog.html'}, 'mapit_changelog'),
]
