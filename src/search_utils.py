from ahocorapy.keywordtree import KeywordTree
from src.database_utils import fetchAllData
from src.search_algorithms.boyer_moore import BMsearch
from src.search_algorithms.knuth_morris_pratt import KMPsearch
from src.search_algorithms.robin_karp import RKsearch
from time import time


def runSearch(tableName, userInput, searchMethod):
    '''
    Parent function for running a search for userInput in tableName.
    Also allows for the selection of one of five different search methods.
    Returns a sorted list of lists of length numberOfResults, taking the form:
        (numberOfMatches, pageURL, pageTitle)
    '''
    # Read website data into the program from database
    startSearchTime = time()
    websiteData = fetchAllData(tableName)
    needle = userInput.lower()
    
    # Keep track of page titles to prevent duplicate entries caused by redirects
    searchTitles = []
        
    # Store the search results in a list of lists
    searchResults = []
    for pageData in websiteData:
        pageURL = pageData[0]
        pageTitle = pageData[1]
        pageDesc = pageData[2]
        haystack = pageData[3].lower()
        
        numberOfMatches = 0
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
        
        if numberOfMatches > 0 and pageTitle not in searchTitles:
            searchResults.append((numberOfMatches, pageURL, pageTitle))
            searchTitles.append(pageTitle)
            
    # Sort and return the list of results
    searchResultsSorted = (sorted(searchResults, reverse=True))
    searchTime = time() - startSearchTime
    return(searchResultsSorted, searchTime)