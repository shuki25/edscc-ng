from django import template
from django.utils.text import camel_case_to_spaces

register = template.Library()


# TEMPLATE USE:  {{ text|to_space:"_" }}
@register.filter
def to_space(value, replacement="_"):
    return str(value).replace(replacement, " ")


@register.filter
def camel2space(value):
    return camel_case_to_spaces(str(value)).title()
