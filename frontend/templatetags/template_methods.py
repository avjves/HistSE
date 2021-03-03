from django import template
from django.utils.safestring import mark_safe


register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_index(l, index):
    return l[index-1]

@register.filter
def prettify_date(date_string):
    return date_string.split("T")[0]

@register.filter
def show_em(data, key):
    if key == 'text' or key == 'first_text':
        splits = data.split("<em>")
        fixed_data = [splits.pop(0)]
        for splitt in splits:
            fixed_data.append(mark_safe('<em class="no-whitespace">'))
            second_splits = splitt.split("</em>")
            fixed_data.append(second_splits.pop(0))
            fixed_data.append(mark_safe("</em>"))
        if splits:
            fixed_data.append(second_splits.pop(0))
        return fixed_data
    else:
        return [data]
