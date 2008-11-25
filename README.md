django-pingback
===============

This two applications provide 3 connected services:
pingback server, pingback client and directory ping client.

Depends on the [django-xmlrpc][].

Configuration
-------------

First, install the [django-xmlrpc][] application. You can download it either
from [repo][django-xmlrpc] or just use setuptools:

    easy_install -f http://pypi.aartemenko.com django-xmlrpc

Next, download and install `django-pingback`:

 * download sources from main [repository][django-pingback]
 * or use `easy_install django-pingback`
 * add `pingback` to your `INSTALLED_APPS`
 * run `./manage.py syncdb`
 * setup client and server callbacks.


Connecting server
-----------------

Pingback server receives pings from other sites, so, we must
create function which binds our URLs an objects.

But first of all, add this urlpattern to your urls configuration:

    ((r'^xmlrpc/$', 'django_xmlrpc.views.handle_xmlrpc', {}, 'xmlrpc'))

It is a handler for all xmlrpc requests.

Usually, blog has a detailed view for each post. Suppose that
our view has name `post_detail` and accepts one keyword arguments
`slug`.

Here is simple example, how to make Post objects pingable:

    from datetime import time, date, datetime
    from time import strptime

    from blog.models import Post
    from pingback import create_ping_func
    from django_xmlrpc import xmlrpcdispatcher

    # create simple function which returns Post object and accepts
    # exactly same arguments as 'details' view.
    def pingback_blog_handler(slug, **kwargs):
        return Post.objects.get(slug=slug)

    # define association between view name and our handler
    ping_details = {'post_detail': pingback_blog_handler}

    # create xml rpc method, which will process all
    # ping requests
    ping_func = create_ping_func(**ping_details)

    # register this method in the dispatcher
    xmlrpcdispatcher.register_function(ping_func, 'pingback.ping')

Now, go at you http://mysweetsite.com/xmlrpc/ and you should
see `pingback.ping` method among few other system methods. If it
is not there, then you made mistake in you server setup.

Also, you need to tell other sites, that your blog accepts
pingbacks. You can do it by adding a link in the head of your site:

    <link rel="pingback" href="{% url 'xmlrpc' %}" />

Or by adding X-Pingback HTTP header. Do do this, just add such line
in the settings.py:

    MIDDLEWARE_CLASSES = [
        # ...
        'pingback.middleware.XPingMiddleware',
    ]

Connecting client signals
-------------------------

Let's suppose, that you have a blog and want to ping external sites
(like Technorati) on post save, and to receive pingbacks from other
sites. Next two sections contain simple 'how-to' enable these features.

At first, setup configuration in the settings, here is an example:

    DIRECTORY_URLS = (
        'http://ping.blogs.yandex.ru/RPC2',
        'http://rpc.technorati.com/rpc/ping',
    )


Next, you must connect some signals to ping workers,
which created using `ping_external_links` and `ping_directories`
functions:

    from django.db.models import signals
    from pingback.client import ping_external_links, ping_directories
    from blog.models import Post

    signals.post_save.connect(
            ping_external_links(content_attr = 'html',
                                url_attr = 'get_absolute_url'),
            sender = Post, weak = False)

    signals.post_save.connect(
            ping_directories(content_attr = 'html',
                             url_attr = 'get_absolute_url'),
            sender = Post, weak = False)

Please note, that in the `content_attr` you must give either attribute or method
name, which returns HTML content of the object.

If you don't have such attribute or method, for example if you apply markdown
filter in the template, then `content_func` argument can be used instead of the
`content_attr`.

`content_func` must return HTML, and must accepts an instance as a single
argument.

Pay attention to the `weak = False` argument. If case of omitting django's event
dispatcher will remove your signal.

Template tags
-------------

To show pingbacks on your page, you can use code like this:

    {% load pingback_tags %}
    {% get_pingback_list for object as pingbacks %}
    {% if pingbacks %}
        <h1>Pingbacks</h1>
        {% for pingback in pingbacks %}
            <div class="b-pingback">
                <p class="b-meta">
                    <a name="pingback-{{ pingback.id }}" href="{{ object.get_absolute_url }}#pingback-{{ pingback.id }}" class="b-permlink">permalink</a>
                    {{ pingback.date }}, pingback from {{ pingback.url|urlizetrunc:40 }}:
                </p>

                <p>{{ pingback.content }}</p>
            </div>
        {% endfor %}
    {% endif %}

Also you can use `{% get_pingback_count for object as cnt %}`, to save
pingbacks' count in the context variable.

[django-xmlrpc]: https://code.launchpad.net/~aartemenko/django-xmlrpc/svetlyak40wt
[django-pingback]: http://hg.piranha.org.ua/django-pingback/
