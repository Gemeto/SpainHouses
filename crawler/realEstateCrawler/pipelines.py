import os
import scrapy
import psycopg2
from scrapy.pipelines.images import ImagesPipeline
from realEstateCrawler.items import ImageItem, AnnouncementItem

class RealestatecrawlerPipeline:
    def process_item(self, item, spider):
        return item
    
class AnnouncementImagesPipeline(ImagesPipeline):
    DEFAULT_IMAGE_EXT = ".jpg"

    def get_media_requests(self, item, info):
        if isinstance(item, ImageItem):
            image_url = item.get('image_url')
            yield scrapy.Request(image_url)

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

        ## Create/Connect to database
        self.connection = psycopg2.connect(host=POSTGRES_HOSTNAME, port=POSTGRES_PORT, user=POSTGRES_USERNAME, password=POSTGRES_PASSWORD, dbname=POSTGRES_DB)
        
        ## Create cursor, used to execute commands
        self.cur = self.connection.cursor()
        
        ## Create announcement table if none exists
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS public.announcement (
                announcementid serial PRIMARY KEY,
                "timestamp" timestamp without time zone,
                update_date date,
                title text,
                description text,
                price integer,
                location text,
                rooms integer,
                constructed_m2 integer,
                ref text,
                energy_calification text,
                energy_consumption text,
                construction_date date,
                owner text,
                offer_type integer,
                image_urls text,
                url text,
                list_url text,
                spider text
            )
        """)

    def process_item(self, item, spider):

        if not isinstance(item, AnnouncementItem):
            return item
        
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

        self.connection.commit()
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()
