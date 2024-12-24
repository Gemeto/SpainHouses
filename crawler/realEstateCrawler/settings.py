import sys
print("ASJHDSAOIHDOSADJPOSAJDPSAJDSAKDJKDLSJALKDJSALKDJL")
sys.path.append("../")
from configuration import projectSettings, secrets

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

#Route to store images
IMAGES_STORE = "../" + projectSettings.IMAGES_PATH

# Default pipelines
ITEM_PIPELINES = {
    "realEstateCrawler.pipelines.AnnouncementImagesPipeline": 1,
    "realEstateCrawler.pipelines.AnnouncementsPostgresPipeline": 2,
}

#Postgres DB settings
POSTGRES_HOSTNAME = secrets.POSTGRES_HOSTNAME
POSTGRES_PORT = secrets.POSTGRES_PORT
POSTGRES_USERNAME = secrets.POSTGRES_USERNAME
POSTGRES_PASSWORD = secrets.POSTGRES_PASSWORD
POSTGRES_DB = secrets.POSTGRES_DB
