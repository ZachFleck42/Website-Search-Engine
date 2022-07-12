import psycopg2
import searchEngine
import sys
import time
import utils
from crawler import crawlWebsite
from psycopg2 import sql


if __name__ == "__main__":
    # Check that the program was called properly
    if not utils.checkValidUsage():
        sys.exit()
        
    # Initialize important variables
    initialURL = sys.argv[1]
    maxDepth = int(sys.argv[2])
    tableName = utils.getTableName(initialURL)
    skipDataCollection = 0

    # If a table already exists for the domain, check with user on how to proceed
    if utils.tableExists(tableName):
        useExistingDataAnswer = input("Database for domain already exists. Use existing data? (y/n): ")
        print("--------------------")
        if useExistingDataAnswer.lower() == 'y':        # If using existing data, no need to crawl website
            skipDataCollection = 1
        elif useExistingDataAnswer.lower() == 'n':      # If not using existing data, drop the table
            utils.dropTable(tableName)
            
    # If database table doesn't exist (or was deleted), crawl the website and collect data
    if not skipDataCollection:
        timestampCrawlerStart = time.time()
        webpageVisitCount = crawlWebsite(initialURL, maxDepth, tableName)
        timestampCrawlerEnd = time.time()
        print("Website successfully crawled and data appended to database.")
        print(f"Total number of webpages visited: {webpageVisitCount}")
        print(f"It took {(timestampCrawlerEnd - timestampCrawlerStart):.2f} seconds to crawl the website.")

    # Allow user to search for terms until program terminated
    while True:
        print("--------------------")
        # Get user input for search term. Allow exiting program via 'x' command
        userInput = input("Enter search term, or enter 'x' to exit: ")
        if userInput.lower() == 'x':
            sys.exit()
        
        # Search the website for the user's input and record how long the search takes
        timestampSearchStart = time.time()
        searchResults = searchEngine.countMethod(tableName, userInput)
        timestampSearchEnd = time.time()
        
        # Print search results
        print(f'Top 10 Results for search of "{userInput}":')
        for result in searchResults[0:10]:
            print(result)
        print(f"Search took {((timestampSearchEnd - timestampSearchStart) * 1000):.2f} milliseconds.")