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
        print(f"Crawled {webpageVisitCount} pages in {((stopCrawlTime - startCrawlTime) - 5):.2f} seconds.")

    print("--------------------")
    # Begin searching the website
    while True:
        # Get user input for which search method to use
        searchMethod = input(f"Which search method would you like to use?\n(1) Python str.count()\n(2) Boyer-Moore\n(3) Knuth-Morris-Pratt\n(4) Robin-Karp\n(5) Aho-Corasick\nInput: ")
        if searchMethod.lower() == 'x':
            sys.exit()
            
        # Get user input for search term
        searchTerm = input("Enter search term, or 'x' to exit: ")
        if searchTerm.lower() == 'x':
            sys.exit()
        
        # Search the website for the user's input and record how long the search takes
        timestampSearchStart = time.time()
        searchResults = runSearch(tableName, searchTerm, int(searchMethod))
        timestampSearchEnd = time.time()
        
        # Print search results
        print("------------------------------------------")
        print(f'Top 10 Results for the search term "{searchTerm}":\n')
        for result in searchResults[0:10]:
            if foundOnPage := result[1]: 
                print(f"{result[0]:<40}", end='')
                print(f"{foundOnPage} matches")
                
        
        print(f"\nSearch took {((timestampSearchEnd - timestampSearchStart) * 1000):.2f} milliseconds.")
        print("--------------------")