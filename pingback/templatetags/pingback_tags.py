#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2008 by Steingrim Dovland <steingrd@ifi.uio.no>

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.template import Library, Node, TemplateSyntaxError, Variable

from pingback.models import Pingback

register = Library()

class FillContextForObjectParser(object):
    def __call__(self, parser, token):
        tokens = token.split_contents()
        if len(tokens) != 6:
            raise TemplateSyntaxError, "%r tag requires 5 arguments" % tokens[0]
        if tokens[1] != 'for':
            raise TemplateSyntaxError, "Second argument in %r tag must be 'for'" % tokens[0]
        if tokens[4] != 'as':
            raise TemplateSyntaxError, "Fourth argument in %r tag must be 'as'" % tokens[0]
        try:
            app_label, model = tokens[2].split('.')
        except ValueError:
            raise TemplateSyntaxError, "Third argument in %r tag must be in the format 'app_label.model'" % tokens[0]
        try:
            content_type = ContentType.objects.get(app_label__exact=app_label, model__exact=model)
        except ContentType.DoesNotExist:
            raise TemplateSyntaxError, "%r tag has invalid content-type '%s.%s'" % (tokens[0], app_label, model)
        object_variable = tokens[3]
        context_variable = tokens[5]
        return self.do_tag(app_label, model, content_type, object_variable, context_variable)

class PingbackListNode(Node):
    def __init__(self, content_type, object_variable, context_variable):
        self.content_type = content_type
        self.context_variable = context_variable
        self.object_variable = Variable(object_variable)

    def render(self, context):
        obj_id = self.object_variable.resolve(context)
        obj = self.content_type.model_class().objects.get(pk=obj_id)
        context[self.context_variable] = Pingback.objects.pingbacks_for_object(obj, content_type=self.content_type)
        return ''

class DoPingbackList(FillContextForObjectParser):
    """
    Gets list of Pingback objects for then given parameter and populates
    the context with a variable containing that list. The variable's
    name is defined by the `as` clause of the tag.

    Syntax::
    
        {% get_pingback_list for [app_label].[model] [context_var_containing_obj_id] as [varname] %}

    Example usage::

        {% get_pingback_list for blog.entry object.id as pingback_list %}

    """
    def do_tag(self, app_label, model_name, content_type, object_variable, context_variable):
        return PingbackListNode(content_type, object_variable, context_variable)
        
class PingbackCountNode(Node):
    def __init__(self, content_type, object_variable, context_variable):
        self.content_type = content_type
        self.context_variable = context_variable
        self.object_variable = Variable(object_variable)

    def render(self, context):
        obj_id = self.object_variable.resolve(context)
        obj = self.content_type.model_class().objects.get(pk=obj_id)
        context[self.context_variable] = Pingback.objects.count_for_object(obj, content_type=self.content_type)
        return ''

class DoPingbackCount(FillContextForObjectParser):
    """
    Gets pingback count for the given params and populates the template
    context with a variable containing that value. The variable's name
    is defined by the `as` clause of the tag.

    Syntax::

        {% get_pingback_count for [app_label].[model] [context_var_containing_obj_id] as [varname]  %}
 	
    Example usage::

        {% get_pingback_count for blog.entry object.id as pingback_count %}

    """
    def do_tag(self, app_label, model_name, content_type, object_variable, context_variable):
        return PingbackCountNode(content_type, object_variable, context_variable)

register.tag("get_pingback_count", DoPingbackCount())
register.tag("get_pingback_list", DoPingbackList())
