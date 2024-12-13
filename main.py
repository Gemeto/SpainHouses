from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from elasticsearchRepo import ElasticsearchRepo
import zoneFilters as zf
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

def main():
    print("+" + "-"*25 + "+")
    print("| Opciones " + " "*16 + "|")
    print("+" + "-"*25 + "+")
    for i, option in zone_filter_names.items():
         print(f"| {i}. {option}" + " "*(25 - len(f"{i}. {option}")) + "|")
    print("+" + "-"*25 + "+")
    zoneFilter = int(input("Selecciona una zona de entre las opciones disponibles: "))
    numSpiders = len(spiders)
    multiprocessing.Pool(numSpiders).starmap(runSpiderThread, zip(spiders, [zoneFilter]*numSpiders))

def runSpiderThread(spider, zoneFilter):
    repository = ElasticsearchRepo(cfg.ELASTICSEARCH_USER, cfg.ELASTICSEARCH_PASS)

    settings = get_project_settings()
    configure_logging(settings)
    process = CrawlerProcess(settings)

    try:
        module = importlib.import_module(f"houseCrawler.spiders.{spider}")
        className = getattr(module, spider.capitalize() + "Spider")
        process.crawl(className, repository=repository, zoneFilter=zoneFilter)
    except Exception as e:
        print(f"No se ha podido cargar el spider {spider} debido a un error: {e}")

    process.start()

if __name__ == '__main__':
    main()
