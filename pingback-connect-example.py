from datetime import time, date, datetime
from time import strptime

from django.db import models
from django.dispatch import dispatcher

import xmlrpc
from pingback.client import ping_external_links, ping_directories
from pingback import create_ping_func
from blog.models import Post


def pingback_blog_handler(year, month, day, slug, **kwargs):
    d = date(*strptime(year + month + day, '%Y%b%d')[:3])
    r = (datetime.combine(d, time.min), datetime.combine(d, time.max))
    return Post.objects.filter(date__range=r).get(slug=slug)

ping_details = {'post_detail': pingback_blog_handler}

xmlrpc.dispatcher.register_function(create_ping_func(**ping_details), 'pingback.ping')


# Connecting client signals
dispatcher.connect(ping_external_links(content_attr='html', url_attr='get_absolute_url'),
                   signal=models.signals.post_save, sender=Post)
dispatcher.connect(ping_directories(content_attr='html', url_attr='get_absolute_url'),
                   signal=models.signals.post_save, sender=Post)
