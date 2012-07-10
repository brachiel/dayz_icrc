
from django import template

## Custom filters

register = template.Library()

@register.filter(is_safe=True)
def mod(value, arg):
    """Returns a number modulo arg"""
    return value % int(arg)
