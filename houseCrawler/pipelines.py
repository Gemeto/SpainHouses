from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from houseCrawler.items import ImageItem
from scrapy.exceptions import DropItem
import scrapy
import os
from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from six import string_types
import logging
import hashlib
import types
import re
from collections import namedtuple

class HousecrawlerPipeline:
    def process_item(self, item, spider):
        return item
    
class ListingImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if isinstance(item, ImageItem):
            image_url = item.get('image_url')
            yield scrapy.Request(image_url)

    def file_path(self, request, response=None, info=None, *, item=None):
        spider_folder = info.spider.name + "Images"
        listing_folder = os.path.join(spider_folder, item.get("ref"))
        file_ext = os.path.splitext(request.url)[1]
        file_ext = file_ext.split("?")[0]
        if file_ext is None:
            file_ext = ".jpg"
        return f'{listing_folder}/{item.get("image_name")}{file_ext}'
    
class ElasticSearchPipeline(object): #TODO Maybe try to convert this to RepoPipeline more generic to be able to switch repos easly
    settings = None
    es = None
    items_buffer = []

    @classmethod
    def validate_settings(cls, settings):
        def validate_setting(setting_key):
            if settings[setting_key] is None:
                raise InvalidSettingsException('%s is not defined in settings.py' % setting_key)

        required_settings = {'ELASTICSEARCH_INDEX'}

        for required_setting in required_settings:
            validate_setting(required_setting)

    @staticmethod
    def _get_version(es):
        info = es.info()
        vers = info['version']['number']
        match = re.match('(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)', vers)
        major_num = int(match['major'])
        minor_num = int(match['minor'])
        patch_num = int(match['patch'])
        return _VersionInfo(major_num, minor_num, patch_num, vers)

    @classmethod
    def validate_vers_spec_settings(cls, settings, es):
        """Validate with version-specific rules
        """
        def require_setting(setting_key, version):
            if settings[setting_key] is None:
                raise InvalidSettingsException('%s is not defined in settings.py when server version is %s'
                                               % (setting_key, version.full))

        vers = cls._get_version(es)

        # Require only if version is less than 6.2.d.
        if vers.major < 6 or (vers.major == 6 and vers.minor < 2):
            require_setting('ELASTICSEARCH_TYPE', vers)

    @classmethod
    def init_es_client(cls, crawler_settings):
        auth_type = crawler_settings.get('ELASTICSEARCH_AUTH')
        es_timeout = crawler_settings.get('ELASTICSEARCH_TIMEOUT',60)

        es_servers = crawler_settings.get('ELASTICSEARCH_SERVERS', 'localhost:9200')
        es_servers = es_servers if isinstance(es_servers, list) else [es_servers]

        if auth_type == 'NTLM':
            from .transportNTLM import TransportNTLM
            es = Elasticsearch(hosts=es_servers,
                               transport_class=TransportNTLM,
                               ntlm_user= crawler_settings['ELASTICSEARCH_USERNAME'],
                               ntlm_pass= crawler_settings['ELASTICSEARCH_PASSWORD'],
                               timeout=es_timeout)

            return es

        es_settings = dict()
        es_settings['hosts'] = es_servers
        es_settings['timeout'] = es_timeout

        if 'ELASTICSEARCH_USERNAME' in crawler_settings and 'ELASTICSEARCH_PASSWORD' in crawler_settings:
            es_settings['http_auth'] = (crawler_settings['ELASTICSEARCH_USERNAME'], crawler_settings['ELASTICSEARCH_PASSWORD'])

        if 'ELASTICSEARCH_CA' in crawler_settings:
            import certifi
            es_settings['port'] = 443
            es_settings['use_ssl'] = True
            es_settings['ca_certs'] = crawler_settings['ELASTICSEARCH_CA']['CA_CERT'] or certifi.where()
            es_settings['client_key'] = crawler_settings['ELASTICSEARCH_CA']['CLIENT_KEY']
            es_settings['client_cert'] = crawler_settings['ELASTICSEARCH_CA']['CLIENT_CERT']

        es = Elasticsearch(**es_settings)
        return es

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        ext.settings = crawler.settings

        cls.validate_settings(ext.settings)
        ext.es = cls.init_es_client(crawler.settings)
        cls.validate_vers_spec_settings(ext.settings, ext.es)
        return ext

    def process_unique_key(self, unique_key):
        if isinstance(unique_key, (list, tuple)):
            unique_key = unique_key[0].encode('utf-8')
        elif isinstance(unique_key, string_types):
            unique_key = unique_key.encode('utf-8')
        else:
            raise Exception('unique key must be str or unicode')

        return unique_key

    def get_id(self, item):
        item_unique_key = item[self.settings['ELASTICSEARCH_UNIQ_KEY']]
        if isinstance(item_unique_key, list):
            item_unique_key = '-'.join(item_unique_key)

        unique_key = self.process_unique_key(item_unique_key)
        item_id = hashlib.sha1(unique_key).hexdigest()
        return item_id

    def index_item(self, item):

        index_name = self.settings['ELASTICSEARCH_INDEX']
        index_suffix_format = self.settings.get('ELASTICSEARCH_INDEX_DATE_FORMAT', None)
        index_suffix_key = self.settings.get('ELASTICSEARCH_INDEX_DATE_KEY', None)
        index_suffix_key_format = self.settings.get('ELASTICSEARCH_INDEX_DATE_KEY_FORMAT', None)

        if index_suffix_format:
            if index_suffix_key and index_suffix_key_format:
                dt = datetime.strptime(item[index_suffix_key], index_suffix_key_format)
            else:
                dt = datetime.now()
            index_name += "-" + datetime.strftime(dt,index_suffix_format)
        elif index_suffix_key:
            index_name += "-" + index_suffix_key

        index_action = {
            '_index': index_name,
            '_source': dict(item)
        }

        # The ES roadmap migrates to a typeless API with ES 7 and later.
        if 'ELASTICSEARCH_TYPE' in self.settings:
            index_action['_type'] = self.settings['ELASTICSEARCH_TYPE']

        if self.settings['ELASTICSEARCH_UNIQ_KEY'] is not None:
            item_id = self.get_id(item)
            index_action['_id'] = item_id
            logging.debug('Generated unique key %s' % item_id)

        self.items_buffer.append(index_action)

        if len(self.items_buffer) >= self.settings.get('ELASTICSEARCH_BUFFER_LENGTH', 500):
            self.send_items()
            self.items_buffer = []

    def send_items(self):
        helpers.bulk(self.es, self.items_buffer)

    def process_item(self, item, spider):
        if isinstance(item, types.GeneratorType) or isinstance(item, list):
            for each in item:
                self.process_item(each, spider)
        else:
            if isinstance(item, ImageItem):#TODO review this custom check to avoid saving img urls on db
                return item
            self.index_item(item)
            logging.debug('Item sent to Elastic Search %s' % self.settings['ELASTICSEARCH_INDEX'])
            return item

    def close_spider(self, spider):
        if len(self.items_buffer):
            self.send_items()

class InvalidSettingsException(Exception):
    pass

_VersionInfo = namedtuple('_VersionInfo', ['major', 'minor', 'patch', 'full'])
