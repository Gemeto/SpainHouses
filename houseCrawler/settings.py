import sys
sys.path.insert(0, "..")
import config as cfg

BOT_NAME = "houseCrawler"
SPIDER_MODULES = ["houseCrawler.spiders"]
NEWSPIDER_MODULE = "houseCrawler.spiders"
#TLS downloader method (TLDv1.2 is required for Idealista)
DOWNLOADER_CLIENT_TLS_METHOD = "TLSv1.2"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
ROBOTSTXT_OBEY = False
CONCURRENT_REQUEST_PER_DOMAIN = 1
#DOWNLOAD_DELAY = 4
RANDOMIZE_DOWNLOAD_DEALY = True
#CLOSESPIDER_ERRORCOUNT = 5
#HTTPERROR_ALLOW_CODES = [404, 403]
RETRY_TIMES = 0
ITEM_PIPELINES = {
    "houseCrawler.pipelines.ListingImagesPipeline": 1,
    "houseCrawler.pipelines.ElasticSearchPipeline": 100
}
IMAGES_STORE = "Images"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"

ELASTICSEARCH_SERVERS = [f"https://{cfg.ELASTICSEARCH_USER}:{cfg.ELASTICSEARCH_PASS}@localhost:9200"]
ELASTICSEARCH_BUFFER_LENGTH = 1
ELASTICSEARCH_INDEX = "announcements_info"
