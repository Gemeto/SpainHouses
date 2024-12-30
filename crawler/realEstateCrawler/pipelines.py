import os
import scrapy
import psycopg2
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
        listing_folder = item.get("ref")
        file_ext = os.path.splitext(request.url)[1]
        file_ext = file_ext.split("?")[0]
        if file_ext == "":
            file_ext = self.DEFAULT_IMAGE_EXT
        return f'{listing_folder}/{item.get("image_name")}{file_ext}'

class AnnouncementsPostgresPipeline:

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            POSTGRES_HOSTNAME = crawler.settings['POSTGRES_HOSTNAME'],
            POSTGRES_PORT = crawler.settings['POSTGRES_PORT'],
            POSTGRES_USERNAME = crawler.settings['POSTGRES_USERNAME'],
            POSTGRES_PASSWORD = crawler.settings['POSTGRES_PASSWORD'],
            POSTGRES_DB = crawler.settings['POSTGRES_DB']
        )

    def __init__(self, POSTGRES_HOSTNAME, POSTGRES_PORT, POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_DB):
        ## Connection to the psotgres database
        self.connection = psycopg2.connect(host=POSTGRES_HOSTNAME, port=POSTGRES_PORT, user=POSTGRES_USERNAME, password=POSTGRES_PASSWORD, database=POSTGRES_DB)
        ## Create cursor to execute commands
        self.cur = self.connection.cursor()
        
    def process_item(self, item, spider):

        if not isinstance(item, AnnouncementItem):
            return item
        else:
            self.saveAnnouncement(item)
            self.connection.commit()
            return item
            
    def saveAnnouncement(self, item):
        self.cur.execute("""
            insert into announcement (
                timestamp,
                update_date,
                title,
                description,
                price,
                location,
                rooms,
                constructed_m2,
                ref,
                energy_calification,
                energy_consumption,
                construction_date,
                owner,
                offer_type,
                image_urls,
                url,
                list_url,
                spider
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
            (
                str(item.get("timestamp", "")),
                str(item.get("update_date", "")) if item.get("update_date", "") is not None else None,
                str(item.get("title", "")) if item.get("title", "") is not None else None,
                str(item.get("description", "")) if item.get("description", "") is not None else None,
                str(item.get("price", "")) if item.get("price", "") is not None else None,
                str(item.get("location", "")) if item.get("location", "") is not None else None,
                str(item.get("rooms", "")) if item.get("rooms", "") is not None else None,
                str(item.get("constructed_m2", "")) if item.get("constructed_m2", "") is not None else None,
                str(item.get("ref", "")) if item.get("ref", "") is not None else None,
                str(item.get("energy_calification", "")) if item.get("energy_calification", "") is not None else None,
                str(item.get("energy_consumption", "")) if item.get("energy_consumption", "") is not None else None,
                str(item.get("construction_date", "")) if item.get("construction_date", "") is not None else None,
                str(item.get("owner", "")) if item.get("owner", "") is not None else None,
                str(item.get("offer_type", "")),
                str(item.get("image_urls", "")) if item.get("image_urls", "") is not None else None,
                str(item.get("url", "")),
                str(item.get("list_url", "")) if item.get("list_url", "") is not None else None,
                str(item.get("spider", ""))
            )
        )

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()
