import json
import shortuuid
import datetime as dt
import requests

from openai import OpenAI
from config import *
from libs.news_search import answer_news_search


def upload_chat_history(user_id, role, text):
    doc = {
        'user_id': user_id,
        'role': role,
        'text': text,
        'timestamp': dt.datetime.now().isoformat(),
    }
    doc_id = shortuuid.uuid()
    
    resp = requests.put(
        url = f"{OPENSEARCH_URL}/chat-history/_doc/{doc_id}",
        data = json.dumps(doc),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH,
    )
    
    print(f'Status code: {resp.status_code}')
    # assert resp.status_code >= 200 and resp.status_code < 300
    assert resp.status_code // 100 == 2
    
    
def fetch_chat_history(user_id):
    query = {
        "query": {
            "term": {
            "user_id": {
                "value": user_id
        }
        }
        },
        "sort": [
            {
            "timestamp": {
                "order": "desc"
            }
            }
        ],
        "size": 100       
    }
    
    resp = requests.get(
        url = f"{OPENSEARCH_URL}/chat-history/_search",
        data = json.dumps(query),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH,
    )

    assert resp.status_code == 200
    
    results = resp.json()
    hits = results['hits']['hits']
    
    chats = [x['_source'] for x in hits]
    chats.sort(key=lambda x: x['timestamp'])
    
    return chats


def generate_answer(user_id, utterance):
    
    client = OpenAI()
    
    messages = [
        {
            'role' : 'system',
            'content' : '나는 민도리야, 질문에 트레이딩 전문가 처럼 얘기해줘'
        },
        
        # {
        #     'role' : 'user',
        #     'content' : utterance,
        # }
    ]
    
    
    # 과거 데이터를 입력해서 프롬프트 만들어주는 부분
    chats = fetch_chat_history(user_id)
    
    for x in chats:
        entry = {
            'role' : x['role'],
            'content': x['text'],
        }
        
        messages.append(entry)
        
    
    
    entry = {
        'role': 'user',
        'content': utterance,
    }
    
    messages.append(entry) 
    
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens= 100,
        
    )
    
    answer = resp.choices[0].message.content.strip()
    
    return answer



def generate_chat_talk(user_id, utterance):
    
    answer = generate_answer(user_id, utterance)
    
    print(f'[Kakao Callback] Answer: {answer}')
    
    upload_chat_history(user_id, 'user', utterance)
    upload_chat_history(user_id, 'assistant', answer)
    
    
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

def main(event, context):
    
    body = json.loads(event['body'])
    user_id = body['userRequest']['user']['id']
    utterance = body['userRequest']['utterance']
    
    print(f"[kakao callback  User ID : {user_id}")
    print(f"[kakao callback  Utterance : {utterance}")
    
    
    if '뉴스' in utterance:
        body = answer_news_search(utterance)
    else:
        body = generate_chat_talk(user_id, utterance)
    
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
