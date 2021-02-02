# from itemadapter import ItemAdapter
import pymongo


class HeadHunterPipeline:
    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client['gb_parse_12_01_2021']

    def process_item(self, item, spider):
        self.db[spider.name].insert_one(item)
