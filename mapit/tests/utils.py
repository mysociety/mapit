import json


def get_content(response):
    if getattr(response, 'streaming', None):
        content = b''.join(response.streaming_content)
    else:
        content = response.content
    content = json.loads(content.decode('utf-8'))
    return content
