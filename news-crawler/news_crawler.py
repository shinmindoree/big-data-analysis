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

def parse_media_info(soup):
    media_info = soup.find('div', {'class': 'media_end_head_info_datestamp'})
    if media_info:
        datestr_list = media_info.find_all('span', {'class':'media_end_head_info_datestamp_time'})
        link = media_info.find('a', {'class': 'media_end_head_origin_link'})
        source_url = link['href'] if link else ''
        return datestr_list, source_url
    
    else:
        RuntimeError()


def parse_datestr(span):

    if span.has_attr('data-date-time'):
        datestr = span['data-date-time']
    elif span.has_attr('data-modify-date-time'):
        datestr = span['data-modify-date-time']
    else:
        return None
    
    date = dt.datetime.fromisoformat(datestr)

    return date


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

    datestr_list, source_url = parse_media_info(soup)
    
    if len(datestr_list) == 1:
        created_at = parse_datestr(datestr_list[0])
        updated_at = created_at
    elif len(datestr_list) == 2:
        created_at = parse_datestr(datestr_list[0])
        updated_at = parse_datestr(datestr_list[1])
    else:
        raise RuntimeError()  
    
    body = soup.find('div', {'id': 'newsct_article'})

    assert body is not None

    body_text = body.text.strip()
    
    images = body.find_all('img')
    image_urls = [x.get('src') or x.get('data-src') for x in images]
    image_urls = list(set(image_urls))

    # print(title)
    # print(publisher)
    # print(source_url)
    # print(created_at)
    # print(updated_at)
    # print(images_urls)

    entry = {
        'title': title,
        'section': 'economy',
        'naver_url': url,
        'source_url': source_url,
        'image_urls': image_urls,
        'publisher': publisher,
        'created_at': created_at.isoformat(),
        'updated_at': updated_at.isoformat(),
        'body': body_text,
        }
    
    print(entry)
    
    return entry

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