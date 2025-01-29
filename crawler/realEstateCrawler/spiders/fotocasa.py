from realEstateCrawler.items import ImageItem, AnnouncementItem
from offerParser import deleteSubstrings, getLocationParsedComponent
import scrapy
import datetime
import dateparser
import json
import sys
sys.path.append("../")
import constants.zoneFilters as zf
import constants.announcementTypeFilters as tf

class FotocasaSpider(scrapy.Spider):
    #Spider name
    name = "fotocasa"

    #Spider settings
    custom_settings = {
        "DOWNLOAD_SLOTS": {
            "www.fotocasa.es": {"delay": 5},
            "api.geocodify.com": {"delay": 2}
        },
        "DOWNLOADER_MIDDLEWARES": {
            'realEstateCrawler.middlewares.SeleniumBaseDownloadMiddleware': 1,
        },
        "JOBDIR": "jobs/" + name
    }

    #Spider starting urls
    start_url = "https://www.fotocasa.es/es/comprar/viviendas/espana/todas-las-zonas/l?sortType=publicationDate"

    geocodify_url = "https://api.geocodify.com/v2/parse?api_key=lCWart5tdT5gPVkKrFFdLioAo892C9WF&address=" #TODO delete my api key from the url

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

    #Selectors for scrolling
    announcement_scroll_selector = "section.sui-SectionInfo:last-of-type"
    list_scroll_selector = "article:last-of-type"

    #Conditions to stop scrolling
    list_scroll_until_condition = "document.querySelectorAll('div.sui-PerfDynamicRendering-placeholder').length == 0"

    def start_requests(self):
        if hasattr(self, "target_announcement_url"):
            url = self.target_announcement_url
            yield scrapy.Request(url, callback=self.parseAnnouncement, cb_kwargs=dict(listUrl="https:://www.fotocasa.es/"), 
                meta={
                    "selenium": True,
                    "scrollTo": self.announcement_scroll_selector,
                }
            )
        else:
            if hasattr(self, "zone_filter"):
                for zone in self.zone_filters[self.zone_filter]:
                    url = self.getUrlWithFilters(f"https://www.fotocasa.es/es/comprar/viviendas/{zone}-provincia/todas-las-zonas/l?sortType=publicationDate")
                    yield scrapy.Request(url, callback=self.parse, priority=1,
                        meta={
                            "selenium": True,
                            "scrollTo": self.list_scroll_selector,
                            "scrollUntil": self.list_scroll_until_condition,
                        }
                    )
            else:
                url = self.getUrlWithFilters(self.start_url)
                yield scrapy.Request(url, callback=self.parse, priority=1,
                    meta={
                        "selenium": True,
                        "scrollTo": self.list_scroll_selector,
                        "scrollUntil": self.list_scroll_until_condition,
                    }
                )


    def parse(self, response):
        for announcement in response.css("article"):
            announcement_url = announcement.css("a:first-of-type::attr(href)").get()
            yield scrapy.Request(response.urljoin(announcement_url), priority=3, callback=self.parseAnnouncement, cb_kwargs=dict(listUrl=response.request.url), 
                meta={
                    "selenium": True,
                    "scrollTo": self.announcement_scroll_selector
                }
            )

        next_page_url = None
        if len(response.css("article")) > 0: #TODO clean this code
            splitUrl = response.request.url.split('l/')
            if len(splitUrl) > 1:
                next_page_number = int(splitUrl[-1].split('?')[0]) + 1
                next_page_str = f"l/{next_page_number}"
            else:
                splitUrl = response.request.url.split('?')
                next_page_number = 2
                next_page_str = f"/{next_page_number}?"
            next_page_url = splitUrl[0] + next_page_str + splitUrl[-1].replace(f"{next_page_number - 1}?", "?")

        if next_page_url is not None:
            yield scrapy.Request(response.urljoin(next_page_url), priority=2, callback=self.parse, 
                meta={
                    "selenium": True, 
                    "scrollTo": self.list_scroll_selector, 
                    "scrollUntil": self.list_scroll_until_condition
                }
            )

    def parseAnnouncement(self, response, listUrl):
        announcement_data = {}
        announcement_data["url"] = response.request.url
        announcement_data["listUrl"] = listUrl
        announcement_data["title"] = response.css("h1:first-of-type::text").get()
        announcement_data["description"] = response.css("p.re-DetailDescription::text").get()
        announcement_data["ref"] = response.css("div.re-FormContactDetailDown-reference:nth-of-type(2) p strong::text").get()
        announcement_data["energyCalification"] = response.css("div.re-DetailEnergyCertificate-item:nth-of-type(1)::text").get()
        announcement_data["energyConsumption"] = response.css("div.re-DetailEnergyCertificate-itemUnits::text").get()
        announcement_data["update_date"] = None

        features = response.css("div.re-DetailFeaturesList-featureContent")
        header_features = response.css("ul.re-DetailHeader-features li")

        announcement_data["rooms"] = self.parseFeature(header_features, "hab", "span:nth-of-type(2)::text", "span:nth-of-type(2) span::text")
        if announcement_data["rooms"] is not None:
            announcement_data["rooms"] = int(announcement_data["rooms"])

        announcement_data["constructed_m2"] = self.parseFeature(header_features, "m²", "span:nth-of-type(2)::text", "span:nth-of-type(2) span::text")
        if announcement_data["constructed_m2"] is not None:
            announcement_data["constructed_m2"] = int(announcement_data["constructed_m2"])

        announcement_data["construction_date"] = None    
        construction_date_string = self.parseFeature(features, "Antigüedad", "p.re-DetailFeaturesList-featureLabel", "div.re-DetailFeaturesList-featureValue::text")
        if construction_date_string is not None:
            if "+" in construction_date_string:
                construction_date_string = construction_date_string.replace("+", "")
            else:
                construction_date_string_splitted = construction_date_string.split()
                construction_date_string = " ".join([construction_date_string_splitted[-2], construction_date_string_splitted[-1]])
            announcement_data["construction_date"] = dateparser.parse("Hace " + construction_date_string).isoformat()

        announcement_data["owner"] = response.css("a.re-FormContactDetail-logo::attr(title)").get()
        if announcement_data["owner"] is None:
            announcement_data["owner"] = "Particular"

        announcement_data["price"] = None
        priceStr = response.css("span.re-DetailHeader-price::text").get()
        if "consultar" not in priceStr:
            announcement_data["price"] = int(deleteSubstrings(response.css("span.re-DetailHeader-price::text").get(), " .€"))

        announcement_data["locationStr"] = response.css("h2.re-DetailMap-address::text").get()
        if announcement_data["locationStr"] is not None:
            if response.css("h2.re-DetailMap-address span::text").get() is not None:
                announcement_data["locationStr"] = announcement_data["locationStr"] + response.css("h2.re-DetailMap-address span::text").get()
        else:
            announcement_data["locationStr"] = response.css("h2.re-DetailMap-address span::text").get()

        askForImages = response.css("div.re-DetailMosaic-ask")
        if askForImages is not None:
            announcement_data["image_urls"] = None
            yield scrapy.Request(self.geocodify_url + announcement_data["locationStr"],
                dont_filter=True,
                priority=5,
                callback=self.parseAnnouncementLocation,
                errback=self.errbackLocationParse,
                cb_kwargs=dict(announcement_data=announcement_data)
            )
        else:
            openGalleryQuery = "&isGalleryOpen=true" if "?" in response.request.url else "?isGalleryOpen=true"
            yield scrapy.Request(response.request.url + openGalleryQuery, priority=4, callback=self.parseAnnouncementImages, cb_kwargs=dict(announcement_data=announcement_data),
                meta={
                    "selenium": True,
                    "scrollScript": "document.querySelectorAll(\"li[id*='image'] div.re-DetailMultimediaImage-container\")[document.querySelectorAll(\"li[id*='image'] div.re-DetailMultimediaImage-container\").length-1].scrollIntoView()",
                    "scrollUntil": "document.querySelectorAll(\"li[id*='image'] div:not(.re-DetailMultimediaImage-container):first-of-type\").length == 0",
                }
            )

    def parseAnnouncementImages(self, response, announcement_data):
        image_urls = response.css("img.re-DetailMultimediaImage-image::attr(src)").getall()
        ref = announcement_data["ref"]

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
        announcement_data["image_urls"] = image_urls

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
            energy_consumption = announcement_data["energyConsumption"],
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
            url = f"{url}&minPrice={self.min_price_filter}"
        if hasattr(self, "max_price_filter"):
            url = f"{url}&maxPrice={self.max_price_filter}"
        if hasattr(self, "min_size_filter") and self.min_size_filter > 0:
            url = f"{url}&minSurface={self.min_size_filter}"
        if hasattr(self, "max_size_filter"):
            url = f"{url}&maxSurface={self.max_size_filter}"
        if hasattr(self, "announcement_type_filter") and self.announcement_type_filter == tf.ALQUILER:
            url = url.replace("comprar", "alquiler")
            
        return url
    
    def parseFeature(self, features, feature_name, feature_name_selector, feature_value_selector):
        index = next((i for i, x in enumerate(features) if feature_name in x.css(feature_name_selector).get()), None)
        if index is not None:
            return features[index].css(feature_value_selector).get()
        return None

    def getLocationParsedComponent(self, location_data, component):
        index = next((x for i, x in enumerate(location_data["response"]) if "label" in location_data["response"][x] and component in location_data["response"][x]["label"]), None)
        if index is not None:
            return location_data["response"][index]["value"]
        return None