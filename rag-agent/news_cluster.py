## 신민석(20239469)

import pdb
import datetime as dt
import pandas as pd
import requests
import json
import numpy as np

from config import *
from dateutil.relativedelta import relativedelta
from openai import OpenAI
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

PAGE_SIZE = 100
TARGET_DATE = '2024-12-24'

## 뉴스 문서 가져오기
def fetch_news_docs():
    print('Fetching news docs from opensearch server')

    date_to = dt.datetime.fromisoformat(TARGET_DATE) + relativedelta(days=1)

    query = {
        "query":{
            "range":{
                "created_at":{
                    "gte" : TARGET_DATE,
                    "lt" : date_to.isoformat(),
                }
            }
        },

        "size":PAGE_SIZE
    }

    
    for p in range(2):
        print(f'-page {p}')

        resp = requests.get(
            url = f"{OPENSEARCH_URL}/news/_search",
            data = json.dumps(query),
            headers = OPENSEARCH_HEADERS,
            auth = OPENSEARCH_AUTH,
        )

        query['from'] = p * PAGE_SIZE
        results = json.loads(resp.content)
        hits = results['hits']['hits']

        if len(hits) == 0:
            break

        for x in hits:
            doc = {
                'doc_id' : x['_id'],
                **x['_source'],
            }

            if len(doc['body']) < 200:
                continue

            yield doc  ## yield와  return은 무슨차이인가??

    # results를 json 파일로 저장
    # with open("results.json", "w", encoding="utf-8") as json_file:json.dump(results, json_file, ensure_ascii=False, indent=4)

    # print(resp.status_code)

 
    # pass

## 임베딩 벡터 생성
def get_embedding_vectors(df):
    print()
    print("Get embedding vectors via openai...")
    
    client = OpenAI()
    embeddings = []

    titles = df['title'].tolist()

    for i in range(0, len(df), PAGE_SIZE):
        print(f'- index {i}')

        resp = client.embeddings.create(
            model = "text-embedding-3-large",
            input = titles[i:i+PAGE_SIZE],
        )


        embeddings += [x.embedding for x in resp.data]


    embeddings = np.array(embeddings)
    print(f'= Embedding shape: {embeddings.shape}')

    return embeddings


## 뉴스 주제 클러스터링
def cluster_news_topics(df, embeds):
    print()
    print("cluster news articles into topics...")


    range_n_clusters = int(len(df) / 5) + np.arange(10)

    best_silhoutte = -1
    best_clusterer = None


    for i in range(5):
        print(f'(Iteration #{i})')

        for n_clusters in range_n_clusters:
            clusterer = KMeans(n_clusters=n_clusters, n_init='auto')
            cluster_labels = clusterer.fit_predict(embeds) # range_n_clusters에서 정의한 cluster number를 labeling

            sillhoutte = silhouette_score(embeds, cluster_labels)

            print(f'- n_clusters : {n_clusters}, silloutttes: {sillhoutte: .4f}')

            if sillhoutte > best_silhoutte:
                best_silhoutte = sillhoutte
                best_clusterer = clusterer


    print()
    print(f'* Best n_clusters : {best_clusterer.n_clusters}')

    similarities = []


    for i in df.index:
        x = best_clusterer.labels_[i] #df의 각 행의 cluster 의 label(range_n_clusters)
        center = best_clusterer.cluster_centers_[x]

        sim = np.dot(embeds[i], center)

        similarities.append(sim)

    df['topic'] = best_clusterer.labels_ # df 각 행에 cluster label을 추가
    df['similarity'] = similarities # df 각 행에 cluster cosine유사도 값 열 추가


    return df

    pass

## 주제 요약 생성 및 저장
def generate_topic_summary(df):
    print()
    print('Generatting topic summaries')

    client = OpenAI()

    df = df.sort_values('similarity', ascending = False) # 유사도 값 높은 순으로 정렬, 유사도가 가장 높은 기사를 선택하기 위한 사전 작업

    topics = df['topic'].drop_duplicates().tolist()

    for i in topics:
        chunk = df.loc[df['topic'] == i]  # 각 Topic와 일치하는 기사를 추출함.
        if len(chunk) <= 2:  # 기사 수가 2 이하면 무시. 
            continue

        print(f'Topic {i} (docs: {len(chunk)})') 
        print(f'sources:')

        for _, x in chunk.iterrows():
            print(f'- {x['title']} ({x['publisher']})')

        doc = chunk.iloc[0] # 각 chunk에서 유사도가 가장 높은[0] 기사를 클러스터를 대표하는 기사로 선택
        
        # GPT를 활용하여 대표 기사를 500자 이내로 요약
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "다음 뉴스 기사를 500자 이내로 요약해줘."},
                {"role": "user", "content": doc['body']}
            ],
        )

        summary = resp.choices[0].message.content.strip()

        print("Summary: ")
        print(summary)
        
        #요약 내용을 vector로 임베딩
        resp = client.embeddings.create(
            model = "text-embedding-3-large",
            input= summary,
        )

        embed = resp.data[0].embedding

        topic_id = f'topic-{TARGET_DATE}-{i:04d}'
        body = {
            'date' : TARGET_DATE,
            'title' : doc['title'],
            'summary' : summary,
            'embed' : embed,
            'sources' : chunk['doc_id'].tolist(),
            'no_sources' : len(chunk),
        }

        resp = requests.put(
            url=f"{OPENSEARCH_URL}/topics/_doc/{topic_id}", 
            data = json.dumps(body),
            headers=OPENSEARCH_HEADERS,
            auth=OPENSEARCH_AUTH,
        )
        assert resp.status_code >= 200 and resp.status_code < 300

        print()

## 메인함수 (위의 모든 단계를 통합하여 실행)
if __name__ == '__main__':

    docs = fetch_news_docs() # 오픈서치 DB에서 뉴스 가져오기
    df = pd.DataFrame(docs) # 데이터 프레임으로 변환
    # print(df)

    embeds = get_embedding_vectors(df) # 임베딩 벡터 생성

    df = cluster_news_topics(df, embeds) #KMeans 클러스터링으로 뉴스 데이터를 주제별로 분류

    generate_topic_summary(df) #각 주제의 대표 문서를 요약하여 오픈서치에 저장

    print('** Completed!! **')




