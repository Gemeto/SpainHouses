import scrapy
import datetime
import dateparser
from scrapy.exceptions import CloseSpider
from realEstateCrawler.items import ImageItem, AnnouncementItem
from utils import deleteSubstrings
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
            "www.idealista.com": {"delay": 2}
        },
        "DOWNLOADER_MIDDLEWARES": {
            'realEstateCrawler.middlewares.SeleniumBaseDownloadMiddleware': 1,
        },
        "JOBDIR": "jobs/" + name,
    }
    #Spider starting urls
    start_url = "https://www.idealista.com"

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

            yield scrapy.Request(url, callback=self.parse)
        
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
                        yield scrapy.Request(response.urljoin(url), priority=1, callback=self.parseZoneAnnouncementsList)
                        
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
            yield scrapy.Request(response.urljoin(next_page), priority=2, callback=self.parseZoneAnnouncementsList)

    def parseAnnouncement(self, response, listUrl):
        if response.css("span.info-data-price span::text").get() is None: #If no price is found, it is a captcha view
            raise CloseSpider("Captcha detected, idealista is blocking this IP")
        
        title = response.css("span.main-info__title-main::text").get()
        description = ''.join(response.css("div.comment div p::text").extract())
        price = int(response.css("span.info-data-price span::text").get().replace(".",""))
        ref = response.css("p.txt-ref::text").get().replace("\n", "")
        energyConsumption = response.css("div.details-property_features:last-of-type span:nth-of-type(2)::text").get()
        header_feaures = response.css("div.info-features > span::text").getall()
        features = response.css("div.details-property_features:first-of-type li::text").getall()

        rooms = None
        rooms_feature_index = next((i for i, x in enumerate(header_feaures) if "hab." in x), None)
        if rooms_feature_index is not None:
            rooms = int(header_feaures[rooms_feature_index].replace("hab.", ""))

        constructed_m2 = None
        constructed_m2_feature_index = next((i for i, x in enumerate(header_feaures) if "m²" in x), None)
        if constructed_m2_feature_index is not None:
            constructed_m2 = int(deleteSubstrings(header_feaures[constructed_m2_feature_index], [".", "m²"]))

        
        energyCalification = response.css("div.details-property_features:last-of-type span:nth-of-type(2)::attr(class)").get()
        if(energyCalification is not None):
            energyCalification = energyCalification.replace("icon-energy-c-", "")

        cosntruction_date = None
        construction_date_feature_index = next((i for i, x in enumerate(features) if x.startswith("Construido")), None)
        if construction_date_feature_index is not None:
            cosntruction_date = datetime.date(int(features[construction_date_feature_index].replace("Construido en ", "")), 1, 1).isoformat()

        location = ""
        location_details = response.css("li.header-map-list::text").getall()
        for location_detail in location_details:
            location = f"{location} {location_detail.strip()}"

        owner = response.css("div.professional-name span:first-of-type input[name='user-name']::attr(value)").get()
        if owner is None:
            owner = response.css("a.about-advertiser-name::text").get()

        date = dateparser.parse(response.css("p.stats-text::text").get().replace("Anuncio actualizado el ", ""))
        update_date = date.isoformat() if date is not None else None

        image_urls = response.css("img.detail-image-gallery::attr(src)").getall()
        img_number = 1
        for image_url in image_urls:
            yield ImageItem(
                image_url=image_url,
                image_name=f'{ref}_{img_number}',
                ref=ref,
                spiderName=self.name,
            )
            img_number = img_number + 1
        if image_urls is not None:
            image_urls = ", ".join(image_urls)

        yield AnnouncementItem(
            timestamp = datetime.datetime.now().isoformat(),
            update_date = update_date,
            title = title,
            description = description,
            price = price,
            location = location,
            rooms = rooms,
            constructed_m2 = constructed_m2,
            ref = ref,
            energy_calification = energyCalification,
            energy_consumption = energyConsumption if energyConsumption is not None else "",
            construction_date = cosntruction_date,
            owner = owner,
            offer_type = self.announcement_type_filter if hasattr(self, "announcement_type_filter") else 1,
            image_urls = image_urls,
            url = response.request.url,
            list_url = listUrl,
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
