""" Server-side pingback realization.

Author::

    Alexander Solovyov

Author of XML-RPC handler is Brendan W. McAdams, who posted it to the Django wiki:
http://code.djangoproject.com/wiki/XML-RPC
"""
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from urlparse import urlsplit
from urllib2 import urlopen, HTTPError, URLError

from BeautifulSoup import BeautifulSoup
from django.http import HttpResponse
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers as ur
from django.conf import settings
from django.core.urlresolvers import get_callable
from django.utils.html import strip_tags

from pingback.models import Pingback


try:
    # Python 2.4
    dispatcher = SimpleXMLRPCDispatcher()
except TypeError:
    # Python 2.5
    dispatcher = SimpleXMLRPCDispatcher(allow_none=False, encoding=None)


def handler(request):
    """ XML-RPC handler

    If POST data is defined, it assumes it's XML-RPC and tries to process.
    If POST data is empty, show service description.
    """
    response = HttpResponse()
    if len(request.POST):
        response.write(dispatcher._marshaled_dispatch(request.raw_post_data))
    else:
        methods = dispatcher.system_listMethods()
        for method in methods:
            response['Content-Type'] = 'text/plain'
            # __doc__
            help = dispatcher.system_methodHelp(method)
            response.write("%s:\n    %s\n\n" % (method, help))
    response['Content-Length'] = str(len(response.content))
    return response


def ping(source, target):
    """ Pingback server function.

    Requires URL of pinger resource and link of pinging resource.

    Determinition of pingable object by it's url is done by setting
    settings.PINGBACK_SERVER in the following format::

        {
        'post_detail': 'pingback.getters.post_get',
        }

    Where:
     - 'post_detail' is name of url
     - 'pingback.getters.post_get' is name of function, which will return
       object using parameters, resolved by URL.
    """
    domain = Site.objects.get_current().domain

    try:
        doc = urlopen(source)
    except (HTTPError, URLError):
        # The source URI does not exist.
        return 0x0010

    soup = BeautifulSoup(doc.read())
    mylink = soup.find('a', href=target)
    if not mylink:
        # The source URI does not contain a link to the target URI, and so cannot be used as a source.
        return 0x0011
    # title
    title = soup.find('title').contents[0]
    title = strip_tags(unicode(title))
    content = unicode(mylink.findParent())
    i = content.index(unicode(mylink))
    content = strip_tags(content)
    max_length = settings.PINGBACK_RESPONSE_LENGTH
    if len(content) > max_length:
        start = i - max_length/2
        if start < 0:
            start = 0
        end = i + len(unicode(mylink)) + max_length/2
        if end > len(content):
            end = len(content)
        content = content[start:end]

    scheme, server, path, query, fragment = urlsplit(target)

    if not server.split(':')[0] == domain:
        # The specified target URI cannot be used as a target.
        return 0x0021

    resolver = ur.RegexURLResolver(r'^/', settings.ROOT_URLCONF)

    try:
        func, smth, params = resolver.resolve(path)
    except ur.Resolver404:
        # The specified target URI does not exist.
        return 0x0020
    name = resolver.reverse_dict[func][-1].name
    if not name in settings.PINGBACK_SERVER:
        # URL can't receive pingback
        return 0x0021
    getter = settings.PINGBACK_SERVER[name]
    if not callable(getter):
        getter = get_callable(getter)
    obj = getter(**params)

    ctype = ContentType.objects.get_for_model(obj)
    try:
        Pingback.objects.get(url=source, content_type=ctype, object_id=obj.id)
        return 0x0030
    except Pingback.DoesNotExist:
        pass

    pb = Pingback(object=obj, url=source, content=content.encode('utf-8'), title=title.encode('utf-8'), approved=True)
    pb.save()

    return 'pingback from %s to %s saved' % (source, target)



dispatcher.register_function(ping, 'pingback.ping')
