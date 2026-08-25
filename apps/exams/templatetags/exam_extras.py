from django import template

register = template.Library()


@register.filter
def dictlookup(d, key):
    """
    Look up a key in a dict from a template variable.
    Usage: {{ my_dict|dictlookup:key_var }}
    """
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def get_marks(existing, student_pk):
    """Get marks_obtained for a student from existing results dict"""
    result = existing.get(student_pk)
    if result:
        return result.marks_obtained
    return ''


@register.filter
def get_absent(existing, student_pk):
    """Get is_absent for a student from existing results dict"""
    result = existing.get(student_pk)
    if result:
        return result.is_absent
    return False


@register.filter
def get_remarks(existing, student_pk):
    """Get remarks for a student from existing results dict"""
    result = existing.get(student_pk)
    if result:
        return result.remarks
    return ''