# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

from xmlrpc import views

urlpatterns = patterns(
    '',
    url(r'^$', views.xmlrpc_handler, name="xmlrpc"),
)
