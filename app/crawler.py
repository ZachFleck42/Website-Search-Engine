import nltk
import re
import requests
from bs4 import BeautifulSoup
from collections import deque
from database_utils import appendData, createTable
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from urllib.parse import urlparse

requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
visitedURLs = set()
urls = deque([])

def crawlWebsite(initialURL, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an entire website.
    '''
    # Add the initial URL to the queue
    urls.append(initialURL)
    visitedCount = 0
    
    # Create a table in the database for the website
    createTable(databaseTable)
    
    # Make sure necessary text-processing files are present
    nltk.download('stopwords')
    nltk.download('punkt')
    
    # While there are still links in the queue...
    while urls:
        url = urls.popleft()
        processURL(url, databaseTable)
        visitedCount += 1
        
    # Return the total number of webpages visited
    return visitedCount
    

def processURL(url, databaseTable):
    '''
    Parent function for connecting to and scraping/storing data from an individual webpage.
    Returns 1 if page was processed without error.
    '''
    print(f"Processing {url} ...")
    visitedURLs.add(url)
    
    # Connect to the URL and get its HTML source
    print("Getting HTML...")
    if not (pageHTML := getHTML(url)):
        print(f"ERROR: Could not get HTML from {url}")
        return 0
    
    # Parse the page and scrape it for data and additional links
    print("Parsing page...")
    parsedPage = BeautifulSoup(pageHTML, 'html.parser')
    print("Scraping data...")
    pageData = scrapeData(parsedPage)

    # Append data to the database
    print("Appending data to database...")
    if not appendData(url, pageData[0], pageData[1], databaseTable):
        print(f"ERROR: Could not append data from {url}")
        return 0
        
    print("Appending links...")
    if pageLinks := getLinks(url, parsedPage):
        for link in pageLinks:
            urls.append(link)
    
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
    
    print("Pre-processing text...")
    processedText = preProcessText(pageText)
    
    return (pageTitle, processedText)
    
    
def preProcessText(pageText):
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
        return cleanLinks(links, url)
    else:
        return []


def cleanLinks(links, pageURL):
    '''
    Accepts a list of raw links/references pulled from a webpage's <a> tags.
    Passes links through a series of filters to prune unwanted links.
    Returns nothing. Instead directly appends suitable links to the queue.
    '''
    unwantedTags = ["/Category:", "/File:", "/Talk:", "/User", "/Blog:", "/User_blog:", "/Special:", "/Template:", 
                    "/Template_talk:", "Wiki_talk:", "/Help:", "/Source:", "/Forum:", "/Forum_talk:", "/ru/", "/es/", 
                    "/ja/", "/de/", "/fi/", "/fr/", "/f/", "/pt-br/", "/uk/", "/he/", "/tr/", "/vi/", "/sv/", "/lt/", 
                    "/pl/", "/hu/", "/ko/", "/da/"]
    unwantedLanguages = ["/es", "/de", "/ja", "/fr", "/zh", "/pl", "/ru", "/nl", "/uk", "/ko", "/it", "/hu", "/sv", 
                        "/cs", "/ms", "/da"]
    unwantedExtensions = ["jpg", "png", "gif", "pdf"]
              
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
            
        if links[index] in visitedURLs:
            continue
        
        if links[index] in urls:
            continue
            
        # Link has passed through all filters and is suitable to be appended to queue
        cleanedLinks.append(links[index])
    
    return list(set(cleanedLinks))
            
            
def currentlyProcessing():
    '''
    Checks if Celery worker still has active tasks. If so, returns the list.
    '''
    if activeTasksDict := app.control.inspect().active():
        return list(activeTasksDict.items())[0][1]
    else:
        return 0