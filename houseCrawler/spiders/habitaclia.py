import scrapy
import datetime
import traceback
import dateparser

class HabitacliaSpider(scrapy.Spider):
    name = "habitaclia"
    platformName = "habitaclia"
    index_failed_urls = "failed_urls"
    custom_settings = {
        "JOBDIR": "persistence/" + name,
        "DOWNLOADER_MIDDLEWARES": {
            'houseCrawler.middlewares.SeleniumBaseDownloadMiddleware': 800,
        }
    }
    start_urls = [
        "https://www.habitaclia.com/",
    ]

    def parse(self, response):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.url)
        for zone in response.css("select#cod_prov option::attr(value)").getall():
            zone_url = "/comprar-vivienda-en-" + zone + "/buscador.htm"
            yield response.follow(zone_url, dont_filter=True, callback=self.parseZoneLinks, errback=self.handleError, meta={"selenium": True})

    def parseZoneLinks(self, response):
        zone_url = response.css("div.ver-todo-zona a::attr(href)").get()
        if zone_url is not None:
            yield response.follow(zone_url, dont_filter=True, callback=self.parseZoneList, errback=self.handleError, meta={"selenium": True})
        else:
            for zone_link in response.css("div#enlacesmapa ul.verticalul li a::attr(href)").getall():
                yield response.follow(zone_link, dont_filter=True, callback=self.parseZoneLinks, errback=self.handleError, meta={"selenium": True})

        if response.css("div#enlacesmapa ul.verticalul li a::attr(href)").getall() is None:
            yield response.follow(response.css("h2 a::attr(href)").get(), dont_filter=True, callback=self.parseZoneList, errback=self.handleError, meta={"selenium": True})

    def parseZoneList(self, response):
        for announcement_link in response.css("article.js-list-item::attr(data-href)").getall():
            yield response.follow(announcement_link, dont_filter=True, callback=self.parseAnnouncement, errback=self.handleError, meta={"selenium": True}, cb_kwargs=dict(listUrl=response.request.url))

        next_page = response.css("li.next a::attr(href)").get()
        if next_page is not None and next_page not in self.state["processedUrls"]:
            yield response.follow(next_page, callback=self.parseZoneList, errback=self.handleError, meta={"selenium": True})

    def parseAnnouncement(self, response, listUrl):
        self.state["processedUrls"] = self.state.get("processedUrls", set())
        self.state["processedUrls"].add(response.request.url)
        try:
            title = response.css("h1:first-of-type::text").get()
            price = int(self.deleteSubstrings(response.css("div.price span[itemprop=price]::text").get(), " .€"))
            location = response.css("article.location h4 a::attr(title)").get()
            if location is not None:
                location = location.replace("  ", "") + response.css("article.location h4::text").get().replace("  ", "")
            else:
                location = response.css("article.location h4::text").get().replace("  ", "")
            distribution = response.css("article.has-aside:nth-of-type(2) ul li::text").getall()
            rooms = None
            rooms_distribution_index = next((i for i, x in enumerate(distribution) if "habitaciones" in x), None)
            if rooms_distribution_index is not None:
                rooms = int(distribution[rooms_distribution_index].replace(" habitaciones", ""))
            constructed_m2 = None
            constructed_m2_distribution_index = next((i for i, x in enumerate(distribution) if x.startswith("Superficie")), None)
            if constructed_m2_distribution_index is not None:
                constructed_m2 = int(self.deleteSubstrings(distribution[constructed_m2_distribution_index], ["Superficie ", "m"]))
            ref = response.css("h4.subtitle::text").get()
            if ref is not None:
                ref = self.deleteSubstrings(ref, ["Referencia del anuncio habitaclia/", ":"])
            energyCalification = response.css("div.rating::attr(class)").get()
            energyConsumption = self.deleteSubstrings(response.css("div.rating-box:first-of-type::text").get(), ["Consumo:", "\n", " "])
            if(energyCalification is not None):
                energyCalification = energyCalification.replace("rating c-", "")
                energyConsumption = energyConsumption.replace(energyCalification, "")
            #energyEmissions
            owner = response.css("h2#titulo-formDades::text").get()
            if owner is not None:
                owner = owner.replace("Contactar ", "")
            update_date = dateparser.parse(response.css("time::text").get()).isoformat()
            features = response.css("article.has-aside:nth-of-type(3) ul li").getall()
            cosntruction_date = None
            construction_date_index = next((i for i, x in enumerate(features) if x.startswith("Año construcción")), None)
            if construction_date_index is not None:
                cosntruction_date = datetime.parse(int(features[construction_date_index].replace("Año construcción ", "")), 1, 1).isoformat()
            image_urls = response.css("div.ficha_foto img::attr(src)").getall()
            if image_urls is not None:
                image_urls = ", ".join(image_urls)
        except Exception as e:
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
