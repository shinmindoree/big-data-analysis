import json


def main(event, context):
    body = {
        "message": "News Trends!!",
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
