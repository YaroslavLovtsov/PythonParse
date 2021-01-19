import os
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import bs4
import pymongo
import datetime

DATE_TIME_NOW = datetime.datetime.now()


class MagnitParser:
    def __init__(self, start_url, data_base):
        self.start_url = start_url
        self.database = data_base["gb_parse_12_01_2021"]

    @staticmethod
    def __get_response(url, *args, **kwargs):
        try:
            response = requests.get(url, *args, **kwargs)
            return response
        except:
            return None

    @property
    def data_template(self):
        return {
            "url": lambda tag: urljoin(self.start_url, tag.attrs.get("href")),
            "title": lambda tag: tag.find(
                "div", attrs={"class": "card-sale__title"}
            ).text,
            "date": lambda tag: tag.find(
                "div", attrs={"class": "card-sale__date"}
            ).text.strip().split('\n'),
            "price": lambda tag: tag.find(
                "div", attrs={"class": "card-sale__price"}
            ).text.strip().split('\n'),
            "header": lambda tag: tag.find(
                "div", attrs={"class": "card-sale__header"}
            ).text,
            "img_url": lambda tag: tag.find("img")

        }

    @staticmethod
    def __get_soup(response):
        return bs4.BeautifulSoup(response.text, 'html.parser')
        # //.BeautifulSoup(response.text, "lxml")// так не получилось у меня

    @staticmethod
    def get_date_from_list(prepared_list):
        month_dict = {'января': 1, 'февраля': 2, 'марта': 3,
                      'апреля': 4, 'мая': 5, 'июня': 6,
                      'июля': 7, 'августа': 8, 'сентября': 9,
                      'октября': 10, 'ноября': 11, 'декабря': 12}

        prepared_list[0] = DATE_TIME_NOW.year

        month_str = prepared_list[2]
        if month_str in month_dict:
            prepared_list[2] = month_dict[month_str]
            date_from_list = prepared_list
        else:
            date_from_list = None

        return date_from_list

    def parse_date_interval(self, dates_list):
        prepared_dates_list = list(map(lambda x: x.split(' '), dates_list))
        if len(prepared_dates_list) == 2:
            from_date_list = prepared_dates_list[0]
            to_date_list = prepared_dates_list[1]

            if len(from_date_list) == 3 and len(to_date_list) == 3:
                from_date_list = self.get_date_from_list(from_date_list)
                to_date_list = self.get_date_from_list(to_date_list)

                if (from_date_list is None) or (to_date_list is None):
                    return [None, None]
                else:
                    try:
                        from_date = datetime.datetime(from_date_list[0], from_date_list[2], int(from_date_list[1]),
                                                      0, 0, 0)
                        to_date = datetime.datetime(to_date_list[0], to_date_list[2], int(to_date_list[1]), 0, 0, 0)
                    except ValueError:
                        return [None, None]

                    if from_date > to_date and from_date.month <= DATE_TIME_NOW.month:
                        return [from_date, datetime.datetime(to_date_list[0] + 1, to_date_list[2], int(to_date_list[1]),
                                                             0, 0, 0)]
                    elif from_date > to_date and from_date.month > DATE_TIME_NOW.month:
                        return [datetime.datetime(from_date_list[0] - 1, from_date_list[2], int(from_date_list[1]),
                                                  0, 0, 0),
                                to_date]
                    else:
                        return [from_date, to_date]
            else:
                return [None, None]
        else:
            return [None, None]

    def run(self):
        for product in self.parse(self.start_url):
            if 'title' in product.keys():
                valid = True

                old_price = None
                new_price = None

                if 'price' not in product.keys():
                    valid = False
                elif len(product['price']) == 6:
                    try:
                        old_price = int(product['price'][0]) + int(product['price'][1]) / 100
                        new_price = int(product['price'][4]) + int(product['price'][5]) / 100
                    except:
                        valid = False
                elif len(product['price']) == 2:
                    try:
                        old_price = None
                        new_price = int(product['price'][0]) + int(product['price'][1]) / 100
                    except:
                        valid = False
                else:
                    valid = False

                if valid:
                    date_interval = self.parse_date_interval(product['date'])
                    product_to_save = {'url': product['url'],
                                       'promo_name': product['header'],
                                       'name': product['title'],
                                       'image_url': urljoin(self.start_url, product['img_url'].attrs['data-src']),
                                       'date_from': date_interval[0],
                                       'date_to': date_interval[1],
                                       'old_price': old_price,
                                       'new_price': new_price
                                       }
                    self.save(product_to_save)

    def parse(self, url):
        soup = self.__get_soup(self.__get_response(url))
        catalog_main = soup.find("div", attrs={"class": "сatalogue__main"})
        for product_tag in catalog_main.find_all(
            "a", attrs={"class": "card-sale"}, reversive=False
        ):
            yield self.__get_product_data(product_tag)

    def __get_product_data(self, product_tag):
        data = {}
        for key, pattern in self.data_template.items():
            try:
                data[key] = pattern(product_tag)
            except AttributeError:
                continue

        return data

    def save(self, data):
        collection = self.database["magnit_product"]
        collection.insert_one(data)


if __name__ == "__main__":
    load_dotenv('.env')
    mongo_data_base = pymongo.MongoClient(os.getenv("DATA_BASE_URL"))
    parser = MagnitParser("https://magnit.ru/promo/?geo=moskva", mongo_data_base)
    parser.run()
