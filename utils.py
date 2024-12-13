import traceback
import datetime

index_failed_urls = "failed_urls"

def saveUrlException(repo, url, spiderName):
        print(traceback.format_exc())
        repo.save(
            table=index_failed_urls,
            data={
                "@timestamp": datetime.datetime.now().isoformat(),
                "url": url,
                "exception_msg": traceback.format_exc(),
                "spider": spiderName
            },
        )

def deleteSubstrings(string, substrings):
    for str in substrings:
        string = string.replace(str, "")
    return string