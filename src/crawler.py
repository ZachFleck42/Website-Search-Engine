import src.database_utils as database
import nltk
import re
import src.redis_utils as redis
import requests
from bs4 import BeautifulSoup
from celery import Celery
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
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
    # Enforce proper URL format
    if (initialURL.split('.', 1)[0] == "www") or ("http" not in initialURL):
        initialURL = "https://" + initialURL
        
    # Check if URL is connectable
    couldNotConnect = 0
    try:
        pageResponse = getPageResponse(initialURL)
    except:
        couldNotConnect = 1
        
    if couldNotConnect or (pageResponse.status_code != 200):
        print(f'ERROR: Could not connect to "{initialURL}"')
        return (0, 0)
    
    # Create a table in the database for the website
    tableName = database.getTableName(initialURL)
    if database.tableExists(tableName):
        database.dropTable(tableName)
    database.createTable(tableName)
    
    # Make sure necessary text-processing files are present and cache is clear
    nltk.download('stopwords')
    nltk.download('punkt')
    redis.clearCache()
    
    # Add the initial URL to the queue
    redis.addToQueue(initialURL)
    startCrawlTime = time()
    
    # While there are still links in the queue...
    while ((redis.getQueueCount()) > 0) or (processingQueue()):
        if url := redis.popFromQueue():
            redis.markVisited(url)
            print(f"Sending to Celery for processing: {url}")
            processURL.delay(url, tableName)
    
    # Return the total number of webpages visited and the time it took to crawl them
    crawlTime = time() - startCrawlTime
    webpageVisitCount = redis.getVisitedCount()
    
    return (webpageVisitCount, crawlTime)
    
    
@app.task
def processURL(url, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an individual webpage.
    Returns 1 if page was processed without error.
    '''
    print(f"Processing {url}")

    # Check to make sure URL is connectable
    pageResponse = getPageResponse(url)
    if pageResponse.status_code != 200:
        print(f"ERROR: Could not connect to {url}")
        return 0
    
    # Parse the page and scrape it for data and additional links
    parsedPage = BeautifulSoup(pageResponse.text, 'html.parser')
    pageData = scrapeData(parsedPage)
    getLinks(url, parsedPage)
    
    # Append data to the database
    if not database.appendData(url, pageData, databaseTable):
        print(f"ERROR: Could not append data from {url}")
        return 0
    
    return 1


def getPageResponse(url):
    '''
    Connects to a URL and returns the response.
    '''
    requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    return requests.get(url, headers=requestHeaders)


def scrapeData(parsedPage):
    ''''
    Pulls and returns data from a parsed webpage.
    '''
    pageTitle = parsedPage.title.string
    pageText = parsedPage.get_text()
    pageDesc = str(parsedPage.find("meta", attrs={'name': 'description'}))[14:-21]
    if not pageDesc:
        pageDesc = "No page description available."

    processedPageText = preProcessPageText(pageText)
    
    return (pageTitle, pageDesc, processedPageText)
    
    
def preProcessPageText(pageText):
    '''
    Accepts the text of a webpage as a string and returns the 'cleaned' text.
    Removes extra whitespace, punctuation, and unwanted words.
    '''
    # Remove unwanted characters
    step1 = re.sub(r'[^A-Za-z0-9\'\-]', ' ', pageText)
    
    # Force all characters to lowercase
    step2 = step1.lower()
    
    # Tokenize the text
    step3 = word_tokenize(step2)
    
    # Remove all stopwords from the text
    stopWords = set(stopwords.words('english'))
    step4 = [word for word in step3 if not word in stopWords]
    
    return " ".join(step4)


def getLinks(url, parsedPage):
    '''
    Gets a list of "raw" links found on the passed-in webpage.
    Passes any links to the filterLinks function for cleaning.
    '''
    # Find all valid links (not NoneType) from the <a> tags on the webpage
    links = []
    for reference in parsedPage.find_all('a'):
        if (link := reference.get('href')):
            links.append(link)

    # Filter unwanted links. Append all others to the queue.
    if links:
        filterLinks(links, url)


def filterLinks(links, pageURL):
    '''
    Accepts a list of raw links/references pulled from a webpage's <a> tags.
    Passes links through a series of filters to prune unwanted links.
    Returns nothing. Instead directly appends suitable links to the queue.
    '''
    unwantedTags = ["/Category:", "/File:", "/Talk:", "/User", "/Blog:", "/User_blog:", "/Special:", "/Template:", 
                    "/Template_talk:", "Wiki_talk:", "/Help:", "/Source:", "/Forum:", "/Forum_talk:", "/ru/", "/es/", 
                    "/ja/", "/de/", "/fi/", "/fr/", "/f/", "/pt-br/", "/uk/", "/he/", "/tr/", "/vi/", "/sv/", "/lt/", 
                    "/pl/", "/hu/", "/ko/", "/da/", "/zh/", "/cs/", "/nl/", "/it/", "/el/", "/pt/", "/th/", "/id/"]
    unwantedLanguages = ["/es", "/de", "/ja", "/fr", "/zh", "/pl", "/ru", "/nl", "/uk", "/ko", "/it", "/hu", "/sv", 
                        "/cs", "/ms", "/da"]
    unwantedExtensions = ["jpg", "png", "gif", "pdf"]
                        
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
        if link.split('.')[-1:][0] in unwantedExtensions:
            continue
        
        # Wiki-specific rules
        if any(tag in link for tag in unwantedTags):
            continue
        if link[-3:] in unwantedLanguages or link[-6:] == "/pt-br":
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
        
        # Ignore already visited URLs
        if redis.hasBeenVisited(links[index]):
            continue
            
        # Link has passed through all filters and is suitable to be appended to queue
        redis.addToQueue(links[index])
            
            
def processingQueue():
    '''
    Checks if Celery worker still has active tasks. If so, returns the list of tasks.
    '''
    if activeTasksDict := app.control.inspect().active():
        return list(activeTasksDict.items())[0][1]
    else:
        return 0