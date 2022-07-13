import redis_utils
import requests
import time
from bs4 import BeautifulSoup
from celery import Celery
from database_utils import appendData, createTable
from urllib.parse import urlparse

app = Celery('Search_Engine', broker='redis://redis:6379/1')


def crawlWebsite(initialURL, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an entire website.
    '''
    # Add the initial URL to the queue
    redis_utils.addToQueue(initialURL)
    
    # Create a table in the database for the website
    createTable(databaseTable)
    
    # While there are still links in the queue...
    timeoutCounter = 0
    while True:
        # Pop a URL from the queue
        item = redis_utils.popFromQueue()
        
        # If the timeout timer is met, stop crawling.
        if item == None:
            if timeoutCounter == 10:
                print("Timed out")
                break
            
            time.sleep(1)
            timeoutCounter += 1
            continue
            
        # If a URL was found in queue, send it to Celery for processing.
        url = item.decode('utf-8')
        timeoutCounter = 0
        print(url)
        processURL.delay(url, databaseTable)

    # Return the total number of webpages visited
    return redis_utils.getVisitedCount()
    
    
@app.task(rate_limit="10/s")
def processURL(url, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an individual webpage.
    '''
    print(f"Processing {url} ...")
    if seen(url):
        print(f"ERROR: {url} already seen. Continuing...")
        return 0
        
    redis_utils.moveToProcessing(url)
    
    # Connect to the URL and get its HTML source
    pageHTML = getHTML(url)
    if not pageHTML:
        print(f"ERROR: Could not get webpage's HTML. Continuing...")
        return 0
    
    # Parse the webpage with BeautifulSoup, scrape data from page, and append to database
    # print(f"Successfully connected to {url}")
    parsedPage = BeautifulSoup(pageHTML, 'html.parser')
    pageData = scrapeData(parsedPage)
    appendData(url, pageData[0], pageData[1], databaseTable)
    # print(f"Successfully saved {url} to database")
    
    # Add all valid, unseen links from the page to the queue
    if pageLinks := getLinks(url, parsedPage):
        # print(f"Appending URLs to queue: {pageLinks}")
        for link in pageLinks:
            redis_utils.addToQueue(link)
        
    # Move URL from Celery processing queue to 'visited'
    redis_utils.moveToVisited(url)
    return 1


def getHTML(url):
    '''
    Connects to a URL, obtains a response, and returns the webpage's HTML if available.
    '''
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    pageResponse = requests.get(url, headers=headers)
    pageStatus = pageResponse.status_code
    if pageStatus != 200:
        return 0
    else:
        return pageResponse.text


def scrapeData(parsedPage):
    ''''
    Pulls and returns data from a parsed webpage.
    '''
    pageTitle = parsedPage.title.string
    pageText = parsedPage.get_text()
    
    return (pageTitle, pageText)
    

def getLinks(url, parsedPage):
    '''
    Gets a list of "raw" links found on the passed-in webpage.
    Passes any links to the cleanLinks function for cleaning.
    Returns the list of cleaned links.
    '''
    # Find all valid links (not NoneType) from the <a> tags on the webpage
    links = []
    for reference in parsedPage.find_all('a'):
        if (link := reference.get('href')):
            links.append(link)

    # Clean the links and return the list
    if links:
        return cleanLinks(links, url)
    
    return 0


def cleanLinks(links, pageURL):
    '''
    Takes a list of 'raw' links and passes them through a series of filters.
    Any links remaining are returned as 'cleaned' links.
    '''
    cleanedLinks = []
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
        parsedInitialURL = urlparse(pageURL)
        parsedLinkURL = urlparse(links[index])
        if parsedLinkURL.hostname == None:
            if links[index][0] == '/':
                links[index] = "https://" + parsedInitialURL.hostname + links[index]
            else:
                links[index] = "https://" + parsedInitialURL.hostname + parsedInitialURL.path.rstrip('/') + "/" + links[index]
                
        # Ignore links to other domains
        if parsedInitialURL.hostname != urlparse(links[index]).hostname:
            continue
        
        # Only visit https:// URLs (not http://)
        if urlparse(links[index]).scheme != "https":
            links[index] = "https" + links[index][4:]
            
        # Do not visit links that have already been visited or are currently in queue or are currently being processed
        if seen(links[index]):
            continue
            
        # All filters passed; link is appended to 'clean' list
        cleanedLinks.append(links[index])

    # Remove any duplicate links in the list and return it
    return list(set(cleanedLinks))
    
    
def seen(url):
    '''
    Checks to see if a URL has been seen by the program at all.
    '''
    return redis_utils.isProcessing(url) or redis_utils.hasBeenVisited(url)