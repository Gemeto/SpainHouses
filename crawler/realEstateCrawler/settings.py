import sys
import os
from pathlib import Path
sys.path.append("../")
from configuration import projectSettings
from dotenv import load_dotenv

#Loading the dotenv file to read the constants
load_dotenv(dotenv_path=projectSettings.ENV_FILE_PATH)

#Default crawler settings
BOT_NAME = "realEstateCrawler"
SPIDER_MODULES = ["realEstateCrawler.spiders"]
NEWSPIDER_MODULE = "realEstateCrawler.spiders"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
DOWNLOADER_CLIENT_TLS_METHOD = "TLSv1.2"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"
ROBOTSTXT_OBEY = False
RANDOMIZE_DOWNLOAD_DEALY = True
CONCURRENT_REQUESTS = 10
CONCURRENT_REQUEST_PER_DOMAIN = 1
RETRY_TIMES = 0
CONCURRENT_ITEMS = 10
#CLOSESPIDER_ITEMCOUNT = 10000
DEPTH_PRIOTITY = 0
SCHEDULER_DISK_QUEUE = "scrapy.squeues.PickleFifoDiskQueue"
SHEDULER_MEMORY_QUEUE = "scrapy.squeues.FifoMemoryQueue"

#Route to store images
IMAGES_STORE = projectSettings.IMAGES_PATH

# Default pipelines
ITEM_PIPELINES = {
    "realEstateCrawler.pipelines.AnnouncementImagesPipeline": 1,
    "realEstateCrawler.pipelines.AnnouncementsPostgresPipeline": 2,
}

#Postgres DB settings
POSTGRES_HOSTNAME = "localhost" #TODO unify hosts os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_USERNAME = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')

#Debug settings
DUPEFILTER_DEBUG = True
