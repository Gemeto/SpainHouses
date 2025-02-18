import os
import scrapy
import pymongo
import logging
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from realEstateCrawler.items import ImageItem, AnnouncementItem

class RealestatecrawlerPipeline:
    def process_item(self, item, spider):
        return item
    
class AnnouncementImagesPipeline(ImagesPipeline):
    #Default image extension used if no extension is found in the URL
    DEFAULT_IMAGE_EXT = ".jpg"

    #Overriding this method to manage wich items are requested
    def get_media_requests(self, item, info):
        if isinstance(item, ImageItem):
            image_url = item.get('image_url')
            yield scrapy.Request(image_url)

    #Overriding this method to manage each image file path
    def file_path(self, request, response=None, info=None, *, item=None):
        spider_folder = item.get("spiderName")
        listing_folder = item.get("ref")
        file_ext = os.path.splitext(request.url)[1]
        file_ext = file_ext.split("?")[0]
        if file_ext == "":
            file_ext = self.DEFAULT_IMAGE_EXT
        return f'{spider_folder}/{listing_folder}/{item.get("image_name")}{file_ext}'

class AnnouncementsMongoDBPipeline:
    collection_name = "announcements"

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        logging.getLogger('pymongo').setLevel(logging.WARNING)

    @classmethod
    def from_crawler(cls, crawler):
        user = crawler.settings.get("MONGO_USER")
        password = crawler.settings.get("MONGO_PASS")
        db = crawler.settings.get("MONGO_DB")
        host = crawler.settings.get("MONGO_HOST")
        
        return cls(
            mongo_uri=f"mongodb://{user}:{password}@{host}?authSource=admin",
            mongo_db=db,
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, AnnouncementItem):
            self.db[self.collection_name].insert_one(ItemAdapter(item).asdict())
        return item
