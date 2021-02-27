import json
import scrapy
from ..items import InstagramItem
from datetime import datetime as dtm


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    tag_path = '/explore/tags/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    user_data = {'user_id': None}

    def __init__(self, login, password, tags: list, cookies_args, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__login = login
        self.__password = password
        self.tags = tags
        self.__cookies_args = cookies_args

    def parse(self, response):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.__login,
                    'enc_password': self.__password,
                },
                headers={
                    'X-CSRFToken': js_data['config']['csrf_token'],
                     'cookie': f'ig_cb=2; ig_did={js_data["device_id"]}; {self.__cookies_args} csrftoken={js_data["config"]["csrf_token"]}',
                     'X-Instagram-Ajax': js_data['rollout_hash']
                 }
            )
        except AttributeError:
            if response.json().get('authenticated'):
                print("Авторизация пройдена успешно")
                self.user_data["user_id"]
                for tag in self.tags:
                    tag_url = f'{self.tag_path}{tag}'
                    yield response.follow(tag_url, callback=self.tag_parse)
            else:
                print("Не удалось авторизоваться!")

    def tag_parse(self, response):
        js_data = self.js_data_extract(response)
        for current_tag in js_data['entry_data']['TagPage']:
            data = {'hashtag': current_tag['graphql']["hashtag"], 'status': 'ok'}
            yield self.parse_graphql(data)

        graphql_url = self.next_tag_graphql_url(response, data)
        if graphql_url is not None:
            yield response.follow(graphql_url, callback=self.parse_graphql)

    def parse_graphql(self, data):
        if isinstance(data, dict):
            edge_hashtag_to_media = data["hashtag"]["edge_hashtag_to_media"]
            is_response = False
        else:
            edge_hashtag_to_media = data.json()["data"]["hashtag"]["edge_hashtag_to_media"]
            is_response = True

        for el in edge_hashtag_to_media["edges"]:
            yield InstagramItem(date_parse=dtm.utcnow(), data=el["node"])

        if is_response:
            graphql_url = self.next_tag_graphql_url(data, data.json()["data"])
            if graphql_url is not None:
                yield data.follow(graphql_url, callback=self.parse_graphql)

    @staticmethod
    def next_tag_graphql_url(response, data):
        edge_hashtag_to_media = data["hashtag"]["edge_hashtag_to_media"]
        if edge_hashtag_to_media["page_info"]["has_next_page"]:
            query_hash = '9b498c08113f1e09617a1703c22b2f32'
            variables_dict = {
                'tag_name': data["hashtag"]["name"],
                'first': 12,
                'after': edge_hashtag_to_media["page_info"]["end_cursor"]
            }
            variables = json.dumps(variables_dict)
            graphql_url = f'https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={variables}'
        else:
            graphql_url = None

        return graphql_url

    @staticmethod
    def js_data_extract(response) -> dict:
        script = response.xpath("/html/body/script[contains(text(), 'window._sharedData = ')]/text()").get()
        return json.loads(script.replace('window._sharedData = ', '')[:-1])


