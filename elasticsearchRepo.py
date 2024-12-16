from repository import Repository
from elasticsearch import Elasticsearch

class ElasticsearchRepo(Repository):

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
                        "type": "long"
                    },
                    "construction_date": {
                        "type": "date"
                    },
                    "description": {
                        "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 1024
                                }
                            }
                    },
                    "energy_calification": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "energy_consumption": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "image_urls": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 1024
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
                    "offer_type": {
                        "type": "long"
                    },
                    "owner": {
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
                    "ref": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "rooms": {
                        "type": "long"
                    },
                    "spider": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 64
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
                    },
                    "url": {
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
                                "ignore_above": 1024
                            }
                        }
                    },
                    "platform": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 64
                            }
                        }
                    },
                    "spider": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 64
                            }
                        }
                    }
                }
            }
        }
    )

    es = None

    def __init__(self, user, password):
        self.es = Elasticsearch(
            [
                {'host': 'localhost', 'port': 9200, "scheme": "https"}
            ],
            basic_auth=(user, password)
        )
        self.create_db_entity(self.index_announcements_info, self.mappings["index_announcements_info"])
        self.create_db_entity(self.index_failed_urls, self.mappings["index_failed_urls"])

    def create_db_entity(self, index_name, mappings):
        if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=mappings)

    def save(self, table, data):
        self.es.index(
            index=table,
            document=data,
        )
    