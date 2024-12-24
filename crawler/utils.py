import traceback
import datetime

index_failed_urls = "failed_urls"

def saveUrlException(url):
        print(traceback.format_exc())
        with open("requestExceptions.txt", "a") as txt:
            txt.write(f"[{datetime.datetime.now().isoformat()}] - URL: {url} \n {traceback.format_exc()} \n")

def deleteSubstrings(string, substrings):
    for str in substrings:
        string = string.replace(str, "")
    return string

def getLastRequestTime(response):
        lastRequestTime = 0
        if "requestTime" in response.request.meta:
            lastRequestTime = response.request.meta["requestTime"]
        return lastRequestTime