# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import httpx
import json
import ali_parser
import pprint


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # page = 1
    # sort_type = 'default'
    # query = 'carplay+4gb+ram'
    # resp = httpx.get("https://www.aliexpress.com/wholesale?"
    #                  f"catId=&SearchText={query}&page={page}",
    #                  follow_redirects=True)

    # получаем страницу товара, нужно явно указать первый sku
    # resp = httpx.get("https://aliexpress.ru/item/1005003494066932.html?sku_id=12000026045916248", follow_redirects=True)
    # print(json.dumps(ali_parser.parse_search(resp), indent=2))
    # ali_parser.extract_search(resp)
    # data = ali_parser.read_json('files/data.txt')
    # pprint.pprint(data)

    ali_parser.extract_data_selenium('carplay+2gb+ram')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
