import psycopg2
import requests
from bs4 import BeautifulSoup
from celery import Celery
from utils import createTable
from utils import databaseConnectionParamaters
from psycopg2 import sql
from urllib.parse import urlparse

app = Celery('Search_Engine',
             backend='rpc://',
             broker='amqp://rabbitmq')
             
def getHTML(url):
    print(f"Attempting to connect to URL: {url} ...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    pageResponse = requests.get(url, headers=headers)
    pageStatus = pageResponse.status_code
    
    if pageStatus != 200:
        print(f"ERROR: {url} could not be accessed (Response code: {pageStatus})")
        print("--------------------")
        return 0
    else:
        print("Connected successfully.")
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
    
    
def getLinks(url, parsedPage):
    # Find all valid links (not NoneType) from the <a> tags on the webpage
    links = []
    for reference in parsedPage.find_all('a'):
        if (link := reference.get('href')):
            links.append(link)

    # Clean the links and return the list
    cleanedLinks = cleanLinks(links, url)
    
    return cleanedLinks


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
            
        # Ignore links to other domains
        if initialHost != linkHost:
            continue

        # All filters passed; link is appended to 'clean' list
        cleanedLinks.append(links[index])

    # Remove any duplicate links in the list and return it
    return list(set(cleanedLinks))


def addNewLinksToQueue(links):
    pass


@app.task        
def crawlWebsite(url):
    # Connect to the website and get its HTML source
    pageHTML = getHTML(url)
    if not pageHTML:
        pass
    
    parsedPage = BeautifulSoup(pageHTML, 'html.parser')
    scrapeData(parsedPage)
    pageLinks = getLinks(url, parsedPage)
    
    addNewLinksToQueue(pageLinks)
    
    
def tempName(tableName):
    pass