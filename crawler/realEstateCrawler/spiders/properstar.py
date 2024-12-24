import scrapy
import datetime
import dateparser
import random
import traceback
from realEstateCrawler.items import ImageItem

class ProperstarSpider(scrapy.Spider):
    name = "properstar"
    platformName = "properstar"
    index_failed_urls = "failed_urls"
    custom_settings = {
        "JOBDIR": "persistence/" + name,
        "DOWNLOADER_MIDDLEWARES": {
            'realEstateCrawler.middlewares.SeleniumBaseDownloadMiddleware': 800,
        }
    }
    start_urls = [
        "https://www.properstar.es/",
    ]

    def parse(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        zone_urls = response.css("div.tab-pane:nth-of-type(1) a.link::attr(href)").getall() #Selling
        random.shuffle(zone_urls)
        for zone_url in zone_urls:
            if zone_url not in self.state["processedUrls"]:
                yield response.follow(zone_url, dont_filter=True, callback=self.parseZoneAnnouncementsList, errback=self.handleError)

    def parseZoneAnnouncementsList(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        for announcement_url in response.css("a.listing-title::attr(href)").getall():
            if "/project/" not in announcement_url and announcement_url not in self.state["processedUrls"]:
                yield response.follow(announcement_url, callback=self.parseAnnouncement, errback=self.handleError, cb_kwargs=dict(listUrl=response.request.url), meta={"selenium": True})

        next_page = response.css("li.page-link.next a::attr(href)").get()
        if next_page is not None and next_page not in self.state["processedUrls"]:
            yield response.follow(next_page, callback=self.parseZoneAnnouncementsList, errback=self.handleError)

    def parseAnnouncement(self, response, listUrl):
        self.state["processedUrls"].add(response.request.url)
        try:
            title = response.css("h1::text").get()
            description = response.css("div.description-text div div div::text").get()
            price = response.css("div.listing-price-main span::text").get()
            if price is not None:
                price = int(self.deleteSubstrings(price, [".", "€"]))
            location = response.css("span.item-info-address-inner-address::text").get()
            energyCalification = response.css("div.energy-rate-compact-value::text").get()
            update_date = response.css("meta[property='og:updated_time']::attr(content)").get()
            energyConsumption = None
            owner = response.css("h4.account-name::text").get()
            ref = response.css("div.item-highlights::text").get().split()[-1]
            features = response.css("div.feature-content")
            rooms = None
            rooms_feature_index = next(
                (i for i, x in enumerate(features) if x.css("span.property-key::text").get() is not None and x.css("span.property-key::text").get().startswith("Habitaciones"))
                , None)
            if rooms_feature_index is not None:
                rooms = int(features[rooms_feature_index].css("span.property-value::text").get())
            constructed_m2 = None
            constructed_m2_feature_index = next(
                (i for i, x in enumerate(features) if x.css("span.property-key::text").get() is not None and x.css("span.property-key::text").get().startswith("Superficie útil"))
                , None)
            if constructed_m2_feature_index is not None:
                constructed_m2 = int(self.deleteSubstrings(features[constructed_m2_feature_index].css("span.property-value::text").get(), [". ", "m²"]))
            construction_date = None
            construction_date_feature_index = next(
                (i for i, x in enumerate(features) if x.css("span.property-key::text").get() is not None and x.css("span.property-key::text").get().startswith("Año de construcción"))
                , None)
            if construction_date_feature_index is not None:
                construction_date = dateparser.parse(features[construction_date_feature_index].css("span.property-value::text").get()).isoformat()
            image_urls = None #As static content can only access 3 first images, should load dynamic or reverse engeneer the load of images per listing
            img_number = 1
            for image_url in image_urls:
                yield ImageItem(
                    image_url=image_url,
                    image_name=f'{ref}_{img_number}',
                    ref=ref
                )
                img_number = img_number + 1
            if image_urls is not None:
                image_urls = ", ".join(image_urls)
        except Exception:
            print(traceback.format_exc())
            self.es.index(
                index=self.index_failed_urls,
                document={
                    "@timestamp": datetime.datetime.now().isoformat(),
                    "url": response.request.url,
                    "exception_msg": traceback.format_exc(),
                    "platform": self.platformName,
                    "spider": self.name
                },
            )

        yield {
            "@timestamp": datetime.datetime.now().isoformat(),
            "update_date": update_date,
            "title": title,
            "description": description,
            "price": price,
            "location": location,
            "rooms": rooms,
            "constructed_m2": constructed_m2,
            "ref": ref,
            "type": "selling",
            "energy_calification": energyCalification,
            "energy_consumption": energyConsumption,
            "construction_date": construction_date,
            "owner": owner,
            "image_urls": image_urls,
            "url": response.request.url,
            "list_url": listUrl,
            "platform": self.platformName
        }

    def handleError(self, failure):
        if failure.value.response.status == 403:
            self.state["failedUrls"] = self.state.get("failedUrls", set())
            self.state["failedUrls"].add(failure.request.url)

    def close(self, reason):
        self.state["failedUrls"] = self.state.get("failedUrls", set())
        for url in self.state["failedUrls"]:
            self.es.index(
                index=self.index_failed_urls,
                document={
                    "@timestamp": datetime.datetime.now().isoformat(),
                    "url": url,
                    "platform": self.platformName,
                    "spider": self.name
                },
            )

    def deleteSubstrings(self, string, substrings):
        for str in substrings:
            string = string.replace(str, "")
        return string