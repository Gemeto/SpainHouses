# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class realEstateCrawlerItem(scrapy.Item):
    pass

class AnnouncementItem(scrapy.Item):
    update_date = scrapy.Field()
    timestamp = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()
    location = scrapy.Field()
    rooms = scrapy.Field()
    constructed_m2 = scrapy.Field()
    ref = scrapy.Field()
    energy_calification = scrapy.Field()
    energy_consumption = scrapy.Field()
    construction_date = scrapy.Field()
    owner = scrapy.Field()
    offer_type = scrapy.Field()
    image_urls = scrapy.Field()
    url = scrapy.Field()
    list_url = scrapy.Field()
    spider = scrapy.Field()

class ImageItem(scrapy.Item):
    image_url = scrapy.Field()
    image_name = scrapy.Field()
    ref = scrapy.Field()
    spiderName = scrapy.Field()
