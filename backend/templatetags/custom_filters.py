from django import template

register = template.Library()

@register.filter(name='class_name')
def class_name(obj):
    """Returns the class name of an object"""
    return obj.__class__.__name__