import scrapy
import datetime
import dateparser
import sys
from houseCrawler.items import ImageItem
sys.path.insert(0, "../..")
from utils import saveUrlException, deleteSubstrings
import zoneFilters as zf

class HabitacliaSpider(scrapy.Spider):
    #Spider name
    name = "habitaclia"
    
    #Spider settings
    custom_settings = {
        "DOWNLOAD_DELAY": 6,
        "DOWNLOADER_MIDDLEWARES": {
            'houseCrawler.middlewares.SeleniumBaseDownloadMiddleware': 800,
        },
        "IMAGES_STORE": 'Images'
    }

    #Spider starting urls
    start_urls = [
        "https://www.habitaclia.com/",
    ]

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

    def parse(self, response):
        for zone in response.css("select#cod_prov option::attr(value)").getall():
            if not hasattr(self, "zoneFilter") or zone in self.zone_filters[self.zoneFilter]:
                zone_url = "/comprar-vivienda-en-" + zone + "/buscador.htm"
                yield response.follow(zone_url, dont_filter=True, callback=self.parseZoneLinks, meta={"selenium": True})

    def parseZoneLinks(self, response):
        zone_url = response.css("div.ver-todo-zona a::attr(href)").get()
        if zone_url is not None:
            yield response.follow(zone_url + "?ordenar=mas_recientes", dont_filter=True, callback=self.parseZoneList, meta={"selenium": True})
        else:
            for zone_link in response.css("div#enlacesmapa ul.verticalul li a::attr(href)").getall():
                yield response.follow(zone_link, dont_filter=True, callback=self.parseZoneLinks, meta={"selenium": True})

        if response.css("div#enlacesmapa ul.verticalul li a::attr(href)").getall() is None:
            yield response.follow(response.css("h2 a::attr(href)").get() + "?ordenar=mas_recientes", dont_filter=True, callback=self.parseZoneList, meta={"selenium": True})

    def parseZoneList(self, response):
        for announcement_link in response.css("article.js-list-item::attr(data-href)").getall():
            yield response.follow(announcement_link, dont_filter=True, callback=self.parseAnnouncement, meta={"selenium": True}, cb_kwargs=dict(listUrl=response.request.url))

        next_page = response.css("li.next a::attr(href)").get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parseZoneList, meta={"selenium": True})

    def parseAnnouncement(self, response, listUrl):
        try:
            title = response.css("h1:first-of-type::text").get()
            price = int(deleteSubstrings(response.css("div.price span[itemprop=price]::text").get(), " .€"))
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
                constructed_m2 = int(deleteSubstrings(distribution[constructed_m2_distribution_index], ["Superficie ", "m"]))
            ref = response.css("h4.subtitle::text").get()
            if ref is not None:
                ref = deleteSubstrings(ref, ["Referencia del anuncio habitaclia/", ":"])
            energyCalification = response.css("div.rating::attr(class)").get()
            energyConsumption = deleteSubstrings(response.css("div.rating-box:first-of-type::text").get(), ["Consumo:", "\n", " "])
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
            img_number = 1
            for image_url in image_urls:
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                yield ImageItem(
                    image_url=image_url,
                    image_name=f'{ref}_{img_number}',
                    ref=ref,
                    spiderName=self.name,
                    repository=self.repository,
                )
                img_number = img_number + 1
            if image_urls is not None:
                image_urls = ", ".join(image_urls)
        except Exception as e:
            saveUrlException(self.repository, response.request.url, self.name)

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
            "spider": self.name
        }
