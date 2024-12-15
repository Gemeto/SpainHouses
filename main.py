from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from elasticsearchRepo import ElasticsearchRepo
import constants.zoneFilters as zf
import constants.announcementTypeFilters as tf
import config as cfg
import importlib
import multiprocessing

spiders = [
    "idealista",
    #"pisos",
    #"properstar",
    #"spainhouses",
    #Full webdriver spiders
    "fotocasa",
    "habitaclia",
]

#Zone filters
zone_filter_names = {
    zf.ANDALUCIA: "Andalucia",
    zf.ARAGON: "Aragon",
    zf.CANTABRIA: "Cantabria",
    zf.CASTILLALEON: "Castilla y Leon",
    zf.CASTILLALAMANCHA: "Castilla-La Mancha",
    zf.CATALUÑA: "Cataluna",
    zf.NAVARRA: "Navarra",
    zf.VALENCIA: "Comunidad Valenciana",
    zf.MADRID: "Madrid",
    zf.EXTREMADURA: "Extremadura",
    zf.GALICIA: "Galicia",
    zf.BALEARES: "Islas Baleares",
    zf.CANARIAS: "Islas Canarias",
    zf.RIOJA: "La Rioja",
    zf.EUSKADI: "Pais Vasco",
    zf.ASTURIAS: "Asturias",
    zf.MURCIA: "Murcia",
}

#Announcement type filters
announcement_type_filter_names = {
    tf.VENTA: "Viviendas en venta",
    tf.ALQUILER: "Viviendas en alquiler",
}

def main():
    print("+" + "-"*25 + "+")
    print("| Opciones " + " "*16 + "|")
    print("+" + "-"*25 + "+")
    for i, option in announcement_type_filter_names.items():
         print(f"| {i}. {option}" + " "*(25 - len(f"{i}. {option}")) + "|")
    print("+" + "-"*25 + "+")
    announcement_type_filter = input("Selecciona una zona de entre las opciones disponibles: ")
    if not announcement_type_filter.isdigit():
        wrongOption()
    announcement_type_filter = int(announcement_type_filter)
    if announcement_type_filter > tf.MAX or announcement_type_filter < tf.MIN:
        wrongOption()
    
    print("+" + "-"*25 + "+")
    print("| Opciones " + " "*16 + "|")
    print("+" + "-"*25 + "+")
    for i, option in zone_filter_names.items():
         print(f"| {i}. {option}" + " "*(25 - len(f"{i}. {option}")) + "|")
    print("+" + "-"*25 + "+")
    zone_filter = input("Selecciona una zona de entre las opciones disponibles: ")
    if not zone_filter.isdigit():
        wrongOption()
    zone_filter = int(zone_filter)
    if zone_filter > zf.MAX or zone_filter < zf.MIN:
        wrongOption()

    min_price_filter = input("Indica el precio mínimo: ")
    if not min_price_filter.isdigit():
        wrongOption()
    min_price_filter = int(min_price_filter)
    if min_price_filter <= 0:
        wrongOption()

    max_price_filter = input("Indica el precio máximo: ")
    if not max_price_filter.isdigit():
        wrongOption()
    max_price_filter = int(max_price_filter)
    if max_price_filter < min_price_filter:
        wrongOption()

    min_size_filter = input("Indica el mínimo tamaño en metros cuadrados: ")
    if not min_size_filter.isdigit():
        wrongOption()
    min_size_filter = int(min_size_filter)
    if min_size_filter <= 0:
        wrongOption()

    max_size_filter = input("Indica el máximo tamaño en metros cuadrados: ")
    if not max_size_filter.isdigit():
        wrongOption()
    max_size_filter = int(max_size_filter)
    if max_size_filter < min_size_filter:
        wrongOption()

    announcement_type_filter = int(announcement_type_filter)
    zone_filter = int(zone_filter)
    num_spiders = len(spiders)
    multiprocessing.Pool(num_spiders).starmap(runSpiderThread, zip(spiders, [zone_filter]*num_spiders,
                                                                [announcement_type_filter]*num_spiders,
                                                                        [min_price_filter]*num_spiders,
                                                                        [max_price_filter]*num_spiders,
                                                                        [min_size_filter]*num_spiders,
                                                                        [max_size_filter]*num_spiders))

def runSpiderThread(spider, zone_filter, announcement_type_filter, min_price_filter, max_price_filter, min_size_filter, max_size_filter):
    repository = ElasticsearchRepo(cfg.ELASTICSEARCH_USER, cfg.ELASTICSEARCH_PASS)

    settings = get_project_settings()
    configure_logging(settings)
    process = CrawlerProcess(settings)

    try:
        module = importlib.import_module(f"houseCrawler.spiders.{spider}")
        class_name = getattr(module, spider.capitalize() + "Spider")
        process.crawl(class_name,
                      repository=repository,
                      zone_filter=zone_filter,
                      announcement_type_filter=announcement_type_filter,
                      min_price_filter=min_price_filter,
                      max_price_filter=max_price_filter,
                      min_size_filter=min_size_filter,
                      max_size_filter=max_size_filter)
    except Exception as e:
        print(f"No se ha podido cargar el spider {spider} debido a un error: {e}")

    process.start()

def wrongOption():
    print("ERROR: Opcion no disponible")
    quit()

if __name__ == '__main__':
    main()
