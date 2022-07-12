import psycopg2
import redis_utils as redis_utils
import requests
from bs4 import BeautifulSoup
from celery import Celery
from psycopg2 import sql
from database_utils import createTable
from database_utils import databaseConnectionParamaters
from urllib.parse import urlparse

app = Celery('Search_Engine', broker='redis://redis:6379/1')

def getHTML(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    pageResponse = requests.get(url, headers=headers)
    pageStatus = pageResponse.status_code
    if pageStatus != 200:
        return 0
    else:
        return pageResponse.text


def scrapeData(url, parsedPage, databaseTable):
    pageTitle = parsedPage.title.string
    pageText = parsedPage.get_text()
    
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    cursor = databaseConnection.cursor()
    cursor.execute(sql.SQL("INSERT INTO {} VALUES (%s, %s, %s);")
        .format(sql.Identifier(databaseTable)),
        [url, pageTitle, pageText])
    databaseConnection.commit()
    databaseConnection.close()
    

def cleanLinks(links, pageURL):
    cleanedLinks = []
    initialHost = (urlparse(pageURL)).hostname
    for index, link in enumerate(links):
        # Ignore any links to the current page
        if link == '/':
            continue

        # Ignore page anchor links
        if '#' in link:
            continue

        # Ignore email address links
        if link[:7] == "mailto:":
            continue

        # Ignore telephone links
        if link[:4] == "tel:":
            continue
        
        # Ignore links that end with unwanted extensions
        unwantedExtensions = ["jpg", "png", "gif", "pdf"]
        if link.split('.')[-1:][0] in unwantedExtensions:
            continue
        
        # Wiki-specific rules
        unwantedTags = ["/Category:", "/File:", "/Talk:", "/User", "/Blog:", "/User_blog:", "/Special:", "/Template:", 
                        "/Template_talk:", "Wiki_talk:", "/Help:", "/Source:", "/Forum:", "/Forum_talk:", "/ru/", "/es/", 
                        "/ja/", "/de/", "/fi/", "/fr/", "/f/", "/pt-br/", "/uk/", "/he/", "/tr/", "/vi/", "/sv/", "/lt/", 
                        "/pl/", "/hu/", "/ko/", "/da/"]
        unwantedLanguages = ["/es", "/de", "/ja", "/fr", "/zh", "/pl", "/ru", "/nl", "/uk", "/ko", "/it", "/hu", "/sv", 
                            "/cs", "/ms", "/da"]
        if any(tag in link for tag in unwantedTags):
            continue
        if link[-3:] in unwantedLanguages:
            continue
        if link[-6:] == "/pt-br":
            continue
        
        # Delete any queries
        links[index] = links[index].split('?', 1)[0]
        
        # Expand internal links
        parsedURL = urlparse(pageURL)
        if links[index][0] == '/':
            links[index] = parsedURL.scheme + "://" + parsedURL.hostname + links[index]
            
        # Expand internal links
        linkHost = (urlparse(links[index])).hostname
        if linkHost is None:
            links[index] = parsedURL.scheme + "://" + parsedURL.hostname + parsedURL.path + "/" + links[index]
            linkHost = parsedURL.hostname
            
        # Ensure we are only visiting https:// versions of webpages
        if urlparse(links[index]).scheme == "http":
            links[index] = "https" + links[index][4:]
        
        # Ignore links to other domains
        if initialHost != linkHost:
            continue

        # All filters passed; link is appended to 'clean' list
        cleanedLinks.append(links[index])

    # Remove any duplicate links in the list and return it
    return list(set(cleanedLinks))


def getLinks(url, parsedPage):
    # Find all valid links (not NoneType) from the <a> tags on the webpage
    links = []
    for reference in parsedPage.find_all('a'):
        if (link := reference.get('href')):
            links.append(link)

    # Clean the links and return the list
    if links:
        return cleanLinks(links, url)
    
    return 0


def seen(url):
    return redis_utils.hasBeenVisited(url) or redis_utils.isProcessing(url)


def addLinksToQueue(links):
    for link in links: 
        if not seen(link):
            redis_utils.addToQueue(link)
    

@app.task        
def processURL(url, databaseTable):
    print(f"Processing {url} ...")
    # Check if URL has already been visited or is currently in the queue
    if seen(url):
        print(f"ERROR: URL has already been seen! Continuing...")
        return 0
        
    # Mark the URL as currently in the Celery queue
    redis_utils.markAsProcessing(url)
    
    # Connect to the URL and get its HTML source
    pageHTML = getHTML(url)
    if not pageHTML:
        print(f"ERROR: Could not get HTML. Continuing...")
        return 0
    
    # Parse the webpage with BeautifulSoup, scrape data from page, and append to database
    parsedPage = BeautifulSoup(pageHTML, 'html.parser')
    scrapeData(url, parsedPage, databaseTable)
    
    # Add all valid, unvisited links from the page to the queue
    pageLinks = getLinks(url, parsedPage)
    if pageLinks:
        addLinksToQueue(pageLinks)
        
    # Move URL from processing to visited
    redis_utils.moveToVisited(url)
    return 1
    

def crawlWebsite(initialURL, databaseTable):
    redis_utils.addToQueue(initialURL)
    createTable(databaseTable)
    
    while True:
        item = redis_utils.popFromQueue(10)
        print(item)
        if item is None:
            print("Timed out")
            break
    
        url = item[1].decode('utf-8')
        processURL.delay(url, databaseTable)

    return redis_utils.getVisitedCount()