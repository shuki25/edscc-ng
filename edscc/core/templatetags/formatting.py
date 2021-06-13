from datetime import datetime

from django import template
from django.utils.safestring import mark_safe
from django.utils.text import camel_case_to_spaces

from edscc.squadron.models import Tags

register = template.Library()


# TEMPLATE USE:  {{ text|to_space:"_" }}
@register.filter
def to_space(value, replacement="_"):
    return str(value).replace(replacement, " ")


@register.filter
def camel2space(value):
    return camel_case_to_spaces(str(value)).title()


@register.filter
def squadron_tag_badge(value):
    qs = Tags.objects.all()
    tags_badge = {i.fdev_id: i.badge_color for i in qs}
    tags = {i.fdev_id: i.name for i in qs}
    html = '<span class="badge badge-pill %s">%s</span>' % (
        tags_badge[value],
        tags[value],
    )
    return mark_safe(html)


@register.filter
def convert_str_date(value):
    if value == "now":
        return datetime.now()
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
