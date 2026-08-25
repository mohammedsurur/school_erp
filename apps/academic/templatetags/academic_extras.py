from django import template

register = template.Library()


@register.filter
def dictlookup(d, key):
    """
    Allow {{ my_dict|dictlookup:key }} in templates.
    Used in timetable_view.html to look up nested dict values.

    Usage:
        {% with entry=timetable|dictlookup:day|dictlookup:period.pk %}
    """
    if isinstance(d, dict):
        return d.get(key)
    return None