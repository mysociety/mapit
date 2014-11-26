from django.conf.urls import patterns

from mapit.shortcuts import render

urlpatterns = patterns(
    '',
    (r'^changelog$', render, {'template_name': 'mapit/changelog.html'}, 'mapit_changelog'),
)
