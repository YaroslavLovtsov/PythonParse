import os
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from instagram.spiders.insta import InstagramSpider


if __name__ == "__main__":
    tags = ['китайскийязык', 'chinesecharacters', 'learnarabic']
    load_dotenv('.env')

    cookies_args = f'mid={os.getenv("MID")}; shbid={os.getenv("SHBID")}; hbts={os.getenv("SHBTS")};'

    crawler_settings = Settings()
    crawler_settings.setmodule("instagram.settings")
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(InstagramSpider, login=os.getenv('INSTA_USERNAME'), password=os.getenv('INSTA_PASSWORD'),
                          tags=tags, cookies_args=cookies_args)
    crawler_process.start()
