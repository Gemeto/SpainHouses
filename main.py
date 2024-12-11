from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from elasticsearch import Elasticsearch
import importlib
import multiprocessing

spiders = [
    "idealista",
    "pisos",
    "properstar",
    "spainhouses",
    #Full webdriver spiders
    "fotocasa",
    "habitaclia",
]
index_announcement_links = "announcement_links"
index_announcements_info = "announcements_info"
index_failed_urls = "failed_urls"
mappings = dict(
      index_announcements_info =
      {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "@timestamp": {
                        "type": "date"
                    },
                    "constructed_m2": {
                    "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "url": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "list_url": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "location": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "platform": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "price": {
                        "type": "long"
                    },
                    "rooms": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "title": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                    }
                    },
                    "update_date": {
                        "type": "date"
                    }
                }
            }
      },
      index_failed_urls =
        {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "@timestamp": {
                        "type": "date"
                    },
                    "url": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "exception_msg": {
                         "type": "text",
                         "fields": {
                              "keyword": {
                                   "type": "keyword",
                                   "ignore_above": 256
                              }
                         }
                    },
                    "platform": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "spider": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    }
                }
            }
        }
)

def main():
    multiprocessing.Pool(len(spiders)).map(runSpiderThread, spiders)

def runSpiderThread(spider):
    es = Elasticsearch(
        [
            {'host': 'localhost', 'port': 9200, "scheme": "https"}
        ],
        basic_auth=('elastic', 'TESTPASS') #TODO Set as docker var to avoid showing credentials on version control
    )
    create_db_index(es, index_announcements_info, mappings["index_announcements_info"])
    create_db_index(es, index_failed_urls, mappings["index_failed_urls"])
    settings = get_project_settings()
    configure_logging(settings)
    process = CrawlerProcess(settings)
    try:
        module = importlib.import_module(f"houseCrawler.spiders.{spider}")
        className = getattr(module, spider.capitalize() + "Spider")
        process.crawl(className, es=es)
    except Exception as e:
        print(f"No se ha podido cargar el spider {spider} debido a un error: {e}")

    process.start()

def create_db_index(es, index_name, mappings):
    if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name, body=mappings)

if __name__ == '__main__':
    main()
