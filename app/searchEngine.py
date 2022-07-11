from psycopg2 import sql

def countMethod(databaseConnection, tableName, userInput):    
    '''
    Accepts user input as a string.
    Returns a list of search results that take the form:
        (Page's title, # of occurrences of user's input found on page)
    '''
    # Read website data into the program and search for occcurrences of user input
    searchResults = {}
    cursor = databaseConnection.cursor()
    cursor.execute(sql.SQL("SELECT * FROM {};").format(sql.Identifier(tableName)))
    rows = cursor.fetchall()
    for row in rows:
        inputOccurrences = (row[2].lower()).count((userInput).lower())
        # Only append to results if webpage has at least one occurrence of user input
        if inputOccurrences > 0:
            searchResults[row[1]] = inputOccurrences
            
    # Sort results in decreasing order of occurrences of user input on pages
    searchResultsSorted = sorted(searchResults.items(), key=lambda x: x[1], reverse=True)
    return(searchResultsSorted)