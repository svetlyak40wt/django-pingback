# -*- coding: utf-8 -*-

from urlparse import urlsplit
from urllib2 import urlopen, HTTPError, URLError

from BeautifulSoup import BeautifulSoup

from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.conf import settings
from django.core.urlresolvers import get_callable
from django.utils.html import strip_tags
from django.utils.encoding import force_unicode, smart_str

from pingback.models import Pingback


class PingbackNotConfigured(Exception):
    pass


class PingbackError(Exception):
    """
    Defines an XML-RPC fault with the appropriate error codes for
    pingback's. These are thrown in the ping method when an error as
    described in the specification occurs. Error codes are taken from
    the specification at http://www.hixie.ch/specs/pingback/pingback

    """

    SOURCE_DOES_NOT_EXIST       = 0x0010
    SOURCE_DOES_NOT_LINK        = 0x0011
    TARGET_DOES_NOT_EXIST       = 0x0020
    TARGET_IS_NOT_PINGABLE      = 0x0021
    PINGBACK_ALREADY_REGISTERED = 0x0030
    ACCESS_DENIED               = 0x0031
    CONNECTION_ERROR            = 0x0032

    def __init__(self, error_code):
        self.error_code = error_code

    def is_error(cls, value):
        return value in [ 0x0010, 0x0011,  0x0020, 0x0021, 0x0030, 0x0031, 0x0032 ]
    is_error = classmethod(is_error)


def create_ping_func(**kwargs):
    """
    Takes any number of named url's as keys and resolver objects as
    values and returns a function that can be used in a xmlrpc handler.

    The resolver objects are simply objects that has a method `resolve`
    that takes keyword arguments and uses those to resolve the object
    that is being pinged. The keyword args given are named and ordered
    the same as the view that is registered as url handler for the
    resource that is being pinged.

    """

    def ping_func(source, target):
        domain = Site.objects.get_current().domain

        # fetch the source request, then check if it really pings the target.
        try:
            doc = urlopen(source)
        except (HTTPError, URLError):
            raise PingbackError(PingbackError.SOURCE_DOES_NOT_EXIST)

        # does the source refer to the target?
        soup = BeautifulSoup(doc.read())
        mylink = soup.find('a', href=target)
        if not mylink:
            raise PingbackError(PingbackError.SOURCE_DOES_NOT_LINK)

        # grab the title of the pingback source
        title = soup.find('title')
        if title:
            title = strip_tags(unicode(title))
        else:
            title = 'Unknown title'

        # extract the text around the incoming link
        content = unicode(mylink.findParent())
        i = content.index(unicode(mylink))
        content = strip_tags(content)
        max_length = getattr(settings, 'PINGBACK_RESPONSE_LENGTH', 200)
        if len(content) > max_length:
            start = i - max_length/2
            if start < 0:
                start = 0
            end = i + len(unicode(mylink)) + max_length/2
            if end > len(content):
                end = len(content)
            content = content[start:end]

        scheme, server, path, query, fragment = urlsplit(target)

        # check if the target is valid target
        if not (server == domain or server.split(':')[0] == domain):
            return PingbackError.TARGET_IS_NOT_PINGABLE

        resolver = urlresolvers.RegexURLResolver(r'^/', settings.ROOT_URLCONF)

        try:
            func, smth, params = resolver.resolve(path)
        except urlresolvers.Resolver404:
            raise PingbackError(PingbackError.TARGET_DOES_NOT_EXIST)

        name = resolver.reverse_dict[func][-1].name
        if name not in kwargs:
            raise PingbackError(PingbackError.TARGET_IS_NOT_PINGABLE)

        object_resolver = kwargs[name]
        obj = object_resolver(**params)

        content_type = ContentType.objects.get_for_model(obj)
        try:
            Pingback.objects.get(url=source, content_type=content_type, object_id=obj.id)
            raise PingbackError(PingbackError.PINGBACK_ALREADY_REGISTERED)
        except Pingback.DoesNotExist:
            pass

        pb = Pingback(object=obj, url=source, content=content.encode('utf-8'), title=title.encode('utf-8'), approved=True)
        pb.save()
        return 'pingback from %s to %s saved' % (source, target)
    return ping_func
