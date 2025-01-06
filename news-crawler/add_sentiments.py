import pdb
import json
import requests
import pandas as pd
from config import *
from transformers import pipeline


def fetch_missing_sentiments():
    query = {
        "query": {
            "bool": {
            "must_not": [
                {
                "exists": {
                    "field": "sentimen"
                }
                }
            ]
            }
        }
    }
    
    query = json.dumps(query)
    
    resp = requests.get(
        f"{OPENSEARCH_URL}/news/_search",
        headers= OPENSEARCH_HEADERS,
        data = query,
        auth = OPENSEARCH_AUTH
    )
    
    
    print(resp)
    
    assert resp.status_code == 200
    
    results = resp.json()
    
    hits = results['hits']['hits']
    docs = [{'id': x['_id'], **x['_source']} for x in hits]
    
    if len(docs) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(docs)
    df = df[['id', 'title']]
    
    return df 



def upload_to_server(df):
    for idx, row in df.iterrows():
        body = {
            "doc":{
                "sentiment": row['label']
            }
        }
        
        body = json.dumps(body)
        
        resp = requests.post(
            f"{OPENSEARCH_URL}/news/_update/{row['id']}",
            headers= OPENSEARCH_HEADERS,
            data = body,
            auth = OPENSEARCH_AUTH
        )
        
        assert resp.status_code == 200
        
        # pdb.set_trace()
        # pass

if __name__ == '__main__':
    classifier = pipeline('sentiment-analysis', model='snunlp/KR-FinBert-SC', device='mps')
    while True:
        df = fetch_missing_sentiments()
        if df.empty:
            break
        
        titles = df['title'].tolist()
        sentiment = classifier(titles)
        df_sents = pd.DataFrame(sentiment)
        
        df = df.join(df_sents)
        print(df)
        
        upload_to_server(df)