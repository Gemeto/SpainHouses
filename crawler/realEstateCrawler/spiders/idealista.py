import scrapy
import datetime
import dateparser
import json
from scrapy.exceptions import CloseSpider
from realEstateCrawler.items import ImageItem, AnnouncementItem
from offerParser import deleteSubstrings, getLocationParsedComponent
import sys
sys.path.append("../")
import constants.zoneFilters as zf
import constants.announcementTypeFilters as tf

class IdealistaSpider(scrapy.Spider):

    #Spider name
    name = "idealista"

    #Spider settings
    custom_settings = {
        "DOWNLOAD_SLOTS": {
            "www.idealista.com": {"delay": 7},
            "api.geocodify.com": {"delay": 2}
        },
        "DOWNLOADER_MIDDLEWARES": {
            'realEstateCrawler.middlewares.SeleniumBaseDownloadMiddleware': 1,
        },
        "JOBDIR": "jobs/" + name,
    }
    #Spider starting urls
    start_url = "https://www.idealista.com"
    
    geocodify_url = "https://api.geocodify.com/v2/parse?api_key=lCWart5tdT5gPVkKrFFdLioAo892C9WF&address=" #TODO delete my api key from the url

    #Default price/size filters
    max_price_filter = 1000000
    price_filter_interval = 50000
    max_size_filter = 2000
    size_filter_interval = 50

    #Zone filters
    zone_filters = {
        zf.ANDALUCIA: "andalucia",
        zf.ARAGON: "aragon",
        zf.CANTABRIA: "cantabria",
        zf.CASTILLALEON: "castilla-y-leon",
        zf.CASTILLALAMANCHA: "castilla-la-mancha",
        zf.CATALUÑA: "cataluna",
        zf.NAVARRA: "navarra",
        zf.VALENCIA: "comunidad-valenciana",
        zf.MADRID: "madrid-provincia",
        zf.EXTREMADURA: "extremadura",
        zf.GALICIA: "galicia",
        zf.BALEARES: "balears-illes",
        zf.CANARIAS: "islas-canarias",
        zf.RIOJA: "la-rioja",
        zf.EUSKADI: "pais-vasco",
        zf.ASTURIAS: "asturias",
        zf.MURCIA: "murcia-provincia",
    }

    def start_requests(self):
        if hasattr(self, "max_price_filter"):
            self.max_price_filter = self.max_price_filter
        if hasattr(self, "max_size_filter"):
            self.max_size_filter = self.max_size_filter

        if hasattr(self, "target_announcement_url"):
                url = self.target_announcement_url
                yield scrapy.Request(url, callback=self.parseAnnouncement, cb_kwargs=dict(listUrl="https://www.idealista.com/"),
                    meta={
                        "selenium": True,
                        "scrollTo": "div.images-slider"
                    }
                )
        else:
            if hasattr(self, "announcement_type_filter") and self.announcement_type_filter == tf.ALQUILER:
                url = f"{self.start_url}/alquiler-viviendas/"
            else:
                url = f"{self.start_url}/venta-viviendas/"

            yield scrapy.Request(url, callback=self.parse, meta={"selenium": True})
        
    def parse(self, response):
        zone_links = response.css("ul.locations-list__links")
        for zone in zone_links:

            size_filter = 0
            if hasattr(self, "min_size_filter"):
                size_filter = self.min_size_filter
            if (self.max_size_filter - size_filter) <= self.size_filter_interval:
                self.size_filter_interval = int((self.max_size_filter - size_filter) / 2)

            zone_link = zone.css("li:nth-child(1) a::attr(href)").get()
            if not hasattr(self, "zone_filter") or self.zone_filters[self.zone_filter] == zone_link.split("/")[-2]:

                size_limit = self.max_size_filter - self.size_filter_interval
                if hasattr(self, "min_size_filter"):
                    size_limit += self.min_size_filter

                while size_filter < size_limit:
                    max_size_filter = self.getMaxSizeFilter(size_filter)
                    price_filter = 0
                    if hasattr(self, "min_price_filter"):
                        price_filter = self.min_price_filter
                    if (self.max_price_filter - price_filter) <= self.price_filter_interval:
                        self.price_filter_interval = int((self.max_price_filter - price_filter) / 2)

                    price_limit = self.max_price_filter - self.price_filter_interval
                    if hasattr(self, "min_price_filter"):
                        price_limit += self.min_price_filter

                    while price_filter < price_limit:
                        max_price_filter = self.getMaxPriceFilter(price_filter)
                        url = (zone_link.replace("/municipios", "") + "/con-precio-hasta_"+str(max_price_filter)+",precio-desde_"+str(price_filter)
                        +",metros-cuadrados-mas-de_"+str(size_filter)+",metros-cuadrados-menos-de_"+str(max_size_filter)
                        +"/?ordenado-por=fecha-publicacion-desc")
                        yield scrapy.Request(response.urljoin(url), priority=1, callback=self.parseZoneAnnouncementsList, meta={"selenium": True})
                        
                        price_filter += self.price_filter_interval
                    size_filter += self.size_filter_interval

    def parseZoneAnnouncementsList(self, response):
        for announcement in response.css("article.item"):
            announcement_link = announcement.css("a.item-link::attr(href)").get()
            yield scrapy.Request(
                response.urljoin(announcement_link),
                priority=3,
                callback=self.parseAnnouncement,
                cb_kwargs=dict(listUrl=response.request.url),
                meta={
                    "selenium": True, 
                    "scrollTo": "div.images-slider"
                }
            )

        next_page = response.css("li.next a::attr(href)").get()
        if next_page is not None:
            yield scrapy.Request(response.urljoin(next_page), priority=2, callback=self.parseZoneAnnouncementsList, meta={"selenium": True})

    def parseAnnouncement(self, response, listUrl):
        #if response.css("span.info-data-price span::text").get() is None: #If no price is found, it is a captcha view
            #raise CloseSpider("Captcha detected, idealista is blocking this IP")
        
        announcement_data = {}
        announcement_data["url"] = response.request.url
        announcement_data["listUrl"] = listUrl
        announcement_data["title"] = response.css("span.main-info__title-main::text").get()
        announcement_data["description"] = ''.join(response.css("div.comment div p::text").extract())
        announcement_data["price"] = int(response.css("span.info-data-price span::text").get().replace(".",""))
        announcement_data["ref"] = response.css("p.txt-ref::text").get().replace("\n", "")
        announcement_data["energyConsumption"] = response.css("div.details-property_features:last-of-type span:nth-of-type(2)::text").get()
        header_features = response.css("div.info-features > span::text").getall()
        features = response.css("div.details-property_features:first-of-type li::text").getall()

        announcement_data["rooms"] = self.parseFeature(header_features, "hab.")
        if announcement_data["rooms"] is not None:
            announcement_data["rooms"] = int(announcement_data["rooms"].replace("hab.", ""))

        announcement_data["constructed_m2"] = self.parseFeature(header_features, "m²")
        if announcement_data["constructed_m2"] is not None:
            announcement_data["constructed_m2"] = int(deleteSubstrings(announcement_data["constructed_m2"], [".", "m²"]))

        announcement_data["energyCalification"] = response.css("div.details-property_features:last-of-type span:nth-of-type(2)::attr(class)").get()
        if announcement_data["energyCalification"] is not None:
            announcement_data["energyCalification"] = announcement_data["energyCalification"].replace("icon-energy-c-", "")

        announcement_data["construction_date"] = self.parseFeature(features, "Construido")
        if announcement_data["construction_date"] is not None:
            announcement_data["construction_date"] = datetime.date(int(announcement_data["construction_date"].replace("Construido en ", "")), 1, 1).isoformat()

        announcement_data["locationStr"] = ""
        location_details = response.css("li.header-map-list::text").getall()
        for location_detail in location_details:
            announcement_data["locationStr"] = f"{announcement_data['locationStr']} {location_detail.strip()}"

        announcement_data["owner"] = response.css("div.professional-name span:first-of-type input[name='user-name']::attr(value)").get()
        if announcement_data["owner"] is None:
            announcement_data["owner"] = response.css("a.about-advertiser-name::text").get()

        date = dateparser.parse(response.css("p.stats-text::text").get().replace("Anuncio actualizado el ", ""))
        announcement_data["update_date"] = date.isoformat() if date is not None else None

        image_urls = response.css("img.detail-image-gallery::attr(src)").getall()
        img_number = 1
        for image_url in image_urls:
            yield ImageItem(
                image_url=image_url,
                image_name=f'{announcement_data["ref"]}_{img_number}',
                ref=announcement_data["ref"],
                spiderName=self.name,
            )
            img_number = img_number + 1
        announcement_data["image_urls"] = ", ".join(image_urls) if image_urls is not None else None

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
        announcement_data["location"]["country"] = getLocationParsedComponent(location_data, "country")
        announcement_data["location"]["state"] = getLocationParsedComponent(location_data, "state")
        announcement_data["location"]["city"] = getLocationParsedComponent(location_data, "city")
        announcement_data["location"]["postcode"] = getLocationParsedComponent(location_data, "postcode")
        announcement_data["location"]["street"] = getLocationParsedComponent(location_data, "road")
        announcement_data["location"]["number"] = getLocationParsedComponent(location_data, "house_number")

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

    def getMaxPriceFilter(self, price_filter):
        max_price_filter = price_filter + self.price_filter_interval
        if max_price_filter > self.max_price_filter:
            max_price_filter = self.max_price_filter
        return max_price_filter
    
    def getMaxSizeFilter(self, size_filter):
        max_size_filter = size_filter + self.size_filter_interval
        if max_size_filter > self.max_size_filter:
            max_size_filter = self.max_size_filter
        return max_size_filter
    
    def parseFeature(self, features, feature_name):
        index = next((i for i, x in enumerate(features) if feature_name in x), None)
        if index is not None:
            return features[index]
        return None

    def getLocationParsedComponent(self, location_data, component):
        index = next((x for i, x in enumerate(location_data["response"]) if "label" in location_data["response"][x] and component in location_data["response"][x]["label"]), None)
        if index is not None:
            return location_data["response"][index]["value"]
        return None