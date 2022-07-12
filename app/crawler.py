import psycopg2
import requests
from bs4 import BeautifulSoup
from celery_app import app
from utils import createTable
from psycopg2 import sql
from urllib.parse import urlparse

# Define HTML headers
requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
databaseConnectionParamaters = {"host": "app", "database": "searchenginedb", "user": "postgres", "password": "postgres"}

# Create a queue of URLs to visit and collect data from.
# Each URL will also have a corresponding 'depth', or number of links removed from the original URL.
# Thus, the queue will be a list of tuples in the form (string URL, int Depth)
urls = []

# Create a list of already-visited links to prevent visiting the same page twice
visitedLinks = []

def cleanLinks(links, pageURL, initialURL):
    '''
    Accepts a list of links and the URL of the page they were found on.
    Returns the 'cleaned' list of links.
    '''
    # 'Clean' the links (see function docstring)
    cleanedLinks = []
    initialHost = (urlparse(initialURL)).hostname
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
            
        # Ignore links to other domains
        if initialHost != linkHost:
            continue
        
        # Ignore all links to previously-visited URLs
        if links[index] in visitedLinks:
            continue

        # Ignore links that are already in the queue
        inQueue = False
        for url in urls:
            if url[0] == links[index]:
                inQueue = True
                break
        if inQueue:
            continue

        # All filters passed; link is appended to 'clean' list
        cleanedLinks.append(links[index])

    # Remove any duplicate links in the list and return it
    return list(set(cleanedLinks))


def getLinks(pageURL, parsedPage, initialURL):
    '''
    Accepts a webpage in the form of a 'response object' from the Requests package.
    Returns a list of cleaned links (as strings) discovered on that webpage.
    '''
    # Find all valid links (not NoneType) from the <a> tags on the webpage
    links = []
    for reference in parsedPage.find_all('a'):
        if (link := reference.get('href')):
            links.append(link)

    # Clean the links and return the list
    cleanedLinks = cleanLinks(links, pageURL, initialURL)
    return cleanedLinks


def collectDataFromPage (tableName, pageURL, parsedPage):
    '''
    Accepts a database connection, the name of a table within that database, the
        URL of a webpage, and the parsed webpage object from BeautifulSoup
    Appends specified data the database. Returns nothing.
    '''
    pageTitle = parsedPage.title.string
    pageText = parsedPage.get_text()
    
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    cursor = databaseConnection.cursor()
    cursor.execute(sql.SQL("INSERT INTO {} VALUES (%s, %s, %s);")
        .format(sql.Identifier(tableName)),
        [pageURL, pageTitle, pageText])
        
    databaseConnection.commit()
    databaseConnection.close()
        
                
@app.task        
def processURL(initialURL, maxDepth, tableName, urlTuple):
    '''
    To do lol
    '''
    pageURL = urlTuple[0]
    # Append current URL to 'visitedLinks' list to prevent visiting again later
    visitedLinks.append(pageURL)

    # Use Requests package to obtain a 'Response' object from the webpage,
    # containing page's HTML, connection status, and other useful info.
    print(f"Attempting to connect to URL: {pageURL}...")
    pageResponse = requests.get(pageURL, headers=requestHeaders)

    # Perform error checking on the URL connection.
    # If webpage can't be properly connected to, an error is raised and
    # program skips to next url in the queue.
    pageStatus = pageResponse.status_code
    if pageStatus != 200:
        print(f"ERROR: {pageURL} could not be accessed (Response code: {pageStatus})")
        print("--------------------")
        return
    else:
        print("Connected successfully.")
        parsedPage = BeautifulSoup(pageResponse.text, 'html.parser')
        
    # Collect data from the webpage
    print(f"Collecting data from page...")
    collectDataFromPage(tableName, pageURL, parsedPage)
    print("Collected data successfully.")

    # If the current webpage is not at MAX_DEPTH, get a list of links found
    # in the page's <a> tags. Links will be 'cleaned' (see function docstring)
    if urlTuple[1] < maxDepth:
        print("Finding links on page...")
        if pageLinks := getLinks(pageURL, parsedPage, initialURL):
            for link in pageLinks:
                urls.append((link, urlTuple[1] + 1))
            print("Links appended to queue: ", end='')
            print(f"{pageLinks}")
        else:
            print("No unique links found.")
            
    # URL done procesing, proceed to next in queue
    print("Continuing...")
    print("--------------------")
    
    
def crawlWebsite(initialURL, maxDepth, tableName):
    '''
    Accepts a database connection and the name of a table within the database.
    Returns a list of webpages visited during the function's call.
    Function also calls a seperate data-collection function for each page. 
        Functions are kept seperate for easy modification in other programs.
    '''
    # Create a table for the website in the database
    createTable(tableName)
    
    # Begin processing the queue
    webpageVisitCount = 0
    urls.append((initialURL, 0))
    for url in urls:
        task = processURL.delay(initialURL, maxDepth, tableName, url)
        webpageVisitCount += 1
    
    return webpageVisitCount