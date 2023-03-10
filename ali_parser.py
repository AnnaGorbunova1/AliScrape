import pprint
from cgitb import text
import time
import httpx
import pandas as pd
from parsel import Selector
import json
from bs4 import BeautifulSoup
import os
from selenium import webdriver


def read_json(file):
    with open(file, 'r') as f:
        jdata = json.load(f)
        return jdata


def parse_sku(data, item):
    '''
    парсит блок со списком вариантов товара
    :param data: текст json, содержит список вариантов товара с ценами
    :param item: товар
    :return: словарь со списком вариантов и ценами на них
    '''

    # print(data['widgets'][1]['props']['skuInfo']['priceList'][1]['skuId']) #где в файле находится номер варианта товара

    skus = {'item': [], 'skuId': [], 'skuAttr': [], 'price': []}
    for sku in data['widgets'][1]['props']['skuInfo']['priceList']:
        # отбираем только варианты с 4 гб оперативы
        if sku['skuAttr'].find(' 4GB') != -1:
            skus['item'].append(item)
            skus['skuId'].append(sku['skuId'])
            skus['skuAttr'].append(sku['skuAttr'])
            skus['price'].append(sku['activityAmount']['value'])

    return skus


def item_list_parser(responce, item):
    '''
    разбирает страницу со списком найденных по запросу товаров
    :param responce: ответ, полученный от сайта на запрос get
    :param item: товар, который смотрим
    :return: датафрейм со списком товаров и ценами
    '''

    soup = BeautifulSoup(responce, "html.parser")
    data = soup.find(id="__AER_DATA__", type="application/json").text
    jdata = json.loads(data)
    df_new = pd.DataFrame(parse_sku(jdata, item))

    return df_new


def extract_data_selenium(query):
    page = 1

    # обходим блокировку парсеров
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.headless = True
    driver = webdriver.Chrome(
        executable_path="files/chromedriver.exe",
        options=options
    )

    driver.get("https://www.aliexpress.com/wholesale?"
                     f"SearchText={query}&page={page}")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    # вытаскиваем из страницы список ссылок на товары
    items_list = soup.find("div", class_="SearchProductFeed_SearchProductFeed__productFeed__tznhm")
    # print(items_list)
    if items_list:
        # создаем датафрейм, куда сложим результаты
        df = pd.DataFrame(columns=['item', 'skuId', 'skuAttr', 'price'])
        print(f'found {len(items_list.div.contents)} items\n')
        for itl in items_list.div.contents:
            item_link = itl.div.a['href']
            driver.get("https://aliexpress.ru" + item_link)
            time.sleep(3)
            item_id = itl['data-product-id']
            print('item ', item_id, '\n')
            # print(responce.text)
            # парсим страницу товара
            df_new = item_list_parser(driver.page_source, item_id)
            # присоединяем то, что нашли, к нашему общему датафрейму
            df = pd.concat([df, df_new])

        print(df)
    else:
        print('Items not found')
    driver.close()
    driver.quit()
