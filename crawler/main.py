from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
import argparse
import importlib
import multiprocessing
import sys
sys.path.append("../")
import constants.zoneFilters as zf
import constants.announcementTypeFilters as tf

spiders = [
    "idealista",
    #"pisos",
    #"properstar",
    #"spainhouses",
    #Full dynamic content spiders
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", help = "Tipo de ofertas")
    parser.add_argument("-z", "--zone", help = "Filtro de zona")
    parser.add_argument("-mp", "--minPrice", help = "Filtro de precio mínimo")
    parser.add_argument("-Mp", "--maxPrice", help = "Filtro de precio máximo")
    parser.add_argument("-ms", "--minSurface", help = "Filtro de superficie mínima")
    parser.add_argument("-Ms", "--maxSurface", help = "Filtro de superficie máxima")
    args = parser.parse_args()
    
    if args.type and args.zone and args.minPrice and args.maxPrice and args.minSurface and args.maxSurface:
        announcement_type_filter = args.type
        zone_filter = args.zone
        min_price_filter = args.minPrice
        max_price_filter = args.maxPrice
        min_size_filter = args.minSurface
        max_size_filter = args.maxSurface
    else:
        announcement_type_filter, zone_filter, minPrice, maxPrice, minSurface, maxSurface = requestInputFilters()
    
    num_spiders = len(spiders)
    with multiprocessing.Pool(num_spiders) as pool:
        try:
            pool.starmap(runSpiderThread,
                zip(
                    spiders,
                    [zone_filter]*num_spiders,
                    [announcement_type_filter]*num_spiders,
                    [min_price_filter]*num_spiders,
                    [max_price_filter]*num_spiders,
                    [min_size_filter]*num_spiders,
                    [max_size_filter]*num_spiders
                )
            )
        except KeyboardInterrupt:
            print("Proceso interrumpido por el usuario")

def runSpiderThread(spider, zone_filter, announcement_type_filter, min_price_filter, max_price_filter, min_size_filter, max_size_filter):
    settings = get_project_settings()
    configure_logging(settings)
    process = CrawlerProcess(settings)

    try:
        module = importlib.import_module(f"realEstateCrawler.spiders.{spider}")
        class_name = getattr(module, spider.capitalize() + "Spider")
        process.crawl(class_name,
                      zone_filter=zone_filter,
                      announcement_type_filter=announcement_type_filter,
                      min_price_filter=min_price_filter,
                      max_price_filter=max_price_filter,
                      min_size_filter=min_size_filter,
                      max_size_filter=max_size_filter)
    except Exception as e:
        print(f"No se ha podido cargar el spider {spider} debido a un error: {e}")

    process.start()
    
def requestInputFilters():
    print("+" + "-"*25 + "+")
    print("| Opciones " + " "*16 + "|")
    print("+" + "-"*25 + "+")
    for i, option in announcement_type_filter_names.items():
         print(f"| {i}. {option}" + " "*(25 - len(f"{i}. {option}")) + "|")
    print("+" + "-"*25 + "+")
    announcement_type_filter = input("Selecciona una de las opciones disponibles: ")
    if not announcement_type_filter.isdigit():
        wrongOptionSelected()
    announcement_type_filter = int(announcement_type_filter)
    if announcement_type_filter > tf.MAX or announcement_type_filter < tf.MIN:
        wrongOptionSelected()
    
    print("+" + "-"*25 + "+")
    print("| Opciones " + " "*16 + "|")
    print("+" + "-"*25 + "+")
    for i, option in zone_filter_names.items():
         print(f"| {i}. {option}" + " "*(25 - len(f"{i}. {option}")) + "|")
    print("+" + "-"*25 + "+")
    zone_filter = input("Selecciona una zona de entre las opciones disponibles: ")
    if not zone_filter.isdigit():
        wrongOptionSelected()
    zone_filter = int(zone_filter)
    if zone_filter > zf.MAX or zone_filter < zf.MIN:
        wrongOptionSelected()

    min_price_filter = input("Indica el precio mínimo: ")
    if not min_price_filter.isdigit():
        wrongOptionSelected()
    min_price_filter = int(min_price_filter)
    if min_price_filter <= 0:
        wrongOptionSelected()

    max_price_filter = input("Indica el precio máximo: ")
    if not max_price_filter.isdigit():
        wrongOptionSelected()
    max_price_filter = int(max_price_filter)
    if max_price_filter < min_price_filter:
        wrongOptionSelected()

    min_size_filter = input("Indica el mínimo tamaño en metros cuadrados: ")
    if not min_size_filter.isdigit():
        wrongOptionSelected()
    min_size_filter = int(min_size_filter)
    if min_size_filter <= 0:
        wrongOptionSelected()

    max_size_filter = input("Indica el máximo tamaño en metros cuadrados: ")
    if not max_size_filter.isdigit():
        wrongOptionSelected()
    max_size_filter = int(max_size_filter)
    if max_size_filter < min_size_filter:
        wrongOptionSelected()
        
    return announcement_type_filter, zone_filter, minPrice, maxPrice, minSurface, maxSurface

def wrongOptionSelected():
    print("ERROR: Opcion no disponible")
    quit()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("/nProceso interrumpido por el usuario")
