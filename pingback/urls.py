from django.conf.urls.defaults import *

from pingback import views

urlpatterns = patterns(
    '',
    url(r'^$', views.handler, name="pingback"),
    )
