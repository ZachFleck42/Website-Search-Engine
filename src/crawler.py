import src.database_utils as database
import src.redis_utils as redis
import requests
import re
from bs4 import BeautifulSoup
from celery import Celery
from time import time
from urllib.parse import urlparse

app = Celery('Search_Engine', broker='redis://redis:6379/1')
app.conf.result_backend = 'redis://redis:6379/1'


def crawlWebsite(initialURL):
    '''
    Parent function for connecting to and scraping/storing data from an entire website.
    Returns the total number of webpages visited by the crawler.
    '''
    startCrawlTime = time()

    # Normalize user-input URL
    if "https" not in initialURL:
        initialURL = "https://" + initialURL
    initialURL = "https://" + urlparse(initialURL).hostname

    # Check if URL is connectable
    pageResponse = getPageResponse(initialURL)
    if not pageResponse:
        print(f'ERROR: Could not connect to "{initialURL}"')
        return (0, 0)

    # Create a table in the database for the website
    tableName = database.getTableName(initialURL)
    if database.tableExists(tableName):
        database.dropTable(tableName)
    database.createTable(tableName)

    # Add the initial URL to the queue
    redis.clearCache()
    redis.addToQueue(initialURL)

    # Process the queue while there are still items in the queue
    while ((redis.getQueueCount()) > 0) or (processingQueue()):
        if url := redis.popFromQueue():
            redis.markVisited(url)
            # DEBUG: print(f"Sending to Celery for processing: {url}")
            processURL.delay(url, tableName)

    # Return the total number of webpages visited and the time it took to crawl them
    webpageVisitCount = redis.getVisitedCount()
    crawlTime = time() - startCrawlTime

    return (webpageVisitCount, crawlTime)


@app.task
def processURL(url, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an individual webpage.
    '''
    print(f"Processing {url}")

    # Get the page's HTML and parse it
    # DEBUG: print(f"Getting page response for {url}")
    pageResponse = getPageResponse(url)
    if not pageResponse:
        print(f"ERROR: Could not connect to {url}")
        return 0
    # DEBUG: print(f"Parsing page for {url}")
    parsedPage = BeautifulSoup(pageResponse.text, 'html.parser')

    # Queue all links from page that are on the same website and have not already been visited/queued
    # DEBUG: print(f"Gettings links from {url}")
    pageLinks = getLinks(url, parsedPage)
    for link in pageLinks:
        if redis.hasBeenVisited(link):
            continue
        #print(f"Adding {link} to queue")
        redis.addToQueue(link)

    # Scrape data from the page and append it to the database
    # DEBUG: print(f"Scraping data from {url}")
    pageData = scrapeData(parsedPage)
    # DEBUG: print(f"Appending data from {url}")
    database.appendData(url, pageData, databaseTable)
    # DEBUG: print(f"Finished processing {url}")


def getPageResponse(url):
    '''
    Connects to a URL and returns the response.
    '''
    # Pretend to be not a robot
    requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'
       }

    couldNotConnect = 0
    try:
        pageResponse = requests.get(url, requestHeaders)
    except:
        couldNotConnect = 1

    if couldNotConnect or (pageResponse.status_code != 200):
        return 0

    return pageResponse


def scrapeData(parsedPage):
    ''''
    Pulls and returns data from a parsed webpage.
    '''
    if parsedPage.title:
        pageTitle = parsedPage.title.string
    else:
        pageTitle = "None"

    rawPageText = parsedPage.get_text()
    pageText = re.sub(r'[^A-Za-z0-9\'\-]', ' ', rawPageText)

    pageDesc = str(parsedPage.find("meta", attrs={'name': 'description'}))[14:-21]
    if not pageDesc:
        pageDesc = "None"

    return (pageTitle, pageDesc, pageText)


def getLinks(url, parsedPage):
    '''
    Gets a list of "raw" links found on the passed-in webpage.
    Passes any links to the cleanLinks function for cleaning.
    '''
    # Find all valid links (not NoneType) from the <a> tags on the webpage
    links = []
    for reference in parsedPage.find_all('a'):
        if (link := reference.get('href')):
            links.append(link)

    # Filter unwanted links before returning.
    if links:
        cleanedLinks = cleanLinks(links, url)
        return cleanedLinks
    else:
        return []


def cleanLinks(links, pageURL):
    '''
    Accepts a list of raw links/references pulled from a webpage's <a> tags.
    Passes links through a series of filters to prune unwanted links.
    Returns a list of cleaned links.
    '''
    badInclusions = ["mailto:", "tel:", "/Category:", "/File:",
                    "/Talk:", "/User:", "/Blog:", "/User_blog:", "/Special:",
                    "/Template:", "/Template_talk:", "Wiki_talk:",  "/Help:",
                    "/Source:", "/Forum:", "/Forum_talk:", "/javascript:void",
                    "/ru/", "/es/", "/ja/", "/de/", "/fi/", "/fr/", "/f/", "/pt-br/",
                    "/uk/", "/he/", "/tr/", "/vi/", "/sv/", "/lt/", "/pl/", "/hu/",
                    "/ko/", "/da/", "/zh/", "/cs/", "/nl/", "/it/", "/el/", "/pt/",
                    "/th/", "/id/", "/lac-es/"]

    # Tuple, not list, because surprisingly str.endswith() accepts tuples
    badExtensions = (".jpg", ".png", ".gif", ".pdf", ".aspx",
                    "/view", "/download",
                    "/es", "/de", "/ja", "/fr", "/zh", "/pl", "/ru", "/nl", "/uk",
                    "/ko", "/it", "/hu", "/sv", "/cs", "/ms", "/da")

    parsedPage = urlparse(pageURL)

    cleanLinks = []
    for link in links:
        potentialLink = link.rstrip('/')

        # Filter links to the initial URL
        if not potentialLink:
            continue

        # Filter links that end with unwanted extensions
        if potentialLink.endswith(badExtensions):
            continue

        # Filter links that contain unwanted tags/sequences
        if any(tag in potentialLink for tag in badInclusions):
            continue

        # Remove any page anchors and/or queries from link
        if not (potentialLink := potentialLink.split('#', 1)[0]):
            continue
        if not (potentialLink := potentialLink.split('?', 1)[0]):
            continue

        # Expand website references to full URL
        if "http" not in potentialLink:
            if potentialLink[0] == '/':
                potentialLink = "https://" + parsedPage.hostname + potentialLink
            else:
                potentialLink = "https://" + parsedPage.hostname + (parsedPage.path).rstrip('/') + "/" + potentialLink

        # Ignore links to other domains
        if parsedPage.hostname != urlparse(potentialLink).hostname:
            continue

        # Only visit https:// URLs (not http://)
        if urlparse(potentialLink).scheme == "http":
            potentialLink = "https" + potentialLink[4:]

        # Link has passed through all filters and is suitable to be appended to queue
        cleanLinks.append(potentialLink)

    return cleanLinks


def processingQueue():
    '''
    Checks if Celery worker still has active tasks.
    Returns a value if active; returns 0 if inactive.
    '''
    inspectWorker = app.control.inspect()
    activeTasksDict = inspectWorker.active()
    if activeTasksDict:
        return list(activeTasksDict.items())[0][1]
    else:
        return 0