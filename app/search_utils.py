from ahocorapy.keywordtree import KeywordTree
from database_utils import fetchAllData
from search_algorithms.boyer_moore import BMsearch
from search_algorithms.robin_karp import RKsearch


def runSearch(tableName, userInput, searchMethod=1):
    # Read website data into the program from database
    rows = fetchAllData(tableName)
    
    # Store the search results in a dictionary
    searchResults = {}
    for row in rows:
        results = 0
        if searchMethod == 1:
            results = (row[2].lower()).count((userInput).lower())
        elif searchMethod == 2:
            results = len(BMsearch(userInput.lower(), row[2].lower()))
        elif searchMethod == 3:
            kwtree = KeywordTree(case_insensitive=True)
            kwtree.add(userInput)
            kwtree.finalize()
            if resultsFound := kwtree.search_all(row[2]):
                results = sum(1 for result in resultsFound)
        elif searchMethod == 4:
            results = len(RKsearch(userInput.lower(), row[2].lower()))
        
        searchResults[row[1]] = results
            
    searchResultsSorted = sorted(searchResults.items(), key=lambda x: x[1], reverse=True)
    return(searchResultsSorted)