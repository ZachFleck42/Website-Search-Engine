import nltk
import re
import src.redis_utils as redis_utils
import requests
from bs4 import BeautifulSoup
from celery import Celery
from src.database_utils import appendData, createTable
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from time import time
from urllib.parse import urlparse

requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
app = Celery('Search_Engine', broker='redis://redis:6379/1')
app.conf.result_backend = 'redis://redis:6379/1'


def crawlWebsite(initialURL, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an entire website.
    Initializes queue, database connections, and asset downloads.
    Returns the total number of webpages visited by the crawler.
    '''
    # Make sure necessary text-processing files are present
    nltk.download('stopwords')
    nltk.download('punkt')
    
    # Add the initial URL to the queue
    startCrawlTime = time()
    redis_utils.addToQueue(initialURL)
    
    # Create a table in the database for the website
    createTable(databaseTable)
    
    # While there are still links in the queue...
    while ((redis_utils.getQueueCount()) > 0) or (currentlyProcessing()):
        if url := redis_utils.popFromQueue():
            redis_utils.markVisited(url)
            print(f"Sending to Celery for processing: {url}")
            processURL.delay(url, databaseTable)
    
    # Return the total number of webpages visited and the time it took to crawl them
    webpageVisitCount = redis_utils.getVisitedCount()
    crawlTime = time() - startCrawlTime
    
    return (webpageVisitCount, crawlTime)
    
    
@app.task
def processURL(url, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an individual webpage.
    Returns 1 if page was processed without error.
    '''
    print(f"Processing {url}")
    
    # Connect to the URL and get its HTML source
    if not (pageHTML := getHTML(url)):
        print(f"ERROR: Could not get HTML from {url}")
        return 0
    
    # Parse the page and scrape it for data and additional links
    parsedPage = BeautifulSoup(pageHTML, 'html.parser')
    pageData = scrapeData(parsedPage)
    getLinks(url, parsedPage)
    
    # Append data to the database
    if not appendData(url, pageData, databaseTable):
        print(f"ERROR: Could not append data from {url}")
        return 0
    
    return 1


def getHTML(url):
    '''
    Connects to a URL, obtains a response, and returns the webpage's HTML if available.
    '''
    pageResponse = requests.get(url, headers=requestHeaders)
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
    pageDesc = str(parsedPage.find("meta", attrs={'name': 'description'}))[14:-21]
    if not pageDesc:
        pageDesc = "None"

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
        
        # Ignore already visited URLs
        if redis_utils.hasBeenVisited(links[index]):
            continue
            
        # Link has passed through all filters and is suitable to be appended to queue
        redis_utils.addToQueue(links[index])
            
            
def currentlyProcessing():
    '''
    Checks if Celery worker still has active tasks. If so, returns the list of tasks.
    '''
    if activeTasksDict := app.control.inspect().active():
        return list(activeTasksDict.items())[0][1]
    else:
        return 0