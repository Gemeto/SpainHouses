import scrapy
import datetime
import dateparser
import random
import traceback
from realEstateCrawler.items import ImageItem

class PisosSpider(scrapy.Spider):
    name = "pisos"
    platformName = "pisos"
    index_failed_urls = "failed_urls"
    custom_settings = {
        "JOBDIR": "persistence/" + name,
        "IMAGES_STORE": 'Images'
    }
    start_urls = [
        "https://www.pisos.com/",
    ]

    def parse(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        zone_urls = response.css("a.seo-box__location-link--level1::attr(href)").getall() #Selling
        random.shuffle(zone_urls)
        for zone_url in zone_urls:
            if zone_url not in self.state["processedUrls"]:
                    if "/venta/" in zone_url:
                        yield response.follow(zone_url, dont_filter=True, callback=self.parseZoneAnnouncementsList, errback=self.handleError)
                    else:
                        yield response.follow(zone_url, dont_filter=True, callback=self.parseZoneAnnouncements, errback=self.handleError)

    def parseZoneAnnouncements(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        zone_urls = response.css("a.seo-box__location-link--level2::attr(href)").getall()
        random.shuffle(zone_urls)
        for zone_url in zone_urls:
            if zone_url not in self.state["processedUrls"]:
                    yield response.follow(zone_url, dont_filter=True, callback=self.parseZoneAnnouncementsList, errback=self.handleError)

        next_page = response.css("div.pagination__next a::attr(href)").get()
        if next_page is not None and next_page not in self.state["processedUrls"]:
            yield response.follow(next_page, callback=self.parseZoneAnnouncementsList, errback=self.handleError)

    def parseZoneAnnouncementsList(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        for announcement_url in response.css("div.ad-preview::attr(data-lnk-href)").getall():
            if announcement_url not in self.state["processedUrls"]:
                yield response.follow(announcement_url, callback=self.parseAnnouncement, errback=self.handleError, cb_kwargs=dict(listUrl=response.request.url))

        next_page = response.css("div.pagination__next a::attr(href)").get()
        if next_page is not None and next_page not in self.state["processedUrls"]:
            yield response.follow(next_page, callback=self.parseZoneAnnouncementsList, errback=self.handleError)

    def parseAnnouncement(self, response, listUrl):
        self.state["processedUrls"].add(response.request.url)
        try:
            title = response.css("h1::text").get()
            description = response.css("div.description__content::text").get()
            price = response.css("div.price__value::text").get()
            price = None if price is not None and "A consultar" in price else price
            if price is not None:
                price = int(self.deleteSubstrings(price, [".", "€"]))
            location = response.css("div.details__block p:first-of-type::text").get()
            energyCalification = response.css("span.energy-certificate__tag::text").get()
            update_date = dateparser.parse(response.css("p.last-update__date::text").get().split()[-1]).isoformat()
            energyConsumption = response.css("div.energy-certificate__data span:nth-of-type(2) span::text").get()
            owner = response.css("p.owner-info__name a::text").get()
            features = response.css("div.features__feature")
            rooms = None
            rooms_feature_index = next((i for i, x in enumerate(features) if x.css("span.features__label::text").get().startswith("Habitaciones: ")), None)
            if rooms_feature_index is not None:
                rooms = int(features[rooms_feature_index].css("span.features__value::text").get())
            constructed_m2 = None
            constructed_m2_feature_index = next((i for i, x in enumerate(features) if x.css("span.features__label::text").get().startswith("Superficie construida: ")), None)
            if constructed_m2_feature_index is not None:
                constructed_m2 = int(self.deleteSubstrings(features[constructed_m2_feature_index].css("span.features__value::text").get(), [".", "m²"]))
            ref = None
            ref_feature_index = next((i for i, x in enumerate(features) if x.css("span.features__label::text").get().startswith("Referencia: ")), None)
            if ref_feature_index is not None:
                ref = features[ref_feature_index].css("span.features__value::text").get().replace("/", "--") #Replacing slashes to avoid creating subdirectories when saving the images
            construction_date = None
            construction_date_feature_index = next((i for i, x in enumerate(features) if x.css("span.features__label::text").get().startswith("Antigüedad: ")), None)
            if construction_date_feature_index is not None:
                cosntruction_date_string = features[construction_date_feature_index].css("span.features__value::text").get()
                if "Entre" in cosntruction_date_string:
                    construction_date = dateparser.parse("Hace " + cosntruction_date_string.split()[-2] + "años").isoformat()
            image_urls = response.css("div[data-media-type='Photo'] div picture img::attr(src)").getall()
            image_urls = image_urls + response.css("div[data-media-type='Photo'] div picture img::attr(data-src)").getall()
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