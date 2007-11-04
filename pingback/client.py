import re
from urlparse import urlsplit
from xmlrpclib import ServerProxy, Fault
from urllib2 import urlopen

from BeautifulSoup import BeautifulSoup
from django.contrib.sites.models import Site
from django.conf import settings

from pingback.models import PingbackClient
from pingback.exceptions import PingbackNotConfigured


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

    for link in links:
        if PingbackClient.objects.count_for_link(instance, link):
            continue
        pingback = PingbackClient(object=instance, url=link)
        try:
            f = urlopen(link)
            server_url = f.info().get('X-Pingback', '') or search_link(f.read(512 * 1024))
            if server_url:
                server = ServerProxy(server_url)
                q = server.pingback.ping(url, link)
                pingback.success = True
        except (IOError, ValueError, Fault), e:
            pass
        pingback.save()
