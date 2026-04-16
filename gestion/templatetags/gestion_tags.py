from django import template

register = template.Library()


@register.filter
def widget_type(field):
    """Retourne le type de widget du champ pour le template."""
    widget = field.field.widget
    cls = widget.__class__.__name__.lower()
    if "textarea" in cls:
        return "textarea"
    if "select" in cls:
        return "select"
    if "file" in cls or "clearable" in cls:
        return "file"
    if "date" in cls:
        return "date"
    return "text"
