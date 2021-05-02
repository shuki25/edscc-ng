from django import template

register = template.Library()


# TEMPLATE USE:  {{ text|to_space:"_" }}
@register.filter
def to_space(value, replacement="_"):
    return str(value).replace(replacement, " ")
