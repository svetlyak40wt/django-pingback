import re
from urlparse import urlsplit
from xmlrpclib import ServerProxy, Fault
from urllib2 import urlopen

from BeautifulSoup import BeautifulSoup
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.urlresolvers import reverse

from pingback.models import PingbackClient, DirectoryPing
from pingback.exceptions import PingbackNotConfigured, PingbackError


def callab(smth):
    if callable(smth):
        return smth()
    else:
        return smth


class PingbackHelper:
    """ Pingback client settings resolver.

    Requires settings.PINGBACK_CLIENT in following format::

        {
        'some.model': {'content': 'body', 'url': 'get_absolute_url'},
        'blog.post': {'content': 'html', 'url': 'get_another_url'},
        }

    Where:
     - 'some.model' and 'blog.post' are 'app_name.model_name' in lowercase
     - 'body' and 'html' are attributes, which contains HTML with links to ping. Can be callable.
     - 'get_*_url' is attribute, which contains URL of object. Can be callable.

    """
    def __init__(self, instance):
        self.instance = instance
        opts = instance._meta
        name = '%s.%s' % (opts.app_label, opts.module_name)
        try:
            conf = settings.PINGBACK_CLIENT[name]
            self.content_attr = conf['content']
            self.url_attr = conf['url']
        except KeyError:
            raise PingbackNotConfigured('Please configure PINGBACK_CLIENT for %s.' % name)

    def get_content(self):
        content = getattr(self.instance, self.content_attr, None)
        return callab(content)

    def get_url(self):
        url = getattr(self.instance, self.url_attr, None)
        return callab(url)


def ping_external_links(instance):
    """ Pingback client function.

    Credits go to Ivan Sagalaev.
    """
    domain = Site.objects.get_current().domain
    ph = PingbackHelper(instance)
    content = ph.get_content()
    url = 'http://%s%s' % (domain, ph.get_url())

    def is_external(external, url):
        path_e = urlsplit(external)[2]
        path_i = urlsplit(url)[2]
        return path_e != path_i

    def search_link(content):
        match = re.search(r'<link rel="pingback" href="([^"]+)" ?/?>', content)
        return match and match.group(1)

    soup = BeautifulSoup(content)
    links = [a['href'] for a in soup.findAll('a') if is_external(a['href'], url)]

    # TODO: execute this code in the thread
    for link in links:
        if PingbackClient.objects.count_for_link(instance, link):
            continue
        pingback = PingbackClient(object=instance, url=link)
        try:
            f = urlopen(link)
            server_url = f.info().get('X-Pingback', '') or search_link(f.read(512 * 1024))
            if server_url:
                server = ServerProxy(server_url)
                try:
                    result = server.pingback.ping(url, link)
                except Exception, e:
                    pingback.success = False
                else:
                    pingback.success = not PingbackError.is_error(result)
        except (IOError, ValueError, Fault), e:
            pass
        pingback.save()

def ping_directories(instance):
    """Ping blog directories"""

    domain = Site.objects.get_current().domain
    ph = PingbackHelper(instance)
    content = ph.get_content()
    blog_name = settings.BLOG_NAME
    blog_url = 'http://%s/' % domain
    object_url = 'http://%s%s' % (domain, ph.get_url())
    # TODO: cleanup generation of RSS feed and use it here instead of ATOM feed
    # because ATOM feed is not supported well by some ugly sites
    feed_url = 'http://%s%s' % (domain, reverse('atom_feed', args=['blog']))

    #TODO: execute this code in the thread
    for directory_url in settings.DIRECTORY_URLS:
        ping = DirectoryPing(object=instance, url=directory_url)
        try:
            server = ServerProxy(directory_url)
            try:
                q = server.weblogUpdates.extendedPing(blog_name, blog_url, object_url, feed_url)
            #TODO: Find out name of exception :-)
            except Exception, ex:
                q = server.weblogUpdates.ping(blog_name, blog_url, object_url)
            if q.get('flerror'):
                ping.success = False
            else:
                ping.success = True
        except (IOError, ValueError, Fault), e:
            pass
        ping.save()
