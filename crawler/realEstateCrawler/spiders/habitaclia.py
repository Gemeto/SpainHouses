import scrapy
import datetime
import dateparser
import json
from realEstateCrawler.items import ImageItem, AnnouncementItem
from offerParser import deleteSubstrings, parseGeocodifyLocationComponents, parseFeature
import sys
sys.path.append("../")
import constants.zoneFilters as zf
import constants.announcementTypeFilters as tf

class HabitacliaSpider(scrapy.Spider):
    #Spider name
    name = "habitaclia"
    
    #Spider settings
    custom_settings = {
        "DOWNLOAD_SLOTS": {
            "www.habitaclia.com": {"delay": 2},
            "api.geocodify.com": {"delay": 2}
        },
        "DOWNLOADER_MIDDLEWARES": {
            "realEstateCrawler.middlewares.SeleniumBaseDownloadMiddleware": 1,
        },
        "JOBDIR": "jobs/" + name
    }

    #Spider starting urls
    start_url = "https://www.habitaclia.com/"

    geocodify_url = "https://api.geocodify.com/v2/parse?api_key=lCWart5tdT5gPVkKrFFdLioAo892C9WF&address=" #TODO delete my api key from the url

    #Zone filters
    zone_filters = {
        zf.ANDALUCIA: ["malaga", "almeria", "cadiz", "cordoba", "granada", "huelva", "jaen", "malaga", "sevilla"],
        zf.ARAGON: ["huesca", "teruel", "zaragoza"],
        zf.CANTABRIA: ["cantabria"],
        zf.CASTILLALEON: ["avila", "burgos", "leon", "palencia", "salamanca", "segovia", "soria", "valladolid", "zamora"],
        zf.CASTILLALAMANCHA: ["albacete", "ciudad_real", "cuenca", "guadalajara", "toledo"],
        zf.CATALUÑA: ["barcelona", "bcn", "girona", "lleida", "tarragona"],
        zf.NAVARRA: ["navarra"],
        zf.VALENCIA: ["alicante", "castellon", "valencia"],
        zf.MADRID: ["madrid"],
        zf.EXTREMADURA: ["badajoz", "caceres"],
        zf.GALICIA: ["la_coruna", "lugo", "ourense", "pontevedra"],
        zf.BALEARES: ["balears"],
        zf.CANARIAS: ["islas_canarias"],
        zf.RIOJA: ["la_rioja"],
        zf.EUSKADI: ["alava", "guipuzcoa", "vizcaya"],
        zf.ASTURIAS: ["asturias"],
        zf.MURCIA: ["murcia"],
    }

    def start_requests(self):
        if hasattr(self, "target_announcement_url"):
                url = self.target_announcement_url
                yield scrapy.Request(url, callback=self.parseAnnouncement, meta={"selenium": True}, cb_kwargs=dict(listUrl="https://www.habitaclia.com/"))
        else:
            url = self.start_url
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for zone in response.css("select#cod_prov option::attr(value)").getall():
            if not hasattr(self, "zone_filter") or zone in self.zone_filters[self.zone_filter]:
                if hasattr(self, "announcement_type_filter") and self.announcement_type_filter == tf.ALQUILER:
                    zone_url = f"/alquiler-vivienda-en-{zone}/buscador.htm"
                else:
                    zone_url = f"/comprar-vivienda-en-{zone}/buscador.htm"
                yield scrapy.Request(response.urljoin(zone_url), priority=1, callback=self.parseZoneLinks, meta={"selenium": True})

    def parseZoneLinks(self, response):
        zone_url = response.css("div.ver-todo-zona a::attr(href)").get()
        if zone_url is not None:
            url = self.getUrlWithFilters(zone_url + "?ordenar=mas_recientes")
            yield scrapy.Request(response.urljoin(url), priority=3, callback=self.parseZoneList, meta={"selenium": True})
        else:
            for zone_link in response.css("div#enlacesmapa ul.verticalul li a::attr(href)").getall():
                yield scrapy.Request(response.urljoin(zone_link), priority=2, callback=self.parseZoneLinks, meta={"selenium": True})
        if response.css("div#enlacesmapa ul.verticalul li a::attr(href)").getall() is None:
            yield scrapy.Request(response.urljoin(url), priority=3, callback=self.parseZoneList, meta={"selenium": True})

    def parseZoneList(self, response):
        for announcement_link in response.css("article.js-list-item::attr(data-href)").getall():
            yield scrapy.Request(
                response.urljoin(announcement_link), 
                priority=3, 
                callback=self.parseAnnouncement, 
                meta={"selenium": True}, 
                cb_kwargs=dict(listUrl=response.request.url)
            )

        next_page = response.css("li.next a::attr(href)").get()
        if next_page is not None:
            yield scrapy.Request(response.urljoin(next_page), priority=4, callback=self.parseZoneList, meta={"selenium": True})

    def parseAnnouncement(self, response, listUrl):
        announcement_urls = response.css("section.typologies-all a[title='Ver anuncio']::attr(href)").getall()
        for announcement_url in announcement_urls:
            yield scrapy.Request(
                response.urljoin(announcement_url), 
                priority=5, 
                callback=self.parseAnnouncement, 
                meta={"selenium": True}, 
                cb_kwargs=dict(listUrl=response.request.url)
            )
        
        if len(announcement_urls) == 0:
            announcement_data = {}
            announcement_data["url"] = response.request.url
            announcement_data["listUrl"] = listUrl
            announcement_data["title"] = response.css("h1:first-of-type::text").get()
            announcement_data["description"] = response.css("p.detail-description::text").get()
            announcement_data["update_date"] = dateparser.parse(response.css("time::text").get()).isoformat()
            distribution = response.css("article.has-aside:nth-of-type(2) ul li::text").getall()
            features = response.css("article.has-aside:nth-of-type(3) ul li::text").getall()

            announcement_data["price"] = None
            priceStr = response.css("div.price span[itemprop=price]::text").get()
            if priceStr is not None:
                announcement_data["price"] = int(deleteSubstrings(priceStr, " .€"))

            announcement_data["locationStr"] = ""
            location_items = response.css("h4.address::text").getall()
            for item in location_items:
                announcement_data["locationStr"] = f"{announcement_data['locationStr']} {item.strip()}"

            announcement_data["rooms"] = parseFeature(distribution, "habitaciones")
            if announcement_data["rooms"] is not None:
                announcement_data["rooms"] = int(announcement_data["rooms"].replace(" habitaciones", ""))

            announcement_data["constructed_m2"] = parseFeature(distribution, "Superficie")
            if announcement_data["constructed_m2"] is not None:
                announcement_data["constructed_m2"] = int(deleteSubstrings(announcement_data["constructed_m2"], ["Superficie ", "m"]))

            announcement_data["ref"] = response.css("h4.subtitle::text").get()
            if announcement_data["ref"] is not None:
                announcement_data["ref"] = deleteSubstrings(announcement_data["ref"], ["Referencia del anuncio habitaclia/", ":", " "])

            announcement_data["energyCalification"] = response.css("div.rating::attr(class)").get()
            announcement_data["energyConsumption"] = response.css("div.rating-box:first-of-type::text").get()
            if announcement_data["energyConsumption"] is not None:
                announcement_data["energyConsumption"] = announcement_data["energyConsumption"].strip().replace("Consumo:", "")
            if announcement_data["energyCalification"] is not None:
                announcement_data["energyCalification"] = announcement_data["energyCalification"].replace("rating c-", "")

            announcement_data["owner"] = response.css("h2#titulo-formDades::text").get()
            if announcement_data["owner"] is not None:
                announcement_data["owner"] = announcement_data["owner"].replace("Contactar ", "")

            announcement_data["construction_date"] = parseFeature(features, "Año construcción")
            if announcement_data["construction_date"] is not None:
                announcement_data["construction_date"] = datetime.date(int(announcement_data["construction_date"].replace("Año construcción ", "")), 1, 1).isoformat()

            announcement_data["image_urls"] = response.css("div.ficha_foto img::attr(src)").getall()
            img_number = 1
            for image_url in announcement_data["image_urls"]:
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                yield ImageItem(
                    image_url=image_url,
                    image_name=f'{announcement_data["ref"]}_{img_number}',
                    ref=announcement_data["ref"],
                    spiderName=self.name,
                )
                img_number = img_number + 1
            if announcement_data["image_urls"] is not None:
                announcement_data["image_urls"] = ", ".join(announcement_data["image_urls"])
            
            announcement_data["url"] = response.request.url
            announcement_data["listUrl"] = listUrl

            yield scrapy.Request(self.geocodify_url + announcement_data["locationStr"],
                dont_filter=True,
                priority=5,
                callback=self.parseAnnouncementLocation,
                errback=self.errbackLocationParse,
                cb_kwargs=dict(announcement_data=announcement_data)
            )

    def parseAnnouncementLocation(self, response, announcement_data):
        location_data = json.loads(response.body)
        announcement_data["location"] = {}
        announcement_data["location"]["text"] = announcement_data["locationStr"]
        announcement_data["location"]["country"] = parseGeocodifyLocationComponents(location_data, "country")
        announcement_data["location"]["state"] = parseGeocodifyLocationComponents(location_data, "state")
        announcement_data["location"]["city"] = parseGeocodifyLocationComponents(location_data, "city")
        announcement_data["location"]["postcode"] = parseGeocodifyLocationComponents(location_data, "postcode")
        announcement_data["location"]["street"] = parseGeocodifyLocationComponents(location_data, "road")
        announcement_data["location"]["number"] = parseGeocodifyLocationComponents(location_data, "house_number")

        yield AnnouncementItem(
            timestamp = datetime.datetime.now().isoformat(),
            update_date = announcement_data["update_date"],
            title = announcement_data["title"],
            description = announcement_data["description"],
            price = announcement_data["price"],
            location = announcement_data["location"],
            rooms = announcement_data["rooms"],
            constructed_m2 = announcement_data["constructed_m2"],
            ref = announcement_data["ref"],
            energy_calification = announcement_data["energyCalification"],
            energy_consumption = announcement_data["energyConsumption"] if announcement_data["energyConsumption"] is not None else "",
            construction_date = announcement_data["construction_date"],
            owner = announcement_data["owner"],
            offer_type = self.announcement_type_filter if hasattr(self, "announcement_type_filter") else 1,
            image_urls = announcement_data["image_urls"],
            url = announcement_data["url"],
            list_url = announcement_data["listUrl"],
            spider = self.name
        )

    def errbackLocationParse(self, failure):
        announcement_data = failure.request.cb_kwargs["announcement_data"]
        announcement_data["location"] = {}
        announcement_data["location"]["text"] = announcement_data["locationStr"]

        yield AnnouncementItem(
            timestamp = datetime.datetime.now().isoformat(),
            update_date = announcement_data["update_date"],
            title = announcement_data["title"],
            description = announcement_data["description"],
            price = announcement_data["price"],
            location = announcement_data["location"],
            rooms = announcement_data["rooms"],
            constructed_m2 = announcement_data["constructed_m2"],
            ref = announcement_data["ref"],
            energy_calification = announcement_data["energyCalification"],
            energy_consumption = announcement_data["energyConsumption"],
            construction_date = announcement_data["construction_date"],
            owner = announcement_data["owner"],
            offer_type = self.announcement_type_filter if hasattr(self, "announcement_type_filter") else 1,
            image_urls = announcement_data["image_urls"],
            url = announcement_data["url"],
            list_url = announcement_data["listUrl"],
            spider = self.name
        )

    def getUrlWithFilters(self, url):
            if hasattr(self, "min_price_filter") and self.min_price_filter > 0:
                url = f"{url}&pmin={self.min_price_filter}"
            if hasattr(self, "max_price_filter"):
                url = f"{url}&pmax={self.max_price_filter}"
            if hasattr(self, "min_size_filter"):
                url = f"{url}&m2={self.min_size_filter}"

            return url
