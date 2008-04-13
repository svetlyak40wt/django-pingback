# -*- coding: utf-8 -*-

from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

try:
    # Python 2.4
    dispatcher = SimpleXMLRPCDispatcher()
except TypeError:
    # Python 2.5
    dispatcher = SimpleXMLRPCDispatcher(allow_none=False, encoding=None)
