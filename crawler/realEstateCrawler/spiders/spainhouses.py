import scrapy
import datetime
import dateparser
import traceback
from realEstateCrawler.items import ImageItem

class SpainhousesSpider(scrapy.Spider):
    name = "spainhouses"
    platformName = "spainhouses"
    index_failed_urls = "failed_urls"
    custom_settings = {
        "JOBDIR": "persistence/" + name,
        "ELASTICSEARCH_INDEX": "announcements_info_test",
        "DOWNLOADER_MIDDLEWARES": {
            'realEstateCrawler.middlewares.SeleniumBaseDownloadMiddleware': 800,
        }
    }
    start_urls = [
            "https://www.spainhouses.net/es/venta-viviendas/mas-recientes.html",
    ]

    def parse(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        for announcement_url in response.css("article::attr(data-href)").getall():
            yield response.follow(announcement_url, callback=self.parseAnnouncement, errback=self.handleError, cb_kwargs=dict(listUrl=response.request.url), meta={"selenium": True})

        next_page = response.css("li.nextPage a::attr(href)").get()
        next_page = None
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parseAnnouncement(self, response, listUrl):
        self.state["processedUrls"].add(response.request.url)
        try:
            title = response.css("h1::text").get()
            description = response.css("div#descriptionText::text").get()
            price = response.css("div.price span::text").get()
            if price is not None:
                price = int(self.deleteSubstrings(price, ["."]))
            location = response.css("div.quarterDistrict a::text").get()
            if location is not None:
                location = location.replace("  ", "") + " - " + response.css("div.zoneDiv::text").get()
            else:
                location = response.css("div.zoneDiv::text").get()
            energyCalification = response.css("img.energyRating::attr(title)").get().replace("Calificación Energética ", "")
            if energyCalification == "0":
                energyCalification = None
            stats = response.css("section.statsBlock div::text").getall()
            update_date = None
            update_date_stat_index = next((i for i, x in enumerate(stats) if x.startswith("Actualizado")), None)
            if update_date_stat_index is not None:
                update_date = dateparser.parse(stats[update_date_stat_index].replace("Actualizado el ", "")).isoformat()
            energyConsumption = None
            owner = response.css("div.userBlock_logo img::attr(alt)").get()
            ref = response.css("div.reference strong::text").get()
            features = response.css("section.characteristics ul li::text").getall()
            rooms = None
            rooms_feature_index = next((i for i, x in enumerate(features) if "dormitorio" in x), None)
            if rooms_feature_index is not None:
                rooms = int(features[rooms_feature_index].split()[0])
            constructed_m2 = None
            constructed_m2_feature_index = next((i for i, x in enumerate(features) if x.startswith("Construida: ")), None)
            if constructed_m2_feature_index is not None:
                constructed_m2 = int(self.deleteSubstrings(features[constructed_m2_feature_index], ["Construida: ", ". ", "m²"]))
            construction_date = None #TODO see more listings to check if any has this info
            image_urls = None #response.css("div.imageCol img::attr(src)").getall() #This doesnt work with static request to the listing
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
