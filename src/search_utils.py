from ahocorapy.keywordtree import KeywordTree
from src.database_utils import fetchAllData
from src.search_algorithms.boyer_moore import BMsearch
from src.search_algorithms.knuth_morris_pratt import KMPsearch
from src.search_algorithms.robin_karp import RKsearch
from time import time


def runSearch(tableName, userInput, searchMethod=1):
    '''
    Parent function for running a search for userInput in tableName.
    Also allows for the selection of one of five different search methods 
        (default is python str.count() method)
    Returns a sorted list of results, each taking the form:
        ("pageTitle", No. of occurrences of userInput on page)
    '''
    # Read website data into the program from database
    startSearchTime = time()
    rows = fetchAllData(tableName)
    needle = userInput.lower()
    
    # Store the search results in a dictionary
    searchResults = []
    for row in rows:
        numberOfMatches = 0
        haystack = row[3]
        if searchMethod == "COUNT":       # Search method is Python str.count() method
            numberOfMatches = (haystack.count(needle))
        elif searchMethod == "BM":     # Search method is Boyer-Moore algorithm
            numberOfMatches = len(BMsearch(needle, haystack))
        elif searchMethod == "KMP":     # Search method is Knuth-Morris-Pratt algorithm
            numberOfMatches = len(KMPsearch(needle, haystack))
        elif searchMethod == "RK":     # Search method is Robin-Karp algorithm
            numberOfMatches = len(RKsearch(needle, haystack))
        elif searchMethod == "AC":     # Search method is Aho-Corasick algorithm
            kwtree = KeywordTree(case_insensitive=True)
            kwtree.add(needle)
            kwtree.finalize()
            if resultsFound := kwtree.search_all(haystack):
                numberOfMatches = sum(1 for result in resultsFound)
        
        # Append results to the dictionary
        pageURL = row[0]
        pageTitle = row[1]
        if numberOfMatches:
            searchResults.append ((numberOfMatches, pageURL, pageTitle))
            
    # Sort and return the list of results
    searchResultsSorted = sorted(searchResults, reverse=True)
    searchTime = time() - startSearchTime
    return(searchResultsSorted, searchTime)