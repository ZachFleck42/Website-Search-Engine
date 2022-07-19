from async_timeout import timeout
import src.database_utils as database
import src.redis_utils as redis
import requests
from bs4 import BeautifulSoup
from celery import Celery
from time import time
from urllib.parse import urlparse

app = Celery('Search_Engine', broker='redis://redis:6379/1')
app.conf.result_backend = 'redis://redis:6379/1'


def crawlWebsite(initialURL):
    '''
    Parent function for connecting to and scraping/storing data from an entire website.
    Initializes queue, database connections, and asset downloads.
    Returns the total number of webpages visited by the crawler.
    '''
    startCrawlTime = time()

    # Normalize user-input URL
    initialURL = initialURL.rstrip('/') + '/'
    if "http" not in initialURL:
        initialURL = "https://" + initialURL

    # Check if URL is connectable
    couldNotConnect = 0
    try: pageResponse = getPageResponse(initialURL)
    except: couldNotConnect = 1
    if couldNotConnect or (pageResponse.status_code != 200):
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
            print(f"Sending to Celery for processing: {url}")
            processURL.delay(url, tableName)

    # Return the total number of webpages visited and the time it took to crawl them
    webpageVisitCount = redis.getVisitedCount()
    crawlTime = time() - startCrawlTime

    return (webpageVisitCount, crawlTime)


@app.task
def processURL(url, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an individual webpage.
    Returns 1 if page was processed without error.
    '''
    print(f"Processing {url}")

    # Get the page's HTML and parse it
    print(f"Getting page response for {url}")               #!
    pageResponse = getPageResponse(url)
    if not pageResponse:
        print(f"ERROR: Could not connect to {url}")
        return 0

    print(f"Parsing page for {url}")                        #!
    parsedPage = BeautifulSoup(pageResponse.text, 'html.parser')

    # Queue all links from page that are on the same website and have not already been visited/queued
    print(f"Gettings links from {url}")                     #!
    pageLinks = getLinks(url, parsedPage)
    for link in pageLinks:
        if redis.hasBeenVisited(link):
            continue
        print(f"Adding {link} to queue")                    #!
        redis.addToQueue(link)

    print(f"Scraping data from {url}")                      #!
    # Scrape data from the page and append it to database
    pageData = scrapeData(parsedPage)

    print(f"Appending data from {url}")                     #!
    database.appendData(url, pageData, databaseTable)


def getPageResponse(url):
    '''
    Connects to a URL and returns the response.
    '''
    requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    couldNotConnect = 0
    try: pageResponse = requests.get(url, requestHeaders)
    except: couldNotConnect = 1
    if couldNotConnect or (pageResponse.status_code != 200):
        return 0

    return pageResponse


def scrapeData(parsedPage):
    ''''
    Pulls and returns data from a parsed webpage.
    '''
    pageTitle = parsedPage.title.string
    pageText = parsedPage.get_text()
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
        return 0


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
                    "/ko/", "/da/", "/zh/", "/cs/", "/nl/", "/it/", "/el/", "/pt/", "/th/", "/id/"]

    # Tuple, not list, because surprisingly str.endswith() accepts tuples
    badExtensions = (".jpg", ".png", ".gif", ".pdf", ".aspx",
                    "/es", "/de", "/ja", "/fr", "/zh", "/pl", "/ru", "/nl", "/uk",
                    "/ko", "/it", "/hu", "/sv", "/cs", "/ms", "/da")

    parsedPage = urlparse(pageURL)

    cleanLinks = []
    for potentialLink in links:
        link = potentialLink

        if link.endswith(badExtensions):
            continue

        if any(tag in link for tag in badInclusions):
            continue

        # Delete any page anchors and/or queries
        link = link.split('#', 1)[0]
        link = link.split('?', 1)[0]

        # Expand internal links
        if "http" not in link:
            if link[0] == '/':
                link = "https://" + parsedPage.hostname + link
            else:
                link = "https://" + parsedPage.hostname + (parsedPage.path).rstrip('/') + "/" + link

        # Ignore links to other domains
        if parsedPage.hostname != urlparse(link).hostname:
            continue

        # Only visit https:// URLs (not http://)
        if urlparse(link).scheme != "https":
            link = "https" + link[4:]

        # Link has passed through all filters and is suitable to be appended to queue
        cleanLinks.append(link)

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