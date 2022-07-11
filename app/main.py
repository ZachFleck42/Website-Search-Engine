import psycopg2
import searchEngine
import sys
import time
import utils
from crawler import crawlWebsite
from psycopg2 import sql

# Define database connection parameters and HTML request headers
databaseConnectionParamaters = {"host": "app", "database": "searchenginedb", "user": "postgres", "password": "postgres"}

if __name__ == "__main__":
    # Check that the program was called properly
    if not utils.checkValidUsage():
        sys.exit()
        
    # Initialize important variables from program call
    initialURL = sys.argv[1]
    maxDepth = int(sys.argv[2])
    
    # Connect to the database and obtain a cursor
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    cursor = databaseConnection.cursor()

    # If a table already exists for the domain, check in with user
    tableName = utils.getTableName(initialURL)
    if utils.tableExists(databaseConnection, tableName):
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
        # Get user input for search term. Allow exiting program via 'x' command
        userInput = input('Enter search term, or enter "x" to exit: ')
        if userInput.lower() == "q":
            sys.exit()
        
        # Search the website for the user's input and record how long the search takes
        timestampSearchStart = time.time()
        searchResults = searchEngine.countMethod(databaseConnection, tableName, userInput)
        timestampSearchEnd = time.time()
        
        # Print search results
        print(f'Top 10 Results for search of "{userInput}":')
        for result in searchResults[0:10]:
            print(result)
        print(f"Search took {((timestampSearchEnd - timestampSearchStart) * 1000):.2f} milliseconds.")