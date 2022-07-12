import psycopg2
from psycopg2 import sql
from utils import databaseConnectionParamaters

def countMethod(tableName, userInput):    
    '''
    Accepts user input as a string.
    Returns a list of search results that take the form:
        (Page's title, # of occurrences of user's input found on page)
    Uses Python's standard library count() method from the string object as the 
        search 'algorithm'.
    Serves as a benchmark to compare against more sophisticated algorithms.
    '''
    # Read website data into the program and search for occcurrences of user input
    searchResults = {}
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    databaseCursor.execute(sql.SQL("SELECT * FROM {};").format(sql.Identifier(tableName)))
    rows = databaseCursor.fetchall()
    
    for row in rows:
        # Only append to results if webpage has at least one occurrence of user input
        if inputOccurrences := (row[2].lower()).count((userInput).lower()):
            searchResults[row[1]] = inputOccurrences
            
    # Sort results in decreasing order of occurrences of user input on pages
    searchResultsSorted = sorted(searchResults.items(), key=lambda x: x[1], reverse=True)
    return(searchResultsSorted)