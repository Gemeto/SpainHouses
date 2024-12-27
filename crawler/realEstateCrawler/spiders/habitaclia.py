import scrapy
import datetime
import dateparser
from realEstateCrawler.items import ImageItem, AnnouncementItem
from utils import deleteSubstrings
import sys
sys.path.append("../")
import constants.zoneFilters as zf
import constants.announcementTypeFilters as tf

class HabitacliaSpider(scrapy.Spider):
    #Spider name
    name = "habitaclia"
    
    #Spider settings
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "realEstateCrawler.middlewares.SeleniumBaseDownloadMiddleware": 1,
        },
        "JOBDIR": "jobs/" + name
    }

    #Spider starting urls
    start_url = "https://www.habitaclia.com/"

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
            yield scrapy.Request(response.urljoin(url), priority=2, callback=self.parseZoneList, meta={"selenium": True})
        else:
            for zone_link in response.css("div#enlacesmapa ul.verticalul li a::attr(href)").getall():
                yield scrapy.Request(response.urljoin(zone_link), priority=1, callback=self.parseZoneLinks, meta={"selenium": True})
        
        if response.css("div#enlacesmapa ul.verticalul li a::attr(href)").getall() is None:
            yield scrapy.Request(response.urljoin(url), priority=2, callback=self.parseZoneList, meta={"selenium": True})

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
            yield scrapy.Request(response.urljoin(next_page), priority=2, callback=self.parseZoneList, meta={"selenium": True})

    def parseAnnouncement(self, response, listUrl):
        announcement_urls = response.css("section.typologies-all a[title='Ver anuncio']::attr(href)").getall()
        for announcement_url in announcement_urls:
            yield scrapy.Request(
                response.urljoin(announcement_url), 
                priority=4, 
                callback=self.parseAnnouncement, 
                meta={"selenium": True}, 
                cb_kwargs=dict(listUrl=response.request.url)
            )
        
        if len(announcement_urls) == 0:
            title = response.css("h1:first-of-type::text").get()
            description = response.css("p.detail-description::text").get()
            update_date = dateparser.parse(response.css("time::text").get()).isoformat()
            distribution = response.css("article.has-aside:nth-of-type(2) ul li::text").getall()
            features = response.css("article.has-aside:nth-of-type(3) ul li").getall()

            price = None
            priceStr = response.css("div.price span[itemprop=price]::text").get()
            if priceStr is not None:
                price = int(deleteSubstrings(priceStr, " .€"))

            location = ""
            location_items = response.css("h4.address::text").getall()
            for item in location_items:
                location =f"{location} {item.strip()}"

            rooms = None
            rooms_distribution_index = next((i for i, x in enumerate(distribution) if "habitaciones" in x), None)
            if rooms_distribution_index is not None:
                rooms = int(distribution[rooms_distribution_index].replace(" habitaciones", ""))

            constructed_m2 = None
            constructed_m2_distribution_index = next((i for i, x in enumerate(distribution) if x.startswith("Superficie")), None)
            if constructed_m2_distribution_index is not None:
                constructed_m2 = int(deleteSubstrings(distribution[constructed_m2_distribution_index], ["Superficie ", "m"]))

            ref = response.css("h4.subtitle::text").get()
            if ref is not None:
                ref = deleteSubstrings(ref, ["Referencia del anuncio habitaclia/", ":", " "])

            energyCalification = response.css("div.rating::attr(class)").get()
            energyConsumption = response.css("div.rating-box:first-of-type::text").get()
            if energyConsumption is not None:
                energyConsumption = energyConsumption.strip().replace("Consumo:", "")
            if(energyCalification is not None):
                energyCalification = energyCalification.replace("rating c-", "")

            owner = response.css("h2#titulo-formDades::text").get()
            if owner is not None:
                owner = owner.replace("Contactar ", "")

            cosntruction_date = None
            construction_date_index = next((i for i, x in enumerate(features) if x.startswith("Año construcción")), None)
            if construction_date_index is not None:
                cosntruction_date = datetime.parse(int(features[construction_date_index].replace("Año construcción ", "")), 1, 1).isoformat()
            image_urls = response.css("div.ficha_foto img::attr(src)").getall()
            img_number = 1
            for image_url in image_urls:
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
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

    def getUrlWithFilters(self, url):
            if hasattr(self, "min_price_filter") and self.min_price_filter > 0:
                url = f"{url}&pmin={self.min_price_filter}"
            if hasattr(self, "max_price_filter"):
                url = f"{url}&pmax={self.max_price_filter}"
            if hasattr(self, "min_size_filter"):
                url = f"{url}&m2={self.min_size_filter}"

            return url

