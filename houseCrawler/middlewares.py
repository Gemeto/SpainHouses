# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class HousecrawlerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class HousecrawlerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

from scrapy.http import HtmlResponse
from seleniumbase import SB
import urllib3
import time
import random
import logging

class SeleniumBaseDownloadMiddleware: #Custom middleware based on scrapy-selenium middleware, in order to use seleniumbase
    def __init__(self, sb):
        self.sb = sb
        #Disabling some logging that is not really useful if you're not debugging
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('seleniumbase').setLevel(logging.WARNING)
        logging.getLogger('websockets').setLevel(logging.WARNING)
        logging.getLogger('uc').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)

    @classmethod
    def from_crawler(cls, crawler):
        #Disabling urllib3 retries
        urllib3.util.retry.Retry.DEFAULT = urllib3.util.retry.Retry(total=0, connect=0, read=0, redirect=0)
        #Instantiatin seleniumbase driver in CDP mode to avoid bot detection
        with SB(uc=True, headless=True, ad_block=True) as sb:
            middleware = cls(sb)
        #Connecting close signal to the spider
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        #Checking if selenium must be used for the current request
        if "selenium" not in request.meta or not request.meta["selenium"]:
            return None
        #Delay of the request based on the spider config
        initRequestTime = time.time()
        #Calculating the total delay
        randomDelayMagnitude = 1
        if "RANDOMIZE_DOWNLOAD_DEALY" in spider.settings and spider.settings["RANDOMIZE_DOWNLOAD_DEALY"]:
            randomDelayMagnitude = random.uniform(0.5, 1.5)
        if "DOWNLOAD_DELAY" in spider.settings:
            delay = spider.settings["DOWNLOAD_DELAY"] * randomDelayMagnitude
        if "DOWNLOAD_SLOTS" in spider.settings:
            for domain, options in spider.settings["DOWNLOAD_SLOTS"].items():
                if domain in request.url:
                    delay = int(options["delay"] * randomDelayMagnitude)
                    break
        #Calculating the final delay removing the laste rquest time from the total delay
        if "lastRequestTime" in request.meta:
            delay = int(delay - request.meta["lastRequestTime"])
        if delay > 0:
            time.sleep(delay)
        #Requesting the URL
        self.sb.activate_cdp_mode(request.url)
        #Scrolling the webpage if scroll is configured
        self.scroll(request)
        if "scrollUntil" in request.meta:
            while not self.sb.cdp.evaluate(request.meta["scrollUntil"]):
                self.scroll(request)
        #Returning the full response to the spider
        body = self.sb.cdp.get_page_source()
        #Calculating the total time this request took
        requestTime = int(time.time() - initRequestTime)
        request.meta["requestTime"] = requestTime
        #Returning the response to the spider
        return HtmlResponse(
            request.url,
            body=body.encode('utf-8'),
            encoding='utf-8',
            request=request
        )
    
    def scroll(self, request):
        if "scrollTo" in request.meta or "scrollScript" in request.meta:
            if "scrollScript" in request.meta and request.meta["scrollScript"]:
                self.sb.cdp.evaluate(request.meta["scrollScript"])
            elif self.sb.cdp.evaluate(f"document.querySelectorAll('{request.meta["scrollTo"]}').length > 0"):
                self.sb.cdp.scroll_into_view(request.meta["scrollTo"])

    def spider_closed(self):
        self.sb.disconnect()
