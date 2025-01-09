import json
import pdb

import requests
from config import *
from openai import OpenAI


def make_advanced_query(text):
    client = OpenAI()
    
    resp = client.embeddings.create(
        model = "text-embedding-3-large",
        input= text, 
    )
    
    embed = resp.data[0].embedding
    
    query_keywords = {
        "script_score": {
            "query": {
                "multi_match": {
                    "query" : text,
                    "fields": ["title^4", "summary"],
                }
            },
            "script": {
                "source": "_score * 1"
            }
        }
    }
    
    query_embedding = {
        "script_score": {
            "query": {
            "knn": {
                "embed":{
                    "vector": embed, 
                    "k": 2,
                    
                }
            }
        },
            "script": {
                "source": "_score * 1"
            }
        }
    }
    
    query = {
        "query": {
            "bool": {
                "should": [
                    query_keywords,
                    query_embedding,
                ],
            }
        },
        "size": 2, 
        "_source": ["title", "summary", "sources"],
    }
    
    return query

def make_basic_query(text):
    client = OpenAI()
    
    resp = client.embeddings.create(
        model = "text-embedding-3-large",
        input= text, 
    )
    
    embed = resp.data[0].embedding
    
    query = {
        "query": {
            "knn": {
                "embed":{
                    "vector": embed, 
                    "k": 2,
                    
                }
            }
        },
        "size": 2, 
        "_source": ["title", "summary", "sources"],
    }
    
    return query

def semantic_search(text):
    
    # query = make_basic_query()
    query = make_advanced_query(text)
    
    
    resp = requests.get(
        url = f'{OPENSEARCH_URL}/topics/_search',
        data = json.dumps(query),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH
    )
    
    
    assert resp.status_code == 200
    
    
    results = resp.json()
    
    hits = results['hits']['hits']
    docs =  [x['_source'] for x in hits]
    
    return docs
    
def generate_answer(topics, utterance):
    buffer = []
    
    for x in topics:
        entry = f"""
제목 : {x['title']}
내용 : {x['summary']}
        """

        buffer.append(entry)
    
    context = '\n'.join(buffer)
    
    prompt = f"""
신문기사
======
{context}

사용자질문
=======
{utterance}
    """

    print(prompt)
    
    client = OpenAI()
    
    messages = [
        {"role": "system", "content": "아래 뉴스기사를 바탕으로 사용자의 질문에 위트넘치게 대답해줘"},
        {"role": "user", "content": prompt}
    ]
    
    resp = client.chat.completions.create(
        model = "gpt-4o-mini" ,
        messages = messages,
    )
    answer = resp.choices[0].message.content.strip()
    
    print(answer)
    
    return answer

def answer_news_search(utterance):
    
    topics = semantic_search(utterance)
    answer = generate_answer(topics, utterance)
    
    # for x in topics:
    #     print(x)
    
    
    body = {
        'version': '2.0',
        'template': {
            'outputs': [
                {
                    'simpleText': {
                        # 'text': f'{utterance} 라고 말했지?',
                        'text' : answer, 
                    }
                }
            ],
        },
    }
    
    return body