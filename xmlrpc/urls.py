# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns(
    '',
    url(r'^$', 'xmlrpc.views.xmlrpc_handler', name="xmlrpc"),
)
