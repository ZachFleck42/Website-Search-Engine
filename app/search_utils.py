from ahocorapy.keywordtree import KeywordTree
from database_utils import fetchAllData
from search_algorithms.boyer_moore import BMsearch
from search_algorithms.knuth_morris_pratt import KMPsearch
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
    needle = userInput.lower()
    rows = fetchAllData(tableName)
    
    # Store the search results in a dictionary
    searchResults = {}
    for row in rows:
        needleOccurrences = 0
        haystack = row[2]
        if searchMethod == 1:       # Search method is Python str.count() method
            needleOccurrences = (haystack.count(needle))
        elif searchMethod == 2:     # Search method is Boyer-Moore algorithm
            needleOccurrences = len(BMsearch(needle, haystack))
        elif searchMethod == 3:     # Search method is Knuth-Morris-Pratt algorithm
            needleOccurrences = len(KMPsearch(needle, haystack))
        elif searchMethod == 4:     # Search method is Robin-Karp algorithm
            needleOccurrences = len(RKsearch(needle, haystack))
        elif searchMethod == 5:     # Search method is Aho-Corasick algorithm
            kwtree = KeywordTree(case_insensitive=True)
            kwtree.add(needle)
            kwtree.finalize()
            if resultsFound := kwtree.search_all(haystack):
                needleOccurrences = sum(1 for result in resultsFound)
        
        # Append results to the dictionary
        pageTitle = row[1]
        searchResults[pageTitle] = needleOccurrences
            
    # Sort and return the list of results
    searchResultsSorted = sorted(searchResults.items(), key=lambda x: x[1], reverse=True)
    return(searchResultsSorted)