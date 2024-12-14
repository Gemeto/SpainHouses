import scrapy
import datetime
import dateparser
import random
import sys
from houseCrawler.items import ImageItem
#Adding root project folder to import custom modules
sys.path.insert(0, "../..")
from utils import saveUrlException, deleteSubstrings
import zoneFilters as zf

class IdealistaSpider(scrapy.Spider):

    #Spider name
    name = "idealista"

    #Spider settings
    custom_settings = {
        #"DOWNLOAD_DELAY": 6,
        "DOWNLOAD_SLOTS": {
            "idealista.com": {"delay": 5}
        },
        "DOWNLOADER_MIDDLEWARES": {
            'houseCrawler.middlewares.SeleniumBaseDownloadMiddleware': 800,
        },
        "IMAGES_STORE": 'Images'
    }
    #Spider starting urls
    start_urls = [
        "https://www.idealista.com/venta-viviendas/",
    ]

    #Price/Size filters
    maxPriceFilter = 3000000
    priceFilterInterval = 50000
    maxSizeFilter = 900
    sizeFilterInterval = 50

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

    #def start_requests(self):
    #    yield scrapy.Request("https://www.idealista.com/inmueble/106176756/", callback=self.parseAnnouncement, cb_kwargs=dict(listUrl="https://www.idealista.com/"), 
    #                meta={
    #                    "selenium": True,
    #                    "scrollTo": "div.images-slider"
    #                }
    #            )

    def parse(self, response):
        zone_links = response.css("ul.locations-list__links") #Selling
        random.shuffle(zone_links)
        for zone in zone_links:
            sizeFilter = 0 #TODO remove upper filter when lower reach max
            zone_link = zone.css("li:nth-child(1) a::attr(href)").get()
            if not hasattr(self, "zoneFilter") or self.zone_filters[self.zoneFilter] == zone_link.split("/")[-2]:
                while sizeFilter <= self.maxSizeFilter - self.sizeFilterInterval:
                    priceFilter = 0 #TODO remove upper filter when lower reach max
                    while priceFilter <= self.maxPriceFilter - self.priceFilterInterval:
                        yield response.follow(zone_link.replace("/municipios", "") + "/con-precio-hasta_"+str(priceFilter + self.priceFilterInterval)+",precio-desde_"+str(priceFilter)
                                              +",metros-cuadrados-mas-de_"+str(sizeFilter)+",metros-cuadrados-menos-de_"+str(sizeFilter + self.sizeFilterInterval)
                                              +"/?ordenado-por=fecha-publicacion-desc", dont_filter=True, callback=self.parseZoneAnnouncementsList)
                        priceFilter += self.priceFilterInterval
                    #priceFilter = 0
                    sizeFilter += self.sizeFilterInterval
                #sizeFilter = 0

    def parseZoneAnnouncementsList(self, response):
        for announcement in response.css("article.item"):
            announcement_link = announcement.css("a.item-link::attr(href)").get()
            yield response.follow(announcement_link, callback=self.parseAnnouncement, cb_kwargs=dict(listUrl=response.request.url), 
                meta={
                    "selenium": True, 
                    "scrollTo": "div.images-slider"
                }
            )

        next_page = response.css("li.next a::attr(href)").get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parseZoneAnnouncementsList)

    def parseAnnouncement(self, response, listUrl):
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
            constructed_m2 = int(deleteSubstrings(response.css("div.info-features > span:first-of-type::text").get(), [".", "m²"]))
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
                    ref=ref,
                    spiderName=self.name,
                    #repository=self.repository,
                )
                img_number = img_number + 1
            if image_urls is not None:
                image_urls = ", ".join(image_urls)
        except Exception:
            saveUrlException(self.repository, response.request.url, self.name)

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
            "spider": self.name
        }
