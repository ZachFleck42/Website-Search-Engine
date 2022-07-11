import psycopg2
import sys
import time
from psycopg2 import sql
from urllib.parse import urlparse

from crawler import crawlWebsite
from utils import checkValidUsage
from utils import tableExists

# Define database connection parameters and HTML request headers
databaseConnectionParamaters = {"host": "app", "database": "searchenginedb", "user": "postgres", "password": "postgres"}

# Store the initial URL as a global variable for reference across functions
INITIAL_URL = (sys.argv[1]).rstrip('/')

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
    # Check that the program was called properly
    if not checkValidUsage():
        sys.exit()
    
    # Create a name for the SQL database table
    pageHost = (urlparse(INITIAL_URL).hostname).lower()
    if pageHost[0:4] == "www.":
        tableName = pageHost[4:].split('.', 1)[0]
    else:
        tableName = pageHost.split('.', 1)[0]
    
    # Connect to the database and obtain a cursor
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    cursor = databaseConnection.cursor()

    # If a table already exists for the domain, check in with user
    if tableExists(databaseConnection, tableName):
        temp = input("Database for domain already exists. Create new one? (y/n): ")
        if temp.lower() == 'n':     # If using existing data, skip right to search
            pass
        if temp.lower() == 'y':     # If re-obtaining data, drop old table
            cursor.execute(sql.SQL("DROP TABLE {};")
                    .format(sql.Identifier(tableName)))
            databaseConnection.commit()
            cursor.execute(sql.SQL("CREATE TABLE {} (page_url VARCHAR, page_title VARCHAR, page_text VARCHAR);")
                    .format(sql.Identifier(tableName)))
            
            # Crawl the website and store data in database
            print("--------------------")
            webpageVisitCount = crawlWebsite(databaseConnection, tableName, INITIAL_URL)
            databaseConnection.commit()
    else:
        cursor.execute(sql.SQL("CREATE TABLE {} (page_url VARCHAR, page_title VARCHAR, page_text VARCHAR);")
                    .format(sql.Identifier(tableName)))
        
        # Crawl the website and store data in database
        print("--------------------")
        webpageVisitCount = crawlWebsite(databaseConnection, tableName, INITIAL_URL)
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