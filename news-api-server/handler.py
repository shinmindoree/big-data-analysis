import json


def hello(event, context):
    body = {
        "message": "gogogo mindoree!!",
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
