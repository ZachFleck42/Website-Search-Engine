import psycopg2
import requests
import sys
import time
from bs4 import BeautifulSoup
from psycopg2 import sql
from urllib.parse import urlparse

# Create a queue of URLs to visit and collect data from.
# Each URL will also have a corresponding 'depth', or number of links removed from the original URL.
# Thus, the queue will be a list of tuples in the form (string URL, int Depth)
urls = []

# Store the initial URL as a global variable for reference across functions
INITIAL_URL = (sys.argv[1]).rstrip('/')

# Define a 'maximum depth', or how far removed from the main URL the program should explore
MAX_DEPTH = int(sys.argv[2])

# Create a list of already-visited links to prevent visiting the same page twice
visitedLinks = []


def tableExists(DbConnection, tableName):
    '''
    Accepts a database connection and a table name to check.
    If table exists in the databse, function returns True. Returns false otherwise.
    '''
    cur = DbConnection.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tableName.replace('\'', '\'\'')))
    if cur.fetchone()[0] == 1:
        cur.close()
        return True

    cur.close()
    return False


def getLinks(pageURL, parsedPage):
    '''
    Accepts a webpage in the form of a 'response object' from the Requests package.
    Returns a list of cleaned links (as strings) discovered on that webpage.
    Links are 'cleaned', meaning page anchor, email address, and telephone links
        are removed. Internal links are expanded to full URLs. Previously-visited
        URLs, URLs currently in the queue, and links to different domains are also removed.
    '''
    # Find all valid links (not NoneType) from the <a> tags on the webpage
    links = []
    for link in parsedPage.find_all('a'):
        if (temp := link.get('href')):
            links.append(temp)

    # 'Clean' the links (see function docstring)
    linksClean = []
    initialHost = (urlparse(INITIAL_URL)).hostname
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

        # Expand internal links
        parsedURL = urlparse(pageURL)
        if link[0] == '/':
            links[index] = parsedURL.scheme + "://" + parsedURL.hostname + link
        
        # Expand internal links
        linkHost = (urlparse(links[index])).hostname
        if linkHost is None:
            links[index] = parsedURL.scheme + "://" + parsedURL.hostname + parsedURL.path + "/" + link
            linkHost = parsedURL.hostname
            
        # Ignore links to other domains
        if initialHost != linkHost:
            continue
        
        # Ignore links that end with unwanted extensions
        if link[-4:] == ".pdf":
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
        linksClean.append(links[index])

    # Remove any duplicate links in the list and return
    return list(set(linksClean))
    
def crawlWebsite(databaseCursor):
    startTime = time.time()         # Start timing how long program takes to run
    webpageVisitCount = 0
    for url in urls:
        pageURL = url[0]

        # Append current URL to 'visitedLinks' list to prevent visiting again later
        visitedLinks.append(pageURL)
        webpageVisitCount += 1

        # Use Requests package to obtain a 'Response' object from the webpage,
        # containing page's HTML, connection status, and other useful info.
        print(f"Attempting to connect to URL: {pageURL}")
        pageResponse = requests.get(pageURL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'})

        # Perform error checking on the URL connection.
        # If webpage can't be properly connected to, an error is raised and
        # program skips to next url in the queue.
        pageStatus = pageResponse.status_code
        if pageStatus != 200:
            print(f"ERROR: {pageURL} could not be accessed (Response code: {pageStatus}")
            print("Continuing...")
            print("--------------------")
            continue
        else:
            print("Connected successfully. ")
            
        # Collect data from webpage
        parsedPage = BeautifulSoup(pageResponse.text, 'html.parser')
        pageTitle = parsedPage.title.string
        pageText = parsedPage.get_text()
        
        # Append data to database
        databaseCursor.execute(
            sql.SQL("INSERT INTO {} VALUES (%s, %s, %s)")
            .format(sql.Identifier(tableName)),
            [pageURL, pageTitle, pageText])

        # If the current webpage is not at MAX_DEPTH, get a list of links found
        # in the page's <a> tags. Links will be 'cleaned' (see function docstring)
        if url[1] < MAX_DEPTH:
            print("Finding links on page...")
            pageLinks = getLinks(pageURL, parsedPage)
            for link in pageLinks:
                urls.append((link, url[1] + 1))
            print("Links appended to queue: ")
            print(f"{pageLinks}")
            
        print("--------------------")

    print("All URLs visited and data added to database.")
    print(f"Total number of webpages visited: {webpageVisitCount}")
    print(f"Program took {(time.time() - startTime):.2f} seconds to crawl the domain.")
        
    return webpageVisitCount
    

if __name__ == "__main__":
    # Check for valid number of arguments (2) in the script call.
    if (len(sys.argv) != 3):
        print("FATAL ERROR: Improper number of arguments. "
              "Please call program as: 'python app.py <URL> <MAX_DEPTH>")
        sys.exit()
    else:
        urls.append((INITIAL_URL, 0))   # Initial URL has a depth of 0
        pageHost = (urlparse(INITIAL_URL).hostname).lower()
        
    # Connect to a SQL database and create a table for the domain
    if pageHost[0:4] == "www.":
        tableName = pageHost[4:].split('.', 1)[0]
    else:
        tableName = pageHost.split('.', 1)[0]
    
    conn = psycopg2.connect(host='app', database='searchenginedb', user='postgres', password='postgres')
    cur = conn.cursor()

    # If a table already exists for the domain, check in with user
    if tableExists(conn, tableName):
        temp = input("Database for domain already exists. Create new one? (y/n): ")
        if temp.lower() == 'n':
            pass
        if temp.lower() == 'y':
            cur.execute(sql.SQL("DROP TABLE {}")
                    .format(sql.Identifier(tableName)))
            cur.execute(sql.SQL("CREATE TABLE {} (page_url VARCHAR, page_title VARCHAR, page_text VARCHAR)")
                    .format(sql.Identifier(tableName)))
            
            webpageVisitCount = crawlWebsite(cur)
    else:
        cur.execute(sql.SQL("CREATE TABLE {} (page_url VARCHAR, page_title VARCHAR, page_text VARCHAR)")
                    .format(sql.Identifier(tableName)))
                   
        webpageVisitCount = crawlWebsite(cur)

    # Commit changes to database
    conn.commit()
    cur.close()
    conn.close()

    while True:
        userInput = input("What would you like to search?: ")
        if userInput.lower() == "exit":
            sys.exit()
        startTime2 = time.time()
        
        conn = psycopg2.connect(host='app', database='searchenginedb', user='postgres', password='postgres')
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT * FROM {};").format(sql.Identifier(tableName)))
        rows = cur.fetchall()

        searchResults = {}
        for row in rows:
            inputOccurrences = (row[2].lower()).count((userInput).lower())
            if inputOccurrences > 0:
                searchResults[row[1]] = inputOccurrences
                
        searchResultsSorted = sorted(searchResults.items(), key=lambda x: x[1], reverse=True)

        for thing in searchResultsSorted:
            print(thing)
        
        print(f'Program took {(time.time() - startTime2):.4f} seconds to search for "{userInput}"')
        