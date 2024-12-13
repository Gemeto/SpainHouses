from repository import Repository
from elasticsearch import Elasticsearch

class ElasticsearchRepo(Repository):

    es = None

    def __init__(self, user, password):
        self.es = Elasticsearch(
            [
                {'host': 'localhost', 'port': 9200, "scheme": "https"}
            ],
            basic_auth=(user, password)
        )

    def save(self, table, data):
        self.es.index(
            index=table,
            document=data,
        )
    