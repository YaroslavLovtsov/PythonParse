import scrapy
import pymongo
import re
from urllib.parse import urljoin

def characteristics_map_hard(data_characteristics):
    keys_list = data_characteristics.css("div.AdvertSpecs_label__2JHnS::text").getall()
    values_list1 = data_characteristics.css("div.AdvertSpecs_data__xK2Qx::text").getall()
    values_list2 = data_characteristics.css("div.AdvertSpecs_data__xK2Qx").css("a::text").getall()

    dict_res = {}

    try:
        dict_res[keys_list[0]] = values_list2[0]
        dict_res[keys_list[1]] = values_list1[0]
        dict_res[keys_list[2]] = values_list2[1]

        for ind in range(3, len(keys_list)):
            dict_res[keys_list[ind]] = values_list1[ind - 2]
    except Exception:
        pass
    return dict_res

def find_user_link(test_str):
    res = re.search(r'youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar', test_str)
    if res is None:
        return None
    else:
        return res.group(1)

class AutoyuolaSpider(scrapy.Spider):
    name = "autoyuola"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]
    css_query = {
        "brands": "div.TransportMainFilters_brandsList__2tIkv div.ColumnItemList_container__5gTrc a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "ads": "div.SerpSnippet_titleWrapper__38bZM a.blackLink"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_client = pymongo.MongoClient()

    data_query = {
        "title": lambda response: response.css("div.AdvertCard_advertTitle__1S1Ak::text").get(),
        "price": lambda response: response.css("div.AdvertCard_price__3dDCr::text").get(),
        "description": lambda response: response.css("div.AdvertCard_descriptionInner__KnuRi::text").get(),
        "pictures": lambda response: [el.attrib['src'] for el in response.css("img.PhotoGallery_photoImage__2mHGn")],
        "characteristics": lambda response: characteristics_map_hard(response.css("div.AdvertSpecs_row__ljPcX")),
        "user_id": lambda response: urljoin('https://youla.ru/user/',
                                            ''.join([link for link in [find_user_link(el)
                                                                       for el in response.css("script").getall()]
                                                     if link is not None]))
    }

    @staticmethod
    def gen_tasks(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib.get("href"), callback=callback)

    def parse(self, response):
        yield from self.gen_tasks(
            response, response.css(self.css_query["brands"]), self.brand_parse
        )

    def brand_parse(self, response):
        yield from self.gen_tasks(
            response, response.css(self.css_query["pagination"]), self.brand_parse
        )
        yield from self.gen_tasks(response, response.css(self.css_query["ads"]), self.ads_parse)

    def ads_parse(self, response):
        data = {}
        for key, selector in self.data_query.items():
            try:
                data[key] = selector(response)
            except (ValueError, AttributeError):
                continue
        self.db_client['gb_parse_12_01_2021'][self.name].insert_one(data)


