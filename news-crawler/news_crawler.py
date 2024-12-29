## 단축키  cmd+p  , cmd+shift+p

import pdb # python debugger
import datetime as dt
import requests

from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse


NAVER_URL = 'https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=101'
NAVER_HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }

def fetch_last_page(datestr):
    url = f'{NAVER_URL}&date={datestr}&page=1000'
    resp = requests.get(url)
    # print(resp.status_code)

    soup = BeautifulSoup(resp.text, 'html.parser')
    paging = soup.find('div', {'class': 'paging'})
    strong = paging.find('strong')
    last_page = int(strong.text)

    # pdb.set_trace() #break point

    return last_page

def fetch_news_list(datestr, page):
    print(f"Fetching page {page}...")

    url = f"{NAVER_URL}&date={datestr}&page={page}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')

    list_body = soup.find('div', {'class' : 'list_body'})

    buffer = []
    for item in list_body.find_all('li'):
        link = item.find_all('a')[-1]
        title = link.text.strip()
        url = link['href']
        parsed_url = urlparse(url)
        tokens = parsed_url.path.split('/')
        doc_id = 'nn-' + '-'.join(tokens[-2:])

        # print(title)
        # print(url)

        entry = (doc_id, title, url)

        buffer.append(entry)

    return buffer


def fetch_news_body(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')

    title = soup.title.text.strip()
    node = soup.find('meta', {'property': 'og:article:author'})
    if node:
        content = node['content']

        if '네이버 스포츠' in content:
            return None
        if 'TV연예' in content:
            return None
        
        tokens = content.split('|')
        publisher = tokens[0].strip()
    else:
        raise RuntimeError()
    

 
    print(title)
    print(publisher)

    pdb.set_trace()
    pass

def fetch_news_list_for_date(date):
    datestr = date.strftime('%Y%m%d')
    print(f'Fetching news list on {datestr}')

    last_page = fetch_last_page(datestr)

    for page in range(1, last_page + 1):
        items = fetch_news_list(datestr, page)
        

        for doc_id, title, url in items:
            print(f"[{doc_id}] {title}")
            
            body = fetch_news_body(url)
        
            pdb.set_trace()


if __name__ == '__main__':
    base_date = dt.datetime(2024, 9, 1)

    for d in range(10):
        date = base_date + relativedelta(days=d)

        fetch_news_list_for_date(date)