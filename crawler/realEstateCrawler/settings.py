import sys
import os
from dotenv import load_dotenv
sys.path.append("../")
from configuration import projectPaths

#Load environment variables
load_dotenv(dotenv_path=projectPaths.ENV_FILE_PATH)

#Default crawler settings
BOT_NAME = "realEstateCrawler"
SPIDER_MODULES = ["realEstateCrawler.spiders"]
NEWSPIDER_MODULE = "realEstateCrawler.spiders"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
DOWNLOADER_CLIENT_TLS_METHOD = "TLSv1.2"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"
ROBOTSTXT_OBEY = False
RANDOMIZE_DOWNLOAD_DEALY = True
#CONCURRENT_REQUESTS = 10
CONCURRENT_REQUEST_PER_DOMAIN = 3
RETRY_TIMES = 0
#CONCURRENT_ITEMS = 10
#CLOSESPIDER_ITEMCOUNT = 10000
DEPTH_PRIOTITY = 0
SCHEDULER_DISK_QUEUE = "scrapy.squeues.PickleFifoDiskQueue"
SHEDULER_MEMORY_QUEUE = "scrapy.squeues.FifoMemoryQueue"

#Route to store images
IMAGES_STORE = projectPaths.IMAGES_PATH

# Default pipelines
ITEM_PIPELINES = {
    "realEstateCrawler.pipelines.AnnouncementImagesPipeline": 1,
    "realEstateCrawler.pipelines.AnnouncementsMongoDBPipeline": 2,
}

#Postgres DB settings
MONGO_HOST = "localhost"
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASS = os.getenv('MONGO_PASS')
MONGO_DB = os.getenv('MONGO_DB')

#Geocodify settings
GEOCODIFY_API_URL = f"https://api.geocodify.com/v2/parse?api_key={os.getenv('GEOCODIFY_API_KEY')}&address="

#Debug settings
DUPEFILTER_DEBUG = True
