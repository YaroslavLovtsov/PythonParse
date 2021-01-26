import os
import requests
import bs4
from dotenv import load_dotenv
from urllib.parse import urljoin
import database
import time
import datetime

class GbParse:
    def __init__(self, start_url, db):
        self.db = db
        self.start_url = start_url
        self.done_url = set()
        self.tasks = [self.parse_task(self.start_url, self.pag_parse)]
        self.done_url.add(self.start_url)

    @staticmethod
    def _get_response(*args, **kwargs):
        # TODO обработки ошибок
        return requests.get(*args, **kwargs)

    def _get_soup(self, *args, **kwargs):
        response = self._get_response(*args, **kwargs)
        return bs4.BeautifulSoup(response.text, "lxml")

    def parse_task(self, url, callback):
        def wrap():
            soup = self._get_soup(url)
            return callback(url, soup)

        return wrap

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.save(result)

    def pag_parse(self, url, soup):
        for a_tag in soup.find("ul", attrs={"class": "gb__pagination"}).find_all("a"):
            pag_url = urljoin(url, a_tag.get("href"))
            if pag_url not in self.done_url:
                task = self.parse_task(pag_url, self.pag_parse)
                self.tasks.append(task)
            self.done_url.add(pag_url)
        for a_post in soup.find("div", attrs={"class": "post-items-wrapper"}).find_all(
                "a", attrs={"class": "post-item__title"}
        ):
            post_url = urljoin(url, a_post.get("href"))
            if post_url not in self.done_url:
                task = self.parse_task(post_url, self.post_parse)
                self.tasks.append(task)
            self.done_url.add(post_url)

    @staticmethod
    def get_comments(*args, **kwargs):
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code >= 299:
                    raise Exception
                time.sleep(0.1)
                return response.json()
            except Exception:
                time.sleep(0.250)

    def get_comments_list(self, dict_of_comments, result_list):
        current_comment = dict_of_comments['comment']
        result_list.append({'id': current_comment['id'], 'user': current_comment['user'],
                            'html': bs4.BeautifulSoup(current_comment['html'], 'lxml').text})
        for child_comment in current_comment['children']:
            self.get_comments_list(child_comment, result_list)

    def post_parse(self, url, soup):
        title = soup.find("h1", attrs={"class": "blogpost-title"}).text
        author_name_tag = soup.find("div", attrs={"itemprop": "author"})

        picture = soup.find("article").find("img").attrs['src']
        article_date = datetime.datetime.strptime(soup.find("time").attrs["datetime"][0:19], "%Y-%m-%dT%H:%M:%S")

        author = {
            "url": urljoin(url, author_name_tag.parent.get("href")),
            "name": author_name_tag.text,
        }
        tags = [
            {"name": tag.text, "url": urljoin(url, tag.get("href"))}
            for tag in soup.find("article").find_all("a", attrs={"class": "small"})
        ]

        commentable_id = soup.find("comments").attrs['commentable-id']
        comment_params = {'commentable_type': 'Post',
                          'commentable_id': commentable_id}

        comments = []
        for comment_dict in self.get_comments("https://geekbrains.ru/api/v2/comments", comment_params):
            self.get_comments_list(comment_dict, comments)

        return {
            "post_data": {
                "url": url,
                "title": title,"picture": picture,
                "publishing_date": article_date,

            },
            "author": author,
            "tags": tags,
            "comments": comments
        }

    def save(self, data: dict):
        # try:
            # print(data)
        self.db.create_post(data)
        # except Exception:
        #     print('----------------------')
        # self.db.create_post(data)


if __name__ == "__main__":
    load_dotenv('.env')
    parser = GbParse("https://geekbrains.ru/posts", database.Database(os.getenv("SQLDB_URL")))
    parser.run()