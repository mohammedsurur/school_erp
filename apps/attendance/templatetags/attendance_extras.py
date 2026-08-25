# apps/attendance/templatetags/attendance_extras.py

from django import template

register = template.Library()

@register.filter
def dictlookup(d, key):
    if isinstance(d, dict):
        return d.get(key)
    return None

@register.filter
def get_att_status(existing, student_pk):
    att = existing.get(student_pk)
    return att.status if att else 'present'

@register.filter
def get_att_note(existing, student_pk):
    att = existing.get(student_pk)
    return att.note if att else ''