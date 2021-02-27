import scrapy
import json
# from datetime import datetime as dtm


class InstaFollowersSpider(scrapy.Spider):
    name = 'insta_followers'
    allowed_domains = ['instagram.com']
    start_urls = ['http://instagram.com/']
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    api_url = "/graphql/query/"
    query_hash = {
        "posts": "56a7068fea504063273cc2120ffd54f3",
        "tag_posts": "9b498c08113f1e09617a1703c22b2f32",
        "follow": "d04b0a864b4b54837c0d870b0e77e076",
        "followers": "c76146de99bb02f6415203be841dd25a",
    }
    follow_set_dict = {}
    followers_set_dict = {}

    def __init__(self, login, password, users, cookies_args, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__login = login
        self.__password = password
        self.users = users
        self.__cookies_args = cookies_args

        for el in users:
            self.follow_set_dict[el] = set([])
            self.followers_set_dict[el] = set([])

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
                for current_user in self.users:
                    yield response.follow(f"/{current_user}/", callback=self.user_page_parse)
            else:
                print("Не удалось авторизоваться!")

    def user_page_parse(self, response):
        user_data = self.js_data_extract(response)["entry_data"]["ProfilePage"][0]["graphql"][
            "user"
        ]
        yield from self.get_api_follow_request(response, user_data)
        yield from self.get_api_followers_request(response, user_data)

    def get_api_follow_request(self, response, user_data, variables=None):
        if not variables:
            variables = {
                "id": user_data["id"],
                "first": 100,
            }
        url = f'{self.api_url}?query_hash={self.query_hash["follow"]}&variables={json.dumps(variables)}'
        yield response.follow(
            url, callback=self.get_api_follow, cb_kwargs={"user_data": user_data}
        )

    def get_api_follow(self, response, user_data):
        if b"application/json" in response.headers["Content-Type"]:
            data = response.json()
            try:
                if data["data"]["user"]["edge_follow"]["page_info"]["has_next_page"]:
                    variables = {
                        "id": user_data["id"],
                        "first": 100,
                        "after": data["data"]["user"]["edge_follow"]["page_info"]["end_cursor"],
                    }

                    yield from self.get_api_follow_request(response, user_data, variables)

                yield from self.get_follow_item(user_data, data["data"]["user"]["edge_follow"]["edges"])

            except Exception:
                print('-------------------------------------------')


    def get_follow_item(self, user_data, follow_users_data):
        for user in follow_users_data:
            self.follow_set_dict[user_data['username']].add(user['node']['username'])

    def get_api_followers_request(self, response, user_data, variables=None):
        if not variables:
            variables = {
                "id": user_data["id"],
                "first": 100,
            }
        url = f'{self.api_url}?query_hash={self.query_hash["followers"]}&variables={json.dumps(variables)}'
        yield response.follow(
            url, callback=self.get_api_followers, cb_kwargs={"user_data": user_data}
        )

    def get_api_followers(self, response, user_data):
        if b"application/json" in response.headers["Content-Type"]:
            data = response.json()
            try:
                if data["data"]["user"]["edge_followed_by"]["page_info"]["has_next_page"]:
                    variables = {
                        "id": user_data["id"],
                        "first": 100,
                        "after": data["data"]["user"]["edge_followed_by"]["page_info"]["end_cursor"],
                    }
                    yield from self.get_api_followers_request(response, user_data, variables)

                yield from self.get_followers_item(user_data, data["data"]["user"]["edge_followed_by"]["edges"])

            except Exception:
                print('-------------------------------------------')


    def get_followers_item(self, user_data, followers_users_data):
        for user in followers_users_data:
            self.followers_set_dict[user_data['username']].add(user['node']['username'])

    @staticmethod
    def js_data_extract(response) -> dict:
        script = response.xpath("/html/body/script[contains(text(), 'window._sharedData = ')]/text()").get()
        return json.loads(script.replace('window._sharedData = ', '')[:-1])