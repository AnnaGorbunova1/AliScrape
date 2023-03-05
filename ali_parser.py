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


def extract_search(response):
    """extract json data from search page"""
    soup = BeautifulSoup(response.text, "html.parser")
    # print(soup.prettify())
    data = soup.find(id="__AER_DATA__", type="application/json").text
    jdata = json.loads(data)
    with open('files/data.txt', 'w') as f:
        json.dump(jdata, f)
    # sel = Selector(response.text)
    # print(os.path.join(os.getcwd(), 'files', 'page.txt'))
    # with open(os.path.join(os.getcwd(), 'files', 'page.txt'), 'w') as f:
    #     f.write(str(soup.prettify(encoding='utf-8')))
    # find script with page data in it
    # script_with_data = sel.xpath('//script[contains(text(),"window.runParams")]')
    # print(script_with_data)
    # # select page data from javascript variable in script tag using regex
    # return json.loads(script_with_data.re(r"window.runParams\s*=\s*({.+?});")[0])


def parse_search(response):
    """Parse search page response for product preview results"""
    data = extract_search(response)
    parsed = []
    for result in data["mods"]["itemList"]["content"]:
        parsed.append(
            {
                "id": result["productId"],
                "url": f"https://www.aliexpress.com/item/{result['productId']}.html",
                "type": result["productType"],  # can be either natural or ad
                "title": result["title"]["displayTitle"],
                "price": result["prices"]["salePrice"]["minPrice"],
                "currency": result["prices"]["salePrice"]["currencyCode"],
                "trade": result.get("trade", {}).get("tradeDesc"),  # trade line is not always present
                "thumbnail": result["image"]["imgUrl"].lstrip("/"),
                "store": {
                    "url": result["store"]["storeUrl"],
                    "name": result["store"]["storeName"],
                    "id": result["store"]["storeId"],
                    "ali_id": result["store"]["aliMemberId"],
                },
            }
        )
    return parsed


def read_json(file):
    with open(file, 'r') as f:
        jdata = json.load(f)
        # print(jdata)
        # pprint.pprint(jdata)
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


    # jdata = read_json('files/data.txt')
    soup = BeautifulSoup(responce, "html.parser")
    data = soup.find(id="__AER_DATA__", type="application/json").text
    jdata = json.loads(data)
    df_new = pd.DataFrame(parse_sku(jdata, item))

    return df_new


def extract_one_item():
    resp = httpx.get("https://aliexpress.ru/item/1005003494066932.html?sku_id=12000026045916248", follow_redirects=True)
    df = pd.DataFrame(columns=['item', 'skuId', 'skuAttr', 'price'])
    df_new = item_list_parser(resp, '1005003494066932')
    df_res = pd.concat([df, df_new])
    print(df_res)


def extract_data(query):
    page = 1
    # запрос и сохранение ответа в файл
    # resp = httpx.get("https://www.aliexpress.com/wholesale?"
    #                  f"catId=&SearchText={query}&page={page}",
    #                  follow_redirects=True)
    # soup = BeautifulSoup(resp.text, "html.parser")
    # with open('files/list.txt', 'w') as f:
    #     f.write(soup.prettify())

    # читаем из сохраненного файла
    with open('files/list.txt', 'r') as f:
        lst = f.read()
    soup = BeautifulSoup(lst, "html.parser")

    # вытаскиваем из страницы список ссылок на товары
    itemslist = soup.find_all("div", class_="product-snippet_ProductSnippet__container__1ettdy product-snippet_ProductSnippet__vertical__1ettdy product-snippet_ProductSnippet__imageSizeM__1ettdy product-snippet_ProductSnippet__hideOptions__1ettdy product-snippet_ProductSnippet__hideDiscount__1ettdy product-snippet_ProductSnippet__hideCashback__1ettdy product-snippet_ProductSnippet__hideSubsidy__1ettdy product-snippet_ProductSnippet__hideFreeDelivery__1ettdy product-snippet_ProductSnippet__hideActions__1ettdy product-snippet_ProductSnippet__hideSponsored__1ettdy product-snippet_ProductSnippet__hasGallery__1ettdy")
    # создаем датафрейм, куда сложим результаты
    df = pd.DataFrame(columns=['item', 'skuId', 'skuAttr', 'price'])
    print(f'found {len(itemslist)} items\n')
    for itl in itemslist:
        itemlink = itl.div.a['href']
        responce = httpx.get("https://aliexpress.ru" + itemlink,
                         follow_redirects=True)
        # print(responce.url)
        if responce.status_code != 200:
            print(f'status code = {responce.status_code} \n')
        else:
            itemId = itl['data-product-id']
            print('item ', itemId, '\n')
            # print(responce.text)
            # парсим страницу товара
            df_new = item_list_parser(responce.text, itemId)
            # присоединяем то, что нашли, к нашему общема датафрейму
            df = pd.concat([df, df_new])

    print(df)


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
    # print(soup.prettify())
    # вытаскиваем из страницы список ссылок на товары
    itemslist = soup.find("div", class_="SearchProductFeed_SearchProductFeed__productFeed__tznhm")
    # print(itemslist)
    if itemslist:
        # создаем датафрейм, куда сложим результаты
        df = pd.DataFrame(columns=['item', 'skuId', 'skuAttr', 'price'])
        print(f'found {len(itemslist.div.contents)} items\n')
        for itl in itemslist.div.contents:
            itemlink = itl.div.a['href']
            driver.get("https://aliexpress.ru" + itemlink)
            time.sleep(3)
            itemId = itl['data-product-id']
            print('item ', itemId, '\n')
            # print(responce.text)
            # парсим страницу товара
            df_new = item_list_parser(driver.page_source, itemId)
            # присоединяем то, что нашли, к нашему общему датафрейму
            df = pd.concat([df, df_new])

        print(df)
    else:
        print('Items not found')
    driver.close()
    driver.quit()
