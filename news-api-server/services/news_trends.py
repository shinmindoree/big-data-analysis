import json
import pdb
import requests
import pandas as pd

from config import *

def query_news_trends(search):
    query = {
    "size": 0,
    "aggs": {
        "group_by_date": {
        "date_histogram": {
            "field": "created_at",
            "interval": "day"
        },
        }
        }
    }
    
    if search:
        query['query'] = {
            "match":{
                "title": search
            }
        }
    
    query = json.dumps(query)
    
    resp = requests.get(
        f"{OPENSEARCH_URL}/news/_search",
        headers= OPENSEARCH_HEADERS,
        data = query,
        auth = OPENSEARCH_AUTH,
    )
    
    
    # print(resp)
    results = resp.json()
    buckets = results['aggregations']['group_by_date']['buckets']
    
    
    if len(buckets) == 0:
        return []
    
    df = pd.DataFrame(buckets)
    df['date'] = df['key_as_string'].str[:10]
    df = df[['date', 'doc_count']]

    return df.to_dict(orient='records')

def main(event, context):
    
    # params = event['queryStringParameters']  -> 아래와 차이점은 해당 키가 없을때 1번은 에러 띄우고 죽음. 2번은 none값을 줌.
    params = event.get('queryStringParameters') # --> none
    
    
    if params:
        search = params.get('search')
    else:
        search = None
    
    
    trends = query_news_trends(search)
    
    body = {
        "message": f"News Trends :{search}",
        "trends" : trends,
    }
    
    
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response