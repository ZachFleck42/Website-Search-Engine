import psycopg2
import searchEngine
import sys
import time
from crawler import crawlWebsite
from psycopg2 import sql
from urllib.parse import urlparse
from utils import checkValidUsage
from utils import tableExists

# Define database connection parameters and HTML request headers
databaseConnectionParamaters = {"host": "app", "database": "searchenginedb", "user": "postgres", "password": "postgres"}

if __name__ == "__main__":
    # Check that the program was called properly
    if not checkValidUsage():
        sys.exit()
    else:
        initialURL = sys.argv[1]
        maxDepth = int(sys.argv[2])
    
    # Create a name for the SQL database table
    pageHost = (urlparse(initialURL).hostname).lower()
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
            
            # Crawl the website and store data in database
            print("--------------------")
            crawlWebsite(databaseConnection, tableName, initialURL, maxDepth)
            databaseConnection.commit()
    else:
        # Crawl the website and store data in database
        print("--------------------")
        crawlWebsite(databaseConnection, tableName, initialURL, maxDepth)
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
        searchResults = searchEngine.countMethod(databaseConnection, tableName, userInput)
        timestampSearchEnd = time.time()
        
        # Print results
        print(f'Top 10 Results for search of "{userInput}":')
        for result in searchResults[0:10]:
            print(result)
        print(f"Search took {((timestampSearchEnd - timestampSearchStart) * 1000):.2f} milliseconds.")