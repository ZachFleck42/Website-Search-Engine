import psycopg2
import requests
import sys
import time
from bs4 import BeautifulSoup
from psycopg2 import sql
from urllib.parse import urlparse

# Define database connection parameters and HTML request headers
databaseConnectionParamaters = {"host": "app", "database": "searchenginedb", "user": "postgres", "password": "postgres"}
requestHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

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


def tableExists(databaseConnection, tableName):
    '''
    Accepts a database connection and a table name to check.
    If table exists in the databse, function returns True. Returns false otherwise.
    '''
    cursor = databaseConnection.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tableName.replace('\'', '\'\'')))
    if cursor.fetchone()[0] == 1:
        return True

    return False


def cleanLinks(links, pageURL):
    '''
    Accepts a list of links and the URL of the page they were found on.
    Returns the 'cleaned' list of links.
    '''
    # 'Clean' the links (see function docstring)
    cleanedLinks = []
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
        
        # Ignore links that end with unwanted extensions
        unwantedExtensions = ["jpg", "png", "gif", "pdf"]
        if link.split('.')[-1:][0] in unwantedExtensions:
            continue
        
        # Wiki-specific rules
        unwantedTags = ["/Category:", "/File:", "/Talk:", "/User", "/Blog:", "/User_blog:", "/Special:", "/Template:", "/Template_talk:", "Wiki_talk:", "/Help:", "/Source:", "/ru/", "/es/", "/ja/", "/de/", "/fi/", "/fr/", "/f/"]
        unwantedLanguages = ["/es", "/de", "/ja", "/fr", "/zh", "/pl", "/ru", "/nl", "/uk", "/ko", "/it", "/hu", "/sv", "/cs", "/ms", "/da"]
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


def getLinks(pageURL, parsedPage):
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
    cleanedLinks = cleanLinks(links, pageURL)
    return cleanedLinks


def collectDataFromPage (databaseConnection, tableName, pageURL, parsedPage):
    '''
    Accepts a database connection, the name of a table within that database, the
        URL of a webpage, and the parsed webpage object from BeautifulSoup
    Appends specified data the database. Returns nothing.
    '''
    pageTitle = parsedPage.title.string
    pageText = parsedPage.get_text()
    
    cursor = databaseConnection.cursor()
    cursor.execute(sql.SQL("INSERT INTO {} VALUES (%s, %s, %s);")
                .format(sql.Identifier(tableName)),
                [pageURL, pageTitle, pageText])
                
    
def crawlWebsite(databaseConnection, tableName):
    '''
    Accepts a database connection and the name of a table within the database.
    Returns a list of webpages visited during the function's call.
    Function also calls a seperate data-collection function for each page. 
        Functions are kept seperate for easy modification in other programs.
    '''
    timestampCrawlStart = time.time()
    webpageVisitCount = 0
    for url in urls:
        pageURL = url[0]

        # Append current URL to 'visitedLinks' list to prevent visiting again later
        visitedLinks.append(pageURL)
        webpageVisitCount += 1

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
            continue
        else:
            print("Connected successfully.")
            parsedPage = BeautifulSoup(pageResponse.text, 'html.parser')
            
        # Collect data from the webpage
        print(f"Collecting data from page...")
        collectDataFromPage(databaseConnection, tableName, pageURL, parsedPage)
        print("Collected data successfully. Continuing...")

        # If the current webpage is not at MAX_DEPTH, get a list of links found
        # in the page's <a> tags. Links will be 'cleaned' (see function docstring)
        if url[1] < MAX_DEPTH:
            print("Finding links on page...")
            if pageLinks := getLinks(pageURL, parsedPage):
                for link in pageLinks:
                    urls.append((link, url[1] + 1))
                print("Links appended to queue: ", end='')
                print(f"{pageLinks}")
                print("Continuing...")
            else:
                print("No unique links found.")
                
        # URL done procesing, proceed to next in queue
        print("--------------------")   
    
    # Print log info
    print("All URLs visited and data added to database.")
    print(f"Total number of webpages visited: {webpageVisitCount}")
    print(f"It took {(time.time() - timestampCrawlStart):.2f} seconds to crawl the domain.")
    
    return webpageVisitCount
    

def runSearch(databaseConnection, userInput):
    '''
    Accepts user input as a string.
    Returns a list of search results that take the form:
        (Page's title, # of occurrences of user's input found on page)
    '''
    # Read website data into the program and search for occcurrences of user input
    searchResults = {}
    cursor = databaseConnection.cursor()
    cursor.execute(sql.SQL("SELECT * FROM {};").format(sql.Identifier(tableName)))
    rows = cursor.fetchall()
    for row in rows:
        inputOccurrences = (row[2].lower()).count((userInput).lower())
        # Only append to results if webpage has at least one occurrence of user input
        if inputOccurrences > 0:
            searchResults[row[1]] = inputOccurrences
            
    # Sort results in decreasing order of occurrences of user input on pages
    searchResultsSorted = sorted(searchResults.items(), key=lambda x: x[1], reverse=True)
    return(searchResultsSorted)


if __name__ == "__main__":
    # Check for valid number of arguments (2) in the script call.
    if (len(sys.argv) != 3):
        print("FATAL ERROR: Improper number of arguments. "
              "Please call program as: 'python app.py <URL> <MAX_DEPTH>")
        sys.exit()
    else:
        urls.append((INITIAL_URL, 0))   # Initial URL has a depth of 0
        pageHost = (urlparse(INITIAL_URL).hostname).lower()
        
    # Create a name for the SQL database table
    if pageHost[0:4] == "www.":
        tableName = pageHost[4:].split('.', 1)[0]
    else:
        tableName = pageHost.split('.', 1)[0]
    
    # Connect to the database and obtain a cursor
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()

    # If a table already exists for the domain, check in with user
    if tableExists(databaseConnection, tableName):
        temp = input("Database for domain already exists. Create new one? (y/n): ")
        if temp.lower() == 'n':     # If using existing data, skip right to search
            pass
        if temp.lower() == 'y':     # If re-obtaining data, drop old table
            databaseCursor.execute(sql.SQL("DROP TABLE {};")
                    .format(sql.Identifier(tableName)))
            databaseConnection.commit()
            databaseCursor.execute(sql.SQL("CREATE TABLE {} (page_url VARCHAR, page_title VARCHAR, page_text VARCHAR);")
                    .format(sql.Identifier(tableName)))
            
            # Crawl the website and store data in database
            print("--------------------")
            webpageVisitCount = crawlWebsite(databaseConnection, tableName)
            databaseConnection.commit()
    else:
        databaseCursor.execute(sql.SQL("CREATE TABLE {} (page_url VARCHAR, page_title VARCHAR, page_text VARCHAR);")
                    .format(sql.Identifier(tableName)))
        
        # Crawl the website and store data in database
        print("--------------------")
        webpageVisitCount = crawlWebsite(databaseConnection, tableName)
        databaseConnection.commit()

    # Allow user to search for as many terms as they like
    while True:
        print("--------------------")
        # Get user input for search term. Allow exiting program via '/exit' command
        userInput = input('Enter search term: ')
        if userInput.lower() == "/exit":
            sys.exit()
        
        # Search the website for the user's input and record how long the search takes
        timestampSearchStart = time.time()
        searchResults = runSearch(databaseConnection, userInput)
        timestampSearchEnd = time.time()
        
        # Print results
        print(f'Top 10 Results for search of "{userInput}":')
        for result in searchResults[0:10]:
            print(result)
        print(f"Search took {((timestampSearchEnd - timestampSearchStart) * 1000):.2f} milliseconds.")