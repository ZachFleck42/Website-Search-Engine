from ahocorapy.keywordtree import KeywordTree
from database_utils import fetchAllData
from search_algorithms.boyer_moore import BMsearch
from search_algorithms.robin_karp import RKsearch


def runSearch(tableName, userInput, searchMethod=1):
    '''
    Parent function for running a search for userInput in tableName.
    Also allows for the selection of one of five different search methods 
        (default is python str.count() method)
    Returns a sorted list of results, each taking the form:
        ("pageTitle", No. of occurrences of userInput on page)
    '''
    # Read website data into the program from database
    rows = fetchAllData(tableName)
    
    # Store the search results in a dictionary
    searchResults = {}
    for row in rows:
        results = 0
        if searchMethod == 1:       # Search method is Python str.count() method
            results = (row[2].lower()).count((userInput).lower())
        elif searchMethod == 2:     # Search method is Boyer-Moore algorithm
            results = len(BMsearch(userInput.lower(), row[2].lower()))
        elif searchMethod == 3:     # Search method is Aho-Corasick algorithm
            kwtree = KeywordTree(case_insensitive=True)
            kwtree.add(userInput)
            kwtree.finalize()
            if resultsFound := kwtree.search_all(row[2]):
                results = sum(1 for result in resultsFound)
        elif searchMethod == 4:      # Search method is Robin-Karp algorithm
            results = len(RKsearch(userInput.lower(), row[2].lower()))
        
        # Append results to the dictionary
        searchResults[row[1]] = results
            
    # Sort and return the list of results
    searchResultsSorted = sorted(searchResults.items(), key=lambda x: x[1], reverse=True)
    return(searchResultsSorted)