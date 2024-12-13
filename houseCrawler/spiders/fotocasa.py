import scrapy
import datetime
import dateparser
import sys
from houseCrawler.items import ImageItem
sys.path.insert(0, "../..")
from utils import saveUrlException, deleteSubstrings
import zoneFilters as zf

class FotocasaSpider(scrapy.Spider):
    #Spider name
    name = "fotocasa"

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
            "https://www.fotocasa.es/es/comprar/viviendas/espana/todas-las-zonas/l?sortType=publicationDate"
    ]

    #Zone filters
    zone_filters = {
        zf.ANDALUCIA: ["malaga", "almeria", "cadiz", "cordoba", "granada", "huelva", "jaen", "malaga", "sevilla"],
        zf.ARAGON: ["huesca", "teruel", "zaragoza"],
        zf.CANTABRIA: ["cantabria"],
        zf.CASTILLALEON: ["avila", "burgos", "leon", "palencia", "salamanca", "segovia", "soria", "valladolid", "zamora"],
        zf.CASTILLALAMANCHA: ["albacete", "ciudad-real", "cuenca", "guadalajara", "toledo"],
        zf.CATALUÑA: ["barcelona", "girona", "lleida", "tarragona"],
        zf.NAVARRA: ["navarra"],
        zf.VALENCIA: ["alicante", "castellon", "valencia"],
        zf.MADRID: ["madrid"],
        zf.EXTREMADURA: ["badajoz", "caceres"],
        zf.GALICIA: ["a-coruna", "lugo", "ourense", "pontevedra"],
        zf.BALEARES: ["illes-balears"],
        zf.CANARIAS: ["las-palmas", "santa-cruz-de-tenerife"],
        zf.RIOJA: ["la-rioja"],
        zf.EUSKADI: ["alava", "guipuzcoa", "vizcaya"],
        zf.ASTURIAS: ["asturias"],
        zf.MURCIA: ["murcia"],
    }

    def start_requests(self):
        if hasattr(self, "zoneFilter"):
            for zone in self.zone_filters[self.zoneFilter]:
                yield scrapy.Request(f"https://www.fotocasa.es/es/comprar/viviendas/{zone}-provincia/todas-las-zonas/l?sortType=publicationDate", callback=self.parse, 
                meta={
                    "selenium": True, 
                    "scrollTo": "article:last-of-type",
                    "scrollUntil": "document.querySelectorAll('div.sui-PerfDynamicRendering-placeholder').length == 0",
                    "scrollWaits": 1
                }
            )
        else:
            for url in self.start_urls:
                yield scrapy.Request(url, callback=self.parse, 
                    meta={
                        "selenium": True, 
                        "scrollTo": "article:last-of-type",
                        "scrollUntil": "document.querySelectorAll('div.sui-PerfDynamicRendering-placeholder').length == 0",
                        "scrollWaits": 1
                    }
                )

    def parse(self, response):
        try:
            for announcement in response.css("article"):
                announcement_url = announcement.css("a:first-of-type::attr(href)").get()
                yield response.follow(announcement_url, callback=self.parseAnnouncement, cb_kwargs=dict(listUrl=response.request.url), 
                    meta={
                        "selenium": True, 
                        "scrollTo": "section.sui-SectionInfo:last-of-type",
                        "scrollWaits": 1
                    }
                )
            next_page = response.css("li.sui-MoleculePagination-item:last-child a::attr(href)").get()
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse, 
                    meta={
                        "selenium": True, 
                        "scrollTo": "article:last-of-type", 
                        "scrollUntil": "document.querySelectorAll('div.sui-PerfDynamicRendering-placeholder').length == 0",
                        "scrollWaits": 1
                    }
                )
        except Exception:
            saveUrlException(self.repository, response.request.url, self.name)

    def parseAnnouncement(self, response, listUrl):
        try:
            announcementData = {}
            announcementData["listUrl"] = listUrl
            announcementData["title"] = response.css("h1:first-of-type::text").get()
            announcementData["description"] = response.css("p.re-DetailDescription::text").get()
            announcementData["price"] = int(deleteSubstrings(response.css("span.re-DetailHeader-price::text").get(), " .€"))
            announcementData["location"] = response.css("h2.re-DetailMap-address::text").get()
            if announcementData["location"] is not None:
                announcementData["location"] = announcementData["location"] + response.css("h2.re-DetailMap-address span::text").get()
            else:
                announcementData["location"] = response.css("h2.re-DetailMap-address span::text").get()
            features = response.css("ul.re-DetailHeader-features li")
            announcementData["rooms"] = None
            rooms_distribution_index = next((i for i, x in enumerate(features) if "hab" in x.css("span:nth-of-type(2)::text").get()), None)
            if rooms_distribution_index is not None:
                announcementData["rooms"] = int(features[rooms_distribution_index].css("span:nth-of-type(2) span::text").get())
            announcementData["constructed_m2"] = None
            constructed_m2_distribution_index = next((i for i, x in enumerate(features) if "m²" in x.css("span:nth-of-type(2)::text").get()), None)
            if constructed_m2_distribution_index is not None:
                announcementData["constructed_m2"] = int(features[constructed_m2_distribution_index].css("span:nth-of-type(2) span::text").get())
            announcementData["ref"] = response.css("div.re-FormContactDetailDown-reference:nth-of-type(2) p strong::text").get()
            announcementData["energyCalification"] = response.css("div.re-DetailEnergyCertificate-item:nth-of-type(1)::text").get()
            announcementData["energyConsumption"] = response.css("div.re-DetailEnergyCertificate-itemUnits:nth-of-type(1)::text").get()
            #energyEmissions
            announcementData["owner"] = response.css("a.re-FormContactDetail-logo::attr(title)").get()
            announcementData["update_date"] = None
            features = response.css("div.re-DetailFeaturesList-featureContent")
            announcementData["cosntruction_date"] = None
            construction_date_index = next((i for i, x in enumerate(features) if "Antigüedad" in x.css("p.re-DetailFeaturesList-featureLabel").get()), None)
            if construction_date_index is not None:
                construction_date_string = features[construction_date_index].css("div.re-DetailFeaturesList-featureValue::text").get()
                if "+" in construction_date_string:
                    construction_date_string = construction_date_string.replace("+", "")
                else:
                    construction_date_string_splitted = construction_date_string.split()
                    construction_date_string = " ".join([construction_date_string_splitted[-2], construction_date_string_splitted[-1]])
                announcementData["cosntruction_date"] = dateparser.parse("Hace " + construction_date_string).isoformat()
            yield scrapy.Request(response.request.url + "&isGalleryOpen=true", callback=self.parseAnnouncementImages, cb_kwargs=dict(announcementData=announcementData),
                meta={
                    "selenium": True,
                    "scrollScript": "document.querySelectorAll(\"li[id*='image'] div.re-DetailMultimediaImage-container\")[document.querySelectorAll(\"li[id*='image'] div.re-DetailMultimediaImage-container\").length-1].scrollIntoView()",
                    "scrollAlwaysToLast": True,
                    "scrollUntil": "document.querySelectorAll(\"li[id*='image'] div:not(.re-DetailMultimediaImage-container):first-of-type\").length == 0",
                    "scrollWaits": 1
                }
            )
        except Exception:
            saveUrlException(self.repository, response.request.url, self.name)

    def parseAnnouncementImages(self, response, announcementData):
        try:
            image_urls = response.css("img.re-DetailMultimediaImage-image::attr(src)").getall()
            ref = announcementData["ref"]
            img_number = 1
            for image_url in image_urls:
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
        except Exception:
            saveUrlException(self.repository, response.request.url, self.name)

        yield {
            "@timestamp": datetime.datetime.now().isoformat(),
            "update_date": announcementData["update_date"],
            "title": announcementData["title"],
            "description": announcementData["description"],
            "price": announcementData["price"],
            "location": announcementData["location"],
            "rooms": announcementData["rooms"],
            "constructed_m2": announcementData["constructed_m2"],
            "ref": announcementData["ref"],
            "type": "selling",
            "energy_calification": announcementData["energyCalification"],
            "energy_consumption": announcementData["energyConsumption"],
            "construction_date": announcementData["cosntruction_date"],
            "owner": announcementData["owner"],
            "image_urls": image_urls,
            "url": response.request.url,
            "list_url": announcementData["listUrl"],
            "spider": self.name
        }
