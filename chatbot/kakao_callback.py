import json


def hello(event, context):
    body = {
        "message": "This is test",
        "event": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
