import json
from django import template

register = template.Library()


@register.filter(name='extract_from_json')
def extract_from_json(value, arg):
    if value:
        data = json.loads(value)
        # Some thing are saved in lists...  I'm not sure what to do if they are.
        if isinstance(data, list):
            obj = data[0]
        else:
            obj = data

        if isinstance(obj, dict) and arg in obj.keys():
            return obj[arg]

    return None
