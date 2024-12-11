import scrapy
import datetime
import dateparser
import random
import traceback
from houseCrawler.items import ImageItem

class IdealistaSpider(scrapy.Spider):
    name = "idealista"
    platformName = "idealista"
    index_failed_urls = "failed_urls"
    maxPriceFilter = 3000000
    priceFilterInterval = 50000
    maxSizeFilter = 900
    sizeFilterInterval = 50
    custom_settings = {
        "JOBDIR": "persistence/" + name,
        "DOWNLOAD_DELAY": 6,
        "DOWNLOADER_MIDDLEWARES": {
            'houseCrawler.middlewares.SeleniumBaseDownloadMiddleware': 800,
        },
        "IMAGES_STORE": 'Images'
    }
    start_urls = [
        "https://www.idealista.com/venta-viviendas/",
    ]

    def parse(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        zone_links = response.css("ul.locations-list__links") #Selling
        random.shuffle(zone_links)
        for zone in zone_links:
            self.state["sizeFilter"] = self.state.get("sizeFilter", 0) #TODO remove upper filter when lower reach max
            zone_link = zone.css("li:nth-child(1) a::attr(href)").get()
            if zone_link not in self.state["processedUrls"]:
                while self.state["sizeFilter"] <= self.maxSizeFilter - self.sizeFilterInterval:
                    self.state["priceFilter"] = self.state.get("priceFilter", 0) #TODO remove upper filter when lower reach max
                    while self.state["priceFilter"] <= self.maxPriceFilter - self.priceFilterInterval:
                        yield response.follow(zone_link.replace("/municipios", "") + "/con-precio-hasta_"+str(self.state["priceFilter"]+self.priceFilterInterval)+",precio-desde_"+str(self.state["priceFilter"])
                                              +",metros-cuadrados-mas-de_"+str(self.state["sizeFilter"])+",metros-cuadrados-menos-de_"+str(self.state["sizeFilter"]+self.sizeFilterInterval)
                                              +"/?ordenado-por=fecha-publicacion-desc", dont_filter=True, callback=self.parseZoneAnnouncementsList, errback=self.handleError)
                        self.state["priceFilter"] += self.priceFilterInterval
                    self.state["priceFilter"] = 0
                    self.state["sizeFilter"] += self.sizeFilterInterval
                self.state["sizeFilter"] = 0

    def parseZoneAnnouncementsList(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        for announcement in response.css("article.item"):
            announcement_link = announcement.css("a.item-link::attr(href)").get()
            if announcement_link not in self.state["processedUrls"]:
                yield response.follow(announcement_link, callback=self.parseAnnouncement, errback=self.handleError, cb_kwargs=dict(listUrl=response.request.url), meta={"selenium": True, "scrollTo": "div.images-slider"})

        next_page = response.css("li.next a::attr(href)").get()
        if next_page is not None and next_page not in self.state["processedUrls"]:
            yield response.follow(next_page, callback=self.parseZoneAnnouncementsList, errback=self.handleError)

    def parseAnnouncement(self, response, listUrl):
        self.state["processedUrls"].add(response.request.url)
        try:
            title = response.css("span.main-info__title-main::text").get()
            description = response.css("div.comment div p::text").get()
            price = int(response.css("span.info-data-price span::text").get().replace(".",""))
            location = response.css("span.main-info__title-minor::text").get()
            rooms = response.css("div.info-features > span:nth-of-type(2)::text").get()
            if rooms is not None and "hab." in rooms: #TODO improve rooms selector and this if
                rooms = int(rooms.replace("hab.", ""))
            else:
                rooms = 0
            constructed_m2 = int(self.deleteSubstrings(response.css("div.info-features > span:first-of-type::text").get(), [".", "m²"]))
            ref = response.css("p.txt-ref::text").get().replace("\n", "")
            energyCalification = response.css("div.details-property_features:last-of-type span:nth-of-type(2)::attr(class)").get()
            if(energyCalification is not None):
                energyCalification = energyCalification.replace("icon-energy-c-", "")
            energyConsumption = response.css("div.details-property_features:last-of-type span:nth-of-type(2)::text").get()
            date = dateparser.parse(response.css("p.date-update-text::text").get().replace("Anuncio actualizado ", ""))
            update_date = date.isoformat() if date is not None else None
            owner = response.css("div.professional-name span:first-of-type::text").get()
            features = response.css("div.details-property_features:first-of-type li::text").getall()
            cosntruction_date = None
            construction_date_feature_index = next((i for i, x in enumerate(features) if x.startswith("Construido")), None)
            if construction_date_feature_index is not None:
                cosntruction_date = datetime.date(int(features[construction_date_feature_index].replace("Construido en ", "")), 1, 1).isoformat()
            image_urls = response.css("img.detail-image-gallery::attr(src)").getall()
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
            "energy_consumption": energyConsumption if energyConsumption is not None else "",
            "construction_date": cosntruction_date,
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
