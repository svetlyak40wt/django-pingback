# -*- coding: utf-8 -*-

from django.http import HttpResponse

from xmlrpc import dispatcher


def xmlrpc_handler(request):
    """
    XML-RPC handler.

    If POST data is defined, it assumes it's XML-RPC and tries to
    process. If this is a GET request, show service description for
    all registered methods.

    """
    if request.method == 'POST':
        return HttpResponse(dispatcher._marshaled_dispatch(request.raw_post_data))
    elif request.method == 'GET':
        response = '\n'.join(dispatcher.system_listMethods())
        return HttpResponse(response)
