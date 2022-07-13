import sys
import time
from crawler import crawlWebsite
from database_utils import getTableName, tableExists, dropTable
from redis_utils import clearCache
from search_utils import runSearch


def checkValidUsage():
    '''Checks to make sure program was called properly. Exits if not.'''
    if (len(sys.argv) != 2):
        print("FATAL ERROR: Improper number of arguments.")
        print("Please call program as: 'python app.py URL")
        sys.exit()
        

if __name__ == "__main__":
    # Check that the program was called properly
    checkValidUsage()
    initialURL = sys.argv[1]
        
    # If a table already exists for the domain, check with user on how to proceed
    tableName = getTableName(initialURL)
    skippingDataCollection = 0
    if tableExists(tableName):
        useExistingDataAnswer = input("Database for domain already exists. Use existing data? (y/n): ")
        print("--------------------")
        if useExistingDataAnswer.lower() == 'y':        # If using existing data, no need to crawl website
            skippingDataCollection = 1
        elif useExistingDataAnswer.lower() == 'n':      # If not using existing data, drop the table
            clearCache()
            dropTable(tableName)
            
    # If database table doesn't exist (or was deleted), crawl the website and collect data
    if not skippingDataCollection:
        startCrawlTime = time.time()
        webpageVisitCount = crawlWebsite(initialURL, tableName)
        stopCrawlTime = time.time()
        print(f"Crawled {webpageVisitCount} pages in {stopCrawlTime - startCrawlTime} seconds.")

    # Begin searching the website
    while True:
        # Get user input for search term. Allow exiting program via 'x' command
        searchMethod = input(f"Which search method would you like to use?\n(1) Python .count() method\n(2) Boyer-Moore\n(3) Aho-Corasick\n(4) Robin-Karp\nInput: ")
        userInput = input("Enter search term, or 'x' to exit: ")
        if userInput.lower() == 'x':
            sys.exit()
        
        # Search the website for the user's input and record how long the search takes
        timestampSearchStart = time.time()
        searchResults = runSearch(tableName, userInput, int(searchMethod))
        timestampSearchEnd = time.time()
        
        # Print search results
        print("--------------------")
        print(f'Top 10 Results for search of "{userInput}":')
        for result in searchResults[0:10]:
            print(result)
        print(f"Search took {((timestampSearchEnd - timestampSearchStart) * 1000):.2f} milliseconds.")
        print("--------------------")