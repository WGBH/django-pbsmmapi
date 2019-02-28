import json
from django import template

register = template.Library()


@register.filter(name='extract_from_json')
def extract_from_json(value, arg):
    if value:
        foo = json.loads(value)
        # Some thing are saved in lists...  I'm not sure what to do if they are.
        if isinstance(foo, list):
            obj = foo[0]
        else:
            obj = foo

        if isinstance(obj, dict) and arg in obj.keys():
            return obj[arg]

    return None
