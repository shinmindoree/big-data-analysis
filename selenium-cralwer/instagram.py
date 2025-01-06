import pdb
import time


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


LOGIN_URL = 'https://www.instagram.com/accounts/login'
LOGIN_ID = 'elgd00@gmail.com'
LOGIN_PW = 'sbk46jo1!'

CRAWLING_URL = 'https://www.instagram.com'

if __name__ == '__main__':
    browser = webdriver.Chrome()
    browser.get(LOGIN_URL)
    browser.implicitly_wait(3)

    elem = browser.find_element(By.NAME, 'username')
    elem.send_keys(LOGIN_ID)

    elem = browser.find_element(By.NAME, 'password')
    elem.send_keys(LOGIN_PW + Keys.ENTER)

    time.sleep(20)

    browser.get(CRAWLING_URL)

    time.sleep(3)
    

#아래로 스크롤을 반복해서 아티클 개수 추가로 확보하기
    for i in range(5):
        elem = browser.find_element(By.TAG_NAME, 'html')
        elem.send_keys(Keys.END)

        time.sleep(3)
        
    articles = browser.find_elements(By.TAG_NAME, 'article')

    for x in articles:
        soup = BeautifulSoup(x.text, 'html.parser')
        print(soup)
        print()

    time.sleep(10)
    